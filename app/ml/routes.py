from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.mapreduce.jobs import METRIC_BY_SOURCE
from app.ml.models import predict_trends, detect_ml_anomalies, latest_ml_result

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


@ml_bp.route("/", methods=["GET"])
@login_required
def index():
    trends = {st: latest_ml_result(st, "trend") for st in METRIC_BY_SOURCE}
    anomalies = {st: latest_ml_result(st, "anomaly") for st in METRIC_BY_SOURCE}
    return render_template(
        "ml/index.html",
        source_types=METRIC_BY_SOURCE.keys(),
        trends=trends,
        anomalies=anomalies,
    )


@ml_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    source_type = request.form.get("source_type")
    try:
        result = predict_trends(source_type)
        flash(f"Trend prediction complete for {len(result['predictions'])} groups.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("ml.index"))


@ml_bp.route("/detect-anomalies", methods=["POST"])
@login_required
def detect_anomalies():
    source_type = request.form.get("source_type")
    try:
        result = detect_ml_anomalies(source_type)
        flash(f"ML anomaly detection complete: {result['anomaly_count']} anomalies found.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("ml.index"))
