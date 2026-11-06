import re
from typing import Dict, List, Set, Any

# Canonical synonym dictionary mapping aliases to unified skill keys
SKILL_SYNONYMS: Dict[str, str] = {
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "natural language processing (nlp)": "natural language processing",
    "ml": "machine learning",
    "machine learning": "machine learning",
    "machine learning (ml)": "machine learning",
    "dl": "deep learning",
    "deep learning": "deep learning",
    "deep learning (dl)": "deep learning",
    "cv": "computer vision",
    "computer vision": "computer vision",
    "computer vision (cv)": "computer vision",
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "dsa": "data structures & algorithms",
    "data structures & algorithms": "data structures & algorithms",
    "data structures and algorithms": "data structures & algorithms",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "psql": "postgresql",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "google cloud platform": "google cloud platform",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "rest": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "restful apis": "rest apis",
}

# Curated actionable preparation checklist suggestions for high-frequency competition skills
SKILL_CHECKLIST_KNOWLEDGE_BASE: Dict[str, str] = {
    "docker": "Dockerize a sample microservice using a multi-stage Dockerfile and test with docker-compose.",
    "kubernetes": "Review core concepts: Pods, Services, Deployments, and write a basic K8s deployment manifest.",
    "fastapi": "Build an asynchronous CRUD API with Pydantic v2 schemas and automatic Swagger docs.",
    "react": "Review React hooks (useState, useEffect, useMemo), state management, and component lifecycle.",
    "flutter": "Build a cross-platform mobile screen with responsive widgets and State management (Provider/Bloc).",
    "pytorch": "Fine-tune a pretrained PyTorch model using transfer learning and create an inference script.",
    "tensorflow": "Review tf.keras functional API and implement a basic neural network pipeline.",
    "machine learning": "Practice data preprocessing, feature engineering, and cross-validation with Scikit-Learn.",
    "natural language processing": "Implement text embeddings, tokenization with HuggingFace, and sentiment/intent classification.",
    "computer vision": "Practice OpenCV image augmentations and object detection with YOLO / TorchVision.",
    "system design": "Review horizontal scaling, caching strategies (Redis), and database indexing tradeoffs.",
    "data structures & algorithms": "Practice LeetCode medium problems on Graphs, Dynamic Programming, and Two Pointers.",
    "postgresql": "Write optimized SQL queries with EXPLAIN ANALYZE, foreign keys, and index tuning.",
    "cybersecurity": "Review OWASP Top 10 vulnerabilities, JWT security, and input sanitization.",
    "blockchain": "Understand smart contract lifecycle, ERC-20/721 standards, and test locally with Hardhat.",
    "firebase": "Configure Firebase Auth, Firestore real-time listeners, and Cloud Storage.",
    "azure": "Deploy a containerized application to Azure App Services and test Azure Cognitive Services.",
    "google cloud platform": "Deploy a Cloud Run microservice and connect Cloud SQL.",
}


def _clean_token(text: str) -> str:
    """Strip punctuation and non-alphanumeric characters for fuzzy matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _normalize_skill(skill: str) -> str:
    """Normalize skill string using lowercase and canonical synonym lookup."""
    lowered = skill.strip().lower()
    if lowered in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[lowered]
    cleaned = _clean_token(skill)
    for syn_key, canonical in SKILL_SYNONYMS.items():
        if _clean_token(syn_key) == cleaned:
            return canonical
    return lowered


def _skills_match(student_skill: str, required_skill: str) -> bool:
    """
    Check if a student's skill matches an opportunity's required skill.
    Uses exact, canonical synonym, alphanumeric stripped, and substring matching.
    """
    norm_student = _normalize_skill(student_skill)
    norm_required = _normalize_skill(required_skill)

    if norm_student == norm_required:
        return True

    # Check alphanumeric stripped forms
    clean_s = _clean_token(student_skill)
    clean_r = _clean_token(required_skill)
    if clean_s == clean_r and clean_s != "":
        return True

    # Substring containment check (e.g. "nlp" in "nlp natural language processing")
    if norm_student in norm_required or norm_required in norm_student:
        return True

    return False


def _generate_checklist_item(skill: str) -> str:
    """Generate an actionable preparation checklist tip for a missing skill."""
    norm = _normalize_skill(skill)
    clean = _clean_token(skill)
    
    # Check knowledge base
    for key, tip in SKILL_CHECKLIST_KNOWLEDGE_BASE.items():
        if key in norm or _clean_token(key) in clean:
            return f"{skill}: {tip}"
    
    # Fallback dynamic actionable checklist
    return f"{skill}: Build a 1-day proof-of-concept project or complete a hands-on tutorial applying {skill} core patterns."


def analyze_skill_gap(student_skills: List[str], required_skills: List[str]) -> Dict[str, Any]:
    """
    Analyzes the overlap and gap between student competencies and event required skills.
    
    Args:
      student_skills: List of skills claimed by the student.
      required_skills: List of skills required by the opportunity.
      
    Returns:
      {
        "matched_skills": List[str],
        "missing_skills": List[str],
        "readiness_score": float (0.0 to 100.0),
        "preparation_checklist": List[str]
      }
    """
    if not required_skills:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "readiness_score": 100.0,
            "preparation_checklist": ["No mandatory technical prerequisites specified. Ideal for early learners!"]
        }

    cleaned_student_skills = [s for s in (student_skills or []) if s and s.strip()]
    matched: List[str] = []
    missing: List[str] = []

    for req in required_skills:
        if not req or not req.strip():
            continue
        req_clean = req.strip()
        is_matched = any(_skills_match(st_skill, req_clean) for st_skill in cleaned_student_skills)
        if is_matched:
            matched.append(req_clean)
        else:
            missing.append(req_clean)

    total_required = len(matched) + len(missing)
    if total_required > 0:
        readiness_score = round((len(matched) / total_required) * 100.0, 2)
    else:
        readiness_score = 100.0

    # Bound readiness score strictly between 0.0 and 100.0
    readiness_score = max(0.0, min(100.0, readiness_score))

    # Generate actionable checklist for missing skills
    preparation_checklist = [_generate_checklist_item(m) for m in missing]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "readiness_score": readiness_score,
        "preparation_checklist": preparation_checklist
    }
