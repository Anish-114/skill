import logging
from sqlalchemy import select, or_, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models import (
    Base,
    User,
    StudentProfile,
    Skill,
    StudentSkill,
    Opportunity,
    SavedOpportunity,
    TeamRequest,
    TeamPost,
)
from app.db.seed_data import SAMPLE_SKILLS, SAMPLE_OPPORTUNITIES, SAMPLE_USERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_synthetic_sih_events(db: Session) -> int:
    """
    Idempotent startup cleanup: Deletes synthetic SIH / Smart India Hackathon records
    and any associated saved opportunity bookmarks.
    Safe to execute repeatedly.
    """
    try:
        sih_opps = (
            db.query(Opportunity)
            .filter(
                or_(
                    Opportunity.source == "Smart India Hackathon",
                    Opportunity.title.ilike("%Smart India%"),
                    Opportunity.title.ilike("%SIH 202%"),
                    Opportunity.official_url.ilike("%sih.gov.in%")
                )
            )
            .all()
        )
        if not sih_opps:
            return 0

        sih_ids = [o.id for o in sih_opps]
        # Clean any bookmarks referencing these opportunities first
        db.query(SavedOpportunity).filter(SavedOpportunity.opportunity_id.in_(sih_ids)).delete(synchronize_session=False)
        deleted_count = db.query(Opportunity).filter(Opportunity.id.in_(sih_ids)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"Idempotent cleanup: Successfully removed {deleted_count} synthetic SIH opportunity records.")
        return deleted_count
    except Exception as exc:
        db.rollback()
        logger.warning(f"Synthetic SIH cleanup note: {exc}")
        return 0


def init_db(db: Session = None) -> None:
    """
    Initializes database schema and populates essential seed data
    if tables are currently empty.
    """
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    # SQLite migration helper to ensure newly added columns exist
    try:
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(opportunities)")).fetchall()]
            if cols:
                if "external_id" not in cols:
                    logger.info("Migrating opportunities table: adding external_id column...")
                    conn.execute(text("ALTER TABLE opportunities ADD COLUMN external_id VARCHAR(255)"))
                    conn.commit()
                if "start_date" not in cols:
                    logger.info("Migrating opportunities table: adding start_date column...")
                    conn.execute(text("ALTER TABLE opportunities ADD COLUMN start_date DATETIME"))
                    conn.commit()

            sp_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(student_profiles)")).fetchall()]
            if sp_cols:
                if "looking_for_team" not in sp_cols:
                    logger.info("Migrating student_profiles table: adding looking_for_team column...")
                    conn.execute(text("ALTER TABLE student_profiles ADD COLUMN looking_for_team BOOLEAN NOT NULL DEFAULT 0"))
                    conn.commit()

            tr_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(team_requests)")).fetchall()]
            if tr_cols:
                if "team_post_id" not in tr_cols:
                    logger.info("Migrating team_requests table: adding team_post_id column...")
                    conn.execute(text("ALTER TABLE team_requests ADD COLUMN team_post_id INTEGER REFERENCES team_posts(id)"))
                    conn.commit()
    except Exception as mig_err:
        logger.warning(f"Column migration check note: {mig_err}")

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Run idempotent cleanup of synthetic SIH records
        cleanup_synthetic_sih_events(db)

        # 1. Seed Skills Taxonomy
        existing_skills_count = db.query(Skill).count()
        if existing_skills_count == 0:
            logger.info("Seeding skills taxonomy...")
            for skill_data in SAMPLE_SKILLS:
                skill = Skill(
                    name=skill_data["name"],
                    category=skill_data["category"]
                )
                db.add(skill)
            db.commit()
            logger.info(f"Successfully seeded {len(SAMPLE_SKILLS)} skills.")
        else:
            logger.info(f"Skills already seeded ({existing_skills_count} skills present).")

        # Map skill names to Skill objects for fast lookup
        skills_map = {skill.name: skill for skill in db.query(Skill).all()}

        # 2. Seed Opportunities ONLY if explicitly enabled for development/testing
        # In production, events are exclusively synchronized from verified real sources
        if getattr(settings, "SEED_SAMPLE_OPPORTUNITIES", False):
            existing_opps_count = db.query(Opportunity).count()
            if existing_opps_count == 0:
                logger.info("SEED_SAMPLE_OPPORTUNITIES is True: Seeding sample opportunities catalogue...")
                for opp_data in SAMPLE_OPPORTUNITIES:
                    opportunity = Opportunity(
                        title=opp_data["title"],
                        organizer=opp_data["organizer"],
                        category=opp_data["category"],
                        description=opp_data["description"],
                        required_skills=opp_data["required_skills"],
                        eligibility_criteria=opp_data["eligibility_criteria"],
                        deadline=opp_data["deadline"],
                        mode=opp_data["mode"],
                        location=opp_data.get("location"),
                        official_url=opp_data["official_url"],
                        source=opp_data["source"],
                        prize_pool=opp_data.get("prize_pool"),
                        is_active=opp_data.get("is_active", True)
                    )
                    db.add(opportunity)
                db.commit()
                logger.info(f"Successfully seeded {len(SAMPLE_OPPORTUNITIES)} sample opportunities.")
            else:
                logger.info(f"Opportunities catalogue already populated ({existing_opps_count} opportunities).")
        else:
            logger.info("Production mode: Sample opportunities seeding disabled. Events will populate via live sync.")

        # 3. Seed Sample Student Users & Profiles
        existing_users_count = db.query(User).count()
        if existing_users_count == 0:
            logger.info("Seeding sample user & student profile...")
            # Use safe password hashing with fallback if passlib/bcrypt encounters runtime issues
            try:
                from app.core.security import get_password_hash
            except Exception:
                get_password_hash = lambda pwd: f"$fakehash${pwd}"

            for user_data in SAMPLE_USERS:
                user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=user_data["is_active"],
                    is_superuser=user_data["is_superuser"]
                )
                db.add(user)
                db.flush()  # Populates user.id

                # Create Student Profile
                prof_data = user_data["profile"]
                profile = StudentProfile(
                    user_id=user.id,
                    phone=prof_data.get("phone"),
                    college_name=prof_data.get("college_name"),
                    degree=prof_data["degree"],
                    branch=prof_data["branch"],
                    year=prof_data["year"],
                    cgpa=prof_data.get("cgpa"),
                    experience_level=prof_data["experience_level"],
                    raw_bio=prof_data.get("raw_bio"),
                    github_url=prof_data.get("github_url"),
                    linkedin_url=prof_data.get("linkedin_url"),
                    portfolio_url=prof_data.get("portfolio_url")
                )
                db.add(profile)
                db.flush()  # Populates profile.id

                # Link Student Skills
                for skill_info in prof_data.get("skills", []):
                    skill_obj = skills_map.get(skill_info["name"])
                    if not skill_obj:
                        skill_obj = Skill(name=skill_info["name"], category="General")
                        db.add(skill_obj)
                        db.flush()
                        skills_map[skill_obj.name] = skill_obj

                    student_skill = StudentSkill(
                        student_profile_id=profile.id,
                        skill_id=skill_obj.id,
                        proficiency_level=skill_info.get("proficiency_level", "Intermediate"),
                        years_of_experience=skill_info.get("years_of_experience", 1.0),
                        verified=skill_info.get("verified", False)
                    )
                    db.add(student_skill)

                # Save a sample bookmarked opportunity for this user if available
                first_opp = db.query(Opportunity).filter(Opportunity.is_active == True).first()
                if first_opp:
                    saved_opp = SavedOpportunity(
                        user_id=user.id,
                        opportunity_id=first_opp.id,
                        status="saved",
                        notes="Bookmarked for skill gap review and pre-application preparation."
                    )
                    db.add(saved_opp)

            db.commit()
            logger.info("Successfully seeded sample user profile, skills, and saved opportunities.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Error during database initialization: {exc}", exc_info=True)
        raise exc
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    init_db()
