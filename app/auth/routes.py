from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.auth.models import User, ROLE_ANALYST
from app.auth.tokens import generate_reset_token, verify_reset_token
from app.auth.emails import send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        name = request.form.get("name", "").strip()

        try:
            user = User.create(email, password, name, ROLE_ANALYST)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("auth.register"))

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/combined.html", active_tab="register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        user = User.get_by_email(email)
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/combined.html", active_tab="login")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        user = User.get_by_email(email)

        # Always show the same confirmation, whether or not the account
        # exists -- avoids leaking which emails are registered.
        if user is not None:
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(user.email, user.name, reset_url)

        flash("If an account exists for that email, a reset link has been sent.", "success")
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if email is None:
        flash("This reset link is invalid or has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/reset_password.html", token=token)

        user = User.get_by_email(email)
        if user is None:
            flash("This account no longer exists.", "error")
            return redirect(url_for("auth.forgot_password"))

        user.set_password(password)
        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
