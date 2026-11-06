import React, { useState } from 'react';
import {
  Sparkles,
  SlidersHorizontal,
  Flame,
  Award,
  BookOpen,
  Filter,
  CheckCircle,
} from 'lucide-react';
import { OpportunityRecommendation, StudentProfile } from '../types';
import { OpportunityCard } from '../components/OpportunityCard';
import { cn } from '../utils/cn';

interface DashboardViewProps {
  recommendations: OpportunityRecommendation[];
  profile: StudentProfile | null;
  loading: boolean;
  onEvaluate: (oppId: number) => void;
  onToggleSave: (oppId: number) => void;
  savedIds: Set<number>;
  getSavedStatus?: (oppId: number) => string | undefined;
  onMarkApplied?: (oppId: number) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  recommendations,
  profile,
  loading,
  onEvaluate,
  onToggleSave,
  savedIds,
  getSavedStatus,
  onMarkApplied,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [minScore, setMinScore] = useState<number>(40);

  const categories = ['all', 'Hackathon', 'Skill Competition', 'Coding Contest', 'Hiring Challenge'];

  // Filter recommendations
  const filtered = recommendations.filter((r) => {
    const normalizedOppCat = r.opportunity.category.toLowerCase().replace(/[\s_-]+/g, '');
    const normalizedSelectedCat = selectedCategory.toLowerCase().replace(/[\s_-]+/g, '');
    const matchesCat =
      selectedCategory === 'all' ||
      normalizedOppCat.includes(normalizedSelectedCat) ||
      normalizedSelectedCat.includes(normalizedOppCat);
    const matchesScore = r.final_score >= minScore;
    return matchesCat && matchesScore;
  });

  const topMatch = recommendations.length > 0 ? recommendations[0] : null;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/15 text-brand-300 border border-brand-500/25 mb-3">
            <Sparkles className="w-3.5 h-3.5 animate-spin" />
            AI Matched For You
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight mb-2">
            Welcome back, {profile?.full_name?.split(' ')[0] || 'Innovator'}!
          </h1>
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed mb-6">
            We analyzed your profile ({profile?.degree || 'B.Tech'} {profile?.branch || 'CSE'}, Year {profile?.year || '3'})
            and ranked competitions, hackathons, and challenges matching your verified skill readiness.
          </p>

          {/* Metric Highlights Pill Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-medium block">Ranked Matches</span>
              <span className="text-xl font-bold text-white">{recommendations.length}</span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-medium block">Top Match Score</span>
              <span className="text-xl font-bold text-emerald-400">
                {topMatch ? `${topMatch.final_score.toFixed(0)}%` : '--'}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-medium block">Verified Skills</span>
              <span className="text-xl font-bold text-indigo-400">
                {profile?.skills?.length || 0}
              </span>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-medium block">Bookmarked</span>
              <span className="text-xl font-bold text-amber-400">{savedIds.size}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl glass-panel bg-slate-900/50">
        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                'px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all',
                selectedCategory === cat
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800'
              )}
            >
              {cat === 'all' ? 'All Recommendations' : cat}
            </button>
          ))}
        </div>

        {/* Min Score Slider */}
        <div className="flex items-center gap-3">
          <SlidersHorizontal className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <span className="text-xs text-slate-300 font-medium whitespace-nowrap">
            Min Score: <span className="font-bold text-brand-400">{minScore}%</span>
          </span>
          <input
            type="range"
            min="0"
            max="80"
            step="5"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-28 sm:w-36 accent-brand-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Recommendations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="glass-card rounded-2xl p-5 h-72 animate-pulse flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="h-4 bg-slate-800 rounded w-1/3" />
                <div className="h-6 bg-slate-800 rounded w-4/5" />
                <div className="h-3 bg-slate-800 rounded w-1/2" />
                <div className="h-14 bg-slate-800 rounded" />
              </div>
              <div className="h-8 bg-slate-800 rounded" />
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((rec) => (
            <OpportunityCard
              key={rec.opportunity.id}
              recommendation={rec}
              opportunity={rec.opportunity}
              onEvaluate={onEvaluate}
              onToggleSave={onToggleSave}
              isSaved={savedIds.has(rec.opportunity.id)}
              savedStatus={getSavedStatus?.(rec.opportunity.id)}
              onMarkApplied={onMarkApplied}
            />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900/30">
          <Flame className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">No Opportunities Match Your Filters</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            Try adjusting your minimum recommendation score slider or select "All Recommendations".
          </p>
          <button
            onClick={() => {
              setSelectedCategory('all');
              setMinScore(0);
            }}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white"
          >
            Reset All Filters
          </button>
        </div>
      )}
    </div>
  );
};
