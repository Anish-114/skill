"""
Verification suite for SkillBridge AI models and database seed logic.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    User,
    StudentProfile,
    Skill,
    StudentSkill,
    Opportunity,
    SavedOpportunity,
)
from app.core.config import settings
from app.db.init_db import init_db
from app.db.seed_data import SAMPLE_OPPORTUNITIES, SAMPLE_SKILLS


def test_models_and_seed_data():
    # Use in-memory SQLite database to test completely isolated from file I/O
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # 1. Ensure schema creates cleanly
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    
    # Enable sample opportunities seeding for this isolated in-memory test
    prev_seed_flag = settings.SEED_SAMPLE_OPPORTUNITIES
    settings.SEED_SAMPLE_OPPORTUNITIES = True

    try:
        # 2. Run seed logic directly on the in-memory database
        init_db(db=session)

        # 3. Verify Opportunities
        opportunities = session.query(Opportunity).all()
        assert len(opportunities) >= len(SAMPLE_OPPORTUNITIES), "Opportunities count mismatch"
        
        # Check specific opportunity properties from sample opportunities
        google_sc = session.query(Opportunity).filter(Opportunity.title.like("%Google Solution Challenge%")).first()
        assert google_sc is not None, "Google Solution Challenge not found in seed"
        assert "Flutter" in google_sc.required_skills
        assert "Python" in google_sc.required_skills
        assert google_sc.is_active is True

        # 4. Verify Skills Taxonomy
        skills = session.query(Skill).all()
        assert len(skills) >= len(SAMPLE_SKILLS), "Skills count mismatch"

        # 5. Verify User and StudentProfile relationship
        user = session.query(User).filter(User.email == "student@skillbridge.ai").first()
        assert user is not None
        assert user.profile is not None
        assert user.profile.degree == "B.Tech"
        assert user.profile.branch == "Computer Science & Engineering"
        assert user.profile.year == 3

        # 6. Verify Many-to-Many StudentSkill association
        assert len(user.profile.student_skills) > 0
        skill_names = [ss.skill.name for ss in user.profile.student_skills]
        assert "Python" in skill_names
        assert "FastAPI" in skill_names

        # 7. Verify SavedOpportunity
        saved = session.query(SavedOpportunity).filter(SavedOpportunity.user_id == user.id).first()
        assert saved is not None
        assert saved.opportunity is not None

        print("\nAll database schema, relationships, and seed validations passed successfully!")
    finally:
        settings.SEED_SAMPLE_OPPORTUNITIES = prev_seed_flag
        session.close()


if __name__ == "__main__":
    test_models_and_seed_data()
