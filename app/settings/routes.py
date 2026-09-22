from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("settings/index.html")


@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    name = request.form.get("name", "").strip()

    if not name:
        flash("Name cannot be empty.", "error")
        return redirect(url_for("settings.index"))

    current_user.set_name(name)
    flash("Profile updated.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("settings.index"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("settings.index"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("settings.index"))

    current_user.set_password(new_password)
    flash("Password changed.", "success")
    return redirect(url_for("settings.index"))
