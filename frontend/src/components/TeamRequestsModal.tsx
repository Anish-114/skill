import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X,
  MessageSquare,
  Check,
  XCircle,
  Clock,
  CheckCircle2,
  Mail,
  Phone,
  Github,
  Linkedin,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Inbox,
  Send,
  Building2,
  Calendar,
  Radio,
  Users,
} from 'lucide-react';
import { TeamRequestItem, TeamPost } from '../types';
import { getMyTeamRequests, updateTeamRequestStatus, getMyTeamPosts, closeTeamPost } from '../api/client';
import { cn } from '../utils/cn';
import { formatToIST } from '../utils/date';

interface TeamRequestsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRequestsUpdated?: () => void;
}

export const TeamRequestsModal: React.FC<TeamRequestsModalProps> = ({
  isOpen,
  onClose,
  onRequestsUpdated,
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'received' | 'sent' | 'my_posts'>('received');
  const [requests, setRequests] = useState<TeamRequestItem[]>([]);
  const [myPosts, setMyPosts] = useState<TeamPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [closingPostId, setClosingPostId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadRequests();
      loadMyPosts();
    }
  }, [isOpen]);

  const loadRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyTeamRequests();
      setRequests(data);
    } catch (err: any) {
      console.error('Failed to load team requests:', err);
      setError(err?.response?.data?.detail || 'Team requests load karne mein samasya aayi.');
    } finally {
      setLoading(false);
    }
  };

  const loadMyPosts = async () => {
    try {
      const data = await getMyTeamPosts();
      setMyPosts(data);
    } catch (err) {
      console.error('Failed to load my team posts:', err);
    }
  };

  const handleRespond = async (requestId: number, newStatus: 'accepted' | 'declined') => {
    setUpdatingId(requestId);
    try {
      const updated = await updateTeamRequestStatus(requestId, newStatus);
      setRequests((prev) =>
        prev.map((r) => (r.id === requestId ? updated : r))
      );
      // Also update in myPosts if present
      setMyPosts((prev) =>
        prev.map((p) => {
          if (!p.requests) return p;
          return {
            ...p,
            requests: p.requests.map((r) => (r.id === requestId ? updated : r)),
          };
        })
      );
      if (onRequestsUpdated) {
        onRequestsUpdated();
      }
    } catch (err: any) {
      console.error('Failed to update request:', err);
      alert(err?.response?.data?.detail || 'Request update karne mein samasya aayi.');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleClosePost = async (postId: number) => {
    setClosingPostId(postId);
    try {
      await closeTeamPost(postId);
      setMyPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, status: 'closed' } : p))
      );
    } catch (err: any) {
      console.error('Failed to close post:', err);
      alert(err?.response?.data?.detail || 'Post band karne mein samasya aayi.');
    } finally {
      setClosingPostId(null);
    }
  };

  if (!isOpen) return null;

  const incomingRequests = requests.filter((r) => !r.is_sender);
  const outgoingRequests = requests.filter((r) => r.is_sender);
  const pendingIncomingCount = incomingRequests.filter((r) => r.status === 'pending').length;

  const currentList = activeTab === 'received' ? incomingRequests : outgoingRequests;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-3xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-800/80 flex items-start justify-between bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
              <MessageSquare className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>{t('team_requests.title')}</span>
                {pendingIncomingCount > 0 && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-brand-500 text-white animate-pulse">
                    {pendingIncomingCount} New
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400">
                {t('team_requests.subtitle')}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Controls: Incoming vs Sent vs My Team Posts */}
        <div className="px-5 pt-3 border-b border-slate-800/80 bg-slate-950/30 flex items-center gap-3 overflow-x-auto">
          <button
            onClick={() => setActiveTab('received')}
            className={cn(
              'pb-3 text-xs font-bold transition-all relative flex items-center gap-2 whitespace-nowrap',
              activeTab === 'received'
                ? 'text-brand-400 border-b-2 border-brand-500'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Inbox className="w-4 h-4" />
            <span>{t('team_requests.tab_incoming')}</span>
            {pendingIncomingCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-brand-500 text-white">
                {pendingIncomingCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('sent')}
            className={cn(
              'pb-3 text-xs font-bold transition-all relative flex items-center gap-2 whitespace-nowrap',
              activeTab === 'sent'
                ? 'text-brand-400 border-b-2 border-brand-500'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Send className="w-4 h-4" />
            <span>{t('team_requests.tab_sent')}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
              {outgoingRequests.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('my_posts')}
            className={cn(
              'pb-3 text-xs font-bold transition-all relative flex items-center gap-2 whitespace-nowrap',
              activeTab === 'my_posts'
                ? 'text-brand-400 border-b-2 border-brand-500'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Radio className="w-4 h-4" />
            <span>{t('team_posts.my_posts_tab')}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
              {myPosts.length}
            </span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4 flex-1">
          {loading && (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400">{t('common.loading')}</p>
            </div>
          )}

          {!loading && error && (
            <div className="py-12 text-center space-y-3">
              <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
              <p className="text-xs text-rose-300">{error}</p>
              <button
                onClick={loadRequests}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white"
              >
                {t('common.retry')}
              </button>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 1 & 2: INCOMING & SENT REQUESTS                      */}
          {/* ======================================================== */}
          {activeTab !== 'my_posts' && !loading && !error && currentList.length === 0 && (
            <div className="py-16 text-center space-y-3 glass-card rounded-2xl p-6 border border-slate-800">
              <MessageSquare className="w-10 h-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-300">
                {activeTab === 'received'
                  ? t('team_requests.empty_incoming_title')
                  : t('team_requests.empty_sent_title')}
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {activeTab === 'received'
                  ? t('team_requests.empty_incoming_subtitle')
                  : t('team_requests.empty_sent_subtitle')}
              </p>
            </div>
          )}

          {activeTab !== 'my_posts' && !loading && !error && currentList.length > 0 && (
            <div className="space-y-3.5">
              {currentList.map((req) => {
                const partner = req.is_sender ? req.to_user : req.from_user;
                const isAccepted = req.status === 'accepted';
                const isPending = req.status === 'pending';
                const isDeclined = req.status === 'declined';
                const isUpdating = updatingId === req.id;

                return (
                  <div
                    key={req.id}
                    className="p-4 sm:p-5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
                  >
                    {/* Header: Partner Profile & Status Badge */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 to-indigo-600 border border-brand-500/30 flex items-center justify-center text-sm font-bold text-white flex-shrink-0 shadow-sm">
                          {partner.full_name ? partner.full_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="text-sm font-bold text-white">{partner.full_name}</h4>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                              Year {partner.year || 3} • {partner.degree || 'B.Tech'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {partner.college_name ? `${partner.college_name} • ` : ''}
                            {partner.branch || 'Engineering'}
                          </p>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <div>
                        {isAccepted && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-bold text-xs">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{t('team_requests.status_accepted')}</span>
                          </span>
                        )}
                        {isPending && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 font-semibold text-xs">
                            <Clock className="w-3.5 h-3.5" />
                            <span>{t('team_requests.status_pending')}</span>
                          </span>
                        )}
                        {isDeclined && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 font-semibold text-xs">
                            <XCircle className="w-3.5 h-3.5" />
                            <span>{t('team_requests.status_declined')}</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Opportunity reference */}
                    <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
                      <span className="text-slate-400">{t('team_requests.event_label')}</span>
                      <span className="font-semibold text-brand-300 truncate">
                        {req.opportunity_title}
                      </span>
                    </div>

                    {/* Message (if any) */}
                    {req.message && (
                      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800/80 text-xs text-slate-300 italic">
                        "{req.message}"
                      </div>
                    )}

                    {/* Skills */}
                    {partner.skills && partner.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {partner.skills.slice(0, 6).map((skill, idx) => (
                          <span
                            key={idx}
                            className="text-[11px] px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 font-mono"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Contact Details (Revealed ONLY when Accepted) */}
                    {isAccepted ? (
                      <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          <span>{t('team_requests.connected_title')}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                          {partner.email && (
                            <a
                              href={`mailto:${partner.email}`}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Mail className="w-3.5 h-3.5 text-brand-400" />
                              <span>{partner.email}</span>
                            </a>
                          )}
                          {partner.phone && (
                            <a
                              href={`tel:${partner.phone}`}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Phone className="w-3.5 h-3.5 text-emerald-400" />
                              <span>{partner.phone}</span>
                            </a>
                          )}
                          {partner.github_url && (
                            <a
                              href={partner.github_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                            >
                              <Github className="w-3.5 h-3.5" />
                              <span>GitHub</span>
                              <ExternalLink className="w-3 h-3 text-slate-500" />
                            </a>
                          )}
                          {partner.linkedin_url && (
                            <a
                              href={partner.linkedin_url}
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
                      <div className="text-[11px] text-slate-500 flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
                        <span>{t('teammates.privacy_hidden')}</span>
                      </div>
                    )}

                    {/* Action Bar for Incoming Requests */}
                    {!req.is_sender && isPending && (
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleRespond(req.id, 'declined')}
                          disabled={isUpdating}
                          className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors"
                        >
                          {t('team_requests.decline_request')}
                        </button>
                        <button
                          onClick={() => handleRespond(req.id, 'accepted')}
                          disabled={isUpdating}
                          className="px-4 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-500/20 active:scale-95 flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>{t('team_requests.accept_request')}</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: MY TEAM POSTS (MERI POSTS)                        */}
          {/* ======================================================== */}
          {activeTab === 'my_posts' && (
            <div className="space-y-4">
              {myPosts.length === 0 ? (
                <div className="py-16 text-center space-y-3 glass-card rounded-2xl p-6 border border-slate-800">
                  <Radio className="w-10 h-10 text-slate-600 mx-auto" />
                  <h3 className="text-sm font-bold text-slate-300">
                    {t('team_posts.empty_my_posts_title')}
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    {t('team_posts.empty_my_posts_subtitle')}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {myPosts.map((post) => {
                    const isOpenPost = post.status === 'open';
                    const isClosing = closingPostId === post.id;
                    const requestsOnPost = post.requests || [];

                    return (
                      <div
                        key={post.id}
                        className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4"
                      >
                        {/* Header: Event Title & Status Badge */}
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-sm">
                                {post.opportunity_title}
                              </span>
                              <span
                                className={cn(
                                  'text-[10px] font-bold px-2 py-0.5 rounded-full border',
                                  isOpenPost
                                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                    : 'bg-slate-800 text-slate-400 border-slate-700'
                                )}
                              >
                                {isOpenPost ? t('team_posts.open_badge') : t('team_posts.closed_badge')}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1 italic font-sans">
                              "{post.message}"
                            </p>
                          </div>

                          {isOpenPost && (
                            <button
                              onClick={() => handleClosePost(post.id)}
                              disabled={isClosing}
                              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors flex-shrink-0"
                            >
                              {isClosing ? 'Closing...' : t('team_posts.close_post_btn')}
                            </button>
                          )}
                        </div>

                        {/* Needed Skills */}
                        <div className="flex flex-wrap items-center gap-1.5 text-xs">
                          <span className="text-slate-400 font-semibold">{t('team_posts.needed_skills')}</span>
                          {post.needed_skills.map((skill, idx) => (
                            <span
                              key={idx}
                              className="text-[11px] px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 font-mono"
                            >
                              {skill}
                            </span>
                          ))}
                          <span className="text-[11px] text-indigo-300 font-mono ml-auto">
                            {t('team_posts.team_size_badge', { count: post.team_size_needed })}
                          </span>
                        </div>

                        {/* Sub-section: Incoming Applicants on this Post */}
                        <div className="pt-3 border-t border-slate-800/80 space-y-2.5">
                          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
                            <span className="flex items-center gap-1.5">
                              <Users className="w-3.5 h-3.5 text-brand-400" />
                              <span>{t('team_posts.applicants_title', { count: requestsOnPost.length })}</span>
                            </span>
                          </div>

                          {requestsOnPost.length === 0 ? (
                            <p className="text-xs text-slate-500 italic py-1">
                              {t('team_posts.no_applicants')}
                            </p>
                          ) : (
                            <div className="space-y-2.5">
                              {requestsOnPost.map((req) => {
                                const applicant = req.from_user;
                                const isReqAccepted = req.status === 'accepted';
                                const isReqPending = req.status === 'pending';
                                const isUpdating = updatingId === req.id;

                                return (
                                  <div
                                    key={req.id}
                                    className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2"
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div>
                                        <div className="flex items-center gap-2">
                                          <span className="text-xs font-bold text-white">
                                            {applicant.full_name}
                                          </span>
                                          <span className="text-[10px] text-slate-400 font-mono">
                                            Year {applicant.year || 3} • {applicant.degree || 'B.Tech'}
                                          </span>
                                        </div>
                                        <p className="text-[11px] text-slate-400">
                                          {applicant.college_name ? `${applicant.college_name} • ` : ''}
                                          {applicant.branch || 'Engineering'}
                                        </p>
                                      </div>

                                      <div>
                                        {isReqAccepted && (
                                          <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                                            {t('team_requests.status_accepted')}
                                          </span>
                                        )}
                                        {isReqPending && (
                                          <span className="text-[11px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                                            {t('team_requests.status_pending')}
                                          </span>
                                        )}
                                        {req.status === 'declined' && (
                                          <span className="text-[11px] text-slate-500">
                                            {t('team_requests.status_declined')}
                                          </span>
                                        )}
                                      </div>
                                    </div>

                                    {req.message && (
                                      <p className="text-xs text-slate-300 italic bg-slate-950/50 p-2 rounded-lg">
                                        "{req.message}"
                                      </p>
                                    )}

                                    {/* Revealed Contact Details if Accepted */}
                                    {isReqAccepted && (
                                      <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                                        {applicant.email && (
                                          <a
                                            href={`mailto:${applicant.email}`}
                                            className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950 text-slate-200 border border-slate-800 hover:text-white"
                                          >
                                            <Mail className="w-3 h-3 text-brand-400" />
                                            <span>{applicant.email}</span>
                                          </a>
                                        )}
                                        {applicant.phone && (
                                          <a
                                            href={`tel:${applicant.phone}`}
                                            className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950 text-slate-200 border border-slate-800 hover:text-white"
                                          >
                                            <Phone className="w-3 h-3 text-emerald-400" />
                                            <span>{applicant.phone}</span>
                                          </a>
                                        )}
                                        {applicant.github_url && (
                                          <a
                                            href={applicant.github_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950 text-slate-200 border border-slate-800 hover:text-white"
                                          >
                                            <Github className="w-3 h-3" />
                                            <span>GitHub</span>
                                          </a>
                                        )}
                                        {applicant.linkedin_url && (
                                          <a
                                            href={applicant.linkedin_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-950 text-slate-200 border border-slate-800 hover:text-white"
                                          >
                                            <Linkedin className="w-3 h-3 text-blue-400" />
                                            <span>LinkedIn</span>
                                          </a>
                                        )}
                                      </div>
                                    )}

                                    {/* Action buttons if Pending */}
                                    {isReqPending && (
                                      <div className="flex items-center justify-end gap-2 pt-1">
                                        <button
                                          onClick={() => handleRespond(req.id, 'declined')}
                                          disabled={isUpdating}
                                          className="px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700"
                                        >
                                          {t('team_requests.decline_request')}
                                        </button>
                                        <button
                                          onClick={() => handleRespond(req.id, 'accepted')}
                                          disabled={isUpdating}
                                          className="px-3 py-1 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm flex items-center gap-1"
                                        >
                                          <Check className="w-3 h-3" />
                                          <span>{t('team_requests.accept_request')}</span>
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>SkillBridge Teammate Matching Protocol</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
          >
            {t('team_requests.close_modal')}
          </button>
        </div>
      </div>
    </div>
  );
};
