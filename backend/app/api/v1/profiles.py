import io
import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_student_profile
from app.db.session import get_db
from app.models import User, StudentProfile, Skill, StudentSkill
from app.schemas.student_profile import (
    StudentProfileUpdate,
    StudentProfileResponse,
    StudentSkillItem,
    SkillParseRequest,
    SkillParseResponse,
)
from app.services.skill_gap_engine import _clean_token, _normalize_skill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

MAX_RESUME_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


def extract_skills_from_text(
    text: str,
    db: Session,
    include_text: bool = False
) -> SkillParseResponse:
    """
    Core NLP skill extractor that parses unstructured text against the
    recognized database skill taxonomy using word boundary and canonical synonyms.
    """
    if not text or not text.strip():
        return SkillParseResponse(
            extracted_skills=[],
            matched_taxonomy_skills=[],
            unmatched_tokens=[],
            extracted_text=text if include_text else None
        )

    # Retrieve all taxonomy skills from DB
    all_taxonomy_skills = db.query(Skill).all()
    clean_bio = " " + text.lower() + " "

    matched_skills = []
    matched_names = set()

    for skill in all_taxonomy_skills:
        name_clean = skill.name.lower()
        # Word boundary or clean token match
        pattern = r"\b" + re.escape(name_clean) + r"\b"
        if re.search(pattern, clean_bio):
            matched_names.add(skill.name)
            matched_skills.append({
                "id": skill.id,
                "name": skill.name,
                "category": skill.category
            })
            continue

        # Check canonical synonym matching
        norm_canonical = _normalize_skill(skill.name)
        if norm_canonical != name_clean:
            syn_pattern = r"\b" + re.escape(norm_canonical) + r"\b"
            if re.search(syn_pattern, clean_bio):
                matched_names.add(skill.name)
                matched_skills.append({
                    "id": skill.id,
                    "name": skill.name,
                    "category": skill.category
                })

    return SkillParseResponse(
        extracted_skills=sorted(list(matched_names)),
        matched_taxonomy_skills=matched_skills,
        unmatched_tokens=[],
        extracted_text=text if include_text else None
    )


def _format_profile_response(profile: StudentProfile, user: User) -> StudentProfileResponse:
    """Helper to convert StudentProfile ORM model to StudentProfileResponse schema."""
    skills_data = []
    if profile.student_skills:
        for ss in profile.student_skills:
            if ss.skill:
                skills_data.append(
                    StudentSkillItem(
                        skill_id=ss.skill.id,
                        name=ss.skill.name,
                        proficiency_level=ss.proficiency_level or "Intermediate",
                        years_of_experience=ss.years_of_experience or 1.0,
                        verified=ss.verified or False
                    )
                )

    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=user.email,
        full_name=user.full_name,
        phone=profile.phone,
        college_name=profile.college_name,
        degree=profile.degree,
        branch=profile.branch,
        year=profile.year,
        cgpa=profile.cgpa,
        experience_level=profile.experience_level,
        raw_bio=profile.raw_bio,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        portfolio_url=profile.portfolio_url,
        skills=skills_data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.get("/me", response_model=StudentProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """Fetch current student's full profile including attached skills."""
    return _format_profile_response(profile, current_user)


@router.put("/me", response_model=StudentProfileResponse)
def update_my_profile(
    update_data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """Update profile fields (academics, bio, social links, and optional full skills list)."""
    fields_to_update = [
        "phone", "college_name", "degree", "branch", "year",
        "cgpa", "experience_level", "raw_bio", "github_url",
        "linkedin_url", "portfolio_url"
    ]

    for field in fields_to_update:
        val = getattr(update_data, field, None)
        if val is not None:
            setattr(profile, field, val)

    # If full skills list is supplied in the update payload, sync them
    if update_data.skills is not None:
        # Clear existing associations
        db.query(StudentSkill).filter(StudentSkill.student_profile_id == profile.id).delete()
        db.flush()

        # Re-attach skills
        for item in update_data.skills:
            skill_name = item.name.strip()
            skill_record = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
            if not skill_record:
                skill_record = Skill(name=skill_name, category="General")
                db.add(skill_record)
                db.flush()

            new_ss = StudentSkill(
                student_profile_id=profile.id,
                skill_id=skill_record.id,
                proficiency_level=item.proficiency_level,
                years_of_experience=item.years_of_experience,
                verified=item.verified
            )
            db.add(new_ss)

    db.commit()
    db.refresh(profile)
    return _format_profile_response(profile, current_user)


@router.post("/me/skills", response_model=StudentSkillItem)
def add_or_update_skill(
    skill_item: StudentSkillItem,
    db: Session = Depends(get_db),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """Add a new skill or update proficiency for an existing skill in student profile."""
    skill_name = skill_item.name.strip()
    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name cannot be empty.")

    # 1. Resolve or create Skill entity in taxonomy
    skill_record = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
    if not skill_record:
        skill_record = Skill(name=skill_name, category="General")
        db.add(skill_record)
        db.flush()

    # 2. Check if student already has this skill
    student_skill = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.student_profile_id == profile.id,
            StudentSkill.skill_id == skill_record.id
        )
        .first()
    )

    if student_skill:
        student_skill.proficiency_level = skill_item.proficiency_level
        student_skill.years_of_experience = skill_item.years_of_experience
        student_skill.verified = skill_item.verified
    else:
        student_skill = StudentSkill(
            student_profile_id=profile.id,
            skill_id=skill_record.id,
            proficiency_level=skill_item.proficiency_level,
            years_of_experience=skill_item.years_of_experience,
            verified=skill_item.verified
        )
        db.add(student_skill)

    db.commit()
    db.refresh(student_skill)

    return StudentSkillItem(
        skill_id=skill_record.id,
        name=skill_record.name,
        proficiency_level=student_skill.proficiency_level,
        years_of_experience=student_skill.years_of_experience,
        verified=student_skill.verified
    )


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_200_OK)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """Remove a skill from the student's profile."""
    record = (
        db.query(StudentSkill)
        .filter(
            StudentSkill.student_profile_id == profile.id,
            StudentSkill.skill_id == skill_id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID {skill_id} not found in student profile."
        )

    db.delete(record)
    db.commit()
    return {"message": "Skill successfully removed from profile", "skill_id": skill_id}


@router.post("/me/parse-bio", response_model=SkillParseResponse)
def parse_raw_bio_for_skills(
    payload: Optional[SkillParseRequest] = None,
    db: Session = Depends(get_db),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """
    NLP skill extractor that parses unstructured bio or resume snippet
    against the recognized database skill taxonomy.
    """
    text = ""
    if payload and payload.raw_bio:
        text = payload.raw_bio
    elif profile.raw_bio:
        text = profile.raw_bio

    return extract_skills_from_text(text, db, include_text=False)


@router.post("/me/parse-resume", response_model=SkillParseResponse)
def parse_resume_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: StudentProfile = Depends(get_current_student_profile)
):
    """
    Parses an uploaded resume PDF in-memory (max 5 MB) using pypdf,
    extracts text, and applies the existing taxonomy skill matching.

    Privacy & Security:
      - The PDF file and full text are NEVER persisted to disk or database.
      - Full resume text is never outputted to logs.
      - Extracted text is returned in response only so user can optionally insert it into bio.
    """
    # 1. Validate file extension and MIME type
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if not filename.endswith(".pdf") and content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sirf PDF files supported hain. Kripya .pdf file upload karein."
        )

    # 2. Read file contents strictly in-memory and validate size
    contents = file.file.read()
    if len(contents) > MAX_RESUME_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size 5 MB se zyada hai. Kripya 5 MB se chhoti PDF upload karein."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload ki gayi PDF file khali hai."
        )

    # 3. Extract text using pypdf in-memory
    try:
        reader = PdfReader(io.BytesIO(contents))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        full_text = "\n".join(text_parts).strip()
    except Exception as exc:
        logger.warning(f"pypdf extraction error for user {current_user.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF file padhne mein samasya aayi. Kripya valid PDF document upload karein."
        )

    # 4. Scanned image or blank text validation (Requirement 5)
    if not full_text or len(full_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Is PDF mein text nahi mila, bio paste karo"
        )

    # Privacy: Log only character length and page count, never resume text
    logger.info(
        f"Resume parsed for user {current_user.id}: {len(reader.pages)} pages, {len(full_text)} characters."
    )

    # 5. Delegate to existing taxonomy skill extractor
    return extract_skills_from_text(full_text, db, include_text=True)
