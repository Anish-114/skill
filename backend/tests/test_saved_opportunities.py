"""
Unit and Integration Tests for Saved Opportunities & Application Tracker:
1. Valid statuses validation ('saved', 'applied', 'in_progress', 'shortlisted', 'selected', 'rejected', 'archived')
2. Rejection of invalid statuses with HTTP 400
3. User isolation (user A cannot modify or view user B's saved opportunities)
4. Notes update independently from status update (and vice versa)
5. Tracking of expired opportunities without deletion
"""
import sys
import unittest
from datetime import datetime, timedelta, timezone

# Ensure backend directory is in sys.path
sys.path.insert(0, "backend")

from fastapi import HTTPException
from app.db.session import SessionLocal
from app.models import User, Opportunity, SavedOpportunity
from app.schemas.saved_opportunity import SavedOpportunityCreate
from app.api.v1.saved import (
    save_or_update_opportunity,
    list_saved_opportunities,
    remove_saved_opportunity,
    VALID_SAVED_STATUSES,
)
from app.core.security import get_password_hash


class TestSavedOpportunitiesTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        # Create 2 test users for isolation testing
        cls.user1 = cls.db.query(User).filter(User.email == "test_user1_tracker@example.com").first()
        if not cls.user1:
            cls.user1 = User(
                email="test_user1_tracker@example.com",
                full_name="Tracker Test User One",
                hashed_password=get_password_hash("Secret123!"),
                is_active=True,
            )
            cls.db.add(cls.user1)

        cls.user2 = cls.db.query(User).filter(User.email == "test_user2_tracker@example.com").first()
        if not cls.user2:
            cls.user2 = User(
                email="test_user2_tracker@example.com",
                full_name="Tracker Test User Two",
                hashed_password=get_password_hash("Secret123!"),
                is_active=True,
            )
            cls.db.add(cls.user2)

        cls.db.commit()
        cls.db.refresh(cls.user1)
        cls.db.refresh(cls.user2)

        # Create test active opportunity and test expired opportunity
        cls.opp_active = cls.db.query(Opportunity).filter(Opportunity.external_id == "tracker-test-opp-active").first()
        if not cls.opp_active:
            cls.opp_active = Opportunity(
                title="Active Hackathon for Tracker",
                organizer="Tracker Test Corp",
                category="Hackathon",
                description="Testing active opportunity tracker.",
                required_skills=["Python", "FastAPI"],
                official_url="https://example.com/tracker-active",
                source="Devfolio",
                external_id="tracker-test-opp-active",
                deadline=datetime.now(timezone.utc) + timedelta(days=10),
                is_active=True,
            )
            cls.db.add(cls.opp_active)

        cls.opp_expired = cls.db.query(Opportunity).filter(Opportunity.external_id == "tracker-test-opp-expired").first()
        if not cls.opp_expired:
            cls.opp_expired = Opportunity(
                title="Past Hackathon for Tracker History",
                organizer="Tracker Test Corp",
                category="Hackathon",
                description="Testing expired opportunity tracker history.",
                required_skills=["React", "TypeScript"],
                official_url="https://example.com/tracker-expired",
                source="Unstop",
                external_id="tracker-test-opp-expired",
                deadline=datetime.now(timezone.utc) - timedelta(days=5),
                is_active=False,
            )
            cls.db.add(cls.opp_expired)

        cls.db.commit()
        cls.db.refresh(cls.opp_active)
        cls.db.refresh(cls.opp_expired)

    @classmethod
    def tearDownClass(cls):
        # Clean up created test data
        cls.db.query(SavedOpportunity).filter(
            SavedOpportunity.user_id.in_([cls.user1.id, cls.user2.id])
        ).delete(synchronize_session=False)

        cls.db.query(Opportunity).filter(
            Opportunity.id.in_([cls.opp_active.id, cls.opp_expired.id])
        ).delete(synchronize_session=False)

        cls.db.query(User).filter(
            User.id.in_([cls.user1.id, cls.user2.id])
        ).delete(synchronize_session=False)

        cls.db.commit()
        cls.db.close()

    def setUp(self):
        # Clear saved records before each test for test users
        self.db.query(SavedOpportunity).filter(
            SavedOpportunity.user_id.in_([self.user1.id, self.user2.id])
        ).delete(synchronize_session=False)
        self.db.commit()

    def test_01_valid_statuses_accepted(self):
        """Verify all 7 allowed statuses are accepted: saved, applied, in_progress, shortlisted, selected, rejected, archived."""
        expected_statuses = {"saved", "applied", "in_progress", "shortlisted", "selected", "rejected", "archived"}
        self.assertEqual(VALID_SAVED_STATUSES, expected_statuses)

        for st in expected_statuses:
            payload = SavedOpportunityCreate(status=st, notes=f"Testing status {st}")
            res = save_or_update_opportunity(
                opportunity_id=self.opp_active.id,
                payload=payload,
                db=self.db,
                current_user=self.user1
            )
            self.assertEqual(res.status, st)
            self.assertEqual(res.notes, f"Testing status {st}")

    def test_02_invalid_status_rejected(self):
        """Verify invalid status raises HTTP 400 Bad Request."""
        payload = SavedOpportunityCreate(status="totally_invalid_status")
        with self.assertRaises(HTTPException) as ctx:
            save_or_update_opportunity(
                opportunity_id=self.opp_active.id,
                payload=payload,
                db=self.db,
                current_user=self.user1
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Allowed statuses are:", ctx.exception.detail)

    def test_03_user_isolation(self):
        """User 1's saved records and notes must be completely isolated from User 2."""
        # User 1 saves with status 'shortlisted' and private notes
        save_or_update_opportunity(
            opportunity_id=self.opp_active.id,
            payload=SavedOpportunityCreate(status="shortlisted", notes="User 1 private interview note"),
            db=self.db,
            current_user=self.user1
        )

        # User 2 list should be empty
        user2_list = list_saved_opportunities(db=self.db, current_user=self.user2)
        self.assertEqual(len(user2_list), 0)

        # User 2 saves same opportunity with 'rejected'
        save_or_update_opportunity(
            opportunity_id=self.opp_active.id,
            payload=SavedOpportunityCreate(status="rejected", notes="User 2 note"),
            db=self.db,
            current_user=self.user2
        )

        # Check User 1 record did not change
        user1_list = list_saved_opportunities(db=self.db, current_user=self.user1)
        self.assertEqual(len(user1_list), 1)
        self.assertEqual(user1_list[0].status, "shortlisted")
        self.assertEqual(user1_list[0].notes, "User 1 private interview note")

        # Check User 2 record
        user2_list = list_saved_opportunities(db=self.db, current_user=self.user2)
        self.assertEqual(len(user2_list), 1)
        self.assertEqual(user2_list[0].status, "rejected")
        self.assertEqual(user2_list[0].notes, "User 2 note")

        # User 2 deletes their bookmark
        remove_saved_opportunity(
            opportunity_id=self.opp_active.id,
            db=self.db,
            current_user=self.user2
        )

        # User 1 record remains completely intact
        user1_list_after = list_saved_opportunities(db=self.db, current_user=self.user1)
        self.assertEqual(len(user1_list_after), 1)
        self.assertEqual(user1_list_after[0].status, "shortlisted")

    def test_04_notes_and_status_independent_update(self):
        """Updating status preserves notes; updating notes preserves status."""
        # Initial save with status 'applied' and initial notes
        save_or_update_opportunity(
            opportunity_id=self.opp_active.id,
            payload=SavedOpportunityCreate(status="applied", notes="Applied on Nov 1st via portal"),
            db=self.db,
            current_user=self.user1
        )

        # Update notes only (status is None)
        save_or_update_opportunity(
            opportunity_id=self.opp_active.id,
            payload=SavedOpportunityCreate(status=None, notes="Round 1 interview confirmed!"),
            db=self.db,
            current_user=self.user1
        )

        record = list_saved_opportunities(db=self.db, current_user=self.user1)[0]
        self.assertEqual(record.status, "applied", "Status must remain 'applied' when only updating notes")
        self.assertEqual(record.notes, "Round 1 interview confirmed!")

        # Update status only (notes is None)
        save_or_update_opportunity(
            opportunity_id=self.opp_active.id,
            payload=SavedOpportunityCreate(status="selected", notes=None),
            db=self.db,
            current_user=self.user1
        )

        record2 = list_saved_opportunities(db=self.db, current_user=self.user1)[0]
        self.assertEqual(record2.status, "selected")
        self.assertEqual(record2.notes, "Round 1 interview confirmed!", "Notes must be preserved when only updating status")

    def test_05_expired_opportunity_saved_and_tracked(self):
        """Expired opportunity remains in saved list with full history and can be updated."""
        save_or_update_opportunity(
            opportunity_id=self.opp_expired.id,
            payload=SavedOpportunityCreate(status="selected", notes="Won 1st prize before deadline passed"),
            db=self.db,
            current_user=self.user1
        )

        saved = list_saved_opportunities(db=self.db, current_user=self.user1)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].opportunity_id, self.opp_expired.id)
        self.assertEqual(saved[0].status, "selected")
        self.assertEqual(saved[0].notes, "Won 1st prize before deadline passed")
        self.assertFalse(saved[0].opportunity.is_active, "Expired opportunity remains is_active=False")


if __name__ == "__main__":
    unittest.main()
