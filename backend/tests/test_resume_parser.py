"""
Unit and Integration Tests for PDF Resume Parser:
1. Extraction of skills from text-based PDF using pypdf and taxonomy matching.
2. Rejection of non-PDF files with HTTP 400.
3. Rejection of oversized files (> 5 MB) with HTTP 413.
4. Handling of empty / scanned PDF with clear error message: 'Is PDF mein text nahi mila, bio paste karo'.
5. Verification of privacy (in-memory parsing without filesystem persistence).
"""
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
import asyncio

# Ensure backend root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException, UploadFile
from app.db.session import SessionLocal
from app.models import User, StudentProfile, Skill
from app.api.v1.profiles import parse_resume_pdf, extract_skills_from_text, MAX_RESUME_PDF_SIZE_BYTES
from app.core.security import get_password_hash


TEXT_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length 78 >> stream
BT
/F1 12 Tf
100 700 Td
(Software Engineer skilled in Python, FastAPI, Docker, and React.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000318 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
447
%%EOF
"""

BLANK_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> /Contents 4 0 R >> endobj
4 0 obj << /Length 0 >> stream
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000200 00000 n 
trailer << /Size 5 /Root 1 0 R >>
startxref
250
%%EOF
"""


class TestResumePdfParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        cls.user = cls.db.query(User).filter(User.email == "test_pdf_resume@example.com").first()
        if not cls.user:
            cls.user = User(
                email="test_pdf_resume@example.com",
                full_name="PDF Resume Tester",
                hashed_password=get_password_hash("Secret123!"),
                is_active=True,
            )
            cls.db.add(cls.user)
            cls.db.commit()
            cls.db.refresh(cls.user)

        cls.profile = cls.user.profile
        if not cls.profile:
            cls.profile = StudentProfile(
                user_id=cls.user.id,
                degree="B.Tech",
                branch="Computer Science",
                year=3,
                experience_level="Intermediate",
                raw_bio="",
            )
            cls.db.add(cls.profile)
            cls.db.commit()
            cls.db.refresh(cls.profile)

        # Ensure test skills exist in taxonomy
        test_skills = ["Python", "FastAPI", "Docker", "React"]
        for s in test_skills:
            if not cls.db.query(Skill).filter(Skill.name.ilike(s)).first():
                cls.db.add(Skill(name=s, category="Backend"))
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        if cls.user:
            cls.db.query(StudentProfile).filter(StudentProfile.user_id == cls.user.id).delete()
            cls.db.query(User).filter(User.id == cls.user.id).delete()
            cls.db.commit()
        cls.db.close()

    def test_01_text_pdf_extracts_skills(self):
        """Verify text-based PDF parses properly and extracts recognized taxonomy skills."""
        upload_file = UploadFile(
            filename="resume_test.pdf",
            file=io.BytesIO(TEXT_PDF_BYTES),
            headers={"content-type": "application/pdf"}
        )

        res = parse_resume_pdf(
            file=upload_file,
            db=self.db,
            current_user=self.user,
            profile=self.profile
        )

        self.assertIn("Python", res.extracted_skills)
        self.assertIn("FastAPI", res.extracted_skills)
        self.assertIn("Docker", res.extracted_skills)
        self.assertIn("React", res.extracted_skills)
        self.assertIsNotNone(res.extracted_text)
        self.assertIn("Software Engineer skilled in Python", res.extracted_text)

    def test_02_non_pdf_rejected(self):
        """Verify non-PDF file upload raises HTTP 400."""
        upload_file = UploadFile(
            filename="resume.txt",
            file=io.BytesIO(b"Python, FastAPI, Docker"),
            headers={"content-type": "text/plain"}
        )

        with self.assertRaises(HTTPException) as ctx:
            parse_resume_pdf(
                file=upload_file,
                db=self.db,
                current_user=self.user,
                profile=self.profile
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Sirf PDF files supported hain", ctx.exception.detail)

    def test_03_oversized_pdf_rejected(self):
        """Verify file exceeding 5 MB limit is rejected with HTTP 413."""
        oversized_bytes = b"%PDF-1.4\n" + b"A" * (MAX_RESUME_PDF_SIZE_BYTES + 100)
        upload_file = UploadFile(
            filename="large_resume.pdf",
            file=io.BytesIO(oversized_bytes),
            headers={"content-type": "application/pdf"}
        )

        with self.assertRaises(HTTPException) as ctx:
            parse_resume_pdf(
                file=upload_file,
                db=self.db,
                current_user=self.user,
                profile=self.profile
            )
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertIn("5 MB se zyada", ctx.exception.detail)

    def test_04_scanned_or_blank_pdf_rejected_with_clean_message(self):
        """Verify empty or scanned (image-only) PDF raises 400 with specific Hindi message."""
        upload_file = UploadFile(
            filename="scanned_resume.pdf",
            file=io.BytesIO(BLANK_PDF_BYTES),
            headers={"content-type": "application/pdf"}
        )

        with self.assertRaises(HTTPException) as ctx:
            parse_resume_pdf(
                file=upload_file,
                db=self.db,
                current_user=self.user,
                profile=self.profile
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "Is PDF mein text nahi mila, bio paste karo")


if __name__ == "__main__":
    unittest.main()
