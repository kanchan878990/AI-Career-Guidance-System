# test_audit.py
# =============
# Automated tests for the AI Career Guidance System.
#
# Uses Python's built-in unittest module and Flask's test client.
# No extra packages are required beyond what is already in requirements.txt.
#
# Run with:
#   venv\Scripts\python.exe test_audit.py   (Windows, no venv activation needed)
#   python test_audit.py                    (any OS, after activating venv)

import json
import unittest

from app import create_app


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

VALID_PROFILE = {
    "name": "Test Student",
    "email": "test@example.com",
    "education_level": "Undergraduate (B.Tech / B.E. / B.Sc)",
    "field_of_study": "Computer Science",
}

# Minimal valid assessment payload (3 skills, 2 interests, required goal fields)
VALID_ASSESSMENT = {
    "skill_python": "1", "prof_python": "4",
    "skill_machine_learning": "1", "prof_machine_learning": "3",
    "skill_statistics": "1", "prof_statistics": "3",
    "interest_build_ml_models": "1",
    "interest_analyse_data": "1",
    "short_term_role": "AI / ML Engineer",
    "work_style": "individual",
}


def _post_profile(client):
    """Submit a valid profile and follow the redirect to /assessment/."""
    client.post("/profile/", data=VALID_PROFILE, follow_redirects=False)


# ---------------------------------------------------------------------------
# 1. Static / public pages
# ---------------------------------------------------------------------------

class TestPublicPages(unittest.TestCase):
    """Pages that require no session and should always return 200."""

    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_200(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)

    def test_homepage_contains_brand(self):
        r = self.client.get("/")
        self.assertIn(b"CareerGuide", r.data)

    def test_about_page_200(self):
        r = self.client.get("/about")
        self.assertEqual(r.status_code, 200)

    def test_profile_form_get_200(self):
        r = self.client.get("/profile/")
        self.assertEqual(r.status_code, 200)

    def test_profile_form_contains_name_field(self):
        r = self.client.get("/profile/")
        self.assertIn(b'name="name"', r.data)

    def test_404_for_unknown_route(self):
        r = self.client.get("/this-route-does-not-exist")
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# 2. Registered routes
# ---------------------------------------------------------------------------

class TestRegisteredRoutes(unittest.TestCase):
    """Confirm that all blueprints are registered and their URLs exist."""

    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.app = app

    def _route_urls(self):
        return [str(rule) for rule in self.app.url_map.iter_rules()]

    def test_home_route_registered(self):
        self.assertIn("/", self._route_urls())

    def test_about_route_registered(self):
        self.assertIn("/about", self._route_urls())

    def test_profile_route_registered(self):
        self.assertIn("/profile/", self._route_urls())

    def test_assessment_route_registered(self):
        self.assertIn("/assessment/", self._route_urls())

    def test_results_latest_route_registered(self):
        self.assertIn("/results/latest", self._route_urls())

    def test_results_show_route_registered(self):
        # The dynamic route is stored as /results/<assessment_id>
        urls = self._route_urls()
        self.assertTrue(
            any("/results/" in u and "assessment_id" in u for u in urls),
            f"No /results/<assessment_id> route found. Routes: {urls}",
        )


# ---------------------------------------------------------------------------
# 3. Profile form — validation
# ---------------------------------------------------------------------------

class TestProfileValidation(unittest.TestCase):
    """Server-side validation rules read from profile.py."""

    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post(self, data):
        return self.client.post("/profile/", data=data, follow_redirects=True)

    def test_valid_profile_redirects_to_assessment(self):
        r = self.client.post("/profile/", data=VALID_PROFILE, follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/assessment/", r.headers.get("Location", ""))

    def test_missing_name_shows_error(self):
        data = dict(VALID_PROFILE, name="")
        r = self._post(data)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Full name is required", r.data)

    def test_missing_education_level_shows_error(self):
        data = dict(VALID_PROFILE, education_level="")
        r = self._post(data)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"education level", r.data.lower())

    def test_missing_field_of_study_shows_error(self):
        data = dict(VALID_PROFILE, field_of_study="")
        r = self._post(data)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"field of study", r.data.lower())

    def test_invalid_email_shows_error(self):
        data = dict(VALID_PROFILE, email="not-an-email")
        r = self._post(data)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"valid email", r.data.lower())

    def test_email_optional_blank_accepted(self):
        data = dict(VALID_PROFILE, email="")
        r = self.client.post("/profile/", data=data, follow_redirects=False)
        self.assertEqual(r.status_code, 302)


# ---------------------------------------------------------------------------
# 4. Session guards
# ---------------------------------------------------------------------------

class TestSessionGuards(unittest.TestCase):
    """
    assessment/ and results/ must redirect unauthenticated visitors
    to the profile page.  Verified against the session guard code in
    assessment.py and results.py.
    """

    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_assessment_get_without_session_redirects(self):
        r = self.client.get("/assessment/", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/profile/", r.headers.get("Location", ""))

    def test_assessment_post_without_session_redirects(self):
        r = self.client.post("/assessment/", data=VALID_ASSESSMENT,
                             follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/profile/", r.headers.get("Location", ""))

    def test_results_show_without_session_redirects(self):
        r = self.client.get("/results/1", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/profile/", r.headers.get("Location", ""))

    def test_results_latest_without_session_redirects(self):
        r = self.client.get("/results/latest", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/profile/", r.headers.get("Location", ""))

    def test_results_nonexistent_id_with_session_redirects(self):
        """
        Even with a valid session, a result ID that does not belong to the
        current student should redirect away (not crash with 500).
        """
        _post_profile(self.client)
        r = self.client.get("/results/999999", follow_redirects=False)
        self.assertEqual(r.status_code, 302)


# ---------------------------------------------------------------------------
# 5. Assessment page (requires session)
# ---------------------------------------------------------------------------

class TestAssessmentPage(unittest.TestCase):

    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()
        _post_profile(self.client)   # establish a session

    def test_assessment_get_200_with_session(self):
        r = self.client.get("/assessment/")
        self.assertEqual(r.status_code, 200)

    def test_assessment_contains_four_sections(self):
        r = self.client.get("/assessment/")
        for section_id in [b"section-skills", b"section-interests",
                           b"section-tech", b"section-goals"]:
            self.assertIn(section_id, r.data,
                          f"Section '{section_id}' not found in assessment page")

    def test_assessment_valid_post_redirects_to_results(self):
        r = self.client.post("/assessment/", data=VALID_ASSESSMENT,
                             follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/results/", r.headers.get("Location", ""))

    def test_assessment_too_few_skills_shows_error(self):
        """Server requires at least 3 skills (from assessment.py validation)."""
        data = dict(VALID_ASSESSMENT)
        # Remove two of the three skills
        del data["skill_machine_learning"]
        del data["skill_statistics"]
        r = self.client.post("/assessment/", data=data, follow_redirects=True)
        # Should re-render the form (200 or 422) with an error, not redirect
        self.assertIn(r.status_code, (200, 422))
        self.assertIn(b"at least 3", r.data)

    def test_assessment_too_few_interests_shows_error(self):
        """Server requires at least 2 interests."""
        data = dict(VALID_ASSESSMENT)
        del data["interest_analyse_data"]   # leave only 1
        r = self.client.post("/assessment/", data=data, follow_redirects=True)
        self.assertIn(r.status_code, (200, 422))
        self.assertIn(b"at least 2", r.data)


# ---------------------------------------------------------------------------
# 6. Recommendation engine (unit tests — no HTTP required)
# ---------------------------------------------------------------------------

class TestScorerUnit(unittest.TestCase):
    """
    Tests for app.engine.scorer.score_assessment().
    Input format verified from scorer.py docstring: accepts a dict with
    keys skills_json, interests_json, technologies_json, goals_json.
    Returns a list of dicts sorted by score descending.
    """

    def setUp(self):
        # score_assessment is a pure function; no app context needed.
        from app.engine.scorer import score_assessment
        self.score = score_assessment

    def _make_input(self, skills=None, interests=None, technologies=None, goals=None):
        return {
            "skills_json":       json.dumps(skills       or {}),
            "interests_json":    json.dumps(interests    or []),
            "technologies_json": json.dumps(technologies or []),
            "goals_json":        json.dumps(goals        or {}),
        }

    def test_returns_seven_results(self):
        results = self.score(self._make_input())
        self.assertEqual(len(results), 7)

    def test_all_scores_in_range(self):
        results = self.score(self._make_input())
        for r in results:
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

    def test_results_sorted_descending(self):
        results = self.score(self._make_input(
            skills={"python": 4, "machine_learning": 4, "statistics": 3},
            interests=["build_ml_models"],
        ))
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_each_result_has_required_keys(self):
        results = self.score(self._make_input())
        required = {"career_name", "score", "match_reasons",
                    "missing_skills", "suggested_techs"}
        for r in results:
            for key in required:
                self.assertIn(key, r, f"Key '{key}' missing from result for {r.get('career_name')}")

    def test_ml_profile_top_result_is_aiml_engineer(self):
        """
        A student with strong ML skills and goals should rank AI/ML Engineer first.
        """
        results = self.score(self._make_input(
            skills={"python": 5, "machine_learning": 5,
                    "statistics": 4, "deep_learning": 4},
            interests=["build_ml_models", "research_papers"],
            technologies=["TensorFlow", "PyTorch"],
            goals={"short_term_role": "AI / ML Engineer",
                   "work_style": "individual",
                   "dream_role": "NLP research",
                   "learning_style": "projects"},
        ))
        self.assertEqual(results[0]["career_name"], "AI/ML Engineer")

    def test_web_profile_top_result_is_web_developer(self):
        results = self.score(self._make_input(
            skills={"html_css": 5, "javascript": 5, "web_frameworks": 4},
            interests=["build_web_apps", "backend_apis"],
            technologies=["React", "Node.js"],
            goals={"short_term_role": "Web Developer",
                   "work_style": "team",
                   "dream_role": "React frontend",
                   "learning_style": "videos"},
        ))
        self.assertEqual(results[0]["career_name"], "Web Developer")

    def test_empty_assessment_does_not_crash(self):
        """Graceful handling when all JSON fields are empty."""
        results = self.score(self._make_input())
        self.assertEqual(len(results), 7)

    def test_invalid_json_does_not_crash(self):
        """If a field contains malformed JSON, the scorer should not raise."""
        bad = {
            "skills_json":       "not valid json",
            "interests_json":    None,
            "technologies_json": "",
            "goals_json":        "{}",
        }
        try:
            results = self.score(bad)
            self.assertEqual(len(results), 7)
        except Exception as exc:
            self.fail(f"score_assessment raised {type(exc).__name__} on bad input: {exc}")


# ---------------------------------------------------------------------------
# 7. Smart Career Matching Engine (Vector Space, Cosine Similarity & Confidence)
# ---------------------------------------------------------------------------

class TestSmartCareerMatching(unittest.TestCase):
    """
    Focused verification tests for Phase 1: Smart Career Matching.
    Verifies vector space dimensions, cosine mathematical bounds, hybrid blending,
    deterministic confidence evaluation, and domain ranking accuracy for ML, Web,
    Security, and Data profiles without hardcoded shortcuts.
    """

    def setUp(self):
        from app.engine.scorer import score_assessment
        from app.engine.vectorizer import (
            build_student_vector,
            compute_cosine_similarities,
            get_or_build_career_matrix,
            evaluate_confidence,
            CANONICAL_SKILLS,
            CANONICAL_INTERESTS,
            CANONICAL_TECHNOLOGIES,
        )
        from app.engine.career_data import get_careers

        self.score = score_assessment
        self.build_student_vector = build_student_vector
        self.compute_sims = compute_cosine_similarities
        self.get_matrix = get_or_build_career_matrix
        self.evaluate_confidence = evaluate_confidence
        self.careers = get_careers()
        self.expected_dim = (
            len(CANONICAL_SKILLS) +
            len(CANONICAL_INTERESTS) +
            len(CANONICAL_TECHNOLOGIES)
        )

    def _make_input(self, skills=None, interests=None, technologies=None, goals=None):
        return {
            "skills_json":       json.dumps(skills       or {}),
            "interests_json":    json.dumps(interests    or []),
            "technologies_json": json.dumps(technologies or []),
            "goals_json":        json.dumps(goals        or {}),
        }

    def test_vector_dimension_consistency(self):
        """Student feature vector must match the canonical feature vocabulary dimension."""
        sample_student = {
            "skills": {"python": 4, "sql": 3},
            "interests": ["analyse_data"],
            "technologies": ["pandas", "SQL"],
        }
        vec = self.build_student_vector(sample_student)
        self.assertEqual(len(vec), self.expected_dim)
        self.assertEqual(len(vec), 63)

    def test_cosine_similarity_bounds(self):
        """Cosine similarity must strictly produce values in [0.0, 1.0]."""
        matrix = self.get_matrix(self.careers)
        sample = {
            "skills": {"python": 5, "machine_learning": 4, "statistics": 4},
            "interests": ["build_ml_models"],
            "technologies": ["PyTorch", "scikit-learn"],
        }
        sims = self.compute_sims(sample, matrix)
        self.assertEqual(len(sims), len(self.careers))
        for s in sims:
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)

    def test_zero_vector_similarity_is_zero(self):
        """An empty student assessment vector must return 0.0 similarity without zero-division error."""
        matrix = self.get_matrix(self.careers)
        empty_student = {"skills": {}, "interests": [], "technologies": []}
        sims = self.compute_sims(empty_student, matrix)
        self.assertEqual(len(sims), len(self.careers))
        for s in sims:
            self.assertEqual(s, 0.0)

    def test_security_profile_top_result_is_cybersecurity_analyst(self):
        """Security-focused student profile must accurately rank Cybersecurity Analyst #1."""
        results = self.score(self._make_input(
            skills={"networking": 5, "cybersecurity": 5, "linux": 4, "python": 3},
            interests=["security_research", "open_source"],
            technologies=["Wireshark", "Kali Linux", "Nmap"],
            goals={
                "short_term_role": "Cybersecurity Analyst",
                "work_style": "team",
                "dream_role": "SOC analyst and ethical hacking security research",
                "learning_style": "projects",
            },
        ))
        self.assertEqual(results[0]["career_name"], "Cybersecurity Analyst")
        self.assertGreaterEqual(results[0]["score"], 80)
        self.assertIn("cosine_similarity", results[0])

    def test_data_analyst_profile_top_result_is_data_analyst(self):
        """Data analytics profile with SQL and BI tools must rank Data Analyst #1."""
        results = self.score(self._make_input(
            skills={"sql": 5, "data_viz": 5, "statistics": 4},
            interests=["analyse_data", "automation"],
            technologies=["SQL", "Power BI", "Tableau", "Excel"],
            goals={
                "short_term_role": "Data Analyst",
                "work_style": "individual",
                "dream_role": "business intelligence reporting dashboard analytics",
                "learning_style": "projects",
            },
        ))
        self.assertEqual(results[0]["career_name"], "Data Analyst")
        self.assertGreaterEqual(results[0]["score"], 80)

    def test_data_science_profile_top_result_is_data_scientist(self):
        """Data science profile with statistics, python, and predictive analytics must rank Data Scientist #1."""
        results = self.score(self._make_input(
            skills={"python": 5, "statistics": 5, "machine_learning": 4, "sql": 4, "data_viz": 4},
            interests=["analyse_data", "build_ml_models"],
            technologies=["pandas", "NumPy", "scikit-learn", "SQL"],
            goals={
                "short_term_role": "Data Scientist",
                "work_style": "team",
                "dream_role": "predictive models machine learning data science insights",
                "learning_style": "projects",
            },
        ))
        self.assertEqual(results[0]["career_name"], "Data Scientist")
        self.assertGreaterEqual(results[0]["score"], 80)

    def test_deterministic_confidence_tiers(self):
        """Verify deterministic confidence evaluation rules across completeness levels."""
        # High completeness: broad differentiated skills, focused interests, tech stack, goals
        high_input = {
            "skills": {"python": 5, "machine_learning": 4, "statistics": 4, "sql": 3, "docker": 3, "linux": 3},
            "interests": ["build_ml_models", "analyse_data", "research_papers"],
            "technologies": ["TensorFlow", "PyTorch", "pandas"],
            "goals": {"short_term_role": "AI / ML Engineer", "dream_role": "deep learning research scientist in NLP"},
        }
        res_high = self.evaluate_confidence(high_input)
        self.assertEqual(res_high["level"], "High")
        self.assertGreaterEqual(res_high["score"], 75)

        # Baseline completeness: minimum 3 beginner skills, 2 interests, no tech
        baseline_input = {
            "skills": {"python": 1, "java": 1, "cpp": 1},
            "interests": ["build_web_apps", "backend_apis"],
            "technologies": [],
            "goals": {"short_term_role": "still exploring — not sure yet", "dream_role": ""},
        }
        res_baseline = self.evaluate_confidence(baseline_input)
        self.assertIn(res_baseline["level"], ["Moderate", "Preliminary"])
        self.assertLess(res_baseline["score"], 75)

        # Empty completeness
        res_empty = self.evaluate_confidence({"skills": {}, "interests": [], "technologies": [], "goals": {}})
        self.assertEqual(res_empty["level"], "Preliminary")
        self.assertLess(res_empty["score"], 50)

    def test_hybrid_score_structure_and_bounds(self):
        """Verify that hybrid results include cosine similarity, rule score, and valid bounded ranges."""
        results = self.score(self._make_input(
            skills={"python": 4, "sql": 3, "docker": 3},
            interests=["backend_apis", "automation"],
            technologies=["Docker", "Flask"],
            goals={"short_term_role": "Software Developer"},
        ))
        for r in results:
            self.assertIn("cosine_similarity", r)
            self.assertIn("rule_score", r)
            self.assertIn("confidence_level", r)
            self.assertGreaterEqual(r["cosine_similarity"], 0)
            self.assertLessEqual(r["cosine_similarity"], 100)
            self.assertGreaterEqual(r["rule_score"], 0)
            self.assertLessEqual(r["rule_score"], 100)
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

            # Check breakdown dictionary
            bd = r["skill_breakdown"]
            self.assertIn("cosine_similarity", bd)
            self.assertIn("confidence_level", bd)
            self.assertIn("confidence_score", bd)

    def test_no_hardcoded_bias(self):
        """Results must depend strictly on assessment inputs, invariant to student metadata or name."""
        payload_1 = {
            "skills_json": json.dumps({"python": 5, "machine_learning": 5, "statistics": 4}),
            "interests_json": json.dumps(["build_ml_models", "research_papers"]),
            "technologies_json": json.dumps(["PyTorch"]),
            "goals_json": json.dumps({"short_term_role": "AI / ML Engineer"}),
            "student_name": "Student Alpha",
        }
        payload_2 = dict(payload_1, student_name="Student Beta")
        res1 = self.score(payload_1)
        res2 = self.score(payload_2)
        for r1, r2 in zip(res1, res2):
            self.assertEqual(r1["career_name"], r2["career_name"])
            self.assertEqual(r1["score"], r2["score"])
            self.assertEqual(r1["cosine_similarity"], r2["cosine_similarity"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)

