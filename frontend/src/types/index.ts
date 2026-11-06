export interface StudentSkillItem {
  skill_id?: number;
  name: string;
  proficiency_level: string; // Beginner | Intermediate | Advanced | Expert
  years_of_experience?: number;
  verified: boolean;
}

export interface StudentProfile {
  id: number;
  user_id: number;
  email?: string;
  full_name?: string;
  phone?: string;
  college_name?: string;
  degree: string;
  branch: string;
  year: number;
  cgpa?: number;
  experience_level: string;
  raw_bio?: string;
  github_url?: string;
  linkedin_url?: string;
  portfolio_url?: string;
  skills: StudentSkillItem[];
  created_at?: string;
  updated_at?: string;
}

export interface Opportunity {
  id: number;
  title: string;
  organizer: string;
  category: string;
  description: string;
  required_skills: string[];
  eligibility_criteria: {
    degrees?: string[];
    branches?: string[];
    allowed_years?: number[];
    min_cgpa?: number;
    team_size?: { min: number; max: number };
    requires_female_member?: boolean;
    allowed_countries?: string[];
    notes?: string;
    [key: string]: any;
  };
  deadline?: string | null;
  start_date?: string | null;
  mode: string; // Online | Hybrid | In-Person
  location?: string;
  official_url: string;
  source: string;
  prize_pool?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  is_saved?: boolean;
  saved_status?: string;
  saved_notes?: string;
}

export interface RecommendationScoreBreakdown {
  skill_match: number;
  interest_match: number;
  experience_match: number;
  mode_match: number;
  eligibility_confidence: number;
}

export interface OpportunityRecommendation {
  opportunity: Opportunity;
  final_score: number;
  breakdown: RecommendationScoreBreakdown;
  explanation: string;
  eligibility_status: 'ELIGIBLE' | 'NEEDS_VERIFICATION' | 'NOT_ELIGIBLE';
  matched_skills: string[];
  missing_skills: string[];
  readiness_score: number;
}

export interface EligibilityCheckResult {
  status: 'ELIGIBLE' | 'NEEDS_VERIFICATION' | 'NOT_ELIGIBLE';
  reasons: string[];
  passed_checks: string[];
  failed_checks: string[];
  missing_data_checks: string[];
}

export interface SkillGapAnalysis {
  matched_skills: string[];
  missing_skills: string[];
  readiness_score: number;
  preparation_checklist: string[];
}

export interface FullEvaluation {
  opportunity_id: number;
  opportunity_title: string;
  eligibility: EligibilityCheckResult;
  skill_gap: SkillGapAnalysis;
  recommendation: {
    final_score: number;
    breakdown: RecommendationScoreBreakdown;
    explanation: string;
  };
}

export interface SavedOpportunityItem {
  id: number;
  user_id: number;
  opportunity_id: number;
  status: string;
  notes?: string;
  saved_at: string;
  opportunity: Opportunity;
}

export interface SkillTaxonomyItem {
  id: number;
  name: string;
  category?: string;
}

export interface SkillParseResponse {
  extracted_skills: string[];
  matched_taxonomy_skills: Array<{ id: number; name: string; category?: string }>;
  unmatched_tokens: string[];
}

export interface UserAccount {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at?: string;
  profile?: StudentProfile;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserAccount;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  degree?: string;
  branch?: string;
  year?: number;
  college_name?: string;
  experience_level?: string;
}
