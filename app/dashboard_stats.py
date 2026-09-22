"""
Aggregated numbers for the dashboard's live stats row. Pulled from the same
sources the rest of the app already writes to (HDFS-sim files + MongoDB) --
no new storage, just a read-only summary.
"""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app import mongo
from app.config import Config
from app.mapreduce.jobs import METRIC_BY_SOURCE, list_all_blocks
from app.alerts.models import list_thresholds, list_triggered_alerts
from app.realtime.stream import stream_status
from app.support.models import list_all_tickets


def _count_rows(block_paths: list[str]) -> int:
    total = 0
    for path in block_paths:
        with open(path, newline="", encoding="utf-8") as f:
            total += max(sum(1 for _ in csv.reader(f)) - 1, 0)  # minus header
    return total


def get_dashboard_stats() -> dict:
    total_records = 0
    total_blocks = 0
    for source_type in METRIC_BY_SOURCE:
        blocks = list_all_blocks(source_type)
        total_blocks += len(blocks)
        total_records += _count_rows(blocks)

    jobs_run = 0
    processed_root = Config.HDFS_PROCESSED
    if os.path.isdir(processed_root):
        for source_type in METRIC_BY_SOURCE:
            job_dir = os.path.join(processed_root, source_type)
            if os.path.isdir(job_dir):
                jobs_run += len([f for f in os.listdir(job_dir) if f.endswith(".json")])

    active_alerts = len([a for a in list_triggered_alerts(limit=1000) if not a.get("acknowledged")])
    active_thresholds = len(list_thresholds(active_only=True))
    active_streams = len(stream_status()["active_sources"])
    open_tickets = len([t for t in list_all_tickets() if t.get("status") == "open"])
    total_users = mongo.db.users.count_documents({})

    return {
        "total_records": total_records,
        "total_blocks": total_blocks,
        "jobs_run": jobs_run,
        "active_alerts": active_alerts,
        "active_thresholds": active_thresholds,
        "active_streams": active_streams,
        "open_tickets": open_tickets,
        "total_users": total_users,
    }


def _time_ago(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def get_recent_activity(limit: int = 8) -> list[dict]:
    """Combine triggered alerts, support tickets, and processing job runs
    into one reverse-chronological feed for the dashboard."""
    events = []

    for alert in list_triggered_alerts(limit=20):
        events.append({
            "type": "alert",
            "icon": "bell-ring",
            "at": alert["triggered_at"],
            "text": f"Alert triggered on {alert['source_type']} ({alert['group_key']}: {alert['observed_value']} {alert['operator']} {alert['threshold_value']})",
        })

    for ticket in list_all_tickets()[:20]:
        events.append({
            "type": "ticket",
            "icon": "life-buoy",
            "at": ticket["created_at"],
            "text": f"New {ticket['category']} ticket from {ticket['user_email']}",
        })

    processed_root = Config.HDFS_PROCESSED
    if os.path.isdir(processed_root):
        for source_type in METRIC_BY_SOURCE:
            job_dir = os.path.join(processed_root, source_type)
            if not os.path.isdir(job_dir):
                continue
            for filename in os.listdir(job_dir):
                if not filename.endswith(".json"):
                    continue
                filepath = os.path.join(job_dir, filename)
                try:
                    with open(filepath, encoding="utf-8") as f:
                        job = json.load(f)
                    at = datetime.fromisoformat(job["generated_at"])
                    events.append({
                        "type": "job",
                        "icon": "cpu",
                        "at": at,
                        "text": f"Processing job completed for {source_type} ({job['blocks_processed']} blocks, {job['total_anomalies']} anomalies)",
                    })
                except (OSError, ValueError, KeyError):
                    continue

    def _sort_key(ev):
        at = ev["at"]
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        return at

    events.sort(key=_sort_key, reverse=True)
    events = events[:limit]
    for ev in events:
        ev["time_ago"] = _time_ago(ev["at"])
        del ev["at"]

    return events


def get_overview_charts(days: int = 7) -> dict:
    """Chart-ready data for the dashboard: records ingested per source, and a
    7-day trend of alerts/tickets/processing jobs."""
    records_by_source = {}
    for source_type in METRIC_BY_SOURCE:
        blocks = list_all_blocks(source_type)
        records_by_source[source_type] = _count_rows(blocks)

    today = datetime.now(timezone.utc).date()
    day_labels = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]
    alerts_by_day = defaultdict(int)
    tickets_by_day = defaultdict(int)
    jobs_by_day = defaultdict(int)

    for alert in list_triggered_alerts(limit=500):
        d = alert["triggered_at"]
        d = d.date() if hasattr(d, "date") else d
        alerts_by_day[d] += 1

    for ticket in list_all_tickets():
        d = ticket["created_at"]
        d = d.date() if hasattr(d, "date") else d
        tickets_by_day[d] += 1

    processed_root = Config.HDFS_PROCESSED
    if os.path.isdir(processed_root):
        for source_type in METRIC_BY_SOURCE:
            job_dir = os.path.join(processed_root, source_type)
            if not os.path.isdir(job_dir):
                continue
            for filename in os.listdir(job_dir):
                if not filename.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(job_dir, filename), encoding="utf-8") as f:
                        job = json.load(f)
                    d = datetime.fromisoformat(job["generated_at"]).date()
                    jobs_by_day[d] += 1
                except (OSError, ValueError, KeyError):
                    continue

    return {
        "records_by_source": {
            "labels": list(records_by_source.keys()),
            "values": list(records_by_source.values()),
        },
        "activity_trend": {
            "labels": [d.isoformat() for d in day_labels],
            "alerts": [alerts_by_day.get(d, 0) for d in day_labels],
            "tickets": [tickets_by_day.get(d, 0) for d in day_labels],
            "jobs": [jobs_by_day.get(d, 0) for d in day_labels],
        },
    }
