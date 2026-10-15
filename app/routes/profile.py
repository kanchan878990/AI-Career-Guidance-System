# ──────────────────────────────────────────────────────────────────────────────
# app/routes/profile.py
#
# The "profile" blueprint handles the student profile form.
#
# Routes:
#   GET  /profile  → Show the blank profile form
#   POST /profile  → Validate the form, save to the database, redirect
#
# Key concepts used here:
#   - request.method  → tells us if the browser sent GET (just loading the page)
#     or POST (the user submitted a form)
#   - request.form    → a dictionary of everything the user typed in the form
#   - session         → a small, secure storage area tied to the user's browser
#                       tab/cookie; we use it to remember which student is active
#   - flash()         → sends a one-time notification shown on the next page
#   - redirect()      → sends the browser to a different URL
# ──────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.database import get_db

# Create the blueprint.
# url_prefix="/profile" means every route here starts with /profile.
profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
def index():
    """
    GET  → Display the empty profile form.
    POST → Read form values, validate them, save to DB, set session, redirect.
    """

    if request.method == "POST":
        # ── Read form values ─────────────────────────────────────────────────
        # .strip() removes accidental leading/trailing spaces the user may type.
        name            = request.form.get("name", "").strip()
        email           = request.form.get("email", "").strip()
        education_level = request.form.get("education_level", "").strip()
        field_of_study  = request.form.get("field_of_study", "").strip()

        # ── Validation ───────────────────────────────────────────────────────
        # Collect all errors into a list so we can show them all at once.
        errors = []

        if not name:
            errors.append("Full name is required.")

        if len(name) > 100:
            errors.append("Name must be 100 characters or fewer.")

        if not education_level:
            errors.append("Please select your education level.")

        if not field_of_study:
            errors.append("Field of study is required.")

        if email and "@" not in email:
            errors.append("Please enter a valid email address (or leave it blank).")

        # If there are any errors, flash them and re-display the form.
        # The form values are passed back so the user doesn't have to retype them.
        if errors:
            for error in errors:
                flash(error, "danger")   # "danger" → red Bootstrap alert
            # Pass back the submitted values so the form re-fills them
            return render_template(
                "profile.html",
                form_data={
                    "name": name,
                    "email": email,
                    "education_level": education_level,
                    "field_of_study": field_of_study,
                }
            )

        # ── Save to database ─────────────────────────────────────────────────
        db = get_db()

        # INSERT a new row into the students table.
        # The ? placeholders protect against SQL injection — never use f-strings
        # or string concatenation to build SQL queries.
        cursor = db.execute(
            """
            INSERT INTO students (name, email, education_level, field_of_study)
            VALUES (?, ?, ?, ?)
            """,
            (name, email or None, education_level, field_of_study)
        )
        db.commit()

        # cursor.lastrowid gives us the auto-generated id of the row we just inserted.
        student_id = cursor.lastrowid

        # ── Store in session ─────────────────────────────────────────────────
        # The session is stored as a signed cookie in the user's browser.
        # We keep the student_id here so assessment and results pages know who's who.
        session["student_id"]   = student_id
        session["student_name"] = name

        # ── Flash success and redirect ───────────────────────────────────────
        flash(f"Welcome, {name}! Your profile has been saved. Now complete your assessment.", "success")

        # Redirect directly to the assessment page (Phase 4 is now built).
        return redirect(url_for("assessment.index"))

    # GET request — just show the blank form
    return render_template("profile.html", form_data={})


@profile_bp.route("/success")
def success():
    """
    Shown after a successful profile submission.
    This is a temporary landing point until the Assessment page (Phase 4) is built.
    """
    student_name = session.get("student_name", "Student")
    return render_template("profile_success.html", student_name=student_name)
