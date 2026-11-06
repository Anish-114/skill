import React, { useState } from 'react';
import { Bookmark, ExternalLink, Trash2, Zap, Calendar, Building2, Globe } from 'lucide-react';
import { SavedOpportunityItem } from '../types';
import { cn } from '../utils/cn';

interface SavedViewProps {
  savedList: SavedOpportunityItem[];
  loading: boolean;
  onEvaluate: (oppId: number) => void;
  onRemoveSave: (oppId: number) => void;
}

export const SavedView: React.FC<SavedViewProps> = ({
  savedList,
  loading,
  onEvaluate,
  onRemoveSave,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  const statuses = ['all', 'saved', 'applied', 'in_progress'];

  const filtered = savedList.filter((item) => {
    if (selectedStatus === 'all') return true;
    return item.status.toLowerCase() === selectedStatus.toLowerCase();
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Bookmark className="w-6 h-6 text-brand-400 fill-brand-400" />
            Bookmarked Opportunities
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Track and monitor competitions you are preparing to compete in.
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex flex-wrap items-center gap-1.5 p-1.5 rounded-xl glass-panel bg-slate-900/60">
          {statuses.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedStatus(s)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all',
                selectedStatus === s
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              {s === 'in_progress' ? 'In Progress' : s}
            </button>
          ))}
        </div>
      </div>

      {/* Bookmarks Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-5 h-60 animate-pulse" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((item) => {
            const opp = item.opportunity;
            const deadlineDate = opp.deadline ? new Date(opp.deadline) : null;
            const now = new Date();
            const diffDays = deadlineDate
              ? Math.ceil((deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
              : null;

            return (
              <div
                key={item.id}
                className="glass-card rounded-2xl p-5 flex flex-col justify-between border border-slate-800"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-brand-500/10 text-brand-300 border border-brand-500/20">
                      {opp.category}
                    </span>

                    <span className="text-[11px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                      {item.status}
                    </span>
                  </div>

                  <h3 className="font-semibold text-lg text-white mb-1 line-clamp-2">
                    {opp.title}
                  </h3>

                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-3">
                    <Building2 className="w-3.5 h-3.5 text-slate-500" />
                    <span className="truncate">{opp.organizer}</span>
                  </div>

                  {item.notes && (
                    <div className="p-2.5 rounded-xl bg-slate-900 text-xs text-slate-300 italic mb-4 border border-slate-800/80">
                      "{item.notes}"
                    </div>
                  )}

                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {(opp.required_skills || []).slice(0, 4).map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>{diffDays === null ? 'Open / Ongoing' : diffDays > 0 ? `${diffDays}d left` : 'Expired'}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => onEvaluate(opp.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-sm"
                    >
                      <Zap className="w-3 h-3" />
                      <span>Report</span>
                    </button>

                    <button
                      onClick={() => onRemoveSave(opp.id)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors border border-slate-700"
                      title="Remove bookmark"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>

                    <a
                      href={opp.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center rounded-3xl glass-panel bg-slate-900/30">
          <Bookmark className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white mb-1">No Bookmarked Opportunities</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Browse the AI Recommendations or Explore catalog to bookmark events you want to prepare for.
          </p>
        </div>
      )}
    </div>
  );
};
