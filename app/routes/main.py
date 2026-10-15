# ──────────────────────────────────────────────────────────────────────────────
# app/routes/main.py
#
# The "main" blueprint handles general pages: home/landing page and about.
#
# What is a Blueprint?
#   A Blueprint is Flask's way of grouping related routes together.
#   Think of it like a chapter in a book — each blueprint handles one section
#   of the website (main pages, profile pages, assessment pages, etc.).
# ──────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, render_template

# Create the blueprint
# "main" is the name; url_prefix is not set so routes start at "/"
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """
    Home page — the landing page students see first.
    render_template() finds the HTML file in the  templates/  folder
    and sends it back to the browser.
    """
    return render_template("landing.html")


@main_bp.route("/about")
def about():
    """
    Simple about page placeholder.
    We'll expand this in a later phase if needed.
    """
    return render_template("about.html")
