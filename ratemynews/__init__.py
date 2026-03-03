from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ratemynews.config import Config
from ratemynews.extensions import csrf, db, login_manager, migrate

limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from ratemynews.auth.routes import auth_bp
    from ratemynews.main.routes import main_bp
    from ratemynews.journalists.routes import journalists_bp
    from ratemynews.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(journalists_bp, url_prefix="/journalists")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}, 200

    # Keep local setup simple: auto-create tables in non-test mode.
    if not app.config.get("TESTING", False):
        with app.app_context():
            db.create_all()

    return app
