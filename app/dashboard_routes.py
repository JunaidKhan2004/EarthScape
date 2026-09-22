from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.weather.service import get_karachi_weather
from app.dashboard_stats import get_dashboard_stats, get_recent_activity, get_overview_charts
from app.predictions.models import list_predictions, list_predictions_for_user, STATUS_PENDING

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    weather = get_karachi_weather()
    stats = get_dashboard_stats()
    activity = get_recent_activity()

    if current_user.is_admin():
        pending_predictions = list_predictions(status=STATUS_PENDING)
        return render_template(
            "dashboard/admin.html",
            user=current_user,
            weather=weather,
            stats=stats,
            activity=activity,
            pending_predictions=pending_predictions,
        )

    my_predictions = list_predictions_for_user(current_user.email)
    return render_template(
        "dashboard/analyst.html",
        user=current_user,
        weather=weather,
        stats=stats,
        activity=activity,
        my_predictions=my_predictions,
    )


@dashboard_bp.route("/api/weather")
@login_required
def api_weather():
    return jsonify(get_karachi_weather())


@dashboard_bp.route("/api/stats")
@login_required
def api_stats():
    return jsonify(get_dashboard_stats())


@dashboard_bp.route("/api/activity")
@login_required
def api_activity():
    return jsonify(get_recent_activity())


@dashboard_bp.route("/api/overview-charts")
@login_required
def api_overview_charts():
    return jsonify(get_overview_charts())
