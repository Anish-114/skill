import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X,
  Users,
  Sparkles,
  Send,
  CheckCircle2,
  Clock,
  Shield,
  ShieldCheck,
  Mail,
  Phone,
  Github,
  Linkedin,
  AlertCircle,
  ExternalLink,
  MessageSquare,
  Check,
} from 'lucide-react';
import { Opportunity, StudentProfile, TeammateCandidate } from '../types';
import {
  getOpportunityTeammates,
  sendTeamRequest,
  updateTeamRequestStatus,
  updateProfile,
} from '../api/client';
import { cn } from '../utils/cn';

interface TeammateModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
  currentUserProfile: StudentProfile | null;
  onProfileUpdated?: (updated: StudentProfile) => void;
  onOpenRequests?: () => void;
}

export const TeammateModal: React.FC<TeammateModalProps> = ({
  isOpen,
  onClose,
  opportunity,
  currentUserProfile,
  onProfileUpdated,
  onOpenRequests,
}) => {
  const { t } = useTranslation();
  const [candidates, setCandidates] = useState<TeammateCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Per-candidate message and sending state
  const [messages, setMessages] = useState<{ [userId: number]: string }>({});
  const [sendingUserId, setSendingUserId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Quick opt-in state
  const [togglingOptIn, setTogglingOptIn] = useState(false);

  useEffect(() => {
    if (isOpen && opportunity) {
      loadTeammates();
    } else {
      setCandidates([]);
      setError(null);
      setActionError(null);
      setMessages({});
    }
  }, [isOpen, opportunity?.id]);

  const loadTeammates = async () => {
    if (!opportunity) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getOpportunityTeammates(opportunity.id);
      setCandidates(data);
    } catch (err: any) {
      console.error('Failed to load teammates:', err);
      setError(
        err?.response?.data?.detail || 'Teammates load karne mein samasya aayi. Kripya punah prayas karein.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (candidate: TeammateCandidate) => {
    if (!opportunity) return;
    setSendingUserId(candidate.user_id);
    setActionError(null);

    const messageText = messages[candidate.user_id] || '';
    try {
      await sendTeamRequest({
        to_user_id: candidate.user_id,
        opportunity_id: opportunity.id,
        message: messageText.trim() || undefined,
      });

      // Optimistically update candidate request status
      setCandidates((prev) =>
        prev.map((c) =>
          c.user_id === candidate.user_id
            ? { ...c, request_status: 'pending', is_outgoing_request: true }
            : c
        )
      );
    } catch (err: any) {
      console.error('Failed to send team request:', err);
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 429) {
        setActionError('Spam rokne ke liye ek din mein maximum 10 requests bhej sakte hain.');
      } else {
        setActionError(detail || 'Request bhejne mein samasya aayi.');
      }
    } finally {
      setSendingUserId(null);
    }
  };

  const handleRespondRequest = async (candidate: TeammateCandidate, newStatus: 'accepted' | 'declined') => {
    if (!candidate.request_id) return;
    setSendingUserId(candidate.user_id);
    setActionError(null);
    try {
      const updated = await updateTeamRequestStatus(candidate.request_id, newStatus);
      // Reload candidates to fetch revealed contact details on accept
      await loadTeammates();
    } catch (err: any) {
      console.error('Failed to respond to request:', err);
      setActionError(err?.response?.data?.detail || 'Request update karne mein samasya aayi.');
    } finally {
      setSendingUserId(null);
    }
  };

  const handleQuickOptIn = async () => {
    if (!currentUserProfile) return;
    setTogglingOptIn(true);
    try {
      const updated = await updateProfile({ looking_for_team: true });
      if (onProfileUpdated) {
        onProfileUpdated(updated);
      }
    } catch (err) {
      console.error('Failed to toggle opt-in:', err);
    } finally {
      setTogglingOptIn(false);
    }
  };

  if (!isOpen || !opportunity) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-3xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-800/80 flex items-start justify-between bg-slate-950/50">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Users className="w-5 h-5" />
              </span>
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>{t('teammates.title')}</span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/25">
                    {t('teammates.badge')}
                  </span>
                </h2>
                <p className="text-xs text-slate-400 truncate max-w-xl">
                  {opportunity.title}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onOpenRequests && (
              <button
                onClick={() => {
                  onClose();
                  onOpenRequests();
                }}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                title="View your pending and accepted team requests"
              >
                <MessageSquare className="w-3.5 h-3.5 text-brand-400" />
                <span>{t('team_requests.title')}</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4 flex-1">
          {/* Action Error Alert */}
          {actionError && (
            <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span>{actionError}</span>
              </div>
              <button
                onClick={() => setActionError(null)}
                className="text-rose-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Opt-In Banner if current user has looking_for_team disabled */}
          {currentUserProfile && !currentUserProfile.looking_for_team && (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 text-amber-300 font-bold text-xs">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span>{t('teammates.opt_in_banner_title')}</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {t('teammates.opt_in_banner_desc')}
                </p>
              </div>
              <button
                onClick={handleQuickOptIn}
                disabled={togglingOptIn}
                className="px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all shadow-sm flex-shrink-0"
              >
                {togglingOptIn ? t('common.loading') : t('teammates.enable_1click')}
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400">
                {t('teammates.loading')}
              </p>
            </div>
          )}

          {/* Error State */}
          {!loading && error && (
            <div className="py-12 text-center space-y-3">
              <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
              <p className="text-xs text-rose-300">{error}</p>
              <button
                onClick={loadTeammates}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white"
              >
                {t('common.retry')}
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && candidates.length === 0 && (
            <div className="py-14 text-center space-y-3 glass-card rounded-2xl p-6 border border-slate-800">
              <Users className="w-10 h-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-300">
                {t('teammates.empty_title')}
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {t('teammates.empty_subtitle')}
              </p>
            </div>
          )}

          {/* Candidates List */}
          {!loading && !error && candidates.length > 0 && (
            <div className="space-y-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>{t('teammates.found_count', { count: candidates.length })}</span>
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Privacy Protected</span>
                </span>
              </div>

              {candidates.map((cand) => {
                const isAccepted = cand.request_status === 'accepted';
                const isPending = cand.request_status === 'pending';
                const isDeclined = cand.request_status === 'declined';
                const isSending = sendingUserId === cand.user_id;

                return (
                  <div
                    key={cand.user_id}
                    className="p-4 sm:p-5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3.5"
                  >
                    {/* Header: User Info & Match Score */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 to-indigo-600 border border-brand-500/30 flex items-center justify-center text-sm font-bold text-white flex-shrink-0 shadow-sm">
                          {cand.full_name ? cand.full_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="text-sm font-bold text-white">{cand.full_name}</h4>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                              Year {cand.year || 3} • {cand.degree || 'B.Tech'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {cand.college_name ? `${cand.college_name} • ` : ''}
                            {cand.branch || 'Engineering'}
                          </p>
                        </div>
                      </div>

                      {/* Match Score Badge */}
                      <div className="text-right flex-shrink-0">
                        <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-gradient-to-r from-emerald-500/15 to-brand-500/15 border border-emerald-500/30 text-emerald-300 font-bold text-xs">
                          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{t('teammates.match_score', { score: cand.match_score })}</span>
                        </div>
                      </div>
                    </div>

                    {/* Explainable Matching Pill */}
                    <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 flex items-start gap-2">
                      <Sparkles className="w-4 h-4 text-ai-primary flex-shrink-0 mt-0.5" />
                      <span className="leading-snug">{cand.explanation}</span>
                    </div>

                    {/* Complementary & Total Skills */}
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
                        <span>Skills:</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {cand.skills.map((skill, idx) => {
                          const isComplementary = cand.complementary_skills.some(
                            (c) => c.toLowerCase() === skill.toLowerCase()
                          );
                          return (
                            <span
                              key={idx}
                              className={cn(
                                'text-[11px] px-2.5 py-0.5 rounded-lg border font-mono transition-colors',
                                isComplementary
                                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/35 font-semibold'
                                  : 'bg-slate-900 text-slate-400 border-slate-800'
                              )}
                            >
                              {isComplementary ? '✓ ' : ''}
                              {skill}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    {/* Privacy & Contact Details (Revealed ONLY when accepted) */}
                    {isAccepted ? (
                      <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span>{t('teammates.connected_title', { name: cand.full_name })}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                          {cand.email && (
                            <a
                              href={`mailto:${cand.email}`}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Mail className="w-3.5 h-3.5 text-brand-400" />
                              <span>{cand.email}</span>
                            </a>
                          )}
                          {cand.phone && (
                            <a
                              href={`tel:${cand.phone}`}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Phone className="w-3.5 h-3.5 text-emerald-400" />
                              <span>{cand.phone}</span>
                            </a>
                          )}
                          {cand.github_url && (
                            <a
                              href={cand.github_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Github className="w-3.5 h-3.5" />
                              <span>GitHub</span>
                              <ExternalLink className="w-3 h-3 text-slate-500" />
                            </a>
                          )}
                          {cand.linkedin_url && (
                            <a
                              href={cand.linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Linkedin className="w-3.5 h-3.5 text-blue-400" />
                              <span>LinkedIn</span>
                              <ExternalLink className="w-3 h-3 text-slate-500" />
                            </a>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between text-[11px] text-slate-500 px-1">
                        <span className="flex items-center gap-1">
                          <Shield className="w-3.5 h-3.5 text-slate-600" />
                          <span>{t('teammates.privacy_hidden')}</span>
                        </span>
                      </div>
                    )}

                    {/* Action Bar */}
                    <div className="pt-2 border-t border-slate-800/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
                      {/* State 1: Already accepted */}
                      {isAccepted && (
                        <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-bold">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>{t('team_requests.status_accepted')}</span>
                        </div>
                      )}

                      {/* State 2: Request Pending */}
                      {isPending && (
                        <div className="flex items-center justify-between w-full">
                          <div className="inline-flex items-center gap-1.5 text-xs text-amber-300 font-semibold">
                            <Clock className="w-4 h-4 text-amber-400" />
                            <span>
                              {cand.is_outgoing_request
                                ? t('teammates.request_sent')
                                : t('teammates.incoming_request')}
                            </span>
                          </div>

                          {/* If recipient, can accept or decline right here */}
                          {!cand.is_outgoing_request && cand.request_id && (
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleRespondRequest(cand, 'accepted')}
                                disabled={isSending}
                                className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm flex items-center gap-1"
                              >
                                <Check className="w-3.5 h-3.5" />
                                <span>{t('teammates.accept')}</span>
                              </button>
                              <button
                                onClick={() => handleRespondRequest(cand, 'declined')}
                                disabled={isSending}
                                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors"
                              >
                                {t('teammates.decline')}
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {/* State 3: Declined */}
                      {isDeclined && (
                        <span className="text-xs text-slate-500 font-medium">
                          {t('team_requests.status_declined')}
                        </span>
                      )}

                      {/* State 4: No request yet -> Show Send Request input + button */}
                      {!cand.request_status && (
                        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full">
                          <input
                            type="text"
                            placeholder={t('teammates.note_placeholder')}
                            value={messages[cand.user_id] || ''}
                            onChange={(e) =>
                              setMessages({ ...messages, [cand.user_id]: e.target.value })
                            }
                            className="flex-1 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                          />
                          <button
                            onClick={() => handleSendRequest(cand)}
                            disabled={isSending}
                            className="flex items-center justify-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-md shadow-brand-500/20 active:scale-95 flex-shrink-0"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>{isSending ? t('teammates.sending') : t('teammates.send_request')}</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>{t('teammates.spam_warning')}</span>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            {t('teammates.close_modal')}
          </button>
        </div>
      </div>
    </div>
  );
};
