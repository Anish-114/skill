import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Filter, Globe, Sparkles, Calendar, Layers } from 'lucide-react';
import { Opportunity } from '../types';
import { OpportunityCard } from '../components/OpportunityCard';
import { cn } from '../utils/cn';

interface ExploreViewProps {
  opportunities: Opportunity[];
  loading: boolean;
  onEvaluate: (oppId: number) => void;
  onToggleSave: (oppId: number) => void;
  savedIds: Set<number>;
  getSavedStatus?: (oppId: number) => string | undefined;
  onMarkApplied?: (oppId: number) => void;
  onFindTeammates?: (opportunity: Opportunity) => void;
}

export const ExploreView: React.FC<ExploreViewProps> = ({
  opportunities,
  loading,
  onEvaluate,
  onToggleSave,
  savedIds,
  getSavedStatus,
  onMarkApplied,
  onFindTeammates,
}) => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedMode, setSelectedMode] = useState('all');

  const categories = ['all', 'Hackathon', 'Skill Competition', 'Coding Contest', 'Hiring Challenge'];
  const modes = ['all', 'Online', 'Hybrid', 'In-Person'];

  const nowTimestamp = Date.now() - 24 * 3600 * 1000;

  const filtered = opportunities
    .filter((opp) => {
      // Show only active and upcoming events
      const isUpcoming =
        opp.is_active !== false &&
        (!opp.deadline || new Date(opp.deadline).getTime() >= nowTimestamp);
      if (!isUpcoming) return false;

      const matchesSearch =
        searchTerm === '' ||
        opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        opp.organizer.toLowerCase().includes(searchTerm.toLowerCase()) ||
        opp.required_skills.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));

      const normalizedOppCat = opp.category.toLowerCase().replace(/[\s_-]+/g, '');
      const normalizedSelectedCat = selectedCategory.toLowerCase().replace(/[\s_-]+/g, '');
      const matchesCat =
        selectedCategory === 'all' ||
        normalizedOppCat.includes(normalizedSelectedCat) ||
        normalizedSelectedCat.includes(normalizedOppCat);

      const matchesMode =
        selectedMode === 'all' ||
        opp.mode.toLowerCase() === selectedMode.toLowerCase();

      return matchesSearch && matchesCat && matchesMode;
    })
    .sort((a, b) => {
      if (!a.deadline && !b.deadline) return 0;
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Title & Search Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Explore Opportunities Catalog
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse verified national and global hackathons, coding cups, and engineering challenges.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={t('explore.search_placeholder')}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors shadow-inner"
          />
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-2xl glass-panel bg-slate-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Category Selector */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold text-slate-400 mr-1 hidden lg:inline">Category:</span>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setSelectedCategory(c)}
              className={cn(
                'px-3 py-1.5 rounded-xl text-xs font-medium transition-all',
                selectedCategory === c
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800'
              )}
            >
              {c === 'all' ? t('explore.filter_category_all') : c}
            </button>
          ))}
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-slate-400 mr-1 hidden lg:inline">Mode:</span>
          {modes.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedMode(m)}
              className={cn(
                'px-3 py-1.5 rounded-xl text-xs font-medium transition-all',
                selectedMode === m
                  ? 'bg-slate-700 text-white border border-slate-600'
                  : 'text-slate-400 hover:text-white bg-slate-900 border border-slate-800'
              )}
            >
              {m === 'all'
                ? t('explore.filter_mode_all')
                : m === 'Online'
                ? t('common.online')
                : m === 'Hybrid'
                ? t('common.hybrid')
                : t('common.offline')}
            </button>
          ))}
        </div>
      </div>

      {/* Grid count summary */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>{t('explore.summary_count', { count: filtered.length })}</span>
      </div>

      {/* Opportunities Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-5 h-64 animate-pulse" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onEvaluate={onEvaluate}
              onToggleSave={onToggleSave}
              isSaved={savedIds.has(opp.id)}
              savedStatus={getSavedStatus?.(opp.id)}
              onMarkApplied={onMarkApplied}
              onFindTeammates={onFindTeammates}
            />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900/30">
          <Layers className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">{t('explore.empty_title')}</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            {t('explore.empty_subtitle')}
          </p>
          <button
            onClick={() => {
              setSearchTerm('');
              setSelectedCategory('all');
              setSelectedMode('all');
            }}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white"
          >
            {t('explore.clear_filters')}
          </button>
        </div>
      )}
    </div>
  );
};
