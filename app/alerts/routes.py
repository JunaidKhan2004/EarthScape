from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.mapreduce.jobs import METRIC_BY_SOURCE
from app.alerts.models import (
    create_threshold,
    list_thresholds,
    deactivate_threshold,
    list_triggered_alerts,
    acknowledge_alert,
)
from app.auth.decorators import roles_required
from app.auth.models import ROLE_ADMIN

alerts_bp = Blueprint("alerts", __name__, url_prefix="/alerts")


@alerts_bp.route("/", methods=["GET"])
@login_required
def index():
    thresholds = list_thresholds(active_only=True)
    triggered = list_triggered_alerts(limit=50)
    return render_template(
        "alerts/index.html",
        source_types=METRIC_BY_SOURCE,
        thresholds=thresholds,
        triggered=triggered,
    )


@alerts_bp.route("/thresholds", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def add_threshold():
    source_type = request.form.get("source_type")
    operator = request.form.get("operator")
    value = request.form.get("value")

    try:
        metric = METRIC_BY_SOURCE[source_type]
        create_threshold(source_type, metric, operator, float(value), current_user.email)
        flash("Threshold created.", "success")
    except (ValueError, KeyError) as exc:
        flash(f"Could not create threshold: {exc}", "error")

    return redirect(url_for("alerts.index"))


@alerts_bp.route("/thresholds/<threshold_id>/deactivate", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def remove_threshold(threshold_id):
    deactivate_threshold(threshold_id)
    flash("Threshold deactivated.", "success")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/triggered/<alert_id>/ack", methods=["POST"])
@login_required
def ack_alert(alert_id):
    acknowledge_alert(alert_id)
    flash("Alert acknowledged.", "success")
    return redirect(url_for("alerts.index"))
