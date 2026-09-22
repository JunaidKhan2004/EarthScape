from bson.errors import InvalidId
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail

from app.config import Config

mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    mail.init_app(app)

    from app.public.routes import public_bp
    from app.auth.routes import auth_bp
    from app.ingestion.routes import ingestion_bp
    from app.dashboard_routes import dashboard_bp
    from app.alerts.routes import alerts_bp
    from app.processing.routes import processing_bp
    from app.ml.routes import ml_bp
    from app.viz.routes import viz_bp
    from app.realtime.routes import realtime_bp
    from app.support.routes import support_bp
    from app.users.routes import users_bp
    from app.predictions.routes import predictions_bp
    from app.settings.routes import settings_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ingestion_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(viz_bp)
    app.register_blueprint(realtime_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(settings_bp)

    from app.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(InvalidId)
    def invalid_object_id(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(error):
        from flask import flash, redirect, request
        flash("File is too large. Maximum upload size is 5 MB.", "error")
        return redirect(request.referrer or "/"), 302

    return app
