# SkillBridge AI — Modern React + TypeScript + Tailwind CSS Frontend

A developer-first, intelligent platform matching college students to hackathons, coding contests, hiring challenges, and grants using semantic embeddings and deterministic eligibility verification.

---

## Architecture Overview

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts            # Axios client & typed endpoint helpers
│   ├── components/
│   │   ├── Navbar.tsx           # Navigation bar with connection health & user pill
│   │   ├── OpportunityCard.tsx  # Dynamic card with match score & eligibility badges
│   │   └── EvaluationModal.tsx  # Pre-application intelligence report modal
│   ├── views/
│   │   ├── DashboardView.tsx    # Top AI ranked matches with min-score filter
│   │   ├── ExploreView.tsx      # Multi-criteria catalog search & filters
│   │   ├── ProfileView.tsx      # Academic profile & NLP Bio skill extractor
│   │   └── SavedView.tsx        # Bookmarks & application tracker
│   ├── types/
│   │   └── index.ts             # Complete TypeScript data model definitions
│   ├── utils/
│   │   └── cn.ts                # Tailwind class utility (clsx + tailwind-merge)
│   ├── App.tsx                  # Master state & view controller
│   ├── main.tsx                 # React DOM mount point
│   └── index.css                # Tailwind directives & dark-slate aesthetic
├── tailwind.config.js           # Slate/zinc, emerald, amber, and violet theme tokens
├── vite.config.ts               # Vite configuration (port 5173)
└── package.json                 # Dependencies (lucide-react, axios, tailwind-merge)
```

---

## Design System & Theme
- **Color Palette:** Dark-slate modern developer aesthetic (`slate-950` background, `slate-900` glassmorphic cards, `slate-800` borders).
- **Accents:**
  - `Indigo` & `Violet`: AI neural matching indicators & primary branding.
  - `Emerald`: `ELIGIBLE` status badge, matched skills, high readiness.
  - `Amber`: `NEEDS VERIFICATION` status, upcoming deadline alerts.
  - `Rose / Red`: `NOT ELIGIBLE` status badge, missing skills.
- **Typography:** `Inter` font paired with `JetBrains Mono` for code and skill chips.

---

## Key Features

1. **AI Recommendations Dashboard:**
   - Displays opportunities ranked in real-time by the 5-factor hybrid scoring algorithm.
   - Interactive minimum match score slider and domain category pills.
   - Metric cards showing active matches, top match score, verified skills, and saved count.

2. **Pre-Application Intelligence Modal (`EvaluationModal`):**
   - 5-factor score breakdown (Skill 35%, Interest 25%, Experience 15%, Mode 10%, Eligibility 15%).
   - Transparent passed/failed criteria checks (academic year, degree, branch, CGPA).
   - Matched vs missing skill gap chips.
   - Actionable preparation checklist tailored for top missing prerequisites.

3. **NLP Skill Extraction from Bio:**
   - On the Profile page, click **"Extract Skills from Bio"** to parse unstructured text against the backend taxonomy.
   - 1-click **"Add All Detected"** to immediately update the student's verified profile.

4. **Explore & Filter Catalog:**
   - Instant search across title, organizer, and required skills.
   - Filter by Mode (`Online`, `Hybrid`, `In-Person`) and Category (`Hackathon`, `Coding Contest`, `Hiring Challenge`).

5. **Saved / Bookmarking System:**
   - Save opportunities with application tracking status (`saved`, `applied`, `in_progress`).

---

## Running Locally

### 1. Start FastAPI Backend (Terminal 1)
```powershell
cd d:\skillbridge\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 2. Start Vite Frontend (Terminal 2)
```powershell
cd d:\skillbridge\frontend
npm run dev
```

Visit **`http://localhost:5173`** in your browser.
