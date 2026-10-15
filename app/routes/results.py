# ──────────────────────────────────────────────────────────────────────────────
# app/routes/results.py
#
# The "results" blueprint renders the career recommendation dashboard.
#
# Routes:
#   GET /results/<assessment_id>
#       → Runs the scorer if results not yet cached; saves to DB; renders page.
#   GET /results/latest
#       → Convenience redirect to the most recent assessment's results.
#
# Security:
#   - Requires session["student_id"].
#   - Every DB query checks that assessment_id belongs to the session student.
#   - Results are re-computed fresh each time they are first needed for an
#     assessment (idempotent: if results already exist they are loaded, not re-run).
# ──────────────────────────────────────────────────────────────────────────────

import json
from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.database import get_db
from app.engine.scorer import score_assessment
from app.engine.roadmap import get_roadmap

results_bp = Blueprint("results", __name__, url_prefix="/results")


@results_bp.route("/latest")
def latest():
    """Redirect to results for the student's most recent assessment."""
    student_id = session.get("student_id")
    if not student_id:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("profile.index"))

    db = get_db()
    row = db.execute(
        "SELECT id FROM assessments WHERE student_id = ? ORDER BY id DESC LIMIT 1",
        (student_id,)
    ).fetchone()

    if not row:
        flash("No assessments found. Please complete the assessment first.", "warning")
        return redirect(url_for("assessment.index"))

    return redirect(url_for("results.show", assessment_id=row["id"]))


@results_bp.route("/<int:assessment_id>")
def show(assessment_id):
    """
    Main results page.
    Loads existing results from DB (or runs scorer if first visit),
    then renders the dashboard.
    """
    student_id = session.get("student_id")
    if not student_id:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("profile.index"))

    db = get_db()

    # ── Authorisation: verify this assessment belongs to the session student ──
    assessment_row = db.execute(
        "SELECT * FROM assessments WHERE id = ? AND student_id = ?",
        (assessment_id, student_id)
    ).fetchone()

    if not assessment_row:
        flash("Results not found or do not belong to your profile.", "danger")
        return redirect(url_for("assessment.index"))

    # ── Check if results are already stored for this assessment ──────────────
    existing = db.execute(
        "SELECT * FROM results WHERE assessment_id = ? ORDER BY rank",
        (assessment_id,)
    ).fetchall()

    if existing:
        # Deserialise stored results
        recommendations = _deserialise_results(existing)
    else:
        # Run the scorer and save results
        all_scores = score_assessment(assessment_row)
        top3 = all_scores[:3]
        recommendations = _save_and_build(db, assessment_id, top3)

    # ── Fetch student info for personalisation ────────────────────────────────
    student = db.execute(
        "SELECT name, field_of_study FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    student_name = student["name"] if student else session.get("student_name", "Student")

    # ── Count total assessments for context ───────────────────────────────────
    total_assessments = db.execute(
        "SELECT COUNT(*) FROM assessments WHERE student_id = ?", (student_id,)
    ).fetchone()[0]

    return render_template(
        "results.html",
        recommendations=recommendations,
        student_name=student_name,
        assessment_id=assessment_id,
        total_assessments=total_assessments,
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _save_and_build(db, assessment_id: int, top3: list[dict]) -> list[dict]:
    """
    Save top-3 results to the  results  table and return the final
    list of recommendation dicts ready for the template.
    Preserves history: never deletes previous results rows.
    """
    recommendations = []

    for rank, rec in enumerate(top3, start=1):
        roadmap_steps = get_roadmap(rec["career_name"], rec["missing_skills"])

        db.execute(
            """
            INSERT INTO results
                (assessment_id, career_name, match_score,
                 match_reasons_json, missing_skills_json, roadmap_json, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                rec["career_name"],
                rec["score"] / 100.0,           # store as 0.0–1.0 per schema
                json.dumps(rec["match_reasons"]),
                json.dumps(rec["missing_skills"]),
                json.dumps(roadmap_steps),
                rank,
            )
        )

        recommendations.append(_build_rec_dict(rec, roadmap_steps, rank))

    db.commit()
    return recommendations


def _deserialise_results(rows) -> list[dict]:
    """Convert stored result rows back into template-ready dicts."""
    recommendations = []
    for row in rows:
        roadmap_steps = json.loads(row["roadmap_json"] or "[]")
        rec = {
            "career_name":    row["career_name"],
            "description":    "",               # not stored — rebuilt from career_data if needed
            "score":          round(row["match_score"] * 100),
            "match_reasons":  json.loads(row["match_reasons_json"]  or "[]"),
            "missing_skills": json.loads(row["missing_skills_json"] or "[]"),
            "suggested_techs": [],
            "skill_breakdown": {},
        }
        recommendations.append(_build_rec_dict(rec, roadmap_steps, row["rank"]))
    return recommendations


def _build_rec_dict(rec: dict, roadmap_steps: list[dict], rank: int) -> dict:
    """Combine scorer output + roadmap into one template-ready dict."""
    return {
        "rank":           rank,
        "career_name":    rec["career_name"],
        "description":    rec.get("description", ""),
        "score":          rec["score"],
        "match_reasons":  rec["match_reasons"],
        "missing_skills": rec["missing_skills"],
        "suggested_techs":rec.get("suggested_techs", []),
        "skill_breakdown":rec.get("skill_breakdown", {}),
        "roadmap":        roadmap_steps,
    }
