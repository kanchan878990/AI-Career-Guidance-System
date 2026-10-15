# ──────────────────────────────────────────────────────────────────────────────
# app/engine/vectorizer.py
#
# Vector space representations, Cosine Similarity computation, and
# deterministic Assessment Confidence scoring for Smart Career Matching.
#
# Mathematics & Methodology:
#   1. Universal Feature Space (D = 63 dimensions):
#      - 18 Technical Skills: normalized proficiency tier [0.0, 1.0] (1.5x weight)
#      - 12 Student Interests: binary indicator [0.0, 1.0] (1.0x weight)
#      - 33 Technologies: binary toolstack indicator [0.0, 1.0] (0.8x weight)
#
#   2. Cosine Similarity:
#      Sim(S, C) = (V_S · V_C) / (||V_S||_2 * ||V_C||_2)
#      Computed via scikit-learn's cosine_similarity. Strictly bounded in [0.0, 1.0].
#
#   3. Deterministic Assessment Confidence:
#      Scores completeness and evidence quality (0–100) based on skill breadth,
#      proficiency distribution, interest focus, hands-on tech exposure, and goal clarity.
# ──────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Any

# ── Canonical Feature Vocabulary ───────────────────────────────────────────────

CANONICAL_SKILLS: list[str] = [
    "python", "java", "cpp", "javascript", "r_lang",
    "machine_learning", "deep_learning", "statistics", "sql", "data_viz",
    "html_css", "web_frameworks", "cloud", "docker",
    "networking", "linux", "cybersecurity", "dsa"
]

CANONICAL_INTERESTS: list[str] = [
    "build_ml_models", "analyse_data", "build_web_apps", "backend_apis",
    "security_research", "cloud_infra", "mobile_apps", "open_source",
    "research_papers", "automation", "teaching_others", "startups"
]

CANONICAL_TECHNOLOGIES: list[str] = [
    "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Hugging Face", "OpenCV",
    "pandas", "NumPy", "Matplotlib / Seaborn", "Power BI", "Tableau", "Apache Spark", "SQL", "Excel",
    "React", "Vue.js", "Angular", "Node.js", "Django", "Flask", "FastAPI",
    "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Git / GitHub",
    "Wireshark", "Metasploit", "Burp Suite", "Nmap", "Kali Linux"
]

# Block importance weights
_WEIGHT_SKILL: float = 1.5
_WEIGHT_INTEREST: float = 1.0
_WEIGHT_TECH: float = 0.8

# Cached career matrix to avoid re-allocating on every query
_cached_career_matrix: np.ndarray | None = None


# ── Vector Construction ────────────────────────────────────────────────────────

def build_career_vector(career: dict) -> np.ndarray:
    """
    Construct a dense float vector for a single career profile.
    Required skills are weighted by tier (1–3); bonus skills contribute at 0.4 rate.
    """
    vec: list[float] = []
    req_skills = set(career.get("required_skills", []))
    bonus_skills = set(career.get("bonus_skills", []))
    weights = career.get("skill_weights", {})

    for s in CANONICAL_SKILLS:
        if s in req_skills:
            w = weights.get(s, 2)
            vec.append(_WEIGHT_SKILL * (w / 3.0))
        elif s in bonus_skills:
            vec.append(_WEIGHT_SKILL * 0.4)
        else:
            vec.append(0.0)

    req_ints = set(career.get("required_interests", []))
    bonus_ints = set(career.get("bonus_interests", []))
    for i in CANONICAL_INTERESTS:
        if i in req_ints:
            vec.append(_WEIGHT_INTEREST * 1.0)
        elif i in bonus_ints:
            vec.append(_WEIGHT_INTEREST * 0.4)
        else:
            vec.append(0.0)

    career_techs = {t.lower() for t in career.get("key_technologies", [])}
    for t in CANONICAL_TECHNOLOGIES:
        if t.lower() in career_techs:
            vec.append(_WEIGHT_TECH * 1.0)
        else:
            vec.append(0.0)

    return np.array(vec, dtype=float)


def get_or_build_career_matrix(careers: list[dict]) -> np.ndarray:
    """
    Returns the cached (or newly computed) 2D feature matrix for all careers.
    Shape: (num_careers, D).
    """
    global _cached_career_matrix
    if _cached_career_matrix is not None and _cached_career_matrix.shape[0] == len(careers):
        return _cached_career_matrix

    matrix = np.array([build_career_vector(c) for c in careers], dtype=float)
    _cached_career_matrix = matrix
    return matrix


def build_student_vector(student_data: dict) -> np.ndarray:
    """
    Construct a dense float vector from a student's parsed assessment data.
    Proficiency levels (1–5) are scaled to [0.2, 1.0]; unrated skills are 0.0.
    """
    vec: list[float] = []
    skills = student_data.get("skills", {})
    interests = set(student_data.get("interests", []))
    techs = {t.lower() for t in student_data.get("technologies", [])}

    for s in CANONICAL_SKILLS:
        prof = skills.get(s, 0)
        try:
            prof_val = float(prof)
        except (ValueError, TypeError):
            prof_val = 0.0
        vec.append(_WEIGHT_SKILL * max(0.0, min(1.0, prof_val / 5.0)))

    for i in CANONICAL_INTERESTS:
        vec.append(_WEIGHT_INTEREST * 1.0 if i in interests else 0.0)

    for t in CANONICAL_TECHNOLOGIES:
        vec.append(_WEIGHT_TECH * 1.0 if t.lower() in techs else 0.0)

    return np.array(vec, dtype=float)


# ── Cosine Similarity ──────────────────────────────────────────────────────────

def compute_cosine_similarities(student_data: dict, career_matrix: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between the student vector and all career vectors.
    Returns 1D array of floats bounded in [0.0, 1.0].
    Handles zero-norm (empty assessment) safely without dividing by zero.
    """
    s_vec = build_student_vector(student_data).reshape(1, -1)
    norm = np.linalg.norm(s_vec)
    if norm == 0:
        return np.zeros(career_matrix.shape[0], dtype=float)

    sims = cosine_similarity(s_vec, career_matrix)[0]
    return np.clip(sims, 0.0, 1.0)


# ── Deterministic Assessment Confidence ────────────────────────────────────────

def evaluate_confidence(student_data: dict) -> dict[str, Any]:
    """
    Compute a deterministic confidence score (0–100) and qualitative tier based
    on assessment completeness, proficiency differentiation, and evidence depth.

    Confidence Tiers:
      - High (>= 75): Comprehensive, multidimensional responses with depth and clear direction.
      - Moderate (50–74): Standard valid assessment with solid directional signal.
      - Preliminary (< 50): Minimal or sparse responses; recommendations are directional.
    """
    skills = student_data.get("skills", {})
    interests = student_data.get("interests", [])
    technologies = student_data.get("technologies", [])
    goals = student_data.get("goals", {})

    score = 0
    factors: list[str] = []

    # 1. Skill Breadth (max 30 pts)
    n_skills = len(skills)
    if n_skills >= 6:
        score += 30
        factors.append("Broad skill assessment (>=6 skills rated)")
    elif n_skills >= 4:
        score += 20
        factors.append("Moderate skill coverage (4–5 skills rated)")
    elif n_skills >= 3:
        score += 10
        factors.append("Baseline skill coverage (3 skills rated)")
    else:
        score += max(0, n_skills * 3)

    # 2. Skill Depth & Differentiation (max 25 pts)
    if n_skills > 0:
        profs: list[float] = []
        for v in skills.values():
            try:
                profs.append(float(v))
            except (ValueError, TypeError):
                pass
        if profs:
            if max(profs) >= 3.0:
                score += 10
                factors.append("Demonstrated proficiency depth (>= intermediate)")
            if len(set(profs)) > 1:
                score += 15
                factors.append("Differentiated proficiency ratings")
            else:
                score += 5

    # 3. Interest Focus (max 20 pts)
    n_interests = len(interests)
    if 3 <= n_interests <= 6:
        score += 20
        factors.append("Focused interest profile (3–6 interests)")
    elif n_interests == 2:
        score += 12
        factors.append("Standard interest baseline (2 interests)")
    elif n_interests > 6:
        score += 14
        factors.append("Wide exploratory interests (>6 interests)")

    # 4. Hands-on Technology Evidence (max 15 pts)
    n_tech = len(technologies)
    if n_tech >= 3:
        score += 15
        factors.append("Strong technology toolstack evidence (>=3 tools)")
    elif n_tech >= 1:
        score += 10
        factors.append("Basic technology exposure (1–2 tools)")
    else:
        factors.append("No specific technologies selected")

    # 5. Goal Clarity (max 10 pts)
    short_term = str(goals.get("short_term_role", "")).strip()
    dream = str(goals.get("dream_role", "")).strip()
    if short_term and short_term.lower() != "still exploring — not sure yet":
        score += 5
        factors.append("Defined short-term career trajectory")
    elif short_term:
        score += 2
        factors.append("Open exploratory objective")

    if len(dream) >= 15:
        score += 5
        factors.append("Detailed career aspirations provided")

    score = min(100, max(0, score))
    if score >= 75:
        level = "High"
    elif score >= 50:
        level = "Moderate"
    else:
        level = "Preliminary"

    return {
        "score": score,
        "level": level,
        "factors": factors
    }
