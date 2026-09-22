from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.mapreduce.jobs import run_pattern_anomaly_job, latest_result, METRIC_BY_SOURCE
from app.alerts.models import evaluate_thresholds_against_groups

processing_bp = Blueprint("processing", __name__, url_prefix="/processing")


@processing_bp.route("/", methods=["GET"])
@login_required
def index():
    results = {st: latest_result(st) for st in METRIC_BY_SOURCE}
    return render_template("processing/index.html", source_types=METRIC_BY_SOURCE.keys(), results=results)


@processing_bp.route("/run", methods=["POST"])
@login_required
def run():
    source_type = request.form.get("source_type")
    try:
        result = run_pattern_anomaly_job(source_type)
        new_alerts = evaluate_thresholds_against_groups(source_type, result["groups"])
        msg = (
            f"Job complete: {result['blocks_processed']} blocks, "
            f"{len(result['groups'])} groups, {result['total_anomalies']} anomalies found."
        )
        if new_alerts:
            msg += f" {new_alerts} threshold alert(s) triggered."
        flash(msg, "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("processing.index"))
