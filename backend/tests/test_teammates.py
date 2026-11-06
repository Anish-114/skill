"""
Unit & Integration Tests for Complementary Teammate Matching & Team Requests:
1. Opt-out users (looking_for_team=False) never appear in recommendations.
2. Only opt-in users (looking_for_team=True) appear.
3. User never appears in their own recommendations.
4. Complementary scoring prioritizes candidates covering missing skills.
5. Privacy guard: sensitive contact info (email, phone, github_url, linkedin_url, portfolio_url)
   is masked (None) prior to team request acceptance.
6. Privacy reveal: contact info is visible to both parties once request is accepted.
7. Authorization: only the recipient can accept or decline requests (HTTP 403 otherwise).
8. Duplicate prevention: cannot send duplicate requests for the same event (HTTP 400).
9. Spam rate limiting: maximum 10 sent requests in 24 hours (HTTP 429 on 11th request).
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
from app.schemas.team_request import TeamRequestCreate, TeamRequestUpdate
from app.services.teammate_engine import find_teammates_for_opportunity
from app.api.v1.team_requests import (
    send_team_request,
    get_my_team_requests,
    update_team_request_status,
    MAX_REQUESTS_PER_24H,
)
from app.core.security import get_password_hash


class TestTeammateMatchingAndRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup in-memory test database
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        # Clean tables
        self.db.query(TeamRequest).delete()
        self.db.query(StudentSkill).delete()
        self.db.query(StudentProfile).delete()
        self.db.query(Opportunity).delete()
        self.db.query(Skill).delete()
        self.db.query(User).delete()
        self.db.commit()

        # Seed Skills
        self.s_python = Skill(name="Python", category="Backend")
        self.s_fastapi = Skill(name="FastAPI", category="Backend")
        self.s_react = Skill(name="React", category="Frontend")
        self.s_docker = Skill(name="Docker", category="DevOps")
        self.db.add_all([self.s_python, self.s_fastapi, self.s_react, self.s_docker])
        self.db.commit()

        # User 1: Alice (Python, FastAPI; missing Docker, React)
        self.u_alice = User(
            email="alice@example.com",
            hashed_password=get_password_hash("pass"),
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

        self.db.add_all([
            StudentSkill(student_profile_id=self.p_alice.id, skill_id=self.s_python.id, proficiency_level="Advanced"),
            StudentSkill(student_profile_id=self.p_alice.id, skill_id=self.s_fastapi.id, proficiency_level="Intermediate"),
        ])
        self.db.commit()

        # User 2: Bob (Docker, React; looking_for_team=True)
        self.u_bob = User(
            email="bob@example.com",
            hashed_password=get_password_hash("pass"),
            full_name="Bob Patel",
            is_active=True,
        )
        self.db.add(self.u_bob)
        self.db.commit()
        self.db.refresh(self.u_bob)

        self.p_bob = StudentProfile(
            user_id=self.u_bob.id,
            degree="B.Tech",
            branch="IT",
            year=3,
            college_name="NIT Surat",
            phone="9123456780",
            github_url="https://github.com/bob",
            linkedin_url="https://linkedin.com/in/bob",
            looking_for_team=True,
        )
        self.db.add(self.p_bob)
        self.db.commit()

        self.db.add_all([
            StudentSkill(student_profile_id=self.p_bob.id, skill_id=self.s_docker.id, proficiency_level="Advanced"),
            StudentSkill(student_profile_id=self.p_bob.id, skill_id=self.s_react.id, proficiency_level="Advanced"),
        ])
        self.db.commit()

        # User 3: Charlie (Docker; looking_for_team=False -> OPTED OUT)
        self.u_charlie = User(
            email="charlie@example.com",
            hashed_password=get_password_hash("pass"),
            full_name="Charlie Verma",
            is_active=True,
        )
        self.db.add(self.u_charlie)
        self.db.commit()
        self.db.refresh(self.u_charlie)

        self.p_charlie = StudentProfile(
            user_id=self.u_charlie.id,
            degree="B.Tech",
            branch="Computer Science",
            year=4,
            college_name="BITS Pilani",
            phone="9988776655",
            looking_for_team=False,  # OPTED OUT!
        )
        self.db.add(self.p_charlie)
        self.db.commit()

        self.db.add_all([
            StudentSkill(student_profile_id=self.p_charlie.id, skill_id=self.s_docker.id, proficiency_level="Intermediate"),
        ])
        self.db.commit()

        # Opportunity: SIH 2026 requiring Python, Docker, React
        self.opp = Opportunity(
            title="Smart India Hackathon 2026",
            organizer="Ministry of Education",
            category="Hackathon",
            description="National hackathon challenge",
            required_skills=["Python", "Docker", "React"],
            eligibility_criteria={"degrees": ["B.Tech"]},
            mode="Online",
            official_url="https://sih.gov.in",
            source="Ministry of Education",
            is_active=True,
        )
        self.db.add(self.opp)
        self.db.commit()
        self.db.refresh(self.opp)

    def tearDown(self):
        self.db.close()

    def test_teammate_suggestions_opt_in_and_self_exclusion(self):
        """Opt-in users appear, opted-out users do not, current user excluded."""
        candidates = find_teammates_for_opportunity(self.db, self.u_alice, self.opp)

        user_ids = [c.user_id for c in candidates]
        # 1. Alice must NOT be in her own recommendations
        self.assertNotIn(self.u_alice.id, user_ids)

        # 2. Bob (opt-in) MUST be in recommendations
        self.assertIn(self.u_bob.id, user_ids)

        # 3. Charlie (opted out) MUST NOT be in recommendations
        self.assertNotIn(self.u_charlie.id, user_ids)

        # 4. Check complementary matching
        bob_cand = next(c for c in candidates if c.user_id == self.u_bob.id)
        self.assertTrue(len(bob_cand.complementary_skills) > 0)
        self.assertIn("Ye teammate aapki missing skills", bob_cand.explanation)

    def test_privacy_guard_before_and_after_request_acceptance(self):
        """Contact info (email, phone, github, etc.) must be None before acceptance and visible after."""
        # 1. Before request: Bob's candidate card has NO contact info
        candidates = find_teammates_for_opportunity(self.db, self.u_alice, self.opp)
        bob_cand = next(c for c in candidates if c.user_id == self.u_bob.id)
        self.assertIsNone(bob_cand.email)
        self.assertIsNone(bob_cand.phone)
        self.assertIsNone(bob_cand.github_url)
        self.assertIsNone(bob_cand.linkedin_url)

        # 2. Alice sends a team request to Bob
        create_payload = TeamRequestCreate(
            to_user_id=self.u_bob.id,
            opportunity_id=self.opp.id,
            message="Hey Bob, let's team up!"
        )
        req_res = send_team_request(create_payload, self.db, self.u_alice)
        self.assertEqual(req_res.status, "pending")
        # In pending request response, Bob's contact info MUST still be masked!
        self.assertIsNone(req_res.to_user.email)
        self.assertIsNone(req_res.to_user.phone)

        # 3. Bob queries his received requests: Alice's contact info MUST still be masked!
        bob_reqs = get_my_team_requests("received", self.db, self.u_bob)
        self.assertEqual(len(bob_reqs), 1)
        self.assertIsNone(bob_reqs[0].from_user.email)
        self.assertIsNone(bob_reqs[0].from_user.phone)

        # 4. Bob accepts the request
        update_payload = TeamRequestUpdate(status="accepted")
        accepted_res = update_team_request_status(req_res.id, update_payload, self.db, self.u_bob)
        self.assertEqual(accepted_res.status, "accepted")
        # Contact info is NOW revealed!
        self.assertEqual(accepted_res.from_user.email, "alice@example.com")
        self.assertEqual(accepted_res.from_user.phone, "9876543210")
        self.assertEqual(accepted_res.to_user.email, "bob@example.com")
        self.assertEqual(accepted_res.to_user.phone, "9123456780")

        # 5. Alice checks candidate list again: Bob is now recognized as accepted teammate!
        candidates_after = find_teammates_for_opportunity(self.db, self.u_alice, self.opp)
        bob_cand_after = next(c for c in candidates_after if c.user_id == self.u_bob.id)
        self.assertEqual(bob_cand_after.request_status, "accepted")
        self.assertEqual(bob_cand_after.email, "bob@example.com")
        self.assertEqual(bob_cand_after.phone, "9123456780")
        self.assertEqual(bob_cand_after.github_url, "https://github.com/bob")

    def test_unauthorized_user_cannot_respond_to_request(self):
        """User cannot accept/decline someone else's request (HTTP 403)."""
        create_payload = TeamRequestCreate(
            to_user_id=self.u_bob.id,
            opportunity_id=self.opp.id,
            message="Hey"
        )
        req = send_team_request(create_payload, self.db, self.u_alice)

        # Charlie tries to accept the request sent to Bob
        with self.assertRaises(HTTPException) as ctx:
            update_team_request_status(req.id, TeamRequestUpdate(status="accepted"), self.db, self.u_charlie)
        self.assertEqual(ctx.exception.status_code, 403)

        # Alice (sender) tries to accept her own sent request
        with self.assertRaises(HTTPException) as ctx2:
            update_team_request_status(req.id, TeamRequestUpdate(status="accepted"), self.db, self.u_alice)
        self.assertEqual(ctx2.exception.status_code, 403)

    def test_cannot_send_request_to_opted_out_user(self):
        """Cannot send team request to a user who opted out (looking_for_team=False)."""
        create_payload = TeamRequestCreate(
            to_user_id=self.u_charlie.id,
            opportunity_id=self.opp.id,
            message="Hey Charlie"
        )
        with self.assertRaises(HTTPException) as ctx:
            send_team_request(create_payload, self.db, self.u_alice)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not currently open", ctx.exception.detail)

    def test_duplicate_request_rejected(self):
        """Cannot send duplicate request to the same user for the same opportunity."""
        create_payload = TeamRequestCreate(
            to_user_id=self.u_bob.id,
            opportunity_id=self.opp.id,
            message="Request 1"
        )
        send_team_request(create_payload, self.db, self.u_alice)

        # 2nd attempt
        with self.assertRaises(HTTPException) as ctx:
            send_team_request(create_payload, self.db, self.u_alice)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already sent a request", ctx.exception.detail)

    def test_spam_rate_limit_10_requests_per_24h(self):
        """User can send at most 10 requests in 24 hours. 11th request triggers HTTP 429."""
        # Create 11 opt-in dummy users
        dummy_users = []
        for i in range(11):
            u = User(
                email=f"dummy_{i}@example.com",
                hashed_password=get_password_hash("pass"),
                full_name=f"Dummy User {i}",
                is_active=True,
            )
            self.db.add(u)
            self.db.commit()
            self.db.refresh(u)

            p = StudentProfile(
                user_id=u.id,
                degree="B.Tech",
                branch="CS",
                year=2,
                looking_for_team=True,
            )
            self.db.add(p)
            self.db.commit()
            dummy_users.append(u)

        # Send 10 requests successfully
        for i in range(10):
            payload = TeamRequestCreate(
                to_user_id=dummy_users[i].id,
                opportunity_id=self.opp.id,
                message=f"Request {i}"
            )
            res = send_team_request(payload, self.db, self.u_alice)
            self.assertEqual(res.status, "pending")

        # 11th request must fail with HTTP 429
        payload_11 = TeamRequestCreate(
            to_user_id=dummy_users[10].id,
            opportunity_id=self.opp.id,
            message="Request 11"
        )
        with self.assertRaises(HTTPException) as ctx:
            send_team_request(payload_11, self.db, self.u_alice)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("Daily limit reached", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
