# ──────────────────────────────────────────────────────────────────────────────
# app/routes/assessment.py
#
# The "assessment" blueprint handles the career assessment form.
#
# Routes:
#   GET  /assessment        → Show the assessment form (session guard applied)
#   POST /assessment        → Validate, serialize to JSON, save to DB, redirect
#   GET  /assessment/<id>   → View a previously submitted assessment
#
# Session guard:
#   If the student hasn't filled their profile yet (no session["student_id"]),
#   they are redirected to /profile/ with an informative flash message.
#   This keeps assessment history correctly linked to the right student.
# ──────────────────────────────────────────────────────────────────────────────

import json
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.database import get_db

assessment_bp = Blueprint("assessment", __name__, url_prefix="/assessment")

# ── Skill definitions ─────────────────────────────────────────────────────────
# Each skill has: key (used in JSON), label (shown to user), category (group header)
# Proficiency scale: 0 = None, 1 = Beginner, 2 = Basic, 3 = Intermediate,
#                    4 = Advanced, 5 = Expert
SKILLS = [
    # Programming Languages
    {"key": "python",        "label": "Python",              "category": "Programming Languages"},
    {"key": "java",          "label": "Java",                "category": "Programming Languages"},
    {"key": "cpp",           "label": "C / C++",             "category": "Programming Languages"},
    {"key": "javascript",    "label": "JavaScript",          "category": "Programming Languages"},
    {"key": "r_lang",        "label": "R",                   "category": "Programming Languages"},
    # Data & AI
    {"key": "machine_learning", "label": "Machine Learning", "category": "Data & AI"},
    {"key": "deep_learning", "label": "Deep Learning",       "category": "Data & AI"},
    {"key": "statistics",    "label": "Statistics & Math",   "category": "Data & AI"},
    {"key": "sql",           "label": "SQL / Databases",     "category": "Data & AI"},
    {"key": "data_viz",      "label": "Data Visualisation",  "category": "Data & AI"},
    # Web & Cloud
    {"key": "html_css",      "label": "HTML / CSS",          "category": "Web & Cloud"},
    {"key": "web_frameworks","label": "Web Frameworks (React/Flask/Django)", "category": "Web & Cloud"},
    {"key": "cloud",         "label": "Cloud Platforms (AWS/Azure/GCP)",    "category": "Web & Cloud"},
    {"key": "docker",        "label": "Docker / Containers", "category": "Web & Cloud"},
    # Security & Systems
    {"key": "networking",    "label": "Computer Networking", "category": "Security & Systems"},
    {"key": "linux",         "label": "Linux / Shell Scripting",            "category": "Security & Systems"},
    {"key": "cybersecurity", "label": "Cybersecurity Concepts",             "category": "Security & Systems"},
    {"key": "dsa",           "label": "Data Structures & Algorithms",       "category": "Security & Systems"},
]

PROFICIENCY_LABELS = {
    "0": "No experience",
    "1": "Beginner",
    "2": "Basic",
    "3": "Intermediate",
    "4": "Advanced",
    "5": "Expert",
}

# ── Interest definitions ───────────────────────────────────────────────────────
INTERESTS = [
    {"key": "build_ml_models",    "label": "Building ML / AI models",        "icon": "bi-cpu"},
    {"key": "analyse_data",       "label": "Analysing data & finding trends", "icon": "bi-graph-up"},
    {"key": "build_web_apps",     "label": "Building websites & web apps",    "icon": "bi-globe2"},
    {"key": "backend_apis",       "label": "Designing APIs & backend systems","icon": "bi-server"},
    {"key": "security_research",  "label": "Security research & ethical hacking","icon": "bi-shield-lock"},
    {"key": "cloud_infra",        "label": "Managing cloud infrastructure",   "icon": "bi-cloud"},
    {"key": "mobile_apps",        "label": "Building mobile apps",            "icon": "bi-phone"},
    {"key": "open_source",        "label": "Contributing to open source",     "icon": "bi-github"},
    {"key": "research_papers",    "label": "Reading & writing research papers","icon": "bi-journal-text"},
    {"key": "automation",         "label": "Automation & scripting",          "icon": "bi-gear"},
    {"key": "teaching_others",    "label": "Teaching / mentoring others",     "icon": "bi-people"},
    {"key": "startups",           "label": "Building startups & products",    "icon": "bi-rocket"},
]

# ── Technology definitions ─────────────────────────────────────────────────────
TECHNOLOGIES = {
    "AI / ML": ["TensorFlow", "PyTorch", "scikit-learn", "Keras", "Hugging Face", "OpenCV"],
    "Data": ["pandas", "NumPy", "Matplotlib / Seaborn", "Power BI", "Tableau", "Apache Spark"],
    "Web": ["React", "Vue.js", "Angular", "Node.js", "Django", "Flask", "FastAPI"],
    "Cloud & DevOps": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Git / GitHub"],
    "Security": ["Wireshark", "Metasploit", "Burp Suite", "Nmap", "Kali Linux"],
}


def _require_session():
    """
    Check that student_id exists in the session.
    Returns the student_id (int) if found, or None if not.
    The caller should redirect if None is returned.
    """
    return session.get("student_id")


@assessment_bp.route("/", methods=["GET", "POST"])
def index():
    """
    GET  → Show the assessment form.
    POST → Validate, save to DB, redirect to submitted confirmation page.
    """
    # ── Session guard ─────────────────────────────────────────────────────────
    student_id = _require_session()
    if not student_id:
        flash("Please complete your profile first before taking the assessment.", "warning")
        return redirect(url_for("profile.index"))

    if request.method == "POST":
        return _handle_post(student_id)

    # GET — fetch student name for personalised greeting
    db = get_db()
    student = db.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    student_name = student["name"] if student else session.get("student_name", "Student")

    return render_template(
        "assessment.html",
        student_name=student_name,
        skills=SKILLS,
        interests=INTERESTS,
        technologies=TECHNOLOGIES,
        proficiency_labels=PROFICIENCY_LABELS,
    )


def _handle_post(student_id):
    """
    Parse, validate, and save a submitted assessment form.
    Kept as a separate function to keep index() readable.
    """
    form = request.form

    # ── Section A: Skills ─────────────────────────────────────────────────────
    # For each skill the user checked, read its proficiency slider value (1–5).
    # Unchecked skills are simply omitted from the dict (proficiency = 0 / not selected).
    skills = {}
    for skill in SKILLS:
        k = skill["key"]
        if form.get(f"skill_{k}"):               # checkbox was ticked
            prof = form.get(f"prof_{k}", "1")
            try:
                prof_int = max(1, min(5, int(prof)))
            except ValueError:
                prof_int = 1
            skills[k] = prof_int

    # ── Section B: Interests ──────────────────────────────────────────────────
    interests = [i["key"] for i in INTERESTS if form.get(f"interest_{i['key']}")]

    # ── Section C: Technologies ───────────────────────────────────────────────
    technologies = []
    for group_techs in TECHNOLOGIES.values():
        for tech in group_techs:
            safe_key = tech.replace(" ", "_").replace("/", "_").replace(".", "_")
            if form.get(f"tech_{safe_key}"):
                technologies.append(tech)

    # ── Section D: Career Goals ───────────────────────────────────────────────
    goals = {
        "short_term_role":  form.get("short_term_role",  "").strip(),
        "work_style":       form.get("work_style",       "").strip(),
        "dream_role":       form.get("dream_role",       "").strip()[:500],
        "learning_style":   form.get("learning_style",   "").strip(),
    }

    # ── Server-side validation ────────────────────────────────────────────────
    errors = []
    if len(skills) < 3:
        errors.append("Please rate at least 3 skills so we can make accurate recommendations.")
    if len(interests) < 2:
        errors.append("Please select at least 2 interests.")
    if not goals["short_term_role"]:
        errors.append("Please select your short-term career goal.")
    if not goals["work_style"]:
        errors.append("Please select a preferred work style.")

    if errors:
        for e in errors:
            flash(e, "danger")
        db = get_db()
        student = db.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
        student_name = student["name"] if student else session.get("student_name", "Student")
        # Re-render with submitted values so user doesn't lose their work
        return render_template(
            "assessment.html",
            student_name=student_name,
            skills=SKILLS,
            interests=INTERESTS,
            technologies=TECHNOLOGIES,
            proficiency_labels=PROFICIENCY_LABELS,
            submitted_skills=skills,
            submitted_interests=interests,
            submitted_technologies=technologies,
            submitted_goals=goals,
        ), 422

    # ── Save to database ──────────────────────────────────────────────────────
    # json.dumps() converts a Python dict/list → a JSON string for storage.
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO assessments
            (student_id, skills_json, interests_json, technologies_json, goals_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            student_id,
            json.dumps(skills),
            json.dumps(interests),
            json.dumps(technologies),
            json.dumps(goals),
        )
    )
    db.commit()
    assessment_id = cursor.lastrowid

    # Store latest assessment_id in session so Results page can access it
    session["assessment_id"] = assessment_id

    # Redirect straight to the results page — the engine runs there
    return redirect(url_for("results.show", assessment_id=assessment_id))


@assessment_bp.route("/submitted/<int:assessment_id>")
def submitted(assessment_id):
    """
    Success page shown after a valid assessment submission.
    Also reachable later to review a past submission.
    """
    student_id = _require_session()
    if not student_id:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("profile.index"))

    db = get_db()
    # Fetch the assessment and verify it belongs to this student
    row = db.execute(
        "SELECT * FROM assessments WHERE id = ? AND student_id = ?",
        (assessment_id, student_id)
    ).fetchone()

    if not row:
        flash("Assessment not found or does not belong to your profile.", "danger")
        return redirect(url_for("assessment.index"))

    # Decode the JSON blobs back into Python objects for display
    skills_data   = json.loads(row["skills_json"]       or "{}")
    interests     = json.loads(row["interests_json"]    or "[]")
    technologies  = json.loads(row["technologies_json"] or "[]")
    goals         = json.loads(row["goals_json"]        or "{}")

    # Build a human-readable skill list: [{"label": "Python", "proficiency": "Advanced"}]
    skill_label_map = {s["key"]: s["label"] for s in SKILLS}
    skills_display = [
        {"label": skill_label_map.get(k, k), "proficiency": PROFICIENCY_LABELS.get(str(v), str(v))}
        for k, v in skills_data.items()
    ]

    interest_label_map = {i["key"]: i["label"] for i in INTERESTS}
    interests_display = [interest_label_map.get(k, k) for k in interests]

    # Count how many previous assessments this student has taken
    count = db.execute(
        "SELECT COUNT(*) FROM assessments WHERE student_id = ?", (student_id,)
    ).fetchone()[0]

    student_name = session.get("student_name", "Student")

    return render_template(
        "assessment_submitted.html",
        assessment_id=assessment_id,
        student_name=student_name,
        skills_display=skills_display,
        interests_display=interests_display,
        technologies=technologies,
        goals=goals,
        submitted_at=row["submitted_at"],
        total_assessments=count,
    )
