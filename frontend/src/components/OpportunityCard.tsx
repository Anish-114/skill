import React from 'react';
import {
  Calendar,
  Globe,
  Building2,
  ExternalLink,
  Bookmark,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Zap,
  Award,
  Check,
} from 'lucide-react';
import { Opportunity, OpportunityRecommendation } from '../types';
import { cn } from '../utils/cn';
import { formatToIST, getDeadlineCountdown } from '../utils/date';

interface OpportunityCardProps {
  recommendation?: OpportunityRecommendation;
  opportunity: Opportunity;
  onEvaluate: (oppId: number) => void;
  onToggleSave: (oppId: number) => void;
  isSaved?: boolean;
  savedStatus?: string;
  onMarkApplied?: (oppId: number) => void;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  recommendation,
  opportunity,
  onEvaluate,
  onToggleSave,
  isSaved,
  savedStatus,
  onMarkApplied,
}) => {
  // Format deadline date in IST and calculate countdown
  const { label: countdownLabel, isUrgent } = getDeadlineCountdown(opportunity.deadline);
  const formattedIST = formatToIST(opportunity.deadline);

  const finalScore = recommendation ? recommendation.final_score : null;
  const eligStatus = recommendation
    ? recommendation.eligibility_status
    : null;

  // Determine readiness score
  const readiness = recommendation ? recommendation.readiness_score : null;
  const isApplied = savedStatus?.toLowerCase() === 'applied';

  return (
    <div className="glass-card rounded-2xl p-5 flex flex-col justify-between relative overflow-hidden group">
      {/* Top Banner Accent Line */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 h-1 transition-colors',
          finalScore && finalScore >= 75
            ? 'bg-gradient-to-r from-emerald-500 to-brand-500'
            : finalScore && finalScore >= 50
            ? 'bg-gradient-to-r from-brand-500 to-indigo-500'
            : 'bg-slate-700'
        )}
      />

      {/* Header Info */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-2.5">
          {/* Category & Mode Badges */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 capitalize">
              {opportunity.category.replace(/_/g, ' ')}
            </span>
            <span
              className={cn(
                'text-xs px-2 py-0.5 rounded-full font-medium border flex items-center gap-1',
                opportunity.mode.toLowerCase() === 'online'
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                  : opportunity.mode.toLowerCase() === 'hybrid'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                  : 'bg-blue-500/10 text-blue-300 border-blue-500/20'
              )}
            >
              <Globe className="w-3 h-3" />
              {opportunity.mode}
            </span>
            {opportunity.source && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60">
                {opportunity.source}
              </span>
            )}
          </div>

          {/* Action Buttons: Mark Applied + Bookmark */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {onMarkApplied && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onMarkApplied(opportunity.id);
                }}
                disabled={isApplied}
                className={cn(
                  'px-2.5 py-1 rounded-xl text-[11px] font-bold flex items-center gap-1 transition-all shadow-sm',
                  isApplied
                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 cursor-default'
                    : 'bg-slate-800 hover:bg-indigo-600/30 text-slate-300 hover:text-white border border-slate-700 hover:border-indigo-500/50 active:scale-95'
                )}
                title={isApplied ? 'Application submitted' : 'Quick mark as Applied (auto-bookmarks)'}
              >
                <Check className="w-3 h-3 text-indigo-400" />
                <span>{isApplied ? 'Applied' : 'Mark Applied'}</span>
              </button>
            )}

            {/* Bookmark Button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleSave(opportunity.id);
              }}
              className={cn(
                'p-2 rounded-xl transition-all',
                isSaved
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent'
              )}
              title={isSaved ? 'Remove bookmark' : 'Bookmark opportunity'}
            >
              <Bookmark className={cn('w-4 h-4', isSaved && 'fill-brand-400')} />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-lg text-white group-hover:text-brand-300 transition-colors line-clamp-2 mb-1.5">
          {opportunity.title}
        </h3>

        {/* Organizer */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-3">
          <Building2 className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
          <span className="truncate">{opportunity.organizer}</span>
        </div>

        {/* Description snippet */}
        <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-4">
          {opportunity.description}
        </p>

        {/* AI Match & Eligibility Ribbon (When recommendation data is present) */}
        {recommendation && (
          <div className="mb-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-3">
            {/* Match Score Badge */}
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'w-11 h-11 rounded-xl flex flex-col items-center justify-center font-bold text-xs shadow-inner',
                  finalScore && finalScore >= 75
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : finalScore && finalScore >= 50
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                )}
              >
                <span className="text-[13px] leading-tight font-extrabold">{finalScore?.toFixed(0)}%</span>
                <span className="text-[8px] uppercase tracking-wider text-slate-400">Match</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-200">AI Compatibility</span>
                <span className="text-[11px] text-slate-400 truncate max-w-[150px]">
                  {readiness !== null ? `${readiness.toFixed(0)}% skill readiness` : 'Evaluated'}
                </span>
              </div>
            </div>

            {/* Tri-State Eligibility Badge */}
            <div>
              {eligStatus === 'ELIGIBLE' && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm">
                  <CheckCircle className="w-3 h-3" />
                  ELIGIBLE
                </span>
              )}
              {eligStatus === 'NEEDS_VERIFICATION' && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  <AlertTriangle className="w-3 h-3" />
                  VERIFY DATA
                </span>
              )}
              {eligStatus === 'NOT_ELIGIBLE' && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg bg-rose-500/15 text-rose-400 border border-rose-500/30">
                  <XCircle className="w-3 h-3" />
                  NOT ELIGIBLE
                </span>
              )}
            </div>
          </div>
        )}

        {/* Required Skills Chips */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-1.5">
            {(opportunity.required_skills || []).slice(0, 4).map((skill, idx) => {
              const isMatched = recommendation?.matched_skills?.some(
                (m) => m.toLowerCase() === skill.toLowerCase()
              );
              return (
                <span
                  key={idx}
                  className={cn(
                    'text-[11px] px-2 py-0.5 rounded-md font-mono border transition-colors',
                    isMatched
                      ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25 font-semibold'
                      : 'bg-slate-800/80 text-slate-300 border-slate-700/60'
                  )}
                >
                  {isMatched ? '✓ ' : ''}
                  {skill}
                </span>
              );
            })}
            {(opportunity.required_skills || []).length > 4 && (
              <span className="text-[11px] px-1.5 py-0.5 rounded-md text-slate-400 bg-slate-900 border border-slate-800">
                +{(opportunity.required_skills || []).length - 4} more
              </span>
            )}
          </div>
        </div>

        {/* Prize Pool Info (if present) */}
        {opportunity.prize_pool && (
          <div className="flex items-center gap-1.5 text-xs text-amber-300/90 font-medium mb-3 bg-amber-500/5 px-2.5 py-1 rounded-lg border border-amber-500/15">
            <Award className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="truncate">{opportunity.prize_pool}</span>
          </div>
        )}
      </div>

      {/* Card Footer: Deadline & Action Buttons */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        {/* Deadline countdown & exact IST date */}
        <div className="flex flex-col gap-0.5 text-xs text-slate-400 min-w-0">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span className={cn('font-medium', isUrgent ? 'text-amber-400' : 'text-slate-300')}>
              {countdownLabel}
            </span>
          </div>
          {opportunity.deadline && (
            <span className="text-[10px] text-slate-400 truncate max-w-[170px]" title={formattedIST}>
              {formattedIST}
            </span>
          )}
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onEvaluate(opportunity.id)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-md shadow-brand-500/20 active:scale-95"
          >
            <Zap className="w-3 h-3" />
            <span>Evaluate</span>
          </button>

          <a
            href={opportunity.official_url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700"
            title="Open official site"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
};
