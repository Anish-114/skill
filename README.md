---
title: SkillBridge AI
emoji: 🎯
colorFrom: indigo
colorTo: green
sdk: gradio
app_file: app.py
---

# SkillBridge AI — Full-Stack Platform

> **Intelligent, AI-Powered Career & Hackathon Matcher for College Students**  
> Bridging university students to national hackathons (Smart India Hackathon, Google Solution Challenge, MyGov, Unstop) through semantic neural matching, deterministic eligibility verification, and actionable skill gap checklists.

---

## System Architecture

```
skillbridge/
├── Dockerfile                     # Multi-stage production container for Hugging Face Spaces
├── backend/                       # Python 3.11 + FastAPI + SQLAlchemy + SentenceTransformers
│   ├── app/
│   │   ├── api/v1/                # REST Controllers (profiles, opportunities, recommendations, evaluation, saved)
│   │   ├── core/                  # Security & Pydantic BaseSettings
│   │   ├── db/                    # SessionLocal & verified seed datasets
│   │   ├── models/                # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/               # Pydantic v2 validation contracts
│   │   └── services/              # VectorMatcher, EligibilityEngine, SkillGapEngine, RecommendationEngine
│   ├── tests/                     # Automated integration & unit test suites (100% pass rate)
│   └── requirements.txt
└── frontend/                      # React 18 + TypeScript + Vite + Tailwind CSS
    ├── src/
    │   ├── api/client.ts          # Typed Axios client (supports relative /api/v1)
    │   ├── components/            # Navbar, OpportunityCard, EvaluationModal
    │   ├── views/                 # DashboardView, ExploreView, ProfileView, SavedView
    │   └── types/                 # TypeScript interfaces
    ├── tailwind.config.js         # Dark-slate & AI neon theme tokens
    └── package.json
```

---

## 4-Phase Delivery Breakdown

- **Phase 1 (Data Foundation):** SQLAlchemy 2.0 models (`User`, `StudentProfile`, `Skill`, `StudentSkill`, `Opportunity`, `SavedOpportunity`), 10 verified opportunities seeded (SIH 2026, Google, Flipkart GRiD, ISRO, Amazon ML, etc.), and startup lifespan initialization.
- **Phase 2 (Core AI & Rules Engines):**
  - `VectorMatcher`: `sentence-transformers/all-MiniLM-L6-v2` dense cosine similarity with Scikit-Learn TF-IDF fallback.
  - `EligibilityEngine`: Deterministic academic year, degree, branch, and CGPA rule verification (`ELIGIBLE`, `NEEDS_VERIFICATION`, `NOT_ELIGIBLE`).
  - `SkillGapEngine`: Canonical synonym resolution and actionable preparation checklist generator.
  - `RecommendationEngine`: 5-factor hybrid scoring ($0.35 \times \text{Skill} + 0.25 \times \text{Interest} + 0.15 \times \text{Experience} + 0.10 \times \text{Mode} + 0.15 \times \text{Eligibility}$) with a 50% penalty cap for ineligible candidates.
- **Phase 3 (REST API Controllers & Schemas):** Complete `/api/v1` routes for student profiles, NLP bio parsing, catalog search & filtering, AI ranked recommendations, and pre-application evaluation.
- **Phase 4 (Modern React Frontend):** Sleek, dark-slate UI with live recommendation cards, tri-state eligibility badges, interactive 5-factor pre-application intelligence modal, NLP bio skill extraction, and application bookmarking.

---

## Deployment to Hugging Face Spaces

1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Set Space SDK to **Docker** (Blank).
3. Push or upload this repository.
4. Hugging Face Spaces will automatically build the multi-stage Docker image, pre-cache the sentence transformers neural weights, pre-seed the database, and serve the application on port **`7860`**!

---

## Local Development

### 1. Run Backend Server
```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Backend Health Check: `http://localhost:8000/health`

### 2. Run Frontend Web App
```powershell
cd frontend
npm run dev
```
- Open Web Application: `http://localhost:5173`

### 3. Run Backend Test Suites
```powershell
cd backend
.venv\Scripts\activate
python -m tests.test_ai_services
python -m tests.test_api_v1_endpoints
python -m tests.test_db_and_models
python -m tests.test_api
```
