import axios from 'axios';
import {
  StudentProfile,
  Opportunity,
  OpportunityRecommendation,
  FullEvaluation,
  SavedOpportunityItem,
  SkillParseResponse,
  SkillTaxonomyItem,
  StudentSkillItem,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Health check
export const checkHealth = async (): Promise<{ status: string; database: string; stats: any }> => {
  const healthUrl = API_BASE.startsWith('http')
    ? API_BASE.replace('/api/v1', '') + '/health'
    : '/health';
  const response = await axios.get(healthUrl, { timeout: 5000 });
  return response.data;
};

// Profile APIs
export const getProfile = async (): Promise<StudentProfile> => {
  const response = await apiClient.get<StudentProfile>('/profiles/me');
  return response.data;
};

export const updateProfile = async (data: Partial<StudentProfile>): Promise<StudentProfile> => {
  const response = await apiClient.put<StudentProfile>('/profiles/me', data);
  return response.data;
};

export const addOrUpdateSkill = async (skill: StudentSkillItem): Promise<StudentSkillItem> => {
  const response = await apiClient.post<StudentSkillItem>('/profiles/me/skills', skill);
  return response.data;
};

export const deleteSkill = async (skillId: number): Promise<{ message: string; skill_id: number }> => {
  const response = await apiClient.delete(`/profiles/me/skills/${skillId}`);
  return response.data;
};

export const parseBio = async (raw_bio?: string): Promise<SkillParseResponse> => {
  const response = await apiClient.post<SkillParseResponse>('/profiles/me/parse-bio', { raw_bio });
  return response.data;
};

// Opportunities APIs
export interface OpportunityQueryParams {
  category?: string;
  mode?: string;
  search?: string;
  min_deadline?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

export const getOpportunities = async (params?: OpportunityQueryParams): Promise<Opportunity[]> => {
  const response = await apiClient.get<Opportunity[]>('/opportunities', { params });
  return response.data;
};

export const getOpportunityDetail = async (id: number): Promise<Opportunity> => {
  const response = await apiClient.get<Opportunity>(`/opportunities/${id}`);
  return response.data;
};

// Recommendations APIs
export interface RecommendationQueryParams {
  min_score?: number;
  category?: string;
  limit?: number;
}

export const getRecommendations = async (
  params?: RecommendationQueryParams
): Promise<OpportunityRecommendation[]> => {
  const response = await apiClient.get<OpportunityRecommendation[]>('/recommendations', { params });
  return response.data;
};

// Evaluation Modal API
export const evaluateOpportunity = async (oppId: number): Promise<FullEvaluation> => {
  const response = await apiClient.get<FullEvaluation>(`/opportunities/${oppId}/evaluate`);
  return response.data;
};

// Saved Opportunities APIs
export const getSavedOpportunities = async (status?: string): Promise<SavedOpportunityItem[]> => {
  const response = await apiClient.get<SavedOpportunityItem[]>('/saved-opportunities', {
    params: status ? { status } : undefined,
  });
  return response.data;
};

export const saveOpportunity = async (
  oppId: number,
  status: string = 'saved',
  notes?: string
): Promise<SavedOpportunityItem> => {
  const response = await apiClient.post<SavedOpportunityItem>(`/saved-opportunities/${oppId}`, {
    status,
    notes,
  });
  return response.data;
};

export const unsaveOpportunity = async (oppId: number): Promise<{ message: string; opportunity_id: number }> => {
  const response = await apiClient.delete(`/saved-opportunities/${oppId}`);
  return response.data;
};

export const toggleSaveOpportunity = async (
  oppId: number,
  isCurrentlySaved: boolean
): Promise<boolean> => {
  if (isCurrentlySaved) {
    await unsaveOpportunity(oppId);
    return false;
  } else {
    await saveOpportunity(oppId, 'saved');
    return true;
  }
};

// Skills Taxonomy
export const getSkillsTaxonomy = async (category?: string, search?: string): Promise<SkillTaxonomyItem[]> => {
  const response = await apiClient.get<SkillTaxonomyItem[]>('/skills', {
    params: { category, search },
  });
  return response.data;
};
