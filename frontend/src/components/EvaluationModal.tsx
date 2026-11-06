import React from 'react';
import {
  X,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Zap,
  BookOpen,
  ExternalLink,
  ShieldCheck,
  Brain,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { FullEvaluation } from '../types';
import { cn } from '../utils/cn';

interface EvaluationModalProps {
  evaluation: FullEvaluation | null;
  isOpen: boolean;
  onClose: () => void;
  officialUrl?: string;
}

export const EvaluationModal: React.FC<EvaluationModalProps> = ({
  evaluation,
  isOpen,
  onClose,
  officialUrl,
}) => {
  if (!isOpen || !evaluation) return null;

  const { eligibility, skill_gap, recommendation } = evaluation;
  const breakdown = recommendation.breakdown;
  const finalScore = recommendation.final_score;

  const factors = [
    { label: 'Skill Match', weight: '35%', score: breakdown.skill_match, color: 'from-emerald-500 to-teal-400' },
    { label: 'Interest & Topic', weight: '25%', score: breakdown.interest_match, color: 'from-indigo-500 to-ai-primary' },
    { label: 'Experience & Year', weight: '15%', score: breakdown.experience_match, color: 'from-blue-500 to-cyan-400' },
    { label: 'Mode Accessibility', weight: '10%', score: breakdown.mode_match, color: 'from-amber-500 to-yellow-400' },
    { label: 'Eligibility Confidence', weight: '15%', score: breakdown.eligibility_confidence, color: 'from-purple-500 to-pink-500' },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-3xl glass-panel bg-slate-950/95 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-6 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900/50">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs uppercase tracking-wider font-bold text-brand-400 flex items-center gap-1">
                <Brain className="w-3.5 h-3.5" />
                Pre-Application Intelligence Report
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white leading-tight">
              {evaluation.opportunity_title}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-5 sm:p-6 space-y-6 overflow-y-auto">
          {/* Top Overall Score Card */}
          <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  'w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-black shadow-lg',
                  finalScore >= 75
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : finalScore >= 50
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                )}
              >
                <span className="text-xl leading-none">{finalScore.toFixed(0)}</span>
                <span className="text-[9px] uppercase tracking-wider mt-0.5 text-slate-400">/ 100</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white">Hybrid Match Rating</span>
                  {eligibility.status === 'ELIGIBLE' && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      ELIGIBLE
                    </span>
                  )}
                  {eligibility.status === 'NEEDS_VERIFICATION' && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      VERIFY DATA
                    </span>
                  )}
                  {eligibility.status === 'NOT_ELIGIBLE' && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                      NOT ELIGIBLE (50% Penalty)
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5 max-w-md">
                  Calculated using semantic neural embeddings, deterministic rules, and weighted skill readiness.
                </p>
              </div>
            </div>

            {/* Quick Readiness Badge */}
            <div className="text-right sm:border-l sm:border-slate-800 sm:pl-4">
              <span className="text-xs text-slate-400">Skill Readiness</span>
              <div className="text-lg font-bold text-emerald-400">
                {skill_gap.readiness_score.toFixed(0)}%
              </div>
              <span className="text-[11px] text-slate-500">
                {skill_gap.matched_skills.length} of {skill_gap.matched_skills.length + skill_gap.missing_skills.length} skills
              </span>
            </div>
          </div>

          {/* AI Explanation Callout */}
          <div className="p-4 rounded-xl bg-brand-500/5 border border-brand-500/15 flex items-start gap-3">
            <Zap className="w-5 h-5 text-brand-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-brand-300 mb-1">
                AI Recommendation Analysis
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed">
                {recommendation.explanation}
              </p>
            </div>
          </div>

          {/* 5-Factor Scoring Breakdown */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-slate-400" />
              Weighted Factor Breakdown
            </h4>
            <div className="space-y-2.5">
              {factors.map((f, i) => (
                <div key={i} className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-medium text-slate-300">
                      {f.label} <span className="text-slate-500">({f.weight})</span>
                    </span>
                    <span className="font-bold text-white">{f.score.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={cn('h-1.5 rounded-full bg-gradient-to-r', f.color)}
                      style={{ width: `${Math.max(2, Math.min(100, f.score))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Deterministic Eligibility Verification Results */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Eligibility Rule Verification
            </h4>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
              {/* Passed checks */}
              {eligibility.passed_checks.map((check, i) => (
                <div key={`p-${i}`} className="flex items-start gap-2 text-emerald-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{check}</span>
                </div>
              ))}

              {/* Failed checks */}
              {eligibility.failed_checks.map((check, i) => (
                <div key={`f-${i}`} className="flex items-start gap-2 text-rose-300">
                  <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                  <span>{check}</span>
                </div>
              ))}

              {/* Missing data checks */}
              {eligibility.missing_data_checks.map((check, i) => (
                <div key={`m-${i}`} className="flex items-start gap-2 text-amber-300">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span>{check}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Skill Gap Analysis (Matched vs Missing) */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-ai-primary" />
              Skill Alignment Matrix
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {/* Matched skills */}
              <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <span className="font-semibold text-emerald-400 block mb-2">
                  ✓ Matched Competencies ({skill_gap.matched_skills.length})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {skill_gap.matched_skills.length > 0 ? (
                    skill_gap.matched_skills.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/25">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 italic">No skills matched yet.</span>
                  )}
                </div>
              </div>

              {/* Missing skills */}
              <div className="p-3.5 rounded-xl bg-rose-500/5 border border-rose-500/20">
                <span className="font-semibold text-rose-400 block mb-2">
                  ✗ Skill Gap Prerequisites ({skill_gap.missing_skills.length})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {skill_gap.missing_skills.length > 0 ? (
                    skill_gap.missing_skills.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-300 border border-rose-500/25">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-emerald-400 italic">100% matched! No skill gaps.</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Actionable Preparation Checklist */}
          {skill_gap.preparation_checklist.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-amber-400" />
                Actionable Preparation Checklist
              </h4>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                {skill_gap.preparation_checklist.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                    <span className="w-5 h-5 rounded-md bg-slate-800 text-brand-300 border border-slate-700 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-5 border-t border-slate-800 flex items-center justify-between gap-3 bg-slate-900/50">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            Close Report
          </button>

          {officialUrl && (
            <a
              href={officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-brand-500/25 transition-all"
            >
              <span>Apply on Official Website</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
