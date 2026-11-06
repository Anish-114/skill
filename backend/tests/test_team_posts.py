"""
Unit & Integration Tests for Team Posts Feature:
1. Model TeamPost creation with valid message, needed_skills, and team_size_needed.
2. Duplicate prevention: user cannot have more than 1 open post for the same opportunity (HTTP 400).
3. Daily rate limit: user can create at most 5 team posts in 24 hours (HTTP 429 on 6th).
4. Authorization guard: only post creator can edit or close their team post (HTTP 403 for others).
5. Join request & privacy guard:
   - Other users can send a join request to an open post.
   - Contact details (GitHub, LinkedIn, email, phone) are strictly masked (None) before acceptance.
   - Contact details are revealed to both parties once accepted.
6. Auto-close on event expiry:
   - When an opportunity's deadline passes, open posts are automatically closed and no join requests accepted.
7. Skill taxonomy validation:
   - Skills must match existing standard Skill taxonomy, unknown skills rejected (HTTP 400).
"""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.models.base import Base
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.skill import Skill, StudentSkill
from app.models.opportunity import Opportunity
from app.models.team_request import TeamRequest
from app.models.team_post import TeamPost
from app.schemas.team_post import TeamPostCreate, TeamPostUpdate, TeamPostJoinRequest
from app.api.v1.team_posts import (
    create_opportunity_team_post,
    list_opportunity_team_posts,
    get_my_team_posts,
    edit_team_post,
    close_team_post,
    join_team_post,
    MAX_POSTS_PER_24H,
)
from app.api.v1.team_requests import update_team_request_status
from app.schemas.team_request import TeamRequestUpdate
from app.core.security import get_password_hash


class TestTeamPosts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite database
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        # Clean tables in safe order
        self.db.query(TeamRequest).delete()
        self.db.query(TeamPost).delete()
        self.db.query(StudentSkill).delete()
        self.db.query(StudentProfile).delete()
        self.db.query(Opportunity).delete()
        self.db.query(Skill).delete()
        self.db.query(User).delete()
        self.db.commit()

        # Seed Skills Taxonomy
        self.s_python = Skill(name="Python", category="Backend")
        self.s_fastapi = Skill(name="FastAPI", category="Backend")
        self.s_react = Skill(name="React", category="Frontend")
        self.s_docker = Skill(name="Docker", category="DevOps")
        self.db.add_all([self.s_python, self.s_fastapi, self.s_react, self.s_docker])
        self.db.commit()

        # User 1: Alice (Creator)
        self.u_alice = User(
            email="alice@college.edu",
            hashed_password=get_password_hash("pass123"),
            full_name="Alice Sharma",
            is_active=True,
        )
        self.db.add(self.u_alice)
        self.db.commit()
        self.db.refresh(self.u_alice)

        self.p_alice = StudentProfile(
            user_id=self.u_alice.id,
            degree="B.Tech",
            branch="Computer Science",
            year=3,
            college_name="IIT Delhi",
            phone="9876543210",
            github_url="https://github.com/alice",
            linkedin_url="https://linkedin.com/in/alice",
            looking_for_team=True,
        )
        self.db.add(self.p_alice)
        self.db.commit()

        # User 2: Bob (Applicant with Docker and React)
        self.u_bob = User(
            email="bob@college.edu",
            hashed_password=get_password_hash("pass123"),
            full_name="Bob Kumar",
            is_active=True,
        )
        self.db.add(self.u_bob)
        self.db.commit()
        self.db.refresh(self.u_bob)

        self.p_bob = StudentProfile(
            user_id=self.u_bob.id,
            degree="B.Tech",
            branch="Information Technology",
            year=3,
            college_name="NSUT Delhi",
            phone="9123456780",
            github_url="https://github.com/bob",
            linkedin_url="https://linkedin.com/in/bob",
            looking_for_team=True,
        )
        self.db.add(self.p_bob)
        self.db.commit()

        # Add Bob's skills
        self.db.add(StudentSkill(student_profile_id=self.p_bob.id, skill_id=self.s_react.id, proficiency_level="Advanced"))
        self.db.add(StudentSkill(student_profile_id=self.p_bob.id, skill_id=self.s_docker.id, proficiency_level="Intermediate"))
        self.db.commit()

        # Opportunity: Active Hackathon (deadline 10 days ahead)
        now_utc = datetime.now(timezone.utc)
        self.opp = Opportunity(
            title="National Hackathon 2026",
            organizer="Tech India",
            category="Hackathon",
            description="Build AI solutions for social impact.",
            required_skills=["Python", "FastAPI", "React", "Docker"],
            eligibility_criteria={"degrees": ["B.Tech"], "allowed_years": [1, 2, 3, 4]},
            deadline=now_utc + timedelta(days=10),
            mode="Online",
            official_url="https://example.com/hackathon",
            source="Devfolio",
            is_active=True,
        )
        self.db.add(self.opp)
        self.db.commit()
        self.db.refresh(self.opp)

    def tearDown(self):
        self.db.close()

    def test_create_team_post_success(self):
        """Alice creates an open team post with valid skills and message."""
        payload = TeamPostCreate(
            message="Looking for a frontend developer (React) and DevOps person for National Hackathon!",
            needed_skills=["React", "Docker"],
            team_size_needed=2,
        )
        res = create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)
        self.assertEqual(res.opportunity_id, self.opp.id)
        self.assertEqual(res.user_id, self.u_alice.id)
        self.assertEqual(res.status, "open")
        self.assertEqual(res.team_size_needed, 2)
        self.assertIn("React", res.needed_skills)
        self.assertIn("Docker", res.needed_skills)
        self.assertTrue(res.is_creator)

    def test_prevent_duplicate_open_post(self):
        """Alice cannot have 2 open posts for the same opportunity."""
        payload = TeamPostCreate(
            message="Post 1: Need frontend partner",
            needed_skills=["React"],
            team_size_needed=1,
        )
        create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)

        # Attempt second open post for same opp
        with self.assertRaises(HTTPException) as ctx:
            create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already have an open team post", ctx.exception.detail)

    def test_taxonomy_validation(self):
        """Post creation fails if a requested skill is not in the Skill taxonomy."""
        payload = TeamPostCreate(
            message="Need someone good in NonExistentMagicSkill",
            needed_skills=["NonExistentMagicSkill"],
            team_size_needed=1,
        )
        with self.assertRaises(HTTPException) as ctx:
            create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not recognized", ctx.exception.detail)

    def test_daily_post_rate_limit(self):
        """User cannot create more than 5 posts in 24 hours."""
        # Create 5 distinct opportunities
        now_utc = datetime.now(timezone.utc)
        opps = []
        for i in range(5):
            o = Opportunity(
                title=f"Hackathon #{i+1}",
                organizer="Org",
                category="Hackathon",
                description="desc",
                required_skills=["Python"],
                deadline=now_utc + timedelta(days=5),
                mode="Online",
                official_url=f"https://example.com/{i+1}",
                source="Devfolio",
                is_active=True,
            )
            self.db.add(o)
            opps.append(o)
        self.db.commit()

        # Alice creates 5 posts
        for o in opps:
            payload = TeamPostCreate(message="Need teammates", needed_skills=["Python"], team_size_needed=1)
            create_opportunity_team_post(o.id, payload, db=self.db, current_user=self.u_alice)

        # 6th post in 24 hours should be blocked by rate limit
        o_extra = Opportunity(
            title="Extra Hackathon",
            organizer="Org",
            category="Hackathon",
            description="desc",
            required_skills=["Python"],
            deadline=now_utc + timedelta(days=5),
            mode="Online",
            official_url="https://example.com/extra",
            source="Devfolio",
            is_active=True,
        )
        self.db.add(o_extra)
        self.db.commit()

        payload = TeamPostCreate(message="Need teammates 6", needed_skills=["Python"], team_size_needed=1)
        with self.assertRaises(HTTPException) as ctx:
            create_opportunity_team_post(o_extra.id, payload, db=self.db, current_user=self.u_alice)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("Daily limit reached", ctx.exception.detail)

    def test_edit_and_close_authorization(self):
        """Only the post creator can edit or close their team post (HTTP 403 for other users)."""
        payload = TeamPostCreate(message="Initial message", needed_skills=["React"], team_size_needed=1)
        post = create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)

        # Bob tries to edit Alice's post
        with self.assertRaises(HTTPException) as ctx:
            edit_team_post(post.id, TeamPostUpdate(message="Hacked message"), db=self.db, current_user=self.u_bob)
        self.assertEqual(ctx.exception.status_code, 403)

        # Bob tries to close Alice's post
        with self.assertRaises(HTTPException) as ctx:
            close_team_post(post.id, db=self.db, current_user=self.u_bob)
        self.assertEqual(ctx.exception.status_code, 403)

        # Alice successfully edits her post
        updated = edit_team_post(post.id, TeamPostUpdate(message="Updated message by Alice"), db=self.db, current_user=self.u_alice)
        self.assertEqual(updated.message, "Updated message by Alice")

        # Alice successfully closes her post
        closed = close_team_post(post.id, db=self.db, current_user=self.u_alice)
        self.assertEqual(closed.status, "closed")

    def test_join_request_privacy_and_acceptance(self):
        """
        Bob requests to join Alice's post:
        - Contact details remain masked before request is accepted.
        - Contact details are revealed once request is accepted.
        """
        payload = TeamPostCreate(message="Looking for React and Docker specialist", needed_skills=["React", "Docker"], team_size_needed=2)
        post = create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)

        # Check Bob viewing the post on the Team Board
        board = list_opportunity_team_posts(self.opp.id, db=self.db, current_user=self.u_bob)
        self.assertEqual(len(board), 1)
        p_view = board[0]
        # Skill match: Bob has both React and Docker
        self.assertEqual(p_view.match_count, 2)
        self.assertEqual(p_view.match_percentage, 100.0)
        self.assertFalse(p_view.has_requested)

        # Privacy check before join/acceptance: Alice's contact details MUST be None
        self.assertIsNone(p_view.creator.email)
        self.assertIsNone(p_view.creator.phone)
        self.assertIsNone(p_view.creator.github_url)
        self.assertIsNone(p_view.creator.linkedin_url)
        self.assertEqual(p_view.creator.full_name, "Alice Sharma")
        self.assertEqual(p_view.creator.college_name, "IIT Delhi")

        # Bob sends join request
        join_payload = TeamPostJoinRequest(message="Hey Alice, I know React and Docker. Let's build together!")
        req = join_team_post(post.id, join_payload, db=self.db, current_user=self.u_bob)
        self.assertEqual(req.status, "pending")
        self.assertEqual(req.from_user_id, self.u_bob.id)
        self.assertEqual(req.to_user_id, self.u_alice.id)

        # Still pending: contact details still hidden
        board_after_req = list_opportunity_team_posts(self.opp.id, db=self.db, current_user=self.u_bob)
        self.assertTrue(board_after_req[0].has_requested)
        self.assertEqual(board_after_req[0].my_request_status, "pending")
        self.assertIsNone(board_after_req[0].creator.email)

        # Alice accepts the request
        update_team_request_status(req.id, TeamRequestUpdate(status="accepted"), db=self.db, current_user=self.u_alice)

        # Privacy Reveal: Now Alice's contact details ARE revealed to Bob!
        board_accepted = list_opportunity_team_posts(self.opp.id, db=self.db, current_user=self.u_bob)
        self.assertEqual(board_accepted[0].my_request_status, "accepted")
        self.assertEqual(board_accepted[0].creator.email, "alice@college.edu")
        self.assertEqual(board_accepted[0].creator.phone, "9876543210")
        self.assertEqual(board_accepted[0].creator.github_url, "https://github.com/alice")
        self.assertEqual(board_accepted[0].creator.linkedin_url, "https://linkedin.com/in/alice")

    def test_expired_event_auto_close(self):
        """
        When an event passes its deadline:
        - Open posts for that event are automatically closed.
        - Team Board returns empty list.
        - Join requests are rejected.
        """
        payload = TeamPostCreate(message="Looking for React partner", needed_skills=["React"], team_size_needed=1)
        post = create_opportunity_team_post(self.opp.id, payload, db=self.db, current_user=self.u_alice)
        self.assertEqual(post.status, "open")

        # Manually expire the opportunity deadline to the past
        self.opp.deadline = datetime.now(timezone.utc) - timedelta(hours=2)
        self.db.commit()

        # Viewing the Team Board triggers auto-close
        board = list_opportunity_team_posts(self.opp.id, db=self.db, current_user=self.u_bob)
        self.assertEqual(len(board), 0)

        # Verify DB row is closed
        db_post = self.db.query(TeamPost).filter(TeamPost.id == post.id).first()
        self.assertEqual(db_post.status, "closed")

        # Joining an expired event's post is rejected
        with self.assertRaises(HTTPException) as ctx:
            join_team_post(post.id, TeamPostJoinRequest(message="Can I still join?"), db=self.db, current_user=self.u_bob)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
