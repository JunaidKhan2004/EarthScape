from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.support.models import create_ticket, list_tickets_for_user, list_all_tickets, resolve_ticket
from app.auth.decorators import roles_required
from app.auth.models import ROLE_ADMIN

support_bp = Blueprint("support", __name__, url_prefix="/support")


@support_bp.route("/", methods=["GET"])
@login_required
def index():
    if current_user.is_admin():
        tickets = list_all_tickets()
    else:
        tickets = list_tickets_for_user(current_user.email)
    return render_template("support/index.html", tickets=tickets)


@support_bp.route("/tickets", methods=["POST"])
@login_required
def create():
    category = request.form.get("category", "general")
    message = request.form.get("message", "")

    try:
        create_ticket(current_user.email, category, message)
        flash("Support ticket submitted.", "success")
    except ValueError as exc:
        flash(str(exc), "error")

    return redirect(url_for("support.index"))


@support_bp.route("/tickets/<ticket_id>/resolve", methods=["POST"])
@login_required
@roles_required(ROLE_ADMIN)
def resolve(ticket_id):
    response = request.form.get("response", "")
    resolve_ticket(ticket_id, response)
    flash("Ticket marked resolved.", "success")
    return redirect(url_for("support.index"))
