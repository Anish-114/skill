from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models import Skill

router = APIRouter(prefix="/skills", tags=["Skills"])


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None


@router.get("", response_model=List[SkillResponse])
def list_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve list of standardized taxonomy skills."""
    query = db.query(Skill)
    if category and isinstance(category, str):
        query = query.filter(Skill.category == category)
    if search and isinstance(search, str):
        query = query.filter(Skill.name.ilike(f"%{search}%"))
    skills = query.order_by(Skill.name.asc()).all()
    return [{"id": s.id, "name": s.name, "category": s.category} for s in skills]
