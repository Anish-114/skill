# SkillBridge AI - Backend

The backend engine for **SkillBridge AI**, an intelligent career and competition discovery platform designed to match college students to hackathons, coding contests, hiring challenges, and grants based on their degree, academic year, and skill proficiencies.

---

## Architecture Overview

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py           # User & StudentProfile authentication dependencies
│   │   └── v1/               # Version 1 REST controllers
│   │       ├── profiles.py   # Student profile & NLP bio skill parsing
│   │       ├── opportunities.py # Search, filtering & detail view
│   │       ├── recommendations.py # AI hybrid ranking controller
│   │       ├── evaluation.py # Modal evaluation (eligibility + skill gap)
│   │       ├── saved.py      # Bookmarks & application tracker
│   │       └── skills.py     # Taxonomy lookup
│   ├── core/
│   │   ├── config.py         # Application configuration & Pydantic settings
│   │   └── security.py       # Password hashing & security utilities
│   ├── db/
│   │   ├── init_db.py        # Database schema creation & seed script
│   │   ├── seed_data.py      # Seed datasets (SIH, Google, Unstop, MyGov, etc.)
│   │   └── session.py        # SQLAlchemy session & engine lifecycle
│   ├── models/
│   │   ├── base.py           # DeclarativeBase foundation
│   │   ├── user.py           # User account model
│   │   ├── student_profile.py# Academic & personal details, degree, branch, year, bio
│   │   ├── skill.py          # Standardized Skill & StudentSkill (M:N) models
│   │   ├── opportunity.py    # Opportunity catalogue with JSON eligibility & skills
│   │   └── saved_opportunity.py# Opportunity bookmarking & tracking
│   ├── schemas/              # Pydantic v2 schemas
│   │   ├── student_profile.py# Profile CRUD & Bio Parsing schemas
│   │   ├── opportunity.py    # Opportunity & filtering schemas
│   │   ├── recommendation.py # Recommendation score breakdown schemas
│   │   ├── evaluation.py     # Eligibility & skill gap evaluation schemas
│   │   └── saved_opportunity.py# Saved opportunity schemas
│   ├── services/
│   │   ├── __init__.py       # Services namespace export
│   │   ├── vector_matcher.py # Sentence Transformers embeddings & TF-IDF fallback
│   │   ├── eligibility_engine.py # Deterministic multi-factor eligibility verifier
│   │   ├── skill_gap_engine.py   # Normalized skill overlap, gap & checklist engine
│   │   └── recommendation_engine.py # Weighted hybrid scoring & explanation pipeline
│   └── main.py               # FastAPI application with lifespan auto-initialization
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variables template
```

---

## Data Models Summary

### 1. User & StudentProfile
- **`User`**: Account identity (email, password hash, active status, superuser status).
- **`StudentProfile`**:
  - Personal Details: Phone, College / University, Portfolio & Social URLs.
  - Academic Profile: Degree (e.g., `B.Tech`, `BCA`), Branch (e.g., `Computer Science`), Year of Study (`1` to `5`), CGPA.
  - Experience & Bio: Experience level (`Beginner`, `Intermediate`, `Advanced`), raw natural language bio.

### 2. Skill & StudentSkill (Many-to-Many)
- **`Skill`**: Standardized skill entity with categorizations (`Programming Languages`, `AI/ML`, `DevOps & Cloud`, `Databases`, `Core CS`).
- **`StudentSkill`**: Association object linking students to skills with `proficiency_level`, `years_of_experience`, and `verified` badge.

### 3. Opportunity
- **Fields**: `title`, `organizer`, `category`, `description`, `deadline`, `mode` (`Online`, `Hybrid`, `In-Person`), `location`, `official_url`, `source`, `prize_pool`, `is_active`.
- **`required_skills`**: JSON array of skill names.
- **`eligibility_criteria`**: Rich structured JSON object defining:
  - Allowed degrees (e.g., `["B.Tech", "B.E.", "MCA"]`)
  - Allowed branches (e.g., `["Computer Science", "Information Technology", "ALL"]`)
  - Allowed academic years (e.g., `[2, 3, 4]`)
  - Minimum CGPA cutoff
  - Team size rules (`{"min": 1, "max": 4}`)
  - Diversity criteria (`requires_female_member`)
  - Country and institution restrictions

### 4. SavedOpportunity
- Links `User` and `Opportunity` with application statuses (`saved`, `applied`, `in_progress`, `shortlisted`, `archived`) and personal notes.

---

## Seed Data Included

`seed_data.py` contains 10 verified, production-grade opportunity entries with realistic rules:
1. **Smart India Hackathon (SIH 2026)** - Software Edition (Ministry of Education / AICTE)
2. **Google Solution Challenge 2026** (GDSC / Google)
3. **MyGov AI for Agriculture & Rural Resiliency Hackathon** (Ministry of Agriculture)
4. **Flipkart GRiD 6.0 - Software Development Track** (Flipkart / Unstop)
5. **Tata Crucible Campus Hackathon 2026** (Tata Group / Unstop)
6. **Microsoft Imagine Cup 2026** (Microsoft)
7. **ISRO Bharatiya Antariksh Hackathon 2026** (ISRO / NRSC / MyGov)
8. **Amazon ML Challenge 2026** (Amazon India / Unstop)
9. **RBI HaRBInger 2026 - Innovation for Transformation** (Reserve Bank of India / MyGov)
10. **Cisco India Innovation Challenge 2026** (Cisco / Unstop)

---

## Core AI & Deterministic Services (Phase 2)

### 1. Vector Matcher (`app.services.vector_matcher`)
- **Neural Embeddings:** Employs `sentence-transformers` (`all-MiniLM-L6-v2`) with a singleton pattern and thread-safe memory caching.
- **Normalized Similarity:** Generates unit-normalized dense vectors and computes dot-product cosine similarity, returning a score strictly bounded between `0.0` and `100.0`.
- **Fault-Tolerant Fallbacks:** Features an automated graceful fallback cascade:
  `SentenceTransformer -> Scikit-Learn TF-IDF Cosine -> Jaccard Token Overlap`.

### 2. Eligibility Engine (`app.services.eligibility_engine`)
- **Deterministic Rules Evaluation:** Verifies academic constraints defined in opportunity criteria:
  - `allowed_years`: Checks student's academic year.
  - `branches` & `degrees`: Case-insensitive, punctuation-tolerant, and token-overlap partial matching.
  - `min_cgpa`: Strict numerical threshold evaluation.
  - `min_age` / `max_age`: Age boundary checks.
- **Tri-State Status:**
  - `NOT_ELIGIBLE`: If any mandatory rule explicitly fails.
  - `NEEDS_VERIFICATION`: If required fields (e.g. CGPA or exact year) are missing from profile.
  - `ELIGIBLE`: Only when all specified rules pass.

### 3. Skill Gap Engine (`app.services.skill_gap_engine`)
- **Normalized Canonical Matching:** Maps acronyms and variations to canonical skill representations (e.g., `FastAPI` $\leftrightarrow$ `fastapi`, `NLP` $\leftrightarrow$ `Natural Language Processing (NLP)`, `ReactJS` $\leftrightarrow$ `React`).
- **Readiness Score:** $\frac{\text{matched\_skills}}{\text{total\_required\_skills}} \times 100\%$ (strictly 0.0 to 100.0).
- **Actionable Checklist:** Generates curated, high-yield preparation tips for each missing technical skill.

### 4. Recommendation Engine (`app.services.recommendation_engine`)
- **Weighted Hybrid Formula:**
  $$\text{Final Score} = 0.35 \times \text{Skill} + 0.25 \times \text{Interest} + 0.15 \times \text{Experience} + 0.10 \times \text{Mode} + 0.15 \times \text{Eligibility}$$
- **Penalty Cap:** Opportunities marked `NOT_ELIGIBLE` receive a 50% penalty cap ($\min(\text{score} \times 0.5, 50.0)$) to prevent ineligible events from ranking above viable opportunities.
- **Natural Language Explanation:** Produces an intuitive, personalized rationale detailing strengths and priority areas to study.

---

## REST API Controllers & Endpoints (Phase 3)

All endpoints are mounted under `/api/v1` with CORS enabled for frontend clients (`http://localhost:5173`, `http://127.0.0.1:5173`).

### 1. Profiles API (`/api/v1/profiles`)
- `GET /me`: Fetch the logged-in student's complete academic, personal, and skill profile.
- `PUT /me`: Update profile fields (academics, bio, experience level, social URLs, and optional skills sync).
- `POST /me/skills`: Add a new skill or update proficiency/years of experience.
- `DELETE /me/skills/{skill_id}`: Remove an individual skill.
- `POST /me/parse-bio`: Quick NLP skill extractor that matches unstructured bio text against the database taxonomy.

### 2. Opportunities API (`/api/v1/opportunities`)
- `GET /`: Paginated opportunity catalog supporting `category`, `mode`, `min_deadline`, and `search` query parameters.
- `GET /{id}`: Full opportunity view including bookmark status (`is_saved`).

### 3. AI Recommendations API (`/api/v1/recommendations`)
- `GET /`: Evaluates and ranks all active opportunities using the 5-factor hybrid recommendation formula. Returns sorted list descending by `final_score` with sub-score breakdowns, readiness score, and natural language explanations.
- Query parameters: `min_score` (default `0.0`), `category`, and `limit`.

### 4. Evaluation API (`/api/v1/opportunities/{id}/evaluate`)
- `GET /{id}/evaluate`: Detailed pre-application modal check. Executes deterministic eligibility verification and skill gap analysis, returning passed/failed checks and an actionable study checklist.

### 5. Saved Opportunities API (`/api/v1/saved-opportunities`)
- `GET /`: Retrieve all bookmarked opportunities (filterable by `status`).
- `POST /{opportunity_id}`: Bookmark an opportunity with optional `status` (`saved`, `applied`, `in_progress`) and `notes`.
- `DELETE /{opportunity_id}`: Unbookmark an opportunity.

---

## Testing

Run all unit and integration test suites:
```bash
# Phase 3 REST API Integration Test Suite
python -m tests.test_api_v1_endpoints

# Phase 2 Core Engines Test Suite (13 tests)
python -m tests.test_ai_services

# Phase 1 Model & Database Integration Test Suite
python -m tests.test_db_and_models

# Phase 1 API Handlers Test Suite
python -m tests.test_api
```

---

## Quickstart

### 1. Create Virtual Environment & Install Requirements
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Initialize Database & Seed Opportunities
You can run the initialization directly:
```bash
python -m app.db.init_db
```
*Note: The database tables and seed data are also automatically verified and loaded during application startup via FastAPI's lifespan event handler!*

### 3. Run FastAPI Development Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser to:
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Opportunities API: `http://127.0.0.1:8000/api/v1/opportunities`
