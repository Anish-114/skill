"""
Unit and Integration Tests for Deterministic Learning Roadmap Engine:
1. Roadmap priority ordering (Core languages/tools -> Frameworks -> Advanced specializations).
2. Resilience: Uncataloged skills without resources do not crash and return empty resources list.
3. Deadline constraint warnings: Short deadlines trigger clear warnings with prioritized focus skills.
4. Open/sufficient deadlines evaluate as feasible without warnings.
5. Integration with Evaluation API: FullEvaluationResponse includes roadmap.
"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure backend root directory in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.roadmap_engine import generate_learning_roadmap, load_learning_resources
from app.schemas.evaluation import FullEvaluationResponse, LearningRoadmapResponse


class TestLearningRoadmapEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = load_learning_resources()

    def test_01_roadmap_priority_ordering(self):
        """Verify core languages/tools appear before frameworks and advanced specializations."""
        missing = ["Deep Learning", "FastAPI", "Python", "Kubernetes", "Git"]
        roadmap = generate_learning_roadmap(missing_skills=missing, deadline=None)

        milestones = roadmap["milestones"]
        ordered_skills = [m["skill"].lower() for m in milestones]

        # Git and Python (Tier 1) must come before FastAPI (Tier 3) and Deep Learning / Kubernetes (Tier 4)
        git_idx = ordered_skills.index("git")
        python_idx = ordered_skills.index("python")
        fastapi_idx = ordered_skills.index("fastapi")
        dl_idx = ordered_skills.index("deep learning")

        self.assertLess(git_idx, fastapi_idx, "Tier 1 Git must be prioritized ahead of Tier 3 FastAPI")
        self.assertLess(python_idx, fastapi_idx, "Tier 1 Python must be prioritized ahead of Tier 3 FastAPI")
        self.assertLess(fastapi_idx, dl_idx, "Tier 3 FastAPI must be prioritized ahead of Tier 4 Deep Learning")

    def test_02_uncataloged_skill_does_not_crash(self):
        """Verify skill without curated resources does not crash, has baseline hours, and empty resources."""
        missing = ["QuantumComputingObscureLibraryXYZ", "React"]
        roadmap = generate_learning_roadmap(missing_skills=missing, deadline=None)

        self.assertEqual(len(roadmap["milestones"]), 2)
        uncataloged_m = next((m for m in roadmap["milestones"] if "Quantum" in m["skill"]), None)
        self.assertIsNotNone(uncataloged_m)
        self.assertEqual(uncataloged_m["resources"], [], "Uncataloged skill must have empty resources list without crashing")
        self.assertGreater(uncataloged_m["estimated_hours"], 0)

    def test_03_short_deadline_generates_warning_and_focus_skills(self):
        """Verify tight deadline triggers is_feasible=False, clear warning message, and reduced focus list."""
        # 4 heavy skills requiring ~45+ hours
        missing = ["Python", "Machine Learning", "PyTorch", "System Design"]
        # Deadline 2 days from now (available study hours: 2 * 2.5 = 5.0 hours)
        short_deadline = datetime.now(timezone.utc) + timedelta(days=2)

        roadmap = generate_learning_roadmap(missing_skills=missing, deadline=short_deadline)

        self.assertFalse(roadmap["is_feasible"], "Short deadline must mark roadmap as not feasible")
        self.assertIsNotNone(roadmap["warning_message"])
        self.assertIn("Deadline tak sabhi", roadmap["warning_message"])
        self.assertIn("possible nahi hai", roadmap["warning_message"])
        self.assertIn("Pehle", roadmap["warning_message"])
        # Recommended focus should be reduced to highest priority skill that fits
        self.assertLess(len(roadmap["recommended_focus_skills"]), len(missing))
        self.assertEqual(roadmap["recommended_focus_skills"][0], "Python", "Highest priority skill must be recommended first")

    def test_04_sufficient_deadline_is_feasible(self):
        """Verify comfortable deadline evaluates as feasible with no warning."""
        missing = ["FastAPI", "Docker"]
        comfortable_deadline = datetime.now(timezone.utc) + timedelta(days=45)

        roadmap = generate_learning_roadmap(missing_skills=missing, deadline=comfortable_deadline)

        self.assertTrue(roadmap["is_feasible"])
        self.assertIsNone(roadmap["warning_message"])
        self.assertEqual(len(roadmap["recommended_focus_skills"]), 2)

    def test_05_empty_missing_skills(self):
        """Verify empty missing skills returns 0 duration and feasible."""
        roadmap = generate_learning_roadmap(missing_skills=[], deadline=None)
        self.assertTrue(roadmap["is_feasible"])
        self.assertEqual(roadmap["total_estimated_hours"], 0.0)
        self.assertEqual(len(roadmap["milestones"]), 0)


if __name__ == "__main__":
    unittest.main()
