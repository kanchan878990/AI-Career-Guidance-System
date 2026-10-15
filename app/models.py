# ──────────────────────────────────────────────────────────────────────────────
# app/models.py
#
# Python dataclasses that mirror the database tables.
#
# Why dataclasses?
#   - They give us clean Python objects to pass around instead of raw tuples.
#   - No ORM (like SQLAlchemy) is needed — we keep things simple with plain SQL.
#   - `@dataclass` auto-generates __init__, __repr__, etc. for free.
# ──────────────────────────────────────────────────────────────────────────────

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Student:
    """Represents one row in the  students  table."""
    name: str
    education_level: str
    field_of_study: str
    email: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Assessment:
    """Represents one row in the  assessments  table."""
    student_id: int
    skills_json: str        # JSON string, e.g. '{"python": 4, "sql": 2}'
    interests_json: str     # JSON string, e.g. '["data analysis", "building ML models"]'
    technologies_json: str  # JSON string, e.g. '["TensorFlow", "pandas"]'
    goals_json: str         # JSON string, e.g. '{"short_term": "ML Intern", ...}'
    id: Optional[int] = None
    submitted_at: Optional[datetime] = None


@dataclass
class Result:
    """Represents one career recommendation row in the  results  table."""
    assessment_id: int
    career_name: str
    match_score: float          # 0.0 to 1.0
    match_reasons_json: str     # JSON list of reason strings
    missing_skills_json: str    # JSON list of skill strings
    roadmap_json: str           # JSON list of learning step strings
    rank: int                   # 1 = best match
    id: Optional[int] = None
    created_at: Optional[datetime] = None
