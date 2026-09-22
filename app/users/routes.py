from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.auth.decorators import roles_required
from app.auth.models import User, ROLE_ADMIN, ROLE_ANALYST

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/", methods=["GET"])
@login_required
@roles_required(ROLE_ADMIN)
def index():
    users = User.list_all()
    return render_template("users/index.html", users=users)


@users_bp.route("/<user_id>/role", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def set_role(user_id):
    role = request.form.get("role")

    if user_id == current_user.id:
        flash("You cannot change your own role.", "error")
        return redirect(url_for("users.index"))

    try:
        User.set_role(user_id, role)
        flash("Role updated.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("users.index"))
