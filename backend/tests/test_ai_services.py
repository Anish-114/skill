"""
Unit tests for SkillBridge AI Core Engines & Deterministic Verification Services:
1. VectorMatcher (Sentence Transformers & Fallbacks)
2. EligibilityEngine
3. SkillGapEngine
4. RecommendationEngine
"""
import sys
from typing import Any, Dict

from app.db.session import SessionLocal
from app.models import Opportunity, Skill, StudentProfile, StudentSkill, User
from app.services.vector_matcher import VectorMatcher, compute_semantic_match
from app.services.eligibility_engine import evaluate_eligibility
from app.services.skill_gap_engine import analyze_skill_gap
from app.services.recommendation_engine import calculate_recommendation_score
from app.db.seed_data import SAMPLE_OPPORTUNITIES


# ==========================================
# 1. Vector Matcher Tests
# ==========================================

def test_vector_matcher_empty_input():
    score1 = compute_semantic_match("", "FastAPI and Python")
    score2 = compute_semantic_match("Python developer", "   ")
    assert score1 == 0.0, f"Expected 0.0 for empty profile text, got {score1}"
    assert score2 == 0.0, f"Expected 0.0 for empty opportunity text, got {score2}"
    print("[PASS] VectorMatcher: empty inputs return 0.0.")


def test_vector_matcher_semantic_similarity():
    profile = "Python machine learning engineer passionate about deep learning, NLP transformers, and PyTorch."
    opp_high = "Amazon ML Challenge: Natural language processing, transformers, and deep neural network models."
    opp_low = "Culinary arts and traditional bakery pastry cooking contest."

    high_score = compute_semantic_match(profile, opp_high)
    low_score = compute_semantic_match(profile, opp_low)

    assert 0.0 <= high_score <= 100.0, f"Score out of bounds: {high_score}"
    assert 0.0 <= low_score <= 100.0, f"Score out of bounds: {low_score}"
    assert high_score > low_score, f"Expected high_score ({high_score}) > low_score ({low_score})"
    assert high_score >= 50.0, f"Expected high semantic similarity, got {high_score}"
    print(f"[PASS] VectorMatcher: high match ({high_score}%) > low match ({low_score}%).")


def test_vector_matcher_fallbacks():
    matcher = VectorMatcher()
    t1 = "FastAPI backend web service with PostgreSQL"
    t2 = "FastAPI microservices and PostgreSQL database APIs"

    # Test TF-IDF fallback
    tfidf_score = matcher._compute_tfidf_match(t1, t2)
    assert 0.0 <= tfidf_score <= 100.0
    assert tfidf_score > 0.0

    # Test token overlap fallback
    token_score = matcher._compute_token_overlap(t1, t2)
    assert 0.0 <= token_score <= 100.0
    assert token_score > 0.0
    print(f"[PASS] VectorMatcher fallbacks verified (TF-IDF: {tfidf_score}%, Token: {token_score}%).")


# ==========================================
# 2. Eligibility Engine Tests
# ==========================================

class MockProfile:
    def __init__(
        self,
        degree="B.Tech",
        branch="Computer Science & Engineering",
        year=3,
        cgpa=8.5,
        age=20,
        experience_level="Intermediate",
        raw_bio="",
        student_skills=None
    ):
        self.degree = degree
        self.branch = branch
        self.year = year
        self.cgpa = cgpa
        self.age = age
        self.experience_level = experience_level
        self.raw_bio = raw_bio
        self.student_skills = student_skills or []


def test_eligibility_fully_eligible():
    profile = MockProfile(degree="B.Tech", branch="Computer Science & Engineering", year=3, cgpa=8.5)
    criteria = {
        "degrees": ["B.Tech", "B.E."],
        "branches": ["Computer Science", "Information Technology"],
        "allowed_years": [2, 3, 4],
        "min_cgpa": 7.0
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "ELIGIBLE", f"Expected ELIGIBLE, got {result['status']}"
    assert len(result["passed_checks"]) == 4
    assert len(result["failed_checks"]) == 0
    assert len(result["missing_data_checks"]) == 0
    print("[PASS] EligibilityEngine: fully eligible candidate passes all checks.")


def test_eligibility_year_failure():
    profile = MockProfile(year=1)
    criteria = {
        "allowed_years": [3, 4],
        "degrees": ["B.Tech"]
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "NOT_ELIGIBLE"
    assert any("Year 1 is not eligible" in r for r in result["failed_checks"])
    print("[PASS] EligibilityEngine: year mismatch triggers NOT_ELIGIBLE.")


def test_eligibility_cgpa_failure():
    profile = MockProfile(cgpa=6.2)
    criteria = {
        "min_cgpa": 7.5,
        "degrees": ["B.Tech"]
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "NOT_ELIGIBLE"
    assert any("CGPA of 6.2 is below the minimum" in r for r in result["failed_checks"])
    print("[PASS] EligibilityEngine: low CGPA triggers NOT_ELIGIBLE.")


def test_eligibility_branch_failure():
    profile = MockProfile(branch="Civil Engineering")
    criteria = {
        "branches": ["Computer Science", "Information Technology", "AI/ML"]
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "NOT_ELIGIBLE"
    assert any("Civil Engineering" in r for r in result["failed_checks"])
    print("[PASS] EligibilityEngine: non-matching branch triggers NOT_ELIGIBLE.")


def test_eligibility_missing_data_needs_verification():
    profile = MockProfile(cgpa=None)
    criteria = {
        "min_cgpa": 7.0,
        "degrees": ["B.Tech"],
        "allowed_years": [3]
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "NEEDS_VERIFICATION"
    assert len(result["missing_data_checks"]) == 1
    assert "CGPA is missing" in result["missing_data_checks"][0]
    print("[PASS] EligibilityEngine: missing critical field triggers NEEDS_VERIFICATION.")


def test_eligibility_explicit_failure_overrides_missing():
    # If degree fails AND cgpa is missing, must be NOT_ELIGIBLE (not merely NEEDS_VERIFICATION)
    profile = MockProfile(degree="MBBS", cgpa=None)
    criteria = {
        "degrees": ["B.Tech", "B.E."],
        "min_cgpa": 7.0
    }
    result = evaluate_eligibility(profile, criteria)
    assert result["status"] == "NOT_ELIGIBLE"
    print("[PASS] EligibilityEngine: explicit failure overrides missing data checks.")


# ==========================================
# 3. Skill Gap Engine Tests
# ==========================================

def test_skill_gap_analysis():
    student_skills = ["Python", "fastapi", "NLP", "ReactJS", "Git"]
    required_skills = [
        "Python",
        "FastAPI",
        "Natural Language Processing (NLP)",
        "React",
        "Docker"
    ]

    gap = analyze_skill_gap(student_skills, required_skills)
    
    assert "Python" in gap["matched_skills"]
    assert "FastAPI" in gap["matched_skills"]
    assert "React" in gap["matched_skills"]
    assert "Natural Language Processing (NLP)" in gap["matched_skills"]
    assert "Docker" in gap["missing_skills"]
    assert len(gap["missing_skills"]) == 1

    # 4 out of 5 matched = 80.0%
    assert gap["readiness_score"] == 80.0
    assert len(gap["preparation_checklist"]) == 1
    assert "Docker:" in gap["preparation_checklist"][0]
    print(f"[PASS] SkillGapEngine: synonym-aware match verified ({gap['readiness_score']}% readiness).")


def test_skill_gap_empty_required():
    gap = analyze_skill_gap(["Python"], [])
    assert gap["readiness_score"] == 100.0
    assert gap["missing_skills"] == []
    print("[PASS] SkillGapEngine: empty requirements return 100.0 readiness.")


def test_skill_gap_zero_match():
    gap = analyze_skill_gap(["Rust"], ["Python", "Django"])
    assert gap["readiness_score"] == 0.0
    assert len(gap["missing_skills"]) == 2
    assert len(gap["preparation_checklist"]) == 2
    print("[PASS] SkillGapEngine: zero match returns 0.0 readiness with checklists.")


# ==========================================
# 4. Recommendation Engine Tests
# ==========================================

def test_recommendation_engine_seeded_candidate():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "student@skillbridge.ai").first()
        assert user is not None, "Seeded test user not found"
        profile = user.profile
        assert profile is not None

        # Test against an active opportunity in DB or sample contest
        opp = db.query(Opportunity).filter(Opportunity.is_active == True).first()
        if not opp:
            opp = Opportunity(
                title="Open Engineering Challenge 2026",
                organizer="Tech Foundation",
                category="Hackathon",
                description="Engineering challenge using Python, ML and APIs.",
                required_skills=["Python", "FastAPI", "Machine Learning"],
                eligibility_criteria={
                    "degrees": ["B.Tech", "B.E.", "MCA"],
                    "branches": ["Computer Science & Engineering", "ALL"],
                    "allowed_years": [1, 2, 3, 4],
                    "min_cgpa": 6.0,
                },
                deadline=datetime.now(timezone.utc) + timedelta(days=30),
                mode="Online",
                official_url="https://challenge.example.org",
                source="Devfolio",
                is_active=True,
            )
            db.add(opp)
            db.commit()

        rec = calculate_recommendation_score(profile, opp)

        # Assert output contract
        assert "final_score" in rec
        assert "breakdown" in rec
        assert "explanation" in rec
        assert "eligibility" in rec
        assert "skill_gap" in rec

        # Check breakdown fields and bounds
        breakdown = rec["breakdown"]
        assert 0.0 <= breakdown["skill_match"] <= 100.0
        assert 0.0 <= breakdown["interest_match"] <= 100.0
        assert 0.0 <= breakdown["experience_match"] <= 100.0
        assert 0.0 <= breakdown["mode_match"] <= 100.0
        assert 0.0 <= breakdown["eligibility_confidence"] <= 100.0

        assert rec["eligibility"]["status"] in ["ELIGIBLE", "NEEDS_VERIFICATION"]
        assert len(rec["explanation"]) > 20

        print(f"[PASS] RecommendationEngine: evaluated '{opp.title}' -> Final Score: {rec['final_score']}%")
        print(f"       Breakdown: {breakdown}")
        print(f"       Explanation: {rec['explanation'][:100]}...")

    finally:
        db.close()


def test_recommendation_ineligible_penalty_cap():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "student@skillbridge.ai").first()
        profile = user.profile

        # Create a mock opportunity with impossible criteria for a 3rd year CSE student
        mock_opp = Opportunity(
            title="Biotech Junior Research Fellowship",
            organizer="Biotech Council",
            category="Fellowship",
            description="Cellular genetics and biotechnology wet lab research.",
            required_skills=["Microbiology", "CRISPR", "Gel Electrophoresis"],
            eligibility_criteria={
                "degrees": ["MBBS", "B.Sc (Microbiology)"],
                "branches": ["Biotechnology", "Genetics"],
                "allowed_years": [1]
            },
            deadline=SAMPLE_OPPORTUNITIES[0]["deadline"],
            mode="In-Person",
            official_url="https://example.com/biotech",
            source="Test"
        )

        rec = calculate_recommendation_score(profile, mock_opp)

        assert rec["eligibility"]["status"] == "NOT_ELIGIBLE"
        assert rec["breakdown"]["eligibility_confidence"] == 0.0
        # Check that the 50% penalty cap is strictly applied!
        assert rec["final_score"] <= 50.0, f"Ineligible score must not exceed 50.0, got {rec['final_score']}"
        assert "penalty applied" in rec["explanation"].lower() or "not meet" in rec["explanation"].lower()

        print(f"[PASS] RecommendationEngine: Ineligible candidate received penalty cap -> Final Score: {rec['final_score']}%.")

    finally:
        db.close()


def run_all_tests():
    print("=" * 60)
    print("RUNNING SKILLBRIDGE AI PHASE 2 SERVICES TEST SUITE")
    print("=" * 60)

    # 1. Vector Matcher
    test_vector_matcher_empty_input()
    test_vector_matcher_semantic_similarity()
    test_vector_matcher_fallbacks()

    # 2. Eligibility Engine
    test_eligibility_fully_eligible()
    test_eligibility_year_failure()
    test_eligibility_cgpa_failure()
    test_eligibility_branch_failure()
    test_eligibility_missing_data_needs_verification()
    test_eligibility_explicit_failure_overrides_missing()

    # 3. Skill Gap Engine
    test_skill_gap_analysis()
    test_skill_gap_empty_required()
    test_skill_gap_zero_match()

    # 4. Recommendation Engine
    test_recommendation_engine_seeded_candidate()
    test_recommendation_ineligible_penalty_cap()

    print("=" * 60)
    print("ALL PHASE 2 UNIT TESTS PASSED SUCCESSFULLY! (13/13)")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
