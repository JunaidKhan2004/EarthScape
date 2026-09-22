from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.mapreduce.jobs import METRIC_BY_SOURCE
from app.ml.models import forecast_7day
from app.predictions.models import (
    create_prediction,
    list_predictions,
    list_predictions_for_user,
    review_prediction,
    STATUS_PENDING,
)
from app.auth.decorators import roles_required
from app.auth.models import ROLE_ADMIN

predictions_bp = Blueprint("predictions", __name__, url_prefix="/predictions")


@predictions_bp.route("/", methods=["GET"])
@login_required
def index():
    if current_user.is_admin():
        predictions = list_predictions()
    else:
        predictions = list_predictions_for_user(current_user.email)
    return render_template(
        "predictions/index.html",
        source_types=METRIC_BY_SOURCE.keys(),
        predictions=predictions,
    )


@predictions_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    source_type = request.form.get("source_type")
    group_key = request.form.get("group_key", "").strip() or None

    try:
        result = forecast_7day(source_type, group_key)
        create_prediction(
            source_type,
            METRIC_BY_SOURCE[source_type],
            group_key or "all",
            result,
            current_user.email,
        )
        flash("7-day forecast generated and submitted for admin approval.", "success")
    except (ValueError, KeyError) as exc:
        flash(str(exc), "error")

    return redirect(url_for("predictions.index"))


@predictions_bp.route("/<prediction_id>/approve", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def approve(prediction_id):
    review_prediction(prediction_id, "approved", current_user.email)
    flash("Prediction approved. It is now visible on the public site.", "success")
    return redirect(url_for("predictions.index"))


@predictions_bp.route("/<prediction_id>/reject", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def reject(prediction_id):
    review_prediction(prediction_id, "rejected", current_user.email)
    flash("Prediction rejected.", "success")
    return redirect(url_for("predictions.index"))
