from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.ingestion.services import (
    SOURCE_TYPES,
    parse_csv_upload,
    ingest_records,
    generate_sample_batch,
)

ingestion_bp = Blueprint("ingestion", __name__, url_prefix="/ingestion")


@ingestion_bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("ingestion/index.html", source_types=SOURCE_TYPES)


@ingestion_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    source_type = request.form.get("source_type")
    file = request.files.get("file")

    if not file or file.filename == "":
        flash("Please choose a CSV file to upload.", "error")
        return redirect(url_for("ingestion.index"))

    if not file.filename.lower().endswith(".csv"):
        flash("Only .csv files are supported.", "error")
        return redirect(url_for("ingestion.index"))

    try:
        records, report = parse_csv_upload(file.stream, source_type)
        path = ingest_records(source_type, records)
        msg = f"Ingested {report['valid_rows']} of {report['total_rows']} rows into {path}."
        skipped = report["duplicate_rows"] + report["incomplete_rows"]
        if skipped:
            msg += f" Skipped {report['duplicate_rows']} duplicate(s) and {report['incomplete_rows']} incomplete row(s)."
        flash(msg, "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("ingestion.index"))


@ingestion_bp.route("/simulate", methods=["POST"])
@login_required
def simulate():
    """Simulate a real-time feed by generating and ingesting synthetic records."""
    source_type = request.form.get("source_type")
    try:
        records = generate_sample_batch(source_type, count=20)
        path = ingest_records(source_type, records)
        flash(f"Simulated {len(records)} real-time records into {path}", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("ingestion.index"))
