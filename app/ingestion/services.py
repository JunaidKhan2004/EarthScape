import csv
import io
import random
from datetime import datetime, timedelta

from app.hdfs_sim.client import write_partitioned

SOURCE_TYPES = ["weather_station", "satellite", "environmental_sensor"]

FIELDS_BY_SOURCE = {
    "weather_station": ["station_id", "timestamp", "temperature_c", "humidity_pct", "pressure_hpa"],
    "satellite": ["satellite_id", "timestamp", "region", "cloud_cover_pct", "surface_temp_c"],
    "environmental_sensor": ["sensor_id", "timestamp", "co2_ppm", "pm2_5", "timestamp_recorded"],
}


def parse_csv_upload(file_stream, source_type: str) -> tuple[list[dict], dict]:
    """
    Parse an uploaded CSV file stream into a list of row dicts.

    Validates that required columns are present, drops exact-duplicate rows,
    and returns a report alongside the clean records so the caller can tell
    the user exactly what happened to their data rather than silently
    dropping anything.
    """
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type: {source_type}")

    text = io.TextIOWrapper(file_stream, encoding="utf-8")
    reader = csv.DictReader(text)

    if reader.fieldnames is None:
        raise ValueError("Uploaded file appears to be empty or not a valid CSV.")

    required_fields = FIELDS_BY_SOURCE[source_type]
    missing_columns = [f for f in required_fields if f not in reader.fieldnames]
    if missing_columns:
        raise ValueError(
            f"CSV is missing required column(s) for {source_type}: {', '.join(missing_columns)}. "
            f"Expected columns: {', '.join(required_fields)}"
        )

    raw_rows = [row for row in reader]
    if not raw_rows:
        raise ValueError("Uploaded file has no data rows.")

    seen = set()
    clean_rows = []
    duplicate_count = 0
    incomplete_count = 0

    for row in raw_rows:
        if any((row.get(f) or "").strip() == "" for f in required_fields):
            incomplete_count += 1
            continue

        key = tuple(row.get(f, "").strip() for f in required_fields)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        clean_rows.append(row)

    if not clean_rows:
        raise ValueError(
            f"No usable rows found: {incomplete_count} incomplete, {duplicate_count} duplicate "
            f"(out of {len(raw_rows)} total rows)."
        )

    report = {
        "total_rows": len(raw_rows),
        "valid_rows": len(clean_rows),
        "duplicate_rows": duplicate_count,
        "incomplete_rows": incomplete_count,
    }
    return clean_rows, report


def ingest_records(source_type: str, records: list[dict], dt: datetime = None) -> str:
    """Write parsed/generated records into the HDFS-sim raw zone. Returns file path."""
    return write_partitioned(source_type, records, dt=dt)


def generate_sample_batch(source_type: str, count: int = 20, dt: datetime = None) -> list[dict]:
    """Generate synthetic climate records for demo/testing (simulates real-time feed)."""
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type: {source_type}")

    dt = dt or datetime.utcnow()
    records = []

    for i in range(count):
        ts = (dt - timedelta(minutes=i)).isoformat()
        if source_type == "weather_station":
            records.append({
                "station_id": f"WS{random.randint(1, 20):03d}",
                "timestamp": ts,
                "temperature_c": round(random.uniform(15, 42), 1),
                "humidity_pct": round(random.uniform(20, 95), 1),
                "pressure_hpa": round(random.uniform(990, 1025), 1),
            })
        elif source_type == "satellite":
            records.append({
                "satellite_id": f"SAT{random.randint(1, 5):02d}",
                "timestamp": ts,
                "region": random.choice(["north", "south", "east", "west", "equatorial"]),
                "cloud_cover_pct": round(random.uniform(0, 100), 1),
                "surface_temp_c": round(random.uniform(-10, 45), 1),
            })
        else:
            records.append({
                "sensor_id": f"ENV{random.randint(1, 50):03d}",
                "timestamp": ts,
                "co2_ppm": round(random.uniform(380, 480), 1),
                "pm2_5": round(random.uniform(5, 150), 1),
                "timestamp_recorded": ts,
            })

    return records
