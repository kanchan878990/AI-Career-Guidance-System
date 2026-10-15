# ──────────────────────────────────────────────────────────────────────────────
# run.py
#
# Entry point for the AI Career Guidance System.
#
# How to use:
#   1. Open a terminal (Command Prompt, PowerShell, or VS Code terminal).
#   2. Navigate to this project folder:
#        cd "AI Career Guidance System"
#   3. Activate your virtual environment (see README.md for setup steps).
#   4. Run:
#        python run.py
#   5. Open your browser and go to:
#        http://127.0.0.1:5000
#
# What this file does:
#   - Calls create_app() from app/__init__.py to build the Flask application.
#   - Starts Flask's built-in development web server on port 5000.
#   - The server reloads automatically when you save changes to Python files.
# ──────────────────────────────────────────────────────────────────────────────

from app import create_app

# Create the Flask app using the factory function
app = create_app()

if __name__ == "__main__":
    # debug=True is already set via Config based on FLASK_DEBUG env variable.
    # We pass it explicitly here as well so running this file directly works
    # even without a .env file.
    app.run(
        host="127.0.0.1",   # Only accessible from your own computer (safe for dev)
        port=5000,           # Visit http://127.0.0.1:5000 in your browser
        debug=app.config["DEBUG"]
    )
