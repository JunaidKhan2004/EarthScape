"""
Real-time data processing simulation.

Real Hadoop deployments pair batch MapReduce with a streaming layer (Spark
Streaming / Kafka + Flink) that continuously ingests and processes data as it
arrives, rather than waiting for a scheduled batch run. Here we simulate that
with an APScheduler background job that, on an interval:

  1. Generates a small batch of synthetic "live" records (as if a sensor/
     station/satellite feed just pushed data) and writes it into the same
     HDFS-sim partitioned raw zone used by manual/batch ingestion.
  2. Immediately re-runs the MapReduce pattern/anomaly job and threshold
     evaluation on that source, so processed results and alerts stay current
     without a human manually clicking "Run Job".

This keeps a single code path (ingestion -> MapReduce -> alerts) serving both
manual batch uploads and the simulated real-time feed, exactly like a real
pipeline where streaming and batch jobs share transformation logic.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.ingestion.services import generate_sample_batch, ingest_records
from app.mapreduce.jobs import run_pattern_anomaly_job
from app.alerts.models import evaluate_thresholds_against_groups

logger = logging.getLogger("realtime_stream")

_scheduler: BackgroundScheduler | None = None
_active_sources: set[str] = set()

_last_tick_info: dict = {}


def _tick(source_type: str):
    try:
        records = generate_sample_batch(source_type, count=10)
        ingest_records(source_type, records)
        result = run_pattern_anomaly_job(source_type)
        new_alerts = evaluate_thresholds_against_groups(source_type, result["groups"])
        _last_tick_info[source_type] = {
            "at": datetime.utcnow().isoformat(),
            "records_ingested": len(records),
            "groups": len(result["groups"]),
            "anomalies": result["total_anomalies"],
            "new_alerts": new_alerts,
            "status": "ok",
        }
    except Exception as exc:
        logger.exception("Real-time tick failed for %s", source_type)
        _last_tick_info[source_type] = {
            "at": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(exc),
        }


def start_stream(source_type: str, interval_seconds: int = 30):
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()

    job_id = f"stream_{source_type}"
    if _scheduler.get_job(job_id):
        return  # already running

    _scheduler.add_job(_tick, "interval", seconds=interval_seconds, id=job_id, args=[source_type])
    _active_sources.add(source_type)
    _tick(source_type)  # run once immediately so the UI has data right away


def stop_stream(source_type: str):
    if _scheduler is None:
        return
    job_id = f"stream_{source_type}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
    _active_sources.discard(source_type)


def is_streaming(source_type: str) -> bool:
    return source_type in _active_sources


def stream_status() -> dict:
    return {
        "active_sources": sorted(_active_sources),
        "last_tick": _last_tick_info,
    }


def shutdown():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    _active_sources.clear()
