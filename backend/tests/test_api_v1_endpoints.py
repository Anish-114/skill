"""
API Integration Test Suite for Phase 3 REST Endpoints:
1. Profiles API (GET/PUT profile, add/delete skill, parse-bio)
2. Opportunities API (list with filters, detailed view)
3. Recommendations API (ranked by final_score descending, min_score threshold)
4. Evaluation API (deterministic eligibility check + skill gap + checklist)
5. Saved Opportunities API (CRUD bookmarks)
"""
from app.db.session import SessionLocal
from app.models import Opportunity, Skill, StudentProfile, User
from app.schemas.student_profile import (
    StudentProfileUpdate,
    StudentSkillItem,
    SkillParseRequest,
)
from app.schemas.saved_opportunity import SavedOpportunityCreate
from app.api.v1.profiles import (
    get_my_profile,
    update_my_profile,
    add_or_update_skill,
    delete_skill,
    parse_raw_bio_for_skills,
)
from app.api.v1.opportunities import (
    list_opportunities,
    get_opportunity_detail,
)
from app.api.v1.recommendations import get_personalized_recommendations
from app.api.v1.evaluation import evaluate_opportunity_for_student
from app.api.v1.saved import (
    list_saved_opportunities,
    save_opportunity,
    remove_saved_opportunity,
)


def get_test_context(db):
    user = db.query(User).filter(User.email == "student@skillbridge.ai").first()
    assert user is not None, "Seeded user student@skillbridge.ai must exist"
    profile = user.profile
    assert profile is not None, "User profile must exist"
    return user, profile


def test_profiles_endpoints():
    db = SessionLocal()
    try:
        user, profile = get_test_context(db)

        # 1. GET /api/v1/profiles/me
        my_prof = get_my_profile(current_user=user, profile=profile)
        assert my_prof.email == user.email
        assert my_prof.degree == "B.Tech"
        assert my_prof.year == 3
        assert len(my_prof.skills) > 0
        print(f"[PASS] GET /profiles/me verified (User: {my_prof.full_name}, Skills: {len(my_prof.skills)}).")

        # 2. PUT /api/v1/profiles/me
        original_bio = profile.raw_bio
        test_bio = "Full-stack developer specializing in FastAPI, React, and Machine Learning."
        update_payload = StudentProfileUpdate(raw_bio=test_bio, experience_level="Advanced")
        updated_prof = update_my_profile(
            update_data=update_payload,
            db=db,
            current_user=user,
            profile=profile
        )
        assert updated_prof.raw_bio == test_bio
        assert updated_prof.experience_level == "Advanced"
        print("[PASS] PUT /profiles/me verified.")

        # 3. POST /api/v1/profiles/me/skills (Add skill)
        new_skill_item = StudentSkillItem(
            name="Kubernetes",
            proficiency_level="Intermediate",
            years_of_experience=1.5,
            verified=True
        )
        added_skill = add_or_update_skill(
            skill_item=new_skill_item,
            db=db,
            profile=profile
        )
        assert added_skill.name == "Kubernetes"
        assert added_skill.proficiency_level == "Intermediate"
        print(f"[PASS] POST /profiles/me/skills added skill '{added_skill.name}'.")

        # 4. DELETE /api/v1/profiles/me/skills/{skill_id}
        del_resp = delete_skill(skill_id=added_skill.skill_id, db=db, profile=profile)
        assert del_resp["skill_id"] == added_skill.skill_id
        print(f"[PASS] DELETE /profiles/me/skills/{added_skill.skill_id} verified.")

        # 5. POST /api/v1/profiles/me/parse-bio
        parse_req = SkillParseRequest(
            raw_bio="I develop reactive UI applications using React, build fast web backends with FastAPI and Python, and train PyTorch deep learning models."
        )
        parsed = parse_raw_bio_for_skills(payload=parse_req, db=db, profile=profile)
        assert len(parsed.extracted_skills) >= 3
        assert "Python" in parsed.extracted_skills
        assert "FastAPI" in parsed.extracted_skills
        assert "React" in parsed.extracted_skills
        print(f"[PASS] POST /profiles/me/parse-bio successfully extracted: {parsed.extracted_skills}.")

        # Restore original bio
        update_my_profile(
            update_data=StudentProfileUpdate(raw_bio=original_bio, experience_level="Intermediate"),
            db=db,
            current_user=user,
            profile=profile
        )

    finally:
        db.close()


def test_opportunities_endpoints():
    db = SessionLocal()
    try:
        user, _ = get_test_context(db)

        # 1. GET /api/v1/opportunities (with filtering)
        all_opps = list_opportunities(
            category="Hackathon",
            mode="Online",
            is_active=True,
            skip=0,
            limit=10,
            db=db
        )
        assert len(all_opps) > 0
        for opp in all_opps:
            assert opp.category == "Hackathon"
            assert opp.mode == "Online"
        print(f"[PASS] GET /opportunities filtered {len(all_opps)} Online Hackathons.")

        # 2. GET /api/v1/opportunities with search
        search_kw = all_opps[0].title.split()[0] if all_opps else "Hackathon"
        search_opps = list_opportunities(
            search=search_kw,
            skip=0,
            limit=5,
            db=db
        )
        assert len(search_opps) >= 1
        assert (
            search_kw.lower() in search_opps[0].title.lower()
            or search_kw.lower() in search_opps[0].description.lower()
            or search_kw.lower() in search_opps[0].organizer.lower()
        )
        print(f"[PASS] GET /opportunities search keyword returned '{search_opps[0].title}'.")

        # 3. GET /api/v1/opportunities/{id}
        first_opp = all_opps[0]
        opp_detail = get_opportunity_detail(id=first_opp.id, db=db, current_user=user)
        assert opp_detail.id == first_opp.id
        assert opp_detail.title == first_opp.title
        assert isinstance(opp_detail.is_saved, bool)
        print(f"[PASS] GET /opportunities/{first_opp.id} detail verified (is_saved: {opp_detail.is_saved}).")

    finally:
        db.close()


def test_recommendations_endpoint():
    db = SessionLocal()
    try:
        _, profile = get_test_context(db)

        # GET /api/v1/recommendations
        recs = get_personalized_recommendations(
            min_score=30.0,
            category=None,
            limit=10,
            db=db,
            profile=profile
        )
        assert len(recs) > 0, "Expected ranked recommendations"

        # Check descending order by final_score
        scores = [r.final_score for r in recs]
        assert scores == sorted(scores, reverse=True), f"Recommendations not sorted descending: {scores}"

        top_match = recs[0]
        assert top_match.final_score >= 60.0
        assert top_match.eligibility_status in ["ELIGIBLE", "NEEDS_VERIFICATION", "NOT_ELIGIBLE"]
        assert len(top_match.explanation) > 20
        assert top_match.breakdown.skill_match >= 0.0

        print(f"[PASS] GET /recommendations ranked {len(recs)} opportunities.")
        print(f"       Top Match: '{top_match.opportunity.title}' (Score: {top_match.final_score}%, Status: {top_match.eligibility_status})")

    finally:
        db.close()


def test_evaluation_endpoint():
    db = SessionLocal()
    try:
        _, profile = get_test_context(db)

        target_opp = db.query(Opportunity).filter(Opportunity.is_active == True).first()
        assert target_opp is not None, "No active opportunity found for evaluation test"

        # GET /api/v1/opportunities/{id}/evaluate
        eval_resp = evaluate_opportunity_for_student(id=target_opp.id, db=db, profile=profile)
        assert eval_resp.opportunity_id == target_opp.id
        assert eval_resp.eligibility.status in ["ELIGIBLE", "NEEDS_VERIFICATION", "NOT_ELIGIBLE"]
        assert eval_resp.skill_gap.readiness_score >= 0.0
        assert "recommendation" in eval_resp.model_dump()
        assert "final_score" in eval_resp.recommendation

        print(f"[PASS] GET /opportunities/{target_opp.id}/evaluate returned:")
        print(f"       Eligibility: {eval_resp.eligibility.status}")
        print(f"       Skill Readiness: {eval_resp.skill_gap.readiness_score}%")
        print(f"       Matched Skills: {eval_resp.skill_gap.matched_skills}")
        print(f"       Preparation Tips: {len(eval_resp.skill_gap.preparation_checklist)} items")

    finally:
        db.close()


def test_saved_opportunities_crud():
    db = SessionLocal()
    try:
        user, _ = get_test_context(db)

        opp = db.query(Opportunity).filter(Opportunity.title.like("%Google Solution Challenge%")).first()
        assert opp is not None

        # 1. Bookmark opportunity: POST /api/v1/saved-opportunities/{id}
        save_payload = SavedOpportunityCreate(
            status="in_progress",
            notes="Forming a team of 3 students for UN SDG theme."
        )
        saved = save_opportunity(
            opportunity_id=opp.id,
            payload=save_payload,
            db=db,
            current_user=user
        )
        assert saved.opportunity_id == opp.id
        assert saved.status == "in_progress"
        assert saved.notes == "Forming a team of 3 students for UN SDG theme."
        print(f"[PASS] POST /saved-opportunities/{opp.id} saved bookmark.")

        # 2. List saved opportunities: GET /api/v1/saved-opportunities
        saved_list = list_saved_opportunities(status_filter=None, db=db, current_user=user)
        assert any(item.opportunity_id == opp.id for item in saved_list)
        print(f"[PASS] GET /saved-opportunities verified ({len(saved_list)} bookmarked events).")

        # 3. Unsave opportunity: DELETE /api/v1/saved-opportunities/{id}
        del_res = remove_saved_opportunity(opportunity_id=opp.id, db=db, current_user=user)
        assert del_res["opportunity_id"] == opp.id

        # Verify removal
        saved_list_after = list_saved_opportunities(status_filter=None, db=db, current_user=user)
        assert not any(item.opportunity_id == opp.id for item in saved_list_after)
        print(f"[PASS] DELETE /saved-opportunities/{opp.id} unsaved bookmark.")

    finally:
        db.close()


def run_all_api_tests():
    print("=" * 65)
    print("RUNNING SKILLBRIDGE AI PHASE 3 REST API INTEGRATION SUITE")
    print("=" * 65)

    test_profiles_endpoints()
    test_opportunities_endpoints()
    test_recommendations_endpoint()
    test_evaluation_endpoint()
    test_saved_opportunities_crud()

    print("=" * 65)
    print("ALL PHASE 3 REST API INTEGRATION TESTS PASSED! (5/5 Modules)")
    print("=" * 65)


if __name__ == "__main__":
    run_all_api_tests()
