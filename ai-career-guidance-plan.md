# AI Career Guidance System — Project Plan

## Top-Level Overview

**Goal:** Build a full-stack web application that helps CSE/AI-ML students identify suitable career paths based on their skills, interests, education, preferred technologies, and career goals.

**Scope:**
- A short landing + profile form (Phase 1)
- A dedicated multi-section assessment page (Phase 2)
- A recommendation engine using scikit-learn (Phase 3)
- A results/roadmap dashboard (Phase 4)
- SQLite persistence for student profiles and results (all phases)

**Approach:** Incremental, phase-by-phase delivery. Each phase produces a working, visible result before the next begins. No phase claims "AI is working" until the model is actually trained and tested.

**Non-Goals (for now):**
- User authentication / login system
- External APIs or cloud deployment
- Mobile native app

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.10+ / Flask | HTTP server, routing, API endpoints |
| Recommendation | scikit-learn, pandas, numpy | Career matching algorithm |
| Database | SQLite + sqlite3 (stdlib) | Persist profiles and results |
| Frontend | HTML5 + CSS3 + JavaScript (ES6) | Pages and interactivity |
| CSS Framework | Bootstrap 5 | Responsive layout, components |
| Icons | Bootstrap Icons or Font Awesome 6 | UI icons |
| Templating | Jinja2 (built into Flask) | Server-side HTML rendering |
| Data Seeding | CSV file read via pandas | Career profiles and skill weights |

---

## Supported Career Paths (Initial)

1. AI/ML Engineer
2. Data Scientist
3. Data Analyst
4. Software Developer
5. Web Developer
6. Cybersecurity Analyst
7. Cloud Engineer

---

## Feature List

### Phase 1 — Foundation + Profile Form
- Project scaffold (folder structure, Flask app factory, config)
- SQLite schema creation on first run
- Landing page: hero section, "Get Started" CTA, brief description of each career path
- Student profile form: name, email, education level, field of study
- Profile saved to SQLite; redirects to assessment

### Phase 2 — Assessment Page
- Full assessment page with all sections visible at once (scroll-based)
- Section A — Skills (checkboxes + proficiency sliders): Python, ML, Statistics, SQL, Web, Cloud, Security, etc.
- Section B — Interests (multi-select cards): building products, analyzing data, solving security problems, etc.
- Section C — Preferred Technologies (checkboxes): TensorFlow, React, AWS, Docker, etc.
- Section D — Career Goals (radio + text): short-term role, dream company type, work style
- Progress indicator bar (purely visual, JS-driven)
- Assessment answers saved to SQLite on submit

### Phase 3 — Recommendation Engine
- Career profiles dataset (CSV): each career mapped to required skills, typical interests, key technologies, and goal alignment scores
- Rule-based scoring layer first (transparent, beginner-understandable)
- scikit-learn cosine similarity or KNN layer on top for ranking
- Each recommendation includes: match percentage, why-matched explanation, missing skills list
- Results stored in SQLite linked to the student profile

### Phase 4 — Results Dashboard
- Clean dashboard showing top 3 recommended careers as cards
- Each card: career title, match %, top matching skills, 2–3 sentence explanation
- "Missing Skills" section: skills the student should develop
- Learning Roadmap section: ordered list of resources/steps per recommended career
- "Retake Assessment" and "Download PDF" (basic HTML print) buttons
- Navigation bar linking Landing → Assessment → Results

---

## Folder Structure

```
AI Career Guidance System/
│
├── app/
│   ├── __init__.py          # Flask app factory — creates the app and registers blueprints
│   ├── config.py            # Configuration (database path, secret key, debug flag)
│   ├── database.py          # SQLite helpers — get_db(), init_db(), close_db()
│   ├── models.py            # Pure Python dataclasses representing DB rows (no ORM needed)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Landing page, about
│   │   ├── profile.py       # Profile form GET/POST
│   │   ├── assessment.py    # Assessment form GET/POST
│   │   └── results.py       # Results dashboard GET
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── career_data.py   # Loads career_profiles.csv into pandas DataFrames
│   │   ├── scorer.py        # Rule-based scoring + cosine similarity ranking
│   │   └── roadmap.py       # Generates learning roadmap per recommended career
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Custom styles on top of Bootstrap
│   │   ├── js/
│   │   │   ├── assessment.js   # Progress bar, slider labels, form validation
│   │   │   └── results.js      # Animate match percentage counters
│   │   └── images/
│   │       └── hero-bg.svg  # Landing page hero illustration
│   │
│   └── templates/
│       ├── base.html        # Base layout: navbar, Bootstrap CDN, footer
│       ├── landing.html     # Landing/home page
│       ├── profile.html     # Student profile form
│       ├── assessment.html  # Full assessment page (all sections)
│       └── results.html     # Results dashboard
│
├── data/
│   └── career_profiles.csv  # Career definitions: skills, interests, tech, goals, weights
│
├── instance/
│   └── career_guidance.db   # SQLite database file (auto-created, git-ignored)
│
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point: creates app and runs dev server
└── .gitignore
```

---

## SQLite Database Design

### Table: `students`
Stores the basic profile collected on the first form.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique student ID |
| `name` | TEXT NOT NULL | Student's full name |
| `email` | TEXT | Optional contact email |
| `education_level` | TEXT | e.g. "High School", "Undergraduate", "Graduate" |
| `field_of_study` | TEXT | e.g. "Computer Science", "Electronics" |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | When profile was created |

### Table: `assessments`
Stores the full assessment form submission. One row per student attempt.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique assessment ID |
| `student_id` | INTEGER REFERENCES students(id) | Links to the student profile |
| `skills_json` | TEXT | JSON blob: skill name → proficiency (0–5) |
| `interests_json` | TEXT | JSON blob: list of selected interest tags |
| `technologies_json` | TEXT | JSON blob: list of selected technologies |
| `goals_json` | TEXT | JSON blob: short-term goal, work style, dream role |
| `submitted_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | When form was submitted |

### Table: `results`
Stores computed recommendations for each assessment.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique result ID |
| `assessment_id` | INTEGER REFERENCES assessments(id) | Links to the assessment |
| `career_name` | TEXT | e.g. "Data Scientist" |
| `match_score` | REAL | 0.0 – 1.0 match percentage |
| `match_reasons_json` | TEXT | JSON list of why-matched strings |
| `missing_skills_json` | TEXT | JSON list of skills to develop |
| `roadmap_json` | TEXT | JSON list of ordered learning steps |
| `rank` | INTEGER | 1 = best match, 2 = second, etc. |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | When result was computed |

### Relationships (Entity Diagram)

```
students (1) ──< assessments (1) ──< results
```

One student can have multiple assessments over time (retake); each assessment produces multiple result rows (one per career recommendation returned).

---

## Data File: `career_profiles.csv`

Each row defines one career path and what student attributes align with it.

**Columns:**
- `career_name` — human-readable name
- `required_skills` — pipe-separated list: `python|statistics|ml`
- `bonus_skills` — nice-to-have: `deep_learning|docker`
- `typical_interests` — pipe-separated interest tags
- `key_technologies` — pipe-separated tech tags
- `goal_keywords` — keywords in goal text that boost score
- `skill_weights` — JSON dict mapping skill → weight multiplier

---

## Implementation Phases (Sub-Tasks)

---

### Sub-Task 1 — Project Scaffold & Database Init
**Status:** `[x] done`

**Intent:** Create the folder structure, Flask app factory, config, database schema, `run.py`, and `requirements.txt`. This gives a runnable (empty) app from day one.

**Expected Outcomes:**
- `python run.py` starts the Flask dev server with no errors
- SQLite DB is created automatically in `instance/` on first run
- All three tables (`students`, `assessments`, `results`) exist
- A placeholder "hello" route returns 200

**Todo List:**
1. Create `requirements.txt` with Flask, scikit-learn, pandas, numpy
2. Create `run.py` entry point
3. Create `app/__init__.py` app factory with `create_app()`
4. Create `app/config.py` with `DATABASE`, `SECRET_KEY`, `DEBUG`
5. Create `app/database.py` with `get_db()`, `init_db()`, `close_db()`
6. Write `schema.sql` (or inline SQL) for all three tables
7. Register `init_db()` in app factory using `with app.app_context()`
8. Create `app/routes/__init__.py` and `app/routes/main.py` with a `/` placeholder route
9. Create `.gitignore` ignoring `instance/`, `__pycache__/`, `*.pyc`, `.env`

**Relevant Context:** `app/__init__.py`, `app/database.py`, `app/config.py`

---

### Sub-Task 2 — Landing Page + Base Layout
**Status:** `[x] done` *(merged into Phase 1 delivery)*

**Intent:** Build `base.html` (navbar + footer) and `landing.html` (hero + career cards overview). This is the visual entry point — first impressions matter.

**Expected Outcomes:**
- Visiting `/` shows a styled landing page
- Navbar has logo, "Home", "Get Started" links
- Hero section with headline, sub-headline, CTA button → `/profile`
- Career cards section: 7 cards in a responsive grid, each with icon, title, 1-line description
- Footer with project name and tagline
- Page is fully responsive on mobile and desktop

**Todo List:**
1. Create `app/templates/base.html` with Bootstrap 5 CDN, Bootstrap Icons CDN, navbar, footer
2. Create `app/static/css/style.css` with custom color palette, font choices, card hover effects
3. Create `app/templates/landing.html` extending `base.html`
4. Build hero section with gradient background, headline, sub-headline, CTA
5. Build 7 career cards using Bootstrap card + grid (responsive: 1 col mobile, 3–4 col desktop)
6. Register `landing` route in `app/routes/main.py`
7. Register `main` blueprint in app factory

**Relevant Context:** `app/templates/`, `app/static/css/style.css`, `app/routes/main.py`

---

### Sub-Task 3 — Student Profile Form
**Status:** `[ ] pending`

**Intent:** Build the short profile form (name, email, education level, field of study), validate and persist to `students` table, redirect to assessment.

**Expected Outcomes:**
- GET `/profile` shows a clean, centered form
- POST `/profile` validates inputs, inserts a row into `students`, stores `student_id` in Flask session, redirects to `/assessment`
- Inline validation errors shown if required fields are empty
- Form is styled with Bootstrap form components

**Todo List:**
1. Create `app/templates/profile.html` extending `base.html`
2. Build form with name (required), email (optional), education level (select), field of study (text)
3. Create `app/routes/profile.py` with GET and POST handlers
4. On POST: validate → insert into `students` → store `student_id` in session → redirect
5. Show flash messages for validation errors
6. Register `profile` blueprint in app factory

**Relevant Context:** `app/routes/profile.py`, `app/database.py`, `app/templates/profile.html`

---

### Sub-Task 4 — Assessment Page
**Status:** `[ ] pending`

**Intent:** Build the full assessment page with all four sections visible at once (scroll-based). Collect skills, interests, technologies, and career goals. Save to `assessments` table.

**Expected Outcomes:**
- GET `/assessment` shows all four sections in one scrollable page
- Section A: ~12 skill checkboxes, each with a 0–5 proficiency slider (visible only when checkbox is checked)
- Section B: interest multi-select cards (toggle on click with visual feedback)
- Section C: technology checkboxes grouped by category
- Section D: career goals — short-term role (select), work style (radio), dream role description (text)
- JS progress bar updates as user fills sections
- POST `/assessment` serializes answers to JSON, saves to `assessments` table, redirects to `/results/<assessment_id>`
- Assessment is linked to `student_id` from session

**Todo List:**
1. Create `app/templates/assessment.html` extending `base.html`
2. Build Section A markup: skill checkbox + range slider pairs (hidden until checked via JS)
3. Build Section B markup: interest tag cards with toggle selection
4. Build Section C markup: technology checkboxes grouped by category (ML, Web, Cloud, Security)
5. Build Section D markup: goal select, work style radios, dream role text area
6. Create `app/static/js/assessment.js`: progress bar logic, slider show/hide, toggle card selection
7. Create `app/routes/assessment.py` GET handler (requires session `student_id`)
8. Create POST handler: parse form, serialize to JSON blobs, insert into `assessments`, redirect to results
9. Register `assessment` blueprint in app factory

**Relevant Context:** `app/routes/assessment.py`, `app/static/js/assessment.js`, `app/templates/assessment.html`

---

### Sub-Task 5 — Career Data File + Recommendation Engine
**Status:** `[ ] pending`

**Intent:** Create `career_profiles.csv`, load it with pandas, implement rule-based scoring, and layer cosine similarity on top to produce ranked career recommendations with explanations.

**Expected Outcomes:**
- `data/career_profiles.csv` has rows for all 7 careers with skill weights, interest tags, tech tags
- `app/engine/career_data.py` loads and exposes the DataFrame
- `app/engine/scorer.py` accepts a student assessment dict and returns a ranked list of career dicts: `{career_name, match_score, match_reasons, missing_skills}`
- `app/engine/roadmap.py` returns an ordered list of learning steps for a given career + missing skills
- Unit-level print test (not UI) confirms scores are non-zero and reasonable
- Results written to `results` table via `app/routes/results.py`

**Todo List:**
1. Create `data/career_profiles.csv` with all 7 career rows and all required columns
2. Create `app/engine/__init__.py`
3. Create `app/engine/career_data.py`: load CSV, expose `get_career_df()`
4. Create `app/engine/scorer.py`: build student feature vector, build career feature matrix, compute cosine similarity score, generate match reasons and missing skills
5. Create `app/engine/roadmap.py`: define per-career roadmap steps, filter/order by student's missing skills
6. Create `app/routes/results.py`: load assessment from DB, call scorer, save results to `results` table, pass to template
7. Register `results` blueprint in app factory
8. Add a simple `python -c "from app.engine.scorer import score; print(score(...))"` smoke test in plan notes

**Relevant Context:** `app/engine/`, `data/career_profiles.csv`, `app/routes/results.py`

---

### Sub-Task 6 — Results Dashboard
**Status:** `[ ] pending`

**Intent:** Build the results page that displays the top 3 career recommendations as rich cards, explains why each matches, lists missing skills, and shows a learning roadmap.

**Expected Outcomes:**
- GET `/results/<assessment_id>` renders the dashboard
- Top 3 career cards: title, icon, animated match % bar, 2–3 reason bullet points
- "Missing Skills" section: tag-style badges
- "Learning Roadmap" section: numbered step list for the top recommended career (expandable for others)
- "Retake Assessment" button clears assessment session and goes to `/assessment`
- "Print / Save as PDF" button triggers `window.print()`
- Page is fully responsive

**Todo List:**
1. Create `app/templates/results.html` extending `base.html`
2. Build top 3 career recommendation cards with Bootstrap progress bars for match %
3. Build match reasons list per card (bullet points from `match_reasons_json`)
4. Build missing skills badge section
5. Build learning roadmap accordion (Bootstrap accordion component) — one panel per career
6. Add "Retake" and "Print" buttons
7. Create `app/static/js/results.js`: animate match % progress bars on page load using `IntersectionObserver`
8. Ensure `app/routes/results.py` queries the `results` table and passes data to template

**Relevant Context:** `app/templates/results.html`, `app/static/js/results.js`, `app/routes/results.py`

---

## Component Responsibility Summary

| Component | Responsibility |
|-----------|---------------|
| `app/__init__.py` | Creates and configures the Flask app, registers blueprints |
| `app/config.py` | Central config — DB path, secret key, debug mode |
| `app/database.py` | Opens/closes SQLite connection per request, creates tables |
| `app/routes/main.py` | Landing page route |
| `app/routes/profile.py` | Profile form routes, session setup |
| `app/routes/assessment.py` | Assessment form routes, saves to DB |
| `app/routes/results.py` | Loads results from DB, calls engine, renders dashboard |
| `app/engine/career_data.py` | Loads `career_profiles.csv` into a usable DataFrame |
| `app/engine/scorer.py` | Core recommendation logic — scoring + explanation |
| `app/engine/roadmap.py` | Generates ordered learning roadmap per career |
| `app/templates/base.html` | Shared layout: navbar, Bootstrap, footer |
| `app/static/css/style.css` | Custom visual design on top of Bootstrap |
| `app/static/js/assessment.js` | Assessment page interactivity |
| `app/static/js/results.js` | Results dashboard animations |
| `data/career_profiles.csv` | Source of truth for career definitions and scoring weights |
| `instance/career_guidance.db` | SQLite database — auto-created, not committed to git |
