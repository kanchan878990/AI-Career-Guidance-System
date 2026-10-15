# ──────────────────────────────────────────────────────────────────────────────
# app/config.py
#
# Central configuration for the Flask application.
#
# How it works:
#   - The app reads settings from this file at startup.
#   - SECRET_KEY is loaded from an environment variable (.env file) for security.
#   - If no .env file exists (e.g. first-time setup), a safe development fallback
#     is used automatically — but you MUST change this before deploying online.
#
# To set your own secret key:
#   1. Create a file named  .env  in the project root folder.
#   2. Add this line inside it:  SECRET_KEY=any_long_random_string_here
# ──────────────────────────────────────────────────────────────────────────────

import os

# Load .env file if it exists (python-dotenv package reads it into os.environ)
from dotenv import load_dotenv
load_dotenv()


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    # Flask uses this key to sign session cookies.
    # os.environ.get() reads from the .env file; the second argument is the
    # fallback used when the variable is not set (development only).
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-change-this-in-production")

    # ── Database ──────────────────────────────────────────────────────────────
    # The SQLite database file will be created inside the  instance/  folder.
    # Flask automatically creates the instance/ folder if it does not exist.
    DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "career_guidance.db")

    # ── Debug Mode ────────────────────────────────────────────────────────────
    # True  → Flask shows detailed error pages and reloads on code changes.
    # False → Production-safe mode (no error details exposed to users).
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
