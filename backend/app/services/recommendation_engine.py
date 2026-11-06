import logging
from typing import Any, Dict, List, Optional

from app.models.student_profile import StudentProfile
from app.models.opportunity import Opportunity
from app.services.vector_matcher import compute_semantic_match
from app.services.eligibility_engine import evaluate_eligibility
from app.services.skill_gap_engine import analyze_skill_gap

logger = logging.getLogger(__name__)


def _extract_student_skill_names(profile: StudentProfile) -> List[str]:
    """Helper to cleanly extract skill name list from profile relationships or attributes."""
    if hasattr(profile, "student_skills") and profile.student_skills:
        names = []
        for ss in profile.student_skills:
            if hasattr(ss, "skill") and ss.skill:
                names.append(ss.skill.name)
            elif isinstance(ss, dict) and "name" in ss:
                names.append(ss["name"])
        if names:
            return names

    # Fallback to direct skills attribute if present
    if hasattr(profile, "skills") and profile.skills:
        names = []
        for s in profile.skills:
            if hasattr(s, "name"):
                names.append(s.name)
            elif isinstance(s, dict) and "name" in s:
                names.append(s["name"])
            elif isinstance(s, str):
                names.append(s)
        return names

    return []


def _compute_experience_match(profile: StudentProfile, opportunity: Opportunity) -> float:
    """
    Evaluates compatibility between student experience level / year
    and opportunity expected sophistication.
    
    Returns:
        float: Normalized score between 0.0 and 100.0.
    """
    level_map = {
        "beginner": 1.0,
        "intermediate": 2.0,
        "advanced": 3.0,
        "expert": 4.0
    }

    student_level_str = getattr(profile, "experience_level", "Beginner") or "Beginner"
    student_level = level_map.get(student_level_str.lower(), 1.5)
    student_year = getattr(profile, "year", 2) or 2

    category = (getattr(opportunity, "category", "") or "").lower()
    opp_skills = getattr(opportunity, "required_skills", []) or []

    # Estimate opportunity target depth
    # Contests / Hiring challenges typically expect higher technical maturity
    if "hiring" in category or "coding contest" in category:
        target_level = 2.5
    elif len(opp_skills) >= 6:
        target_level = 2.2
    else:
        target_level = 1.8

    # Calculate base level score
    diff = student_level - target_level
    if diff >= 0:
        base_score = 92.0 + min(8.0, diff * 5.0)
    elif diff >= -0.5:
        base_score = 80.0
    elif diff >= -1.0:
        base_score = 65.0
    else:
        base_score = 50.0

    # Year calibration: Upperclassmen (3rd/4th year) get small boost for hiring challenges;
    # Underclassmen (1st/2nd) get high parity for open hackathons
    if "hiring" in category and student_year >= 3:
        base_score = min(100.0, base_score + 8.0)
    elif "hackathon" in category and student_year in [1, 2, 3]:
        base_score = min(100.0, base_score + 5.0)

    return round(max(0.0, min(100.0, base_score)), 2)


def _compute_mode_match(profile: StudentProfile, opportunity: Opportunity) -> float:
    """
    Evaluates mode suitability (Online, Hybrid, In-Person).
    Online events are universally accessible (100.0).
    Hybrid events require partial travel (85.0).
    In-Person events (70.0 - 95.0 depending on location alignment).
    """
    mode = (getattr(opportunity, "mode", "Online") or "Online").strip().lower()

    if mode == "online":
        return 100.0
    elif mode == "hybrid":
        return 85.0
    elif mode == "in-person":
        # Check if student college location matches opportunity location
        student_college = (getattr(profile, "college_name", "") or "").lower()
        opp_location = (getattr(opportunity, "location", "") or "").lower()
        if opp_location and student_college and (opp_location in student_college or student_college in opp_location):
            return 95.0
        return 70.0
    
    return 80.0


def _generate_explanation(
    final_score: float,
    breakdown: Dict[str, float],
    eligibility_status: str,
    matched_skills: List[str],
    missing_skills: List[str],
    opportunity_title: str
) -> str:
    """Generates an intuitive, personalized explanation for the student."""
    reasons = []

    if final_score >= 85.0:
        tier = "Exceptional Match"
    elif final_score >= 70.0:
        tier = "Strong Match"
    elif final_score >= 55.0:
        tier = "Moderate Match"
    else:
        tier = "Challenging / Low Match"

    reasons.append(f"{tier} ({final_score}/100) for '{opportunity_title}'.")

    # Eligibility context
    if eligibility_status == "ELIGIBLE":
        reasons.append("Your degree, branch, and academic year fully satisfy all eligibility criteria.")
    elif eligibility_status == "NEEDS_VERIFICATION":
        reasons.append("Certain eligibility fields (e.g. CGPA or exact discipline) require profile verification.")
    else:
        reasons.append("You do not meet one or more mandatory eligibility requirements (penalty applied).")

    # Skills overlap
    if matched_skills:
        sample_matched = ", ".join(matched_skills[:3])
        reasons.append(f"Strong skill alignment on {sample_matched} (readiness: {breakdown['skill_match']}%).")
    
    if missing_skills:
        sample_missing = ", ".join(missing_skills[:2])
        reasons.append(f"To maximize competitiveness, focus on picking up {sample_missing}.")

    # Topic semantic alignment
    if breakdown["interest_match"] >= 65.0:
        reasons.append("The event theme strongly resonates with your stated academic focus and background.")

    return " ".join(reasons)


def calculate_recommendation_score(profile: StudentProfile, opportunity: Opportunity) -> Dict[str, Any]:
    """
    Computes a weighted hybrid recommendation score matching a student to an opportunity.
    
    Weighted Formula:
      Final Score = (0.35 * skill_match)
                  + (0.25 * interest_match)
                  + (0.15 * experience_match)
                  + (0.10 * mode_match)
                  + (0.15 * eligibility_confidence)

    Rules:
      - All component scores strictly between 0.0 and 100.0.
      - Eligibility confidence: ELIGIBLE = 100.0, NEEDS_VERIFICATION = 50.0, NOT_ELIGIBLE = 0.0.
      - Ineligible penalty: If NOT_ELIGIBLE, final score is penalized by 50% and capped at 50.0.

    Returns:
      {
        "final_score": float,
        "breakdown": {
          "skill_match": float,
          "interest_match": float,
          "experience_match": float,
          "mode_match": float,
          "eligibility_confidence": float
        },
        "explanation": str,
        "eligibility": dict,
        "skill_gap": dict
      }
    """
    # 1. Eligibility Evaluation
    eligibility_result = evaluate_eligibility(
        profile=profile,
        criteria=opportunity.eligibility_criteria or {}
    )
    elig_status = eligibility_result["status"]
    if elig_status == "ELIGIBLE":
        eligibility_confidence = 100.0
    elif elig_status == "NEEDS_VERIFICATION":
        eligibility_confidence = 50.0
    else:
        eligibility_confidence = 0.0

    # 2. Skill Match & Gap Analysis
    student_skills = _extract_student_skill_names(profile)
    skill_gap = analyze_skill_gap(
        student_skills=student_skills,
        required_skills=opportunity.required_skills or []
    )
    skill_match = skill_gap["readiness_score"]

    # 3. Interest & Semantic Text Match
    profile_text = (
        f"{profile.degree or ''} student in {profile.branch or ''}, year {profile.year or ''}. "
        f"{profile.raw_bio or ''}. "
        f"Skills: {', '.join(student_skills)}."
    )
    opp_text = (
        f"{opportunity.title}. Organizer: {opportunity.organizer}. "
        f"Category: {opportunity.category}. Description: {opportunity.description}. "
        f"Required skills: {', '.join(opportunity.required_skills or [])}."
    )
    interest_match = compute_semantic_match(profile_text, opp_text)

    # 4. Experience Match
    experience_match = _compute_experience_match(profile, opportunity)

    # 5. Mode Match
    mode_match = _compute_mode_match(profile, opportunity)

    # Weighted Hybrid Calculation
    raw_final_score = (
        (0.35 * skill_match)
        + (0.25 * interest_match)
        + (0.15 * experience_match)
        + (0.10 * mode_match)
        + (0.15 * eligibility_confidence)
    )

    # Apply 50% penalty cap for ineligible opportunities
    if elig_status == "NOT_ELIGIBLE":
        final_score = round(min(raw_final_score * 0.5, 50.0), 2)
    else:
        final_score = round(max(0.0, min(100.0, raw_final_score)), 2)

    breakdown = {
        "skill_match": round(skill_match, 2),
        "interest_match": round(interest_match, 2),
        "experience_match": round(experience_match, 2),
        "mode_match": round(mode_match, 2),
        "eligibility_confidence": round(eligibility_confidence, 2)
    }

    explanation = _generate_explanation(
        final_score=final_score,
        breakdown=breakdown,
        eligibility_status=elig_status,
        matched_skills=skill_gap["matched_skills"],
        missing_skills=skill_gap["missing_skills"],
        opportunity_title=opportunity.title
    )

    return {
        "final_score": final_score,
        "breakdown": breakdown,
        "explanation": explanation,
        "eligibility": eligibility_result,
        "skill_gap": skill_gap
    }
