import React, { useState, useEffect, useCallback } from 'react';
import { Navbar, TabType } from './components/Navbar';
import { DashboardView } from './views/DashboardView';
import { ExploreView } from './views/ExploreView';
import { ProfileView } from './views/ProfileView';
import { SavedView } from './views/SavedView';
import { EvaluationModal } from './components/EvaluationModal';
import { AuthModal } from './components/AuthModal';
import {
  StudentProfile,
  Opportunity,
  OpportunityRecommendation,
  SavedOpportunityItem,
  FullEvaluation,
  UserAccount,
} from './types';
import {
  getProfile,
  getRecommendations,
  getOpportunities,
  getSavedOpportunities,
  evaluateOpportunity,
  toggleSaveOpportunity,
  checkHealth,
  getToken,
  logout,
} from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [recommendations, setRecommendations] = useState<OpportunityRecommendation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [savedList, setSavedList] = useState<SavedOpportunityItem[]>([]);
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());

  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(Boolean(getToken()));
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Loading states
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [loadingOpps, setLoadingOpps] = useState(true);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [serverHealthy, setServerHealthy] = useState<boolean | null>(null);

  // Modal evaluation state
  const [selectedEvaluation, setSelectedEvaluation] = useState<FullEvaluation | null>(null);
  const [evaluatingUrl, setEvaluatingUrl] = useState<string | undefined>(undefined);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadInitialData = useCallback(async () => {
    // 1. Check health
    try {
      const health = await checkHealth();
      setServerHealthy(health.status === 'healthy');
    } catch (err) {
      console.warn('Backend server unreachable:', err);
      setServerHealthy(false);
    }

    // 2. Fetch Student Profile
    try {
      setLoadingProfile(true);
      const profData = await getProfile();
      setProfile(profData);
    } catch (err) {
      console.error('Failed to load profile:', err);
      setProfile(null);
    } finally {
      setLoadingProfile(false);
    }

    // 3. Fetch Recommendations
    try {
      setLoadingRecs(true);
      const recsData = await getRecommendations();
      setRecommendations(recsData);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setRecommendations([]);
    } finally {
      setLoadingRecs(false);
    }

    // 4. Fetch Active & Upcoming Opportunities
    try {
      setLoadingOpps(true);
      const oppsData = await getOpportunities({
        is_active: true,
        min_deadline: new Date().toISOString(),
        limit: 100,
      });
      // Sort upcoming events chronologically ascending (earliest upcoming deadline first, rolling/open last)
      const sorted = [...oppsData].sort((a, b) => {
        if (!a.deadline && !b.deadline) return 0;
        if (!a.deadline) return 1;
        if (!b.deadline) return -1;
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      });
      setOpportunities(sorted);
    } catch (err) {
      console.error('Failed to load opportunities:', err);
    } finally {
      setLoadingOpps(false);
    }

    // 5. Fetch Saved Opportunities
    try {
      setLoadingSaved(true);
      const savedData = await getSavedOpportunities();
      setSavedList(savedData);
      setSavedIds(new Set(savedData.map((s) => s.opportunity_id)));
    } catch (err) {
      console.error('Failed to load saved items:', err);
      setSavedList([]);
      setSavedIds(new Set());
    } finally {
      setLoadingSaved(false);
    }
  }, []);

  // Load all initial data on mount
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleAuthSuccess = (newProfile: StudentProfile, _user: UserAccount) => {
    setIsAuthenticated(true);
    setProfile(newProfile);
    // Reload recommendations and saved list for the newly authenticated user
    getRecommendations().then((recs) => setRecommendations(recs));
    getSavedOpportunities().then((saved) => {
      setSavedList(saved);
      setSavedIds(new Set(saved.map((s) => s.opportunity_id)));
    });
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
    // Reload initial data (falls back to demo or clean baseline)
    loadInitialData();
  };

  const handleToggleSave = async (oppId: number) => {
    const isCurrentlySaved = savedIds.has(oppId);
    try {
      // Optimistic UI update
      const nextSavedIds = new Set(savedIds);
      if (isCurrentlySaved) {
        nextSavedIds.delete(oppId);
        setSavedList((prev) => prev.filter((s) => s.opportunity_id !== oppId));
      } else {
        nextSavedIds.add(oppId);
        const opp = opportunities.find((o) => o.id === oppId);
        if (opp) {
          setSavedList((prev) => [
            {
              id: Date.now(),
              user_id: profile?.user_id || 1,
              opportunity_id: oppId,
              status: 'saved',
              saved_at: new Date().toISOString(),
              opportunity: opp,
            },
            ...prev,
          ]);
        }
      }
      setSavedIds(nextSavedIds);

      await toggleSaveOpportunity(oppId, isCurrentlySaved);
    } catch (err) {
      console.error('Failed to toggle save:', err);
      // Revert on error
      const refreshed = await getSavedOpportunities();
      setSavedList(refreshed);
      setSavedIds(new Set(refreshed.map((s) => s.opportunity_id)));
    }
  };

  const handleOpenEvaluationModal = async (oppId: number) => {
    try {
      const opp = opportunities.find((o) => o.id === oppId);
      setEvaluatingUrl(opp?.official_url);
      const report = await evaluateOpportunity(oppId);
      setSelectedEvaluation(report);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Failed to load evaluation report:', err);
    }
  };

  const handleProfileUpdated = (updatedProfile: StudentProfile) => {
    setProfile(updatedProfile);
    // Reload recommendations with fresh profile competencies
    getRecommendations().then((recs) => setRecommendations(recs));
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        savedCount={savedIds.size}
        serverHealthy={serverHealthy}
        studentName={profile?.full_name}
        isAuthenticated={isAuthenticated}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardView
            recommendations={recommendations}
            profile={profile}
            loading={loadingRecs}
            onEvaluate={handleOpenEvaluationModal}
            onToggleSave={handleToggleSave}
            savedIds={savedIds}
          />
        )}

        {activeTab === 'explore' && (
          <ExploreView
            opportunities={opportunities}
            loading={loadingOpps}
            onEvaluate={handleOpenEvaluationModal}
            onToggleSave={handleToggleSave}
            savedIds={savedIds}
          />
        )}

        {activeTab === 'saved' && (
          <SavedView
            savedList={savedList}
            loading={loadingSaved}
            onEvaluate={handleOpenEvaluationModal}
            onRemoveSave={(id) => handleToggleSave(id)}
          />
        )}

        {activeTab === 'profile' && (
          <ProfileView
            profile={profile}
            onProfileUpdated={handleProfileUpdated}
          />
        )}
      </main>

      {/* Pre-Application Intelligence Modal */}
      <EvaluationModal
        isOpen={isModalOpen}
        evaluation={selectedEvaluation}
        onClose={() => setIsModalOpen(false)}
        officialUrl={evaluatingUrl}
      />

      {/* Authentication / Switch User Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        SkillBridge AI Platform • Powered by Neural Embeddings & Deterministic Verification
      </footer>
    </div>
  );
};

export default App;
