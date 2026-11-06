import re
from typing import Any, Dict, List, Optional
from app.models.student_profile import StudentProfile


def _normalize_string(text: str) -> str:
    """Lowercase and strip non-alphanumeric characters for fuzzy-tolerant comparisons."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _degree_matches(student_degree: str, allowed_degrees: List[str]) -> bool:
    """
    Check if the student degree matches any allowed degree.
    Handles variants like 'B.Tech', 'BTech', 'B.E.', 'b.tech'.
    """
    if not student_degree or not allowed_degrees:
        return False

    norm_student = _normalize_string(student_degree)
    
    for allowed in allowed_degrees:
        norm_allowed = _normalize_string(allowed)
        if norm_allowed in ["all", "any", "alldegrees", "anydegree"]:
            return True
        if norm_student == norm_allowed:
            return True
        # Handle 'btech' vs 'be' / 'bachelor of technology' equivalence
        if norm_student in ["btech", "be"] and norm_allowed in ["btech", "be"]:
            return True
        if norm_student in norm_allowed or norm_allowed in norm_student:
            return True

    return False


def _branch_matches(student_branch: str, allowed_branches: List[str], student_degree: Optional[str] = None) -> bool:
    """
    Check if the student branch matches any allowed branch.
    Supports partial match like 'Computer Science & Engineering' matching 'Computer Science'.
    """
    if not student_branch or not allowed_branches:
        return False

    norm_student = _normalize_string(student_branch)

    for allowed in allowed_branches:
        norm_allowed = _normalize_string(allowed)
        if norm_allowed in ["all", "any", "allbranches", "anybranch"]:
            return True
        if "allengineering" in norm_allowed:
            # If engineering branch, matches
            engineering_keywords = ["computer", "tech", "engineer", "information", "electronics", "electrical", "mechanical", "civil"]
            if any(k in norm_student for k in engineering_keywords):
                return True
            if student_degree and any(eng in _normalize_string(student_degree) for eng in ["btech", "be", "mtech", "me"]):
                return True
        if norm_student == norm_allowed:
            return True
        # Partial match / substring match
        if norm_allowed in norm_student or norm_student in norm_allowed:
            return True

    return False


def evaluate_eligibility(profile: StudentProfile, criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule evaluator checking student profile attributes against
    JSON eligibility rules.
    
    Rules evaluated:
      - `allowed_years`: List of eligible academic years.
      - `branches`: Allowed academic branches/disciplines.
      - `degrees`: Allowed academic degrees.
      - `min_cgpa`: Minimum required cumulative grade point average.
      - `min_age` / `max_age`: Age constraints (if defined).

    Returns:
      {
        "status": "ELIGIBLE" | "NOT_ELIGIBLE" | "NEEDS_VERIFICATION",
        "reasons": List[str],
        "passed_checks": List[str],
        "failed_checks": List[str],
        "missing_data_checks": List[str]
      }
    """
    passed_checks: List[str] = []
    failed_checks: List[str] = []
    missing_data_checks: List[str] = []

    if not criteria:
        return {
            "status": "ELIGIBLE",
            "reasons": ["No restrictive eligibility criteria defined for this opportunity."],
            "passed_checks": ["Open to all participants without restrictions."],
            "failed_checks": [],
            "missing_data_checks": []
        }

    # 1. Degree Evaluation
    allowed_degrees = criteria.get("degrees")
    if allowed_degrees:
        if not getattr(profile, "degree", None):
            missing_data_checks.append("Degree information is missing in your student profile.")
        else:
            if _degree_matches(profile.degree, allowed_degrees):
                passed_checks.append(f"Degree '{profile.degree}' satisfies eligible degrees: {', '.join(allowed_degrees)}.")
            else:
                failed_checks.append(f"Degree '{profile.degree}' does not match eligible degrees: {', '.join(allowed_degrees)}.")

    # 2. Branch Evaluation
    allowed_branches = criteria.get("branches")
    if allowed_branches:
        if not getattr(profile, "branch", None):
            missing_data_checks.append("Branch / Discipline information is missing in your student profile.")
        else:
            if _branch_matches(profile.branch, allowed_branches, getattr(profile, "degree", None)):
                passed_checks.append(f"Branch '{profile.branch}' satisfies eligible branches: {', '.join(allowed_branches)}.")
            else:
                failed_checks.append(f"Branch '{profile.branch}' is not in the eligible disciplines: {', '.join(allowed_branches)}.")

    # 3. Academic Year Evaluation
    allowed_years = criteria.get("allowed_years")
    if allowed_years:
        student_year = getattr(profile, "year", None)
        if student_year is None:
            missing_data_checks.append("Academic year is missing in your student profile.")
        else:
            if student_year in allowed_years:
                passed_checks.append(f"Year {student_year} is eligible (allowed: {allowed_years}).")
            else:
                failed_checks.append(f"Year {student_year} is not eligible (allowed years: {allowed_years}).")

    # 4. Minimum CGPA Evaluation
    min_cgpa = criteria.get("min_cgpa")
    if min_cgpa is not None and float(min_cgpa) > 0.0:
        student_cgpa = getattr(profile, "cgpa", None)
        if student_cgpa is None:
            missing_data_checks.append(f"CGPA is missing in your profile (minimum required: {min_cgpa}).")
        else:
            if float(student_cgpa) >= float(min_cgpa):
                passed_checks.append(f"CGPA of {student_cgpa} meets the minimum requirement of {min_cgpa}.")
            else:
                failed_checks.append(f"CGPA of {student_cgpa} is below the minimum required {min_cgpa}.")

    # 5. Age Evaluation (if present in criteria)
    min_age = criteria.get("min_age")
    max_age = criteria.get("max_age")
    if min_age is not None or max_age is not None:
        student_age = getattr(profile, "age", None)
        if student_age is None:
            missing_data_checks.append("Age is required for eligibility verification but not provided in your profile.")
        else:
            age_failed = False
            if min_age is not None and student_age < min_age:
                failed_checks.append(f"Age {student_age} is below minimum age of {min_age}.")
                age_failed = True
            if max_age is not None and student_age > max_age:
                failed_checks.append(f"Age {student_age} exceeds maximum age of {max_age}.")
                age_failed = True
            if not age_failed:
                passed_checks.append(f"Age {student_age} satisfies age range constraints.")

    # Determine overall status
    if failed_checks:
        status = "NOT_ELIGIBLE"
        reasons = failed_checks
    elif missing_data_checks:
        status = "NEEDS_VERIFICATION"
        reasons = [f"Verification required: {item}" for item in missing_data_checks]
    else:
        status = "ELIGIBLE"
        reasons = ["All evaluated eligibility criteria have been successfully verified."]

    return {
        "status": status,
        "reasons": reasons,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_data_checks": missing_data_checks
    }
