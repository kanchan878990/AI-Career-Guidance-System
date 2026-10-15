# ──────────────────────────────────────────────────────────────────────────────
# app/engine/career_data.py
#
# Loads and validates the career_profiles.csv dataset.
#
# Why a separate module?
#   Keeping data loading separate from scoring makes each piece easier to
#   understand, test, and change. If we switch from CSV to a database table
#   later, only this file needs to change.
#
# What this module provides:
#   get_careers()  → list of career dicts, each fully parsed and validated
# ──────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd

# Absolute path to the CSV file — works regardless of which directory Python
# is run from.
_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "career_profiles.csv",
)

# Cache the loaded data so we only read the file once per app lifetime.
_careers_cache: list[dict] | None = None


def _parse_pipe(value: str) -> list[str]:
    """Split a pipe-separated string into a cleaned list, skipping empty parts."""
    if not value or pd.isna(value):
        return []
    return [s.strip() for s in str(value).split("|") if s.strip()]


def _parse_weights(value: str) -> dict[str, int]:
    """
    Parse a pipe-separated weight string like 'python:3|sql:2' into a dict
    {'python': 3, 'sql': 2}.
    """
    weights = {}
    for part in _parse_pipe(value):
        if ":" in part:
            skill, w = part.split(":", 1)
            try:
                weights[skill.strip()] = int(w.strip())
            except ValueError:
                pass
    return weights


def get_careers() -> list[dict]:
    """
    Return the list of career profile dicts, loading from CSV on first call.

    Each dict has these keys:
        career_name        str   — e.g. "AI/ML Engineer"
        description        str   — one-sentence description
        required_skills    list  — skill keys that are important
        bonus_skills       list  — nice-to-have skill keys
        skill_weights      dict  — {skill_key: weight_int}
        required_interests list  — interest keys that align strongly
        bonus_interests    list  — secondary interest keys
        key_technologies   list  — technology strings
        goal_keywords      list  — keywords to match in student's dream_role text

    Raises FileNotFoundError if career_profiles.csv is missing.
    Raises ValueError if required columns are absent.
    """
    global _careers_cache
    if _careers_cache is not None:
        return _careers_cache

    if not os.path.exists(_CSV_PATH):
        raise FileNotFoundError(
            f"Career profiles dataset not found at: {_CSV_PATH}\n"
            "Make sure data/career_profiles.csv exists in the project root."
        )

    df = pd.read_csv(_CSV_PATH)

    required_columns = {
        "career_name", "description", "required_skills", "bonus_skills",
        "skill_weights", "required_interests", "bonus_interests",
        "key_technologies", "goal_keywords",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"career_profiles.csv is missing columns: {missing}")

    careers = []
    for _, row in df.iterrows():
        careers.append({
            "career_name":        str(row["career_name"]).strip(),
            "description":        str(row["description"]).strip(),
            "required_skills":    _parse_pipe(row["required_skills"]),
            "bonus_skills":       _parse_pipe(row["bonus_skills"]),
            "skill_weights":      _parse_weights(row["skill_weights"]),
            "required_interests": _parse_pipe(row["required_interests"]),
            "bonus_interests":    _parse_pipe(row["bonus_interests"]),
            "key_technologies":   _parse_pipe(row["key_technologies"]),
            "goal_keywords":      _parse_pipe(row["goal_keywords"]),
        })

    _careers_cache = careers
    return careers
