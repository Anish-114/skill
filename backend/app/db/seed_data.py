from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

# Realistic standardized skills taxonomy across modern software domains
SAMPLE_SKILLS = [
    # Programming Languages
    {"name": "Python", "category": "Programming Languages"},
    {"name": "Java", "category": "Programming Languages"},
    {"name": "C++", "category": "Programming Languages"},
    {"name": "TypeScript", "category": "Programming Languages"},
    {"name": "JavaScript", "category": "Programming Languages"},
    {"name": "Go", "category": "Programming Languages"},
    {"name": "Rust", "category": "Programming Languages"},
    {"name": "SQL", "category": "Programming Languages"},
    
    # Web & Backend Frameworks
    {"name": "FastAPI", "category": "Backend Frameworks"},
    {"name": "Django", "category": "Backend Frameworks"},
    {"name": "Node.js", "category": "Backend Frameworks"},
    {"name": "Express.js", "category": "Backend Frameworks"},
    {"name": "Spring Boot", "category": "Backend Frameworks"},
    {"name": "React", "category": "Frontend Frameworks"},
    {"name": "Next.js", "category": "Frontend Frameworks"},
    {"name": "Flutter", "category": "Mobile Development"},
    {"name": "Android", "category": "Mobile Development"},
    
    # AI / ML & Data Science
    {"name": "Machine Learning", "category": "AI/ML"},
    {"name": "Deep Learning", "category": "AI/ML"},
    {"name": "Natural Language Processing (NLP)", "category": "AI/ML"},
    {"name": "Computer Vision", "category": "AI/ML"},
    {"name": "PyTorch", "category": "AI/ML"},
    {"name": "TensorFlow", "category": "AI/ML"},
    {"name": "Scikit-Learn", "category": "AI/ML"},
    {"name": "Transformers", "category": "AI/ML"},
    {"name": "OpenAI API", "category": "AI/ML"},
    
    # Cloud, DevOps & Databases
    {"name": "Docker", "category": "DevOps & Cloud"},
    {"name": "Kubernetes", "category": "DevOps & Cloud"},
    {"name": "AWS", "category": "DevOps & Cloud"},
    {"name": "Google Cloud Platform", "category": "DevOps & Cloud"},
    {"name": "Azure", "category": "DevOps & Cloud"},
    {"name": "PostgreSQL", "category": "Databases"},
    {"name": "MongoDB", "category": "Databases"},
    {"name": "Redis", "category": "Databases"},
    
    # Core Engineering & Systems
    {"name": "Data Structures & Algorithms", "category": "Core CS"},
    {"name": "System Design", "category": "Core CS"},
    {"name": "Computer Networks", "category": "Core CS"},
    {"name": "Cybersecurity", "category": "Cybersecurity"},
    {"name": "Blockchain", "category": "Web3 & Blockchain"},
    {"name": "Git", "category": "Tools & Version Control"},
]

def get_future_date(days_from_now: int) -> datetime:
    """Helper to generate consistent deadlines in UTC."""
    return datetime.now(timezone.utc) + timedelta(days=days_from_now)

# 10 Detailed and realistic sample opportunities
SAMPLE_OPPORTUNITIES: List[Dict[str, Any]] = [
    {
        "title": "Smart India Hackathon (SIH 2026) - Software Edition",
        "organizer": "Ministry of Education's Innovation Cell (MIC) & AICTE",
        "category": "Hackathon",
        "description": "A premier nationwide platform providing students with the opportunity to solve pressing real-world problems faced by ministries, public sector undertakings, and industry partners. Problem statements span Smart Education, Healthcare, Disaster Management, Agriculture, and Cyber Security.",
        "required_skills": [
            "Python",
            "React",
            "FastAPI",
            "Docker",
            "Machine Learning",
            "PostgreSQL",
            "REST APIs"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "MCA", "BCA", "B.Sc (CS)"],
            "branches": [
                "Computer Science & Engineering",
                "Information Technology",
                "Electronics & Communication",
                "Data Science",
                "All Engineering Branches"
            ],
            "allowed_years": [1, 2, 3, 4, 5],
            "min_cgpa": 6.0,
            "team_size": {"min": 6, "max": 6},
            "requires_female_member": True,
            "allowed_countries": ["India"],
            "institution_types": ["AICTE / UGC / State Govt approved institutions"],
            "notes": "Every team must have exactly 6 members from the same college with at least one female team member."
        },
        "deadline": get_future_date(28),
        "mode": "Hybrid",
        "location": "Multiple Nodal Centers across India / Remote Preliminary",
        "official_url": "https://sih.gov.in",
        "source": "Smart India Hackathon",
        "prize_pool": "₹1,00,000 per problem statement (over 150+ winners nationwide)",
        "is_active": True
    },
    {
        "title": "Google Solution Challenge 2026",
        "organizer": "Google Developer Student Clubs (GDSC)",
        "category": "Hackathon",
        "description": "Annual global contest inviting university and college students to build innovative technological solutions that address one or more of the 17 United Nations Sustainable Development Goals using Google developer platforms.",
        "required_skills": [
            "Flutter",
            "Firebase",
            "TensorFlow",
            "Google Cloud Platform",
            "Android",
            "Python",
            "Web Development"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc", "M.Sc", "M.Tech"],
            "branches": ["All Branches"],
            "allowed_years": [1, 2, 3, 4, 5],
            "min_cgpa": 0.0,
            "team_size": {"min": 1, "max": 4},
            "requires_female_member": False,
            "allowed_countries": ["Global"],
            "institution_types": ["Any accredited college or university"],
            "notes": "At least one team member must be an active member of a recognized Google Developer Student Club chapter."
        },
        "deadline": get_future_date(45),
        "mode": "Online",
        "location": "Global / Remote",
        "official_url": "https://developers.google.com/community/gdsc-solution-challenge",
        "source": "Google Developers",
        "prize_pool": "$12,000 USD for Top 3 Winners + 1:1 Google Engineering Mentorship",
        "is_active": True
    },
    {
        "title": "MyGov AI for Agriculture & Rural Resiliency Hackathon",
        "organizer": "Ministry of Agriculture & Farmers Welfare, Govt of India",
        "category": "Hackathon",
        "description": "Develop computer vision, satellite remote sensing, and lightweight predictive AI models to detect early pest infestations, automate localized crop disease diagnostics, and empower smallholder farmers in vernacular languages.",
        "required_skills": [
            "Python",
            "PyTorch",
            "Computer Vision",
            "Natural Language Processing (NLP)",
            "FastAPI",
            "Scikit-Learn"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "MCA", "M.Sc"],
            "branches": [
                "Computer Science",
                "Artificial Intelligence",
                "Data Science",
                "Agricultural Engineering",
                "Information Technology"
            ],
            "allowed_years": [2, 3, 4],
            "min_cgpa": 6.5,
            "team_size": {"min": 2, "max": 4},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["UGC / AICTE Recognized Universities"],
            "notes": "Participants must build functional prototypes using open government datasets available on data.gov.in."
        },
        "deadline": get_future_date(21),
        "mode": "Online",
        "location": "New Delhi / Remote Evaluation",
        "official_url": "https://innovateindia.mygov.in/ai-agriculture-hackathon/",
        "source": "MyGov",
        "prize_pool": "₹5,00,000 (1st: ₹2,50,000, 2nd: ₹1,50,000, 3rd: ₹1,00,000)",
        "is_active": True
    },
    {
        "title": "Flipkart GRiD 6.0 - Software Development Track",
        "organizer": "Flipkart",
        "category": "Coding Contest",
        "description": "Flipkart's flagship campus engineering competition designed to test algorithmic problem solving, distributed architecture design, and low-latency system scalability under peak festive commerce loads.",
        "required_skills": [
            "Java",
            "C++",
            "Data Structures & Algorithms",
            "System Design",
            "SQL",
            "Computer Networks"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "Dual Degree"],
            "branches": [
                "Computer Science",
                "Information Technology",
                "Electrical Engineering",
                "Electronics & Communication"
            ],
            "allowed_years": [2, 3, 4],
            "min_cgpa": 7.0,
            "team_size": {"min": 1, "max": 3},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["All premier engineering colleges in India"],
            "notes": "Batch of 2025, 2026, 2027, and 2028 engineering students."
        },
        "deadline": get_future_date(14),
        "mode": "Online",
        "location": "Remote",
        "official_url": "https://unstop.com/competitions/flipkart-grid-60-software-development-track",
        "source": "Unstop",
        "prize_pool": "₹5,25,000 + Pre-Placement Interviews (PPIs) for SDE-1 / SDE Intern Roles",
        "is_active": True
    },
    {
        "title": "Tata Crucible Campus Hackathon 2026",
        "organizer": "Tata Sons & Tata Group",
        "category": "Hackathon",
        "description": "Ideate and build technological solutions addressing decarbonization, renewable energy distribution, smart industrial IoT, and customer experience across major Tata Group companies.",
        "required_skills": [
            "Python",
            "Node.js",
            "React",
            "Docker",
            "Machine Learning",
            "PostgreSQL"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "MBA Tech"],
            "branches": ["All Engineering & Technical Disciplines"],
            "allowed_years": [2, 3, 4],
            "min_cgpa": 6.5,
            "team_size": {"min": 2, "max": 5},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["Accredited Higher Education Institutes"],
            "notes": "Teams must submit an executive summary and GitHub repo demonstrating working architecture."
        },
        "deadline": get_future_date(35),
        "mode": "Hybrid",
        "location": "Mumbai / Online Round 1",
        "official_url": "https://unstop.com/competitions/tata-crucible-campus-hackathon-2026",
        "source": "Unstop",
        "prize_pool": "₹3,50,000 + Fast-track internships within Tata digital innovation labs",
        "is_active": True
    },
    {
        "title": "Microsoft Imagine Cup 2026",
        "organizer": "Microsoft Corporation",
        "category": "Hackathon",
        "description": "Global competition challenging student developers to bring visionary tech startups to life with Microsoft Azure Cloud, OpenAI service, and enterprise developer tools.",
        "required_skills": [
            "Azure",
            "OpenAI API",
            "Python",
            "TypeScript",
            "React",
            "Docker"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc", "M.Tech", "M.S."],
            "branches": ["All Branches"],
            "allowed_years": [1, 2, 3, 4, 5],
            "min_cgpa": 0.0,
            "team_size": {"min": 1, "max": 4},
            "requires_female_member": False,
            "allowed_countries": ["Global"],
            "institution_types": ["Accredited high schools, colleges, and universities"],
            "notes": "Participants must be at least 16 years of age and currently enrolled students."
        },
        "deadline": get_future_date(60),
        "mode": "Online",
        "location": "Global Remote / World Finals in Seattle, WA",
        "official_url": "https://imaginecup.microsoft.com/",
        "source": "Microsoft",
        "prize_pool": "$100,000 USD + Mentorship from Satya Nadella",
        "is_active": True
    },
    {
        "title": "ISRO Bharatiya Antariksh Hackathon 2026",
        "organizer": "Indian Space Research Organisation (ISRO) & NRSC",
        "category": "Hackathon",
        "description": "Tackle mission-critical challenges in space tech, including automated satellite imagery segmentation, high-resolution Earth observation analysis, and orbit prediction using raw ISRO payload telemetry.",
        "required_skills": [
            "Python",
            "Computer Vision",
            "Deep Learning",
            "PyTorch",
            "Docker",
            "Scikit-Learn"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "M.Sc (Physics/CS/Geoinformatics)"],
            "branches": [
                "Computer Science",
                "Aerospace Engineering",
                "Electronics & Communication",
                "Data Science",
                "Geoinformatics"
            ],
            "allowed_years": [3, 4],
            "min_cgpa": 7.0,
            "team_size": {"min": 3, "max": 4},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["UGC / AICTE / IITs / NITs / IIITs"],
            "notes": "Valid Indian college identification and proof of enrollment required during registration."
        },
        "deadline": get_future_date(25),
        "mode": "Hybrid",
        "location": "ISRO NRSC Hyderabad & Online",
        "official_url": "https://innovateindia.mygov.in/isro-hackathon/",
        "source": "MyGov",
        "prize_pool": "₹4,00,000 + Commendation and visit to Satish Dhawan Space Centre (SDSC) SHAR",
        "is_active": True
    },
    {
        "title": "Amazon ML Challenge 2026",
        "organizer": "Amazon India",
        "category": "Coding Contest",
        "description": "High-stakes machine learning competition evaluating extreme multi-label text and image classification, product entity extraction, and multi-modal embeddings for e-commerce search at billions-scale.",
        "required_skills": [
            "Python",
            "Natural Language Processing (NLP)",
            "PyTorch",
            "Transformers",
            "Scikit-Learn",
            "Deep Learning"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "Dual Degree", "PhD"],
            "branches": [
                "Computer Science",
                "Data Science",
                "Information Technology",
                "Mathematics & Computing"
            ],
            "allowed_years": [3, 4],
            "min_cgpa": 7.5,
            "team_size": {"min": 2, "max": 4},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["All recognized Indian Engineering Colleges"],
            "notes": "Exclusively for 3rd and 4th year engineering students graduating in 2026 or 2027."
        },
        "deadline": get_future_date(18),
        "mode": "Online",
        "location": "Remote",
        "official_url": "https://unstop.com/competitions/amazon-ml-challenge-2026",
        "source": "Unstop",
        "prize_pool": "₹10,00,000 + Direct interview fast-track for Applied Scientist & ML Interns",
        "is_active": True
    },
    {
        "title": "RBI HaRBInger 2026 - Innovation for Transformation",
        "organizer": "Reserve Bank of India (RBI)",
        "category": "Hackathon",
        "description": "Global regulatory technology hackathon focusing on alternate offline payments for telecom-shadow zones, context-aware cybersecurity defenses for UPI, and real-time AML fraud detection algorithms.",
        "required_skills": [
            "Python",
            "FastAPI",
            "Cybersecurity",
            "Blockchain",
            "Data Structures & Algorithms",
            "SQL"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E.", "M.Tech", "MCA", "M.Sc", "MBA (FinTech)"],
            "branches": ["Computer Science", "Information Security", "FinTech", "All Branches"],
            "allowed_years": [2, 3, 4, 5],
            "min_cgpa": 6.5,
            "team_size": {"min": 1, "max": 5},
            "requires_female_member": False,
            "allowed_countries": ["India", "Global"],
            "institution_types": ["Any accredited college, university or early-stage startup team"],
            "notes": "Must present architectural documentation showcasing transaction throughput and fault tolerance."
        },
        "deadline": get_future_date(40),
        "mode": "Online",
        "location": "Mumbai / Remote",
        "official_url": "https://harbinger.rbi.org.in",
        "source": "MyGov",
        "prize_pool": "₹40,00,000 across multiple prize categories",
        "is_active": True
    },
    {
        "title": "Cisco India Innovation Challenge 2026",
        "organizer": "Cisco Networking Academy & Unstop",
        "category": "Hiring Challenge",
        "description": "Challenge focusing on programmable edge routers, automated Zero-Trust network policy enforcement, network telemetry visualization, and cloud-native packet inspection.",
        "required_skills": [
            "Python",
            "Computer Networks",
            "Cybersecurity",
            "Docker",
            "REST APIs",
            "Linux"
        ],
        "eligibility_criteria": {
            "degrees": ["B.Tech", "B.E."],
            "branches": [
                "Computer Science",
                "Information Technology",
                "Electronics & Telecommunication"
            ],
            "allowed_years": [3, 4],
            "min_cgpa": 7.0,
            "team_size": {"min": 1, "max": 2},
            "requires_female_member": False,
            "allowed_countries": ["India"],
            "institution_types": ["Cisco NetAcad affiliated colleges and accredited Indian institutes"],
            "notes": "Pre-final and final year undergraduate students eligible for hiring shortlist."
        },
        "deadline": get_future_date(22),
        "mode": "Online",
        "location": "Remote",
        "official_url": "https://unstop.com/competitions/cisco-india-innovation-challenge",
        "source": "Unstop",
        "prize_pool": "₹4,50,000 + Cisco certification sponsorship vouchers & PPIs",
        "is_active": True
    }
]

# Sample student profiles for demonstration and local testing
SAMPLE_USERS = [
    {
        "email": "student@skillbridge.ai",
        "full_name": "Aarav Sharma",
        "password": "Password@123",  # Will be hashed
        "is_active": True,
        "is_superuser": False,
        "profile": {
            "phone": "+91 9876543210",
            "college_name": "Indian Institute of Information Technology",
            "degree": "B.Tech",
            "branch": "Computer Science & Engineering",
            "year": 3,
            "cgpa": 8.75,
            "experience_level": "Intermediate",
            "raw_bio": "Pre-final year Computer Science undergraduate passionate about building distributed backend systems, RESTful microservices, and practical machine learning solutions. Winner of 2 collegiate hackathons and active open-source contributor.",
            "github_url": "https://github.com/aaravsharma-dev",
            "linkedin_url": "https://linkedin.com/in/aarav-sharma-tech",
            "portfolio_url": "https://aaravsharma.dev",
            "skills": [
                {"name": "Python", "proficiency_level": "Advanced", "years_of_experience": 2.5, "verified": True},
                {"name": "FastAPI", "proficiency_level": "Intermediate", "years_of_experience": 1.5, "verified": True},
                {"name": "Docker", "proficiency_level": "Intermediate", "years_of_experience": 1.0, "verified": False},
                {"name": "PostgreSQL", "proficiency_level": "Intermediate", "years_of_experience": 2.0, "verified": True},
                {"name": "Machine Learning", "proficiency_level": "Intermediate", "years_of_experience": 1.5, "verified": True},
                {"name": "PyTorch", "proficiency_level": "Beginner", "years_of_experience": 0.8, "verified": False},
                {"name": "React", "proficiency_level": "Intermediate", "years_of_experience": 1.2, "verified": False},
                {"name": "Data Structures & Algorithms", "proficiency_level": "Advanced", "years_of_experience": 2.5, "verified": True},
            ]
        }
    }
]
