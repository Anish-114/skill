from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.skill_gap_engine import _clean_token, _normalize_skill

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "learning_resources.json"

# Cached resources dictionary
_RESOURCES_CACHE: Optional[Dict[str, List[dict]]] = None

# Daily learning commitment in hours for a typical engineering student
DAILY_HOURS_BUDGET = 2.5

# Skill priority tiers (Lower tier number = higher priority)
SKILL_PRIORITY_TIERS = {
    # Tier 1: Core Programming Languages & Version Control
    "git": 1,
    "python": 1,
    "javascript": 1,
    "typescript": 1,
    "c++": 1,
    "java": 1,
    "go": 1,
    "sql": 1,
    
    # Tier 2: Foundational CS & Databases
    "data structures & algorithms": 2,
    "postgresql": 2,
    "redis": 2,
    "system design": 2,
    
    # Tier 3: Core Frameworks & Containerization
    "fastapi": 3,
    "react": 3,
    "node.js": 3,
    "next.js": 3,
    "docker": 3,
    "flutter": 3,
    "django": 3,
    
    # Tier 4: Advanced Specializations
    "machine learning": 4,
    "deep learning": 4,
    "pytorch": 4,
    "tensorflow": 4,
    "natural language processing": 4,
    "computer vision": 4,
    "kubernetes": 4,
    "cybersecurity": 4,
    "blockchain": 4,
}


def load_learning_resources() -> Dict[str, List[dict]]:
    """Loads learning resources from JSON file with module-level caching."""
    global _RESOURCES_CACHE
    if _RESOURCES_CACHE is not None:
        return _RESOURCES_CACHE

    if not DATA_PATH.exists():
        logger.warning(f"learning_resources.json not found at {DATA_PATH}")
        _RESOURCES_CACHE = {}
        return _RESOURCES_CACHE

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            # Normalize keys to lowercase for robust lookup
            _RESOURCES_CACHE = {k.strip().lower(): v for k, v in raw_data.items()}
    except Exception as exc:
        logger.error(f"Error loading learning_resources.json: {exc}", exc_info=True)
        _RESOURCES_CACHE = {}

    return _RESOURCES_CACHE


def _find_resources_for_skill(skill_name: str, resources_db: Dict[str, List[dict]]) -> List[dict]:
    """
    Finds curated resources for a skill using exact, canonical synonym,
    and partial token matching. Returns empty list if uncataloged.
    """
    if not skill_name:
        return []

    lowered = skill_name.strip().lower()
    if lowered in resources_db:
        return resources_db[lowered]

    # Check normalized canonical form
    normalized = _normalize_skill(skill_name)
    if normalized in resources_db:
        return resources_db[normalized]

    # Fuzzy clean token match
    clean_s = _clean_token(skill_name)
    for key, res_list in resources_db.items():
        if _clean_token(key) == clean_s:
            return res_list
        if _clean_token(key) in clean_s or clean_s in _clean_token(key):
            if len(key) >= 4:  # avoid short accidental substring collisions
                return res_list

    return []


def _format_duration_label(hours: float) -> str:
    """Formats estimated hours into clean human duration string."""
    if hours <= 0:
        return "1-2 hours"
    days = max(1, math.ceil(hours / DAILY_HOURS_BUDGET))
    if days == 1:
        return f"~1 day ({hours:.0f} hrs)"
    elif days < 7:
        return f"~{days} days ({hours:.0f} hrs)"
    else:
        weeks = round(days / 7, 1)
        return f"~{weeks} weeks ({days} days, {hours:.0f} hrs)"


def generate_learning_roadmap(
    missing_skills: List[str],
    deadline: Optional[datetime] = None,
    daily_budget_hours: float = DAILY_HOURS_BUDGET
) -> Dict[str, Any]:
    """
    Generates a deterministic learning roadmap for missing skills tailored to the event deadline.
    No LLM or GPU is used.

    Args:
        missing_skills: List of skill names the student needs to learn.
        deadline: UTC datetime of the event deadline (or None if ongoing).
        daily_budget_hours: Assumed daily study hours (default 2.5 hrs/day).

    Returns:
        Dict conforming to LearningRoadmapResponse schema.
    """
    resources_db = load_learning_resources()

    if not missing_skills:
        return {
            "is_feasible": True,
            "warning_message": None,
            "total_estimated_hours": 0.0,
            "estimated_duration": "0 days",
            "days_until_deadline": None,
            "recommended_focus_skills": [],
            "milestones": []
        }

    # Deduplicate skills while preserving case
    seen = set()
    unique_missing = []
    for s in missing_skills:
        clean = s.strip()
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            unique_missing.append(clean)

    # 1. Gather resources and compute individual skill hours
    skill_items = []
    for skill in unique_missing:
        res_list = _find_resources_for_skill(skill, resources_db)
        if res_list:
            hours = sum(float(r.get("estimated_hours", 4.0)) for r in res_list)
        else:
            # Default baseline estimate for uncataloged skills
            hours = 6.0

        norm_key = _normalize_skill(skill)
        tier = SKILL_PRIORITY_TIERS.get(norm_key, SKILL_PRIORITY_TIERS.get(skill.lower(), 3))

        skill_items.append({
            "skill": skill,
            "tier": tier,
            "estimated_hours": hours,
            "resources": res_list
        })

    # 2. Priority Sorting: Tier ascending (core first), then estimated hours ascending (quick wins)
    skill_items.sort(key=lambda x: (x["tier"], x["estimated_hours"]))

    # 3. Calculate cumulative hours & milestones
    total_hours = sum(item["estimated_hours"] for item in skill_items)
    total_days = max(1, math.ceil(total_hours / daily_budget_hours))
    if total_days < 7:
        duration_label = f"{total_days} days (at {daily_budget_hours} hrs/day)"
    else:
        weeks = round(total_days / 7, 1)
        duration_label = f"{weeks} weeks ({total_days} days at {daily_budget_hours} hrs/day)"

    # 4. Check Deadline Feasibility
    days_until_deadline: Optional[float] = None
    is_feasible = True
    warning_message: Optional[str] = None
    recommended_focus: List[str] = []

    if deadline is not None:
        now = datetime.now(timezone.utc)
        # Handle naive deadline as UTC
        if deadline.tzinfo is None:
            deadline_aware = deadline.replace(tzinfo=timezone.utc)
        else:
            deadline_aware = deadline

        diff_seconds = (deadline_aware - now).total_seconds()
        days_until_deadline = max(0.0, round(diff_seconds / 86400.0, 1))

        # Available study hours until deadline
        available_study_hours = days_until_deadline * daily_budget_hours

        if total_hours > available_study_hours:
            is_feasible = False
            # Determine which high-priority skills can realistically fit
            accumulated_hours = 0.0
            for item in skill_items:
                if accumulated_hours + item["estimated_hours"] <= available_study_hours or not recommended_focus:
                    recommended_focus.append(item["skill"])
                    accumulated_hours += item["estimated_hours"]
                else:
                    break

            focus_count = len(recommended_focus)
            if focus_count == 1:
                focus_str = f"'{recommended_focus[0]}'"
            else:
                focus_str = f"in {focus_count} skills par ({', '.join(recommended_focus)})"

            warning_message = (
                f"Deadline tak sabhi {len(skill_items)} skills cover karna possible nahi hai "
                f"({total_hours:.0f} hrs required vs ~{available_study_hours:.0f} hrs available). "
                f"Pehle {focus_str} focus karo."
            )
        else:
            is_feasible = True
            recommended_focus = [item["skill"] for item in skill_items]
    else:
        recommended_focus = [item["skill"] for item in skill_items]

    # 5. Build Milestones output
    milestones = []
    for idx, item in enumerate(skill_items, start=1):
        milestones.append({
            "skill": item["skill"],
            "priority": idx,
            "estimated_hours": item["estimated_hours"],
            "duration_label": _format_duration_label(item["estimated_hours"]),
            "resources": item["resources"]
        })

    return {
        "is_feasible": is_feasible,
        "warning_message": warning_message,
        "total_estimated_hours": round(total_hours, 1),
        "estimated_duration": duration_label,
        "days_until_deadline": days_until_deadline,
        "recommended_focus_skills": recommended_focus,
        "milestones": milestones
    }
