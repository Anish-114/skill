import os
import sys
import zoneinfo
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base, Opportunity
from app.services.events_sync.base import parse_and_normalize_to_utc, IST
from app.api.v1.opportunities import list_opportunities
from app.api.v1.events import list_active_events
from app.schemas.opportunity import OpportunityResponse


def test_ist_naive_conversion_and_no_early_expiration():
    """
    Validates timezone normalization and ensures an event scheduled in IST
    does NOT prematurely expire 5.5 hours early.
    """
    print("\n" + "=" * 65)
    print("TEST: Naive IST Datetime Normalization & Expiry Check")
    print("=" * 65)

    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    print(f"Current UTC time : {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Current IST time : {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Case 1: An event scheduled to close 2 hours from now in India (IST)
    # The source provides this as a naive string without timezone offset.
    event_future_ist = now_ist + timedelta(hours=2)
    naive_ist_string = event_future_ist.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nSource gives naive IST string: '{naive_ist_string}' (2 hours from now in IST)")

    # 1. Parse using parse_and_normalize_to_utc
    normalized_deadline = parse_and_normalize_to_utc(naive_ist_string)
    assert normalized_deadline is not None
    assert normalized_deadline.tzinfo == timezone.utc, "Must be timezone-aware UTC"

    # 2. Verify UTC hour calculation matches IST - 5:30
    expected_utc = event_future_ist.astimezone(timezone.utc)
    diff_seconds = abs((normalized_deadline - expected_utc).total_seconds())
    assert diff_seconds < 1.0, f"Expected {expected_utc}, got {normalized_deadline}"

    # 3. CRITICAL EXPIRY CHECK:
    # The event is 2 hours in the future in India. It must NOT expire now!
    is_active_now = normalized_deadline >= now_utc
    remaining_seconds = (normalized_deadline - now_utc).total_seconds()
    remaining_hours = remaining_seconds / 3600.0

    print(f"Normalized UTC deadline     : {normalized_deadline.isoformat()}")
    print(f"Time remaining until expiry : {remaining_hours:.2f} hours")
    assert is_active_now is True, "Event must remain active! It should NOT expire prematurely."
    assert 1.9 <= remaining_hours <= 2.1, f"Expected ~2 hours remaining, got {remaining_hours:.2f}h"

    # 4. COUNTERFACTUAL VERIFICATION:
    # If the naive string was erroneously treated as naive UTC and then offset by -5.5h,
    # or if naive IST was compared to naive UTC directly, it would have expired 3.5 hours ago!
    erroneous_early_shift = normalized_deadline - timedelta(hours=5, minutes=30)
    would_be_expired_if_broken = erroneous_early_shift < now_utc
    assert would_be_expired_if_broken is True, "5.5h early shift would have falsely expired the event."
    print("[PASS] Confirmed: Event does NOT expire 5.5 hours early.")

    # 5. Database Integration & API Query Verification
    test_engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSession()

    try:
        # Create opportunity with normalized UTC deadline
        opp = Opportunity(
            title="Future Hackathon India",
            organizer="Tech India",
            category="Hackathon",
            description="Active contest with naive IST deadline converted to UTC.",
            required_skills=["Python", "FastAPI"],
            eligibility_criteria={},
            deadline=normalized_deadline,
            mode="Online",
            official_url="https://futurehack.in",
            source="Devfolio",
            is_active=True
        )
        db.add(opp)
        db.commit()

        # Query via opportunities endpoint (is_active=True)
        active_opps = list_opportunities(is_active=True, db=db)
        assert len(active_opps) == 1, "Opportunity must be returned as active and upcoming"
        assert active_opps[0].title == "Future Hackathon India"

        # Query via events endpoint
        active_events = list_active_events(db=db)
        assert len(active_events) == 1, "Must be returned in active events list"

        # Verify API response serializes deadline with 'Z' suffix
        resp_schema = OpportunityResponse.model_validate(opp)
        resp_json = resp_schema.model_dump_json()
        assert resp_json is not None
        assert '"deadline":"' in resp_json
        assert resp_json.split('"deadline":"')[1].split('"')[0].endswith("Z"), "API deadline must end with 'Z'"
        print(f"[PASS] API JSON deadline serialized as: {resp_schema.deadline}")

        # Case 2: Past Event (30 minutes ago in IST)
        past_ist = now_ist - timedelta(minutes=30)
        past_deadline = parse_and_normalize_to_utc(past_ist.strftime("%Y-%m-%d %H:%M:%S"))
        opp_past = Opportunity(
            title="Past Hackathon India",
            organizer="Past Tech",
            category="Hackathon",
            description="Expired contest.",
            required_skills=["Python"],
            eligibility_criteria={},
            deadline=past_deadline,
            mode="Online",
            official_url="https://pasthack.in",
            source="Devfolio",
            is_active=True
        )
        db.add(opp_past)
        db.commit()

        # Querying active events must exclude the past event
        active_filtered = list_opportunities(is_active=True, db=db)
        assert len(active_filtered) == 1, "Past event must be filtered out!"
        assert active_filtered[0].title == "Future Hackathon India"
        print("[PASS] Verified: Past event is filtered out based on deadline >= now.")

    finally:
        db.close()

    print("\n" + "=" * 65)
    print("ALL TIMEZONE & EXPIRY TESTS PASSED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    test_ist_naive_conversion_and_no_early_expiration()
