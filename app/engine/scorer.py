# ──────────────────────────────────────────────────────────────────────────────
# app/engine/scorer.py
#
# Transparent, weighted compatibility scorer.
#
# IMPORTANT — What this is and what it is NOT:
#   This is a rule-based, weighted scoring system built from documented career
#   requirements. It has NOT been trained on real student outcome data and does
#   NOT predict employment probability. Scores reflect how well a student's
#   self-reported skills and interests align with published career requirements.
#
# Scoring breakdown (100 points total per career):
#
#   Component              Max pts  Notes
#   ─────────────────────────────────────────────────────────────────────────
#   A. Skill presence       30      Required skills the student has rated ≥ 1
#   B. Skill proficiency    25      Weighted average proficiency on required skills
#   C. Interest alignment   20      Required + bonus interests matched
#   D. Technology overlap   10      Known technologies matching career stack
#   E. Goal alignment       15      short_term_role match + dream_role keywords
#   ─────────────────────────────────────────────────────────────────────────
#   Total                  100
#
# Design goal: every point deducted or added is traceable to a specific
# piece of student data, making the score explainable.
# ──────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import json
from typing import Any
from app.engine.career_data import get_careers
from app.engine.vectorizer import (
    get_or_build_career_matrix,
    compute_cosine_similarities,
    evaluate_confidence,
)

# Maximum points for each component (must sum to 100)
_MAX_SKILL_PRESENCE    = 30
_MAX_SKILL_PROFICIENCY = 25
_MAX_INTERESTS         = 20
_MAX_TECHNOLOGY        = 10
_MAX_GOAL              = 15

# Human-readable labels for proficiency integers
PROF_LABELS = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}


# ── Public entry point ────────────────────────────────────────────────────────

def score_assessment(assessment_row: Any) -> list[dict]:
    """
    Score a student's assessment against all career profiles using a calibrated
    hybrid model combining scikit-learn Cosine Similarity (40%) and domain
    qualification heuristics (60%).

    Parameters
    ----------
    assessment_row : sqlite3.Row or dict
        One row from the  assessments  table.  Must have the keys:
        skills_json, interests_json, technologies_json, goals_json.

    Returns
    -------
    list of dicts, sorted by score descending. Each dict contains:
        career_name        str
        score              int   0–100 (hybrid compatibility)
        cosine_similarity  int   0–100 (vector semantic alignment)
        rule_score         int   0–100 (qualification rules)
        confidence_level   str   "High" | "Moderate" | "Preliminary"
        match_reasons      list[str]   human-readable explanations
        missing_skills     list[str]   important skills to develop
        suggested_techs    list[str]   technologies to learn
        skill_breakdown    dict        per-component scores + vector metrics
    """
    # ── Parse JSON fields safely ──────────────────────────────────────────────
    student = _parse_assessment(assessment_row)
    careers = get_careers()
    career_matrix = get_or_build_career_matrix(careers)

    # ── Vector Space Cosine Similarity & Deterministic Confidence ─────────────
    cosine_sims = compute_cosine_similarities(student, career_matrix)
    confidence = evaluate_confidence(student)

    results = []
    for idx, career in enumerate(careers):
        rule_result = _score_one(student, career)
        rule_score = rule_result["score"]

        cos_sim = float(cosine_sims[idx])
        cos_score = int(round(cos_sim * 100))

        # Calibrated Hybrid Formula: 40% Vector Cosine Similarity + 60% Rule Alignment
        hybrid_score = int(round(0.40 * cos_score + 0.60 * rule_score))
        hybrid_score = max(0, min(100, hybrid_score))

        # Enrich match reasons with explainable AI similarity insight
        match_reasons = list(rule_result["match_reasons"])
        if cos_score >= 35:
            match_reasons.insert(
                0,
                f"AI Smart Match: {cos_score}% vector profile alignment ({confidence['level']} Confidence)."
            )
        elif cos_score > 0:
            match_reasons.insert(
                0,
                f"AI Smart Match: {cos_score}% vector profile alignment."
            )

        # Enrich skill breakdown dictionary with vector and confidence metadata
        skill_breakdown = dict(rule_result["skill_breakdown"])
        skill_breakdown["cosine_similarity"] = cos_score
        skill_breakdown["rule_score"] = rule_score
        skill_breakdown["confidence_level"] = confidence["level"]
        skill_breakdown["confidence_score"] = confidence["score"]

        enriched = {
            "career_name":       career["career_name"],
            "description":       career["description"],
            "score":             hybrid_score,
            "cosine_similarity": cos_score,
            "rule_score":        rule_score,
            "confidence_level":  confidence["level"],
            "match_reasons":     match_reasons,
            "missing_skills":    rule_result["missing_skills"],
            "suggested_techs":   rule_result["suggested_techs"],
            "skill_breakdown":   skill_breakdown,
        }
        results.append(enriched)

    # Sort descending by hybrid score, tie-breaking on cosine similarity and rule score
    results.sort(
        key=lambda r: (r["score"], r["cosine_similarity"], r["rule_score"]),
        reverse=True
    )
    return results


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_assessment(row: Any) -> dict:
    """
    Safely parse an assessment DB row into plain Python types.
    Missing or invalid JSON fields fall back to empty collections.
    """
    def _load(field, fallback):
        try:
            val = row[field] if not isinstance(row, dict) else row.get(field)
            return json.loads(val) if val else fallback
        except (json.JSONDecodeError, TypeError, KeyError):
            return fallback

    return {
        "skills":       _load("skills_json",       {}),   # {skill_key: proficiency(1-5)}
        "interests":    _load("interests_json",     []),   # [interest_key, ...]
        "technologies": _load("technologies_json",  []),   # [tech_name, ...]
        "goals":        _load("goals_json",         {}),   # {short_term_role, work_style, ...}
    }


def _score_one(student: dict, career: dict) -> dict:
    """
    Compute a compatibility score between one student and one career.
    Returns a detailed result dict.
    """
    reasons: list[str] = []
    missing: list[str] = []

    # ── Component A: Skill presence (0–30) ────────────────────────────────────
    # Points awarded for each required skill the student has rated.
    # Bonus skills contribute at half rate.
    req_skills   = career["required_skills"]
    bonus_skills = career["bonus_skills"]
    student_skills: dict = student["skills"]

    req_present  = [s for s in req_skills   if s in student_skills]
    bonus_present = [s for s in bonus_skills if s in student_skills]

    # Proportion of required skills present (0–1)
    req_ratio = len(req_present) / len(req_skills) if req_skills else 0.0
    # Bonus adds up to 20% of the max presence score
    bonus_ratio = (len(bonus_present) / len(bonus_skills)) * 0.2 if bonus_skills else 0.0

    score_presence = round(min(1.0, req_ratio + bonus_ratio) * _MAX_SKILL_PRESENCE)

    if req_present:
        skill_labels = {
            s["key"]: s["label"]
            for s in _SKILL_LABEL_LIST()
        }
        readable = [skill_labels.get(k, k) for k in req_present[:3]]
        reasons.append(f"You have {len(req_present)}/{len(req_skills)} key skills: {', '.join(readable)}{'...' if len(req_present) > 3 else ''}.")

    # Record missing required skills for feedback
    missing_required = [s for s in req_skills if s not in student_skills]
    if missing_required:
        skill_labels = {s["key"]: s["label"] for s in _SKILL_LABEL_LIST()}
        missing.extend([skill_labels.get(k, k) for k in missing_required])

    # ── Component B: Skill proficiency (0–25) ─────────────────────────────────
    # For each required skill present, compare student's proficiency against
    # the career's expected weight (1–3 in the CSV, treated as expected tier).
    weights = career["skill_weights"]
    weighted_score = 0.0
    weight_total   = 0.0

    for skill in req_skills:
        if skill not in student_skills:
            continue
        expected_weight = weights.get(skill, 2)        # 1=minor, 2=important, 3=critical
        student_prof    = student_skills[skill]         # 1–5
        # Normalise: if student meets or exceeds what the weight implies, full score
        # Weight 3 (critical) → need proficiency ≥ 4 for full marks
        # Weight 2 (important)→ need proficiency ≥ 3
        # Weight 1 (minor)    → need proficiency ≥ 2
        needed_prof = expected_weight + 1              # maps 1→2, 2→3, 3→4
        contribution = min(1.0, student_prof / needed_prof) * expected_weight
        weighted_score += contribution
        weight_total   += expected_weight

    score_proficiency = round((weighted_score / weight_total * _MAX_SKILL_PROFICIENCY)
                              if weight_total > 0 else 0)

    # Add a proficiency observation to reasons if there are strong skills
    top_skills = sorted(
        [(k, v) for k, v in student_skills.items() if k in req_skills],
        key=lambda x: x[1], reverse=True
    )[:2]
    if top_skills:
        skill_labels = {s["key"]: s["label"] for s in _SKILL_LABEL_LIST()}
        for k, v in top_skills:
            if v >= 4:
                reasons.append(f"Strong {skill_labels.get(k, k)} proficiency ({PROF_LABELS.get(v, v)}).")

    # ── Component C: Interest alignment (0–20) ────────────────────────────────
    req_interests   = career["required_interests"]
    bonus_interests = career["bonus_interests"]
    student_ints    = set(student["interests"])

    req_int_match   = [i for i in req_interests   if i in student_ints]
    bonus_int_match = [i for i in bonus_interests if i in student_ints]

    req_int_ratio   = len(req_int_match)   / len(req_interests)   if req_interests   else 0.0
    bonus_int_ratio = (len(bonus_int_match)/ len(bonus_interests)) * 0.3 if bonus_interests else 0.0

    score_interests = round(min(1.0, req_int_ratio + bonus_int_ratio) * _MAX_INTERESTS)

    int_labels = {
        "build_ml_models":   "Building ML/AI models",
        "analyse_data":      "Data analysis",
        "build_web_apps":    "Web development",
        "backend_apis":      "Backend/APIs",
        "security_research": "Security research",
        "cloud_infra":       "Cloud infrastructure",
        "mobile_apps":       "Mobile apps",
        "open_source":       "Open source",
        "research_papers":   "Research",
        "automation":        "Automation",
        "teaching_others":   "Teaching/mentoring",
        "startups":          "Startups/products",
    }
    matched_int_labels = [int_labels.get(i, i) for i in req_int_match + bonus_int_match]
    if matched_int_labels:
        reasons.append(f"Your interests align: {', '.join(matched_int_labels[:3])}.")

    # ── Component D: Technology overlap (0–10) ────────────────────────────────
    career_techs  = set(career["key_technologies"])
    student_techs = set(student["technologies"])
    matched_techs = list(career_techs & student_techs)

    tech_ratio    = len(matched_techs) / len(career_techs) if career_techs else 0.0
    score_tech    = round(min(1.0, tech_ratio * 2) * _MAX_TECHNOLOGY)  # 50% overlap = full score

    # Technologies the student doesn't have yet
    suggested_techs = [t for t in career["key_technologies"] if t not in student_techs][:5]

    if matched_techs:
        reasons.append(f"You already know: {', '.join(matched_techs[:3])}{'...' if len(matched_techs)>3 else ''}.")

    # ── Component E: Goal alignment (0–15) ────────────────────────────────────
    goals         = student["goals"]
    short_term    = goals.get("short_term_role", "").lower()
    dream_text    = goals.get("dream_role", "").lower()
    goal_keywords = [kw.lower() for kw in career["goal_keywords"]]
    career_lower  = career["career_name"].lower()

    score_goal = 0

    # Direct match: student chose this career as their short-term role
    if career_lower in short_term or short_term in career_lower:
        score_goal += 10
        reasons.append(f"Your stated career goal matches: '{goals.get('short_term_role')}'.")
    elif short_term == "still exploring — not sure yet":
        score_goal += 3   # small bonus — any career is possible

    # Keyword match in dream role free text
    kw_hits = [kw for kw in goal_keywords if kw in dream_text]
    if kw_hits:
        score_goal += min(5, len(kw_hits) * 2)
        reasons.append(f"Your described goals mention relevant keywords: {', '.join(kw_hits[:3])}.")

    score_goal = min(_MAX_GOAL, score_goal)

    # ── Total ─────────────────────────────────────────────────────────────────
    total = score_presence + score_proficiency + score_interests + score_tech + score_goal
    total = max(0, min(100, total))  # clamp to 0–100

    # Fall-back reason if nothing matched
    if not reasons:
        reasons.append("Limited overlap with this career's requirements based on your current assessment.")

    return {
        "career_name":    career["career_name"],
        "description":    career["description"],
        "score":          total,
        "match_reasons":  reasons,
        "missing_skills": missing,
        "suggested_techs": suggested_techs,
        "skill_breakdown": {
            "skill_presence":    score_presence,
            "skill_proficiency": score_proficiency,
            "interests":         score_interests,
            "technologies":      score_tech,
            "goals":             score_goal,
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _SKILL_LABEL_LIST() -> list[dict]:
    """
    Returns the same SKILLS list used in assessment.py without importing it
    (to avoid a circular import). Defined once here to keep scorer self-contained.
    """
    return [
        {"key": "python",          "label": "Python"},
        {"key": "java",            "label": "Java"},
        {"key": "cpp",             "label": "C / C++"},
        {"key": "javascript",      "label": "JavaScript"},
        {"key": "r_lang",          "label": "R"},
        {"key": "machine_learning","label": "Machine Learning"},
        {"key": "deep_learning",   "label": "Deep Learning"},
        {"key": "statistics",      "label": "Statistics & Math"},
        {"key": "sql",             "label": "SQL / Databases"},
        {"key": "data_viz",        "label": "Data Visualisation"},
        {"key": "html_css",        "label": "HTML / CSS"},
        {"key": "web_frameworks",  "label": "Web Frameworks"},
        {"key": "cloud",           "label": "Cloud Platforms"},
        {"key": "docker",          "label": "Docker / Containers"},
        {"key": "networking",      "label": "Computer Networking"},
        {"key": "linux",           "label": "Linux / Shell Scripting"},
        {"key": "cybersecurity",   "label": "Cybersecurity Concepts"},
        {"key": "dsa",             "label": "Data Structures & Algorithms"},
    ]
