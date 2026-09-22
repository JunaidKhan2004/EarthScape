"""
Simulated HDFS layer.

Real Hadoop's HDFS is a distributed, replicated filesystem. For this project we
simulate its two properties that matter for the app logic:

  1. Partitioning: files are organized as raw/<source_type>/<year>/<month>/<day>/*.csv
     so that a MapReduce-style job can target a date range or a source without
     scanning the whole dataset (mirrors Hive/HDFS partition pruning).
  2. Write-once semantics: ingested files are named with a timestamp + uuid so
     writes never overwrite existing blocks, similar to HDFS append-only files.

Swapping this module for `hdfs3` / `pyarrow.hdfs` / `pywebhdfs` against a real
cluster later only requires changing `write_partitioned` and `list_partition`.
"""
import csv
import os
import uuid
from datetime import datetime

from app.config import Config


def _partition_dir(source_type: str, dt: datetime, root: str) -> str:
    return os.path.join(
        root,
        source_type,
        f"{dt.year:04d}",
        f"{dt.month:02d}",
        f"{dt.day:02d}",
    )


def write_partitioned(source_type: str, records: list[dict], dt: datetime = None, root: str = None) -> str:
    """Write records into the partitioned raw zone. Returns the file path written."""
    dt = dt or datetime.utcnow()
    root = root or Config.HDFS_RAW

    partition_dir = _partition_dir(source_type, dt, root)
    os.makedirs(partition_dir, exist_ok=True)

    filename = f"{dt.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.csv"
    filepath = os.path.join(partition_dir, filename)

    if not records:
        raise ValueError("No records to write.")

    fieldnames = list(records[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return filepath


def list_partition(source_type: str, dt: datetime, root: str = None) -> list[str]:
    """List all block files under a given source/date partition."""
    root = root or Config.HDFS_RAW
    partition_dir = _partition_dir(source_type, dt, root)
    if not os.path.isdir(partition_dir):
        return []
    return [
        os.path.join(partition_dir, name)
        for name in sorted(os.listdir(partition_dir))
        if name.endswith(".csv")
    ]


def list_all_blocks(source_type: str = None, root: str = None) -> list[str]:
    """Walk the raw zone and return all block file paths, optionally filtered by source_type."""
    root = root or Config.HDFS_RAW
    base = os.path.join(root, source_type) if source_type else root
    if not os.path.isdir(base):
        return []

    blocks = []
    for dirpath, _, filenames in os.walk(base):
        for name in filenames:
            if name.endswith(".csv"):
                blocks.append(os.path.join(dirpath, name))
    return sorted(blocks)


def read_blocks_as_dicts(block_paths: list[str]) -> list[dict]:
    """Read a list of block CSV files and return all rows as dicts."""
    rows = []
    for path in block_paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows.extend(reader)
    return rows
