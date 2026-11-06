"""
Unit & integration tests for SkillBridge AI API route handlers.
"""
from app.db.session import SessionLocal
from app.main import root, health_check, list_opportunities, list_skills


def test_api_endpoints():
    db = SessionLocal()
    try:
        # 1. Test root endpoint
        root_data = root()
        assert root_data["status"] == "online"
        assert root_data["version"] == "1.0.0"
        print("[PASS] Root endpoint verified.")

        # 2. Test health check endpoint
        health_data = health_check(db=db)
        assert health_data["status"] == "healthy"
        assert health_data["database"] == "connected"
        assert health_data["stats"]["opportunities"] >= 10
        assert health_data["stats"]["skills"] >= 40
        assert health_data["stats"]["users"] >= 1
        print(f"[PASS] Health check verified: {health_data['stats']}")

        # 3. Test list_opportunities endpoint
        all_opps = list_opportunities(db=db)
        assert len(all_opps) == 10
        print(f"[PASS] Retrieved {len(all_opps)} opportunities.")

        # Filter by category
        hackathons = list_opportunities(category="Hackathon", db=db)
        assert len(hackathons) > 0
        assert all((getattr(h, "category", None) or h.get("category")) == "Hackathon" for h in hackathons)
        print(f"[PASS] Category filter 'Hackathon' matched {len(hackathons)} items.")

        # Filter by mode
        online_opps = list_opportunities(mode="Online", db=db)
        assert len(online_opps) > 0
        assert all((getattr(o, "mode", None) or o.get("mode")) == "Online" for o in online_opps)
        print(f"[PASS] Mode filter 'Online' matched {len(online_opps)} items.")

        # 4. Test list_skills endpoint
        all_skills = list_skills(db=db)
        assert len(all_skills) >= 40
        ai_skills = list_skills(category="AI/ML", db=db)
        assert len(ai_skills) > 0
        assert all((getattr(s, "category", None) or (s.get("category") if isinstance(s, dict) else None)) == "AI/ML" for s in ai_skills)
        print(f"[PASS] Skills taxonomy verified ({len(all_skills)} total skills, {len(ai_skills)} AI/ML skills).")

        print("\nAll API route tests passed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    test_api_endpoints()
