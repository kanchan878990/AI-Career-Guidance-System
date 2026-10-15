# AI Career Guidance System

A full-stack web application that helps CSE / AI-ML students identify suitable career paths
based on their self-reported skills, interests, education, preferred technologies, and career
goals. Built with Python, Flask, pandas, and Bootstrap 5.

> **Status:** All core phases complete and tested.

---

## Features

| Feature | Status |
|---------|--------|
| Landing page — hero section, career overview cards, CTA | ✅ |
| Student profile form (`/profile/`) | ✅ |
| Career assessment form — 4 scrollable sections (`/assessment/`) | ✅ |
| Rule-based career recommendation engine | ✅ |
| Results dashboard — top 3 careers (`/results/<id>`) | ✅ |
| Match explanations, missing skills, suggested technologies | ✅ |
| Per-career learning roadmap with priority steps | ✅ |
| Assessment history preserved on every retake | ✅ |
| Flask session-based student tracking | ✅ |
| Responsive UI — Bootstrap 5, mobile-friendly | ✅ |
| Print / Save as PDF button | ✅ |
| SQLite database — auto-created on first run | ✅ |

---

## Quick Start

### Requirements

- Python 3.10 or later
- pip (bundled with Python)

---

### Step 1 — Navigate to the project folder

```bash
cd "AI Career Guidance System"
```

---

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

---

### Step 3 — Activate the virtual environment

**Windows — PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

**Windows — Command Prompt:**

```cmd
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

After activation your terminal prompt should show `(venv)`.

---

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — (Optional) Create a `.env` file

Create a file named `.env` in the project root and add:

```
SECRET_KEY=replace-this-with-a-long-random-string
FLASK_DEBUG=true
```

If this file is absent, the application falls back to a hard-coded development key.
**Never deploy to production with the fallback key.**

---

### Step 6 — Run the application

```bash
python run.py
```

Open your browser at: **http://127.0.0.1:5000**

The SQLite database file is created automatically inside `instance/` the first time the
application starts. No manual database setup is required.

---

## Running the Tests

The project includes an automated test suite in `test_audit.py` containing **36 verified tests** built with Python's standard `unittest` module and Flask's test client (no third-party test runners or additional packages required).

### How to Run

**Windows (PowerShell — direct execution, no activation required):**

```powershell
.\venv\Scripts\python.exe test_audit.py
```

**Windows (Command Prompt):**

```cmd
venv\Scripts\python.exe test_audit.py
```

**With activated virtual environment (all platforms):**

```bash
python test_audit.py
```

### Expected Output

```
Ran 36 tests in ~1.3s

OK
```

### Test Suite Structure (36 Tests)

The 36 tests are grouped into 6 focused test suites covering end-to-end routing, validation, security guards, and algorithm logic:

| Suite | Tests | Description |
|-------|:-----:|-------------|
| **1. Public Pages** (`TestPublicPages`) | 6 | Verifies unauthenticated access to landing page (`/`), brand name presence ("CareerGuide"), about page (`/about`), profile form (`/profile/`), name input field presence, and 404 handler for non-existent routes. |
| **2. Registered Routes** (`TestRegisteredRoutes`) | 6 | Ensures all blueprint URL patterns are registered in the Flask URL map: `/`, `/about`, `/profile/`, `/assessment/`, `/results/latest`, and `/results/<assessment_id>`. |
| **3. Profile Form Validation** (`TestProfileValidation`) | 6 | Validates server-side constraints: valid submission redirect to `/assessment/` (302), required name, required education level, required field of study, invalid email rejection, and acceptance of blank optional email. |
| **4. Session Guards** (`TestSessionGuards`) | 5 | Ensures unauthenticated visitors attempting to access `/assessment/` (GET/POST) or `/results/` are redirected to `/profile/`. Also ensures non-existent result IDs redirect safely without HTTP 500 errors. |
| **5. Assessment Page & Validation** (`TestAssessmentPage`) | 5 | Verifies authenticated `/assessment/` GET (200 OK), presence of all 4 form sections (`skills`, `interests`, `tech`, `goals`), valid assessment submission redirect, minimum skill threshold enforcement (≥3 required), and minimum interest threshold enforcement (≥2 required). |
| **6. Recommendation Scorer Engine** (`TestScorerUnit`) | 8 | Unit tests for pure scoring functions in `app/engine/scorer.py`: generates recommendations for all 7 careers, score boundary guarantees (0–100), descending ranking order, required response schema keys, accurate top ranking for AI/ML profile, accurate top ranking for Web profile, graceful empty payload handling, and resilience against malformed/invalid JSON. |

If any test fails after a fresh install, check the Troubleshooting section below.

---

## Application Flow

```
http://127.0.0.1:5000             Landing page
    ↓  "Start Your Assessment"
/profile/                         Enter name, education, field of study
    ↓  "Save & Continue"
/assessment/                      Rate skills, pick interests, set goals
    ↓  "Submit Assessment"
/results/<assessment_id>          View top 3 career recommendations
    ↓  "Retake Assessment"        Creates a new row; previous data preserved
/assessment/
```

---

## Project Structure

```
AI Career Guidance System/
│
├── app/
│   ├── __init__.py               Flask app factory
│   ├── config.py                 Secret key, DB path, debug flag
│   ├── database.py               SQLite helpers: get_db, init_db, close_db
│   ├── models.py                 Python dataclasses mirroring DB tables
│   │
│   ├── routes/
│   │   ├── main.py               Landing page (/)
│   │   ├── profile.py            /profile/ — student profile form
│   │   ├── assessment.py         /assessment/ — career assessment form
│   │   └── results.py            /results/<id> — recommendation dashboard
│   │
│   ├── engine/
│   │   ├── career_data.py        Loads and validates career_profiles.csv
│   │   ├── scorer.py             Rule-based weighted compatibility scorer
│   │   └── roadmap.py            Per-career learning roadmap generator
│   │
│   ├── static/
│   │   ├── css/style.css         Custom design on top of Bootstrap 5
│   │   └── js/
│   │       ├── assessment.js     Skill sliders, interest cards, progress bar
│   │       └── results.js        Animated score bars (IntersectionObserver)
│   │
│   └── templates/
│       ├── base.html                  Shared navbar and footer
│       ├── landing.html               Home page
│       ├── profile.html               Profile form
│       ├── profile_success.html       Post-profile confirmation
│       ├── assessment.html            Assessment form (4 sections)
│       ├── assessment_submitted.html  Post-assessment summary
│       └── results.html               Recommendation dashboard
│
├── data/
│   └── career_profiles.csv       Career definitions, skill weights, keywords
│
├── instance/
│   └── career_guidance.db        SQLite database (auto-created; excluded from git)
│
├── test_audit.py                 Automated test suite (36 tests, unittest)
├── requirements.txt              Python dependencies
├── run.py                        Development server entry point
└── README.md
```

---

## Technology Stack

| Technology | Role |
|-----------|------|
| Python 3.10+ | Backend language |
| Flask 3.0 | Web framework and HTTP routing |
| Jinja2 | Server-side HTML templating (bundled with Flask) |
| SQLite | Lightweight file-based relational database |
| pandas | Loading and parsing `career_profiles.csv` |
| scikit-learn | Installed as a dependency; reserved for a future ML model layer |
| numpy | Numerical support (dependency of pandas / scikit-learn) |
| python-dotenv | Reads `.env` file into environment variables |
| Bootstrap 5 | Responsive CSS framework (loaded via CDN) |
| Bootstrap Icons | Icon font (loaded via CDN) |
| Vanilla JavaScript | Assessment interactivity and score bar animations |

---

## Recommendation Engine

The engine in `app/engine/scorer.py` is a **rule-based weighted scoring system**.
It compares a student's self-reported assessment against documented requirements for each
career path defined in `data/career_profiles.csv`.

**scikit-learn is installed but is not used for model training or inference in the current
version.** It is available as a foundation for a future supervised learning layer once
labeled student-outcome data exists.

### Compatibility Score (0–100)

Each career receives a score made up of five components. The weights below are taken
directly from `app/engine/scorer.py`:

| Component | Max pts | What it measures |
|-----------|--------:|-----------------|
| Skill presence | 30 | Proportion of required skills the student has rated ≥ 1 |
| Skill proficiency | 25 | Student's depth of skill relative to how critical each skill is for that career |
| Interest alignment | 20 | Overlap between selected interests and the career's required / bonus interests |
| Technology overlap | 10 | Technologies the student knows that appear in the career's tech stack |
| Goal alignment | 15 | Short-term role selection and keyword matches in the student's dream-role text |
| **Total** | **100** | |

> **Important:** Compatibility scores are alignment indicators based entirely on
> self-reported information. They are not probabilities of employment and should be used
> as a starting point for your own research, not as definitive career advice.

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `students` | One row per profile submission — name, email, education level, field of study |
| `assessments` | One row per submission attempt, linked to a student; skills, interests, technologies, and goals stored as JSON |
| `results` | Three rows per assessment (one per recommended career); full history is preserved on every retake |

---

## Session Handling

This application uses **Flask's built-in session mechanism** (a signed browser cookie) to
track which student is active. This is a convenience mechanism, not a full authentication
system. Key points:

- No user account, password, or login page exists.
- The session persists as long as the browser cookie is valid (by default, until the browser
  session ends or the cookie expires).
- Clearing browser cookies or opening an incognito window starts a fresh session.
- All submitted data — profile, assessments, and results — is stored permanently in SQLite
  and is not lost when a session ends. A student can rebuild their session by filling the
  profile form again.

---

## Screenshots

Recommended screenshots to capture for submission or documentation.
After taking them, save the image files in a `screenshots/` folder at the project root and
replace the placeholder paths below with the actual filenames.

| Screenshot | What to show |
|-----------|-------------|
| `screenshots/01-landing.png` | Full landing page — hero section and career cards grid |
| `screenshots/02-profile-form.png` | Profile form with all fields visible |
| `screenshots/03-assessment-skills.png` | Assessment page — skill checkboxes with proficiency sliders revealed |
| `screenshots/04-assessment-interests.png` | Interest cards section with selected cards highlighted |
| `screenshots/05-assessment-goals.png` | Goals section — work-style cards and short-term role dropdown |
| `screenshots/06-results-dashboard.png` | Results page — all three career recommendation cards with score bars |
| `screenshots/07-results-roadmap.png` | Learning roadmap accordion expanded for the top match |
| `screenshots/08-print-layout.png` | Browser print preview — clean layout with navbar and buttons hidden |

To link them once captured, add image references to this README:

```markdown
![Landing Page](screenshots/01-landing.png)
```

---

## GitHub Setup

### What to commit

- All files under `app/` (source code, templates, static assets)
- `data/career_profiles.csv`
- `requirements.txt`
- `run.py`
- `test_audit.py` (automated test suite)
- `README.md`
- `ai-career-guidance-plan.md` (optional — project planning document)

### What to exclude (add to `.gitignore`)

```
# Virtual environment
venv/
.venv/

# Python bytecode cache
__pycache__/
*.py[cod]

# Secret / environment configuration
.env
.env.*
!.env.example

# SQLite database (contains student and test data — never commit)
instance/*.db
instance/*.sqlite
instance/*.sqlite3

# OS files
.DS_Store
Thumbs.db
```

> **Never commit** your `.env` file, the `instance/` database, or any file containing a
> real `SECRET_KEY`, API key, password, or personal student data.

### License

This project does not currently include a `LICENSE` file. Before publishing publicly on
GitHub, choose an appropriate open-source license — for example MIT, Apache 2.0, or
GPL — and add a `LICENSE` file to the repository root. GitHub provides a license picker
when creating or editing a repository.

---

## Known Limitations

| Limitation | Notes |
|-----------|-------|
| No login / authentication system | Student tracking uses Flask session cookies, not accounts. See the Session Handling section above. |
| Rule-based scorer only | Scores are weighted alignment calculations; no ML model has been trained. scikit-learn is available for a future phase. |
| 7 career paths only | DevOps Engineer and UI/UX Designer are planned for a future release; adding them requires only new rows in `career_profiles.csv`. |
| Contact email not used | Email is collected on the profile form but is not sent or verified. |
| Development server only | `python run.py` uses Flask's built-in server. For production, use Gunicorn or uWSGI behind a reverse proxy such as Nginx. |

---

## Stopping the Server

Press `Ctrl + C` in the terminal where `python run.py` is running.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `ModuleNotFoundError: No module named 'flask'` | Make sure the virtual environment is active (`(venv)` in prompt), then run `pip install -r requirements.txt` |
| Port 5000 already in use | Edit `run.py` and change `port=5000` to `port=5001`, then visit `http://127.0.0.1:5001` |
| `Activate.ps1 cannot be loaded` (PowerShell) | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` once and retry. Alternatively, call the venv Python directly (see below). |
| Database file missing | The `instance/career_guidance.db` file is created automatically when the application starts for the first time. If it is missing, just run `python run.py`. |
| Tests fail after fresh install | Ensure the virtual environment is active and all packages are installed. Run `pip install -r requirements.txt` again if unsure. |

### Using the virtual environment Python directly

If activating the virtual environment fails, you can run any command by calling the
interpreter inside `venv\Scripts\` directly:

```powershell
.\venv\Scripts\python.exe run.py
.\venv\Scripts\python.exe test_audit.py
```

This bypasses the need to activate and works in any shell.
