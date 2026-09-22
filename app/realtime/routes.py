from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required

from app.mapreduce.jobs import METRIC_BY_SOURCE
from app.realtime.stream import start_stream, stop_stream, is_streaming, stream_status
from app.auth.decorators import roles_required
from app.auth.models import ROLE_ADMIN

realtime_bp = Blueprint("realtime", __name__, url_prefix="/realtime")


@realtime_bp.route("/", methods=["GET"])
@login_required
def index():
    active = {st: is_streaming(st) for st in METRIC_BY_SOURCE}
    return render_template("realtime/index.html", source_types=METRIC_BY_SOURCE.keys(), active=active)


@realtime_bp.route("/start", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def start():
    source_type = request.form.get("source_type")
    if source_type not in METRIC_BY_SOURCE:
        flash("Unknown source type.", "error")
        return redirect(url_for("realtime.index"))

    start_stream(source_type, interval_seconds=30)
    flash(f"Real-time simulation started for {source_type} (every 30s).", "success")
    return redirect(url_for("realtime.index"))


@realtime_bp.route("/stop", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def stop():
    source_type = request.form.get("source_type")
    stop_stream(source_type)
    flash(f"Real-time simulation stopped for {source_type}.", "success")
    return redirect(url_for("realtime.index"))


@realtime_bp.route("/api/status", methods=["GET"])
@login_required
def api_status():
    return jsonify(stream_status())
