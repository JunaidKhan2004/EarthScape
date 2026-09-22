from flask import Blueprint, render_template, jsonify
from flask_login import login_required

from app.mapreduce.jobs import METRIC_BY_SOURCE, latest_result
from app.ml.models import latest_ml_result

viz_bp = Blueprint("viz", __name__, url_prefix="/viz")


@viz_bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("viz/index.html", source_types=list(METRIC_BY_SOURCE.keys()))


@viz_bp.route("/api/chart-data/<source_type>", methods=["GET"])
@login_required
def chart_data(source_type):
    if source_type not in METRIC_BY_SOURCE:
        return jsonify({"error": "unknown source_type"}), 404

    processing_result = latest_result(source_type)
    trend_result = latest_ml_result(source_type, "trend")
    anomaly_result = latest_ml_result(source_type, "anomaly")

    payload = {
        "source_type": source_type,
        "metric": METRIC_BY_SOURCE[source_type],
        "group_stats": {
            "labels": [],
            "means": [],
            "mins": [],
            "maxs": [],
        },
        "trend": {
            "labels": [],
            "last_values": [],
            "predicted_next": [],
        },
        "anomaly_count": 0,
        "anomaly_points": [],
    }

    if processing_result:
        for g in processing_result["groups"]:
            payload["group_stats"]["labels"].append(g["group_key"])
            payload["group_stats"]["means"].append(g["mean"])
            payload["group_stats"]["mins"].append(g["min"])
            payload["group_stats"]["maxs"].append(g["max"])

    if trend_result:
        for p in trend_result["predictions"]:
            if p["predicted_next"] is None:
                continue
            payload["trend"]["labels"].append(p["group_key"])
            payload["trend"]["last_values"].append(p["last_value"])
            payload["trend"]["predicted_next"].append(p["predicted_next"])

    if anomaly_result:
        payload["anomaly_count"] = anomaly_result["anomaly_count"]
        payload["anomaly_points"] = [
            {"x": a["timestamp"], "y": a["value"], "group": a["group_key"]}
            for a in anomaly_result["anomalies"]
        ]

    return jsonify(payload)
