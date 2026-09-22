"""
Simulated Hadoop MapReduce jobs.

Real Hadoop MapReduce distributes map/reduce functions across cluster nodes
operating on HDFS blocks in parallel. Here we simulate the same map -> shuffle
-> reduce shape using Python's multiprocessing pool over the partitioned block
files produced by app.hdfs_sim, so swapping in real Hadoop Streaming jobs later
only means replacing `_map_block` / `_reduce_group` with actual mapper.py /
reducer.py scripts run via `hadoop jar hadoop-streaming.jar`.
"""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool

from app.config import Config
from app.hdfs_sim.client import list_all_blocks, read_blocks_as_dicts

METRIC_BY_SOURCE = {
    "weather_station": "temperature_c",
    "satellite": "surface_temp_c",
    "environmental_sensor": "co2_ppm",
}

GROUP_KEY_BY_SOURCE = {
    "weather_station": "station_id",
    "satellite": "region",
    "environmental_sensor": "sensor_id",
}

# Values outside this z-score are flagged as anomalies.
ANOMALY_Z_THRESHOLD = 2.5


def _map_block(args):
    """Map phase: read one block file, emit (group_key, metric_value) pairs.
    Rows with missing/non-numeric metric values are skipped (missing-data handling)."""
    block_path, source_type = args
    metric_field = METRIC_BY_SOURCE[source_type]
    group_field = GROUP_KEY_BY_SOURCE[source_type]

    rows = read_blocks_as_dicts([block_path])
    emitted = []
    for row in rows:
        raw_value = row.get(metric_field, "").strip()
        group_key = row.get(group_field, "unknown")
        if raw_value == "":
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        emitted.append((group_key, value, row.get("timestamp", "")))

    return emitted


def _shuffle(mapped_results: list[list[tuple]]) -> dict:
    """Shuffle phase: group emitted (key, value) pairs by key."""
    grouped = defaultdict(list)
    for emitted in mapped_results:
        for group_key, value, timestamp in emitted:
            grouped[group_key].append((value, timestamp))
    return grouped


def _reduce_group(group_key: str, values: list[tuple]) -> dict:
    """Reduce phase: compute stats + flag anomalies for one group's values."""
    nums = [v for v, _ in values]
    n = len(nums)
    mean = sum(nums) / n
    variance = sum((x - mean) ** 2 for x in nums) / n if n > 1 else 0.0
    stddev = variance ** 0.5

    anomalies = []
    if stddev > 0:
        for value, timestamp in values:
            z = (value - mean) / stddev
            if abs(z) >= ANOMALY_Z_THRESHOLD:
                anomalies.append({"value": value, "timestamp": timestamp, "z_score": round(z, 2)})

    return {
        "group_key": group_key,
        "count": n,
        "mean": round(mean, 2),
        "min": round(min(nums), 2),
        "max": round(max(nums), 2),
        "stddev": round(stddev, 2),
        "anomalies": anomalies,
    }


def run_pattern_anomaly_job(source_type: str, processes: int = 4) -> dict:
    """
    Full simulated MapReduce job: scans all raw blocks for a source type,
    computes per-group statistics and flags anomalies (values >= 2.5 std devs
    from the group mean). Writes result JSON into the processed zone and
    returns the summary dict.
    """
    if source_type not in METRIC_BY_SOURCE:
        raise ValueError(f"Unknown source_type: {source_type}")

    blocks = list_all_blocks(source_type)
    if not blocks:
        raise ValueError(f"No ingested data found for source_type={source_type}")

    map_inputs = [(block, source_type) for block in blocks]

    with Pool(processes=min(processes, len(map_inputs))) as pool:
        mapped_results = pool.map(_map_block, map_inputs)

    grouped = _shuffle(mapped_results)

    reduced = [_reduce_group(key, values) for key, values in grouped.items()]
    reduced.sort(key=lambda r: r["group_key"])

    total_anomalies = sum(len(r["anomalies"]) for r in reduced)
    result = {
        "source_type": source_type,
        "metric": METRIC_BY_SOURCE[source_type],
        "generated_at": datetime.utcnow().isoformat(),
        "blocks_processed": len(blocks),
        "groups": reduced,
        "total_anomalies": total_anomalies,
    }

    _write_result(source_type, result)
    return result


def _write_result(source_type: str, result: dict) -> str:
    out_dir = os.path.join(Config.HDFS_PROCESSED, source_type)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return filepath


def latest_result(source_type: str) -> dict | None:
    out_dir = os.path.join(Config.HDFS_PROCESSED, source_type)
    if not os.path.isdir(out_dir):
        return None
    files = sorted(f for f in os.listdir(out_dir) if f.endswith(".json"))
    if not files:
        return None
    with open(os.path.join(out_dir, files[-1]), encoding="utf-8") as f:
        return json.load(f)
