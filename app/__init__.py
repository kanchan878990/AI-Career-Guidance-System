# ──────────────────────────────────────────────────────────────────────────────
# app/__init__.py
#
# The Flask Application Factory.
#
# What is an "app factory"?
#   Instead of creating the Flask app as a global variable, we wrap it in a
#   function called create_app(). This is the recommended Flask pattern because:
#     1. It makes testing easier (you can create fresh app instances per test).
#     2. It avoids circular import problems as the project grows.
#     3. It cleanly separates configuration from app creation.
#
# When you run  python run.py , it calls create_app() which:
#   1. Creates the Flask instance.
#   2. Loads config from Config class.
#   3. Initialises the database (creates tables if missing).
#   4. Registers all blueprints (route groups).
# ──────────────────────────────────────────────────────────────────────────────

from flask import Flask
from .config import Config
from .database import init_db, close_db


def create_app():
    """
    Create and configure the Flask application.
    Returns the fully configured app object.
    """

    # Flask(__name__) tells Flask where to find templates/ and static/ folders.
    # __name__ is the name of the current package ("app").
    app = Flask(__name__)

    # ── Load Configuration ────────────────────────────────────────────────────
    app.config.from_object(Config)

    # ── Database Setup ────────────────────────────────────────────────────────
    # Register close_db so Flask automatically closes the DB after every request.
    app.teardown_appcontext(close_db)

    # Create tables on first run (safe to call every startup — uses IF NOT EXISTS).
    with app.app_context():
        init_db()

    # ── Register Blueprints ───────────────────────────────────────────────────
    # Import blueprints here (inside the function) to avoid circular imports.
    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    from .routes.profile import profile_bp
    app.register_blueprint(profile_bp)

    from .routes.assessment import assessment_bp
    app.register_blueprint(assessment_bp)

    from .routes.results import results_bp
    app.register_blueprint(results_bp)

    return app
