# ──────────────────────────────────────────────────────────────────────────────
# app/database.py
#
# SQLite database helpers.
#
# Key concepts for beginners:
#   - SQLite stores the entire database in a single file (career_guidance.db).
#   - We open a connection per HTTP request and close it when the request ends.
#   - Flask's  g  object is a temporary storage bag that lives for one request.
#   - init_db() creates the tables the first time the app starts.
# ──────────────────────────────────────────────────────────────────────────────

import sqlite3
import os
from flask import g, current_app


def get_db():
    """
    Open (or reuse) the SQLite database connection for the current request.

    Flask's `g` object is like a request-scoped dictionary.
    If we already opened a connection this request, reuse it.
    If not, open a new one and store it in g.
    """
    if "db" not in g:
        # Connect to the database file defined in config.py
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES  # Enables automatic type conversion
        )
        # Row factory makes each row behave like a dictionary:
        # row["name"] instead of row[0]
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """
    Close the database connection at the end of the request.
    Flask calls this automatically because we register it with teardown_appcontext.
    The  e  parameter receives any exception that caused the request to end.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Create all database tables if they don't already exist.
    Called once when the Flask app starts for the first time.
    """
    # Ensure the instance/ directory exists BEFORE opening the DB file.
    # exist_ok=True means: don't raise an error if the folder already exists.
    os.makedirs(os.path.dirname(current_app.config["DATABASE"]), exist_ok=True)

    db = get_db()

    # CREATE TABLE IF NOT EXISTS means: only create if the table isn't there yet.
    # This is safe to run every startup — it won't delete existing data.
    db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            email           TEXT,
            education_level TEXT,
            field_of_study  TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id          INTEGER NOT NULL REFERENCES students(id),
            skills_json         TEXT,
            interests_json      TEXT,
            technologies_json   TEXT,
            goals_json          TEXT,
            submitted_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS results (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id       INTEGER NOT NULL REFERENCES assessments(id),
            career_name         TEXT,
            match_score         REAL,
            match_reasons_json  TEXT,
            missing_skills_json TEXT,
            roadmap_json        TEXT,
            rank                INTEGER,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    db.commit()
