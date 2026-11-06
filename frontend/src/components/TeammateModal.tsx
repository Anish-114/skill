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
  Plus,
  Radio,
  UserCheck,
} from 'lucide-react';
import { Opportunity, StudentProfile, TeammateCandidate, TeamPost } from '../types';
import {
  getOpportunityTeammates,
  sendTeamRequest,
  updateTeamRequestStatus,
  updateProfile,
  getOpportunityTeamPosts,
  createOpportunityTeamPost,
  closeTeamPost,
  joinTeamPost,
} from '../api/client';
import { cn } from '../utils/cn';

interface TeammateModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
  currentUserProfile: StudentProfile | null;
  onProfileUpdated?: (updated: StudentProfile) => void;
  onOpenRequests?: () => void;
  initialTab?: 'board' | 'suggestions';
}

export const TeammateModal: React.FC<TeammateModalProps> = ({
  isOpen,
  onClose,
  opportunity,
  currentUserProfile,
  onProfileUpdated,
  onOpenRequests,
  initialTab = 'board',
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'board' | 'suggestions'>(initialTab);

  // AI Matches state
  const [candidates, setCandidates] = useState<TeammateCandidate[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);

  // Team Board state
  const [teamPosts, setTeamPosts] = useState<TeamPost[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);

  // Create Team Post Form state
  const [isCreatingPost, setIsCreatingPost] = useState(false);
  const [postMessage, setPostMessage] = useState('');
  const [postSkills, setPostSkills] = useState<string[]>([]);
  const [postTeamSize, setPostTeamSize] = useState<number>(2);
  const [customSkillInput, setCustomSkillInput] = useState('');
  const [submittingPost, setSubmittingPost] = useState(false);
  const [postFormError, setPostFormError] = useState<string | null>(null);

  // Per-candidate message and sending state (AI Matches)
  const [messages, setMessages] = useState<{ [userId: number]: string }>({});
  const [sendingUserId, setSendingUserId] = useState<number | null>(null);

  // Join Post state (Team Board)
  const [joinMessages, setJoinMessages] = useState<{ [postId: number]: string }>({});
  const [joiningPostId, setJoiningPostId] = useState<number | null>(null);
  const [closingPostId, setClosingPostId] = useState<number | null>(null);

  const [actionError, setActionError] = useState<string | null>(null);

  // Quick opt-in state
  const [togglingOptIn, setTogglingOptIn] = useState(false);

  useEffect(() => {
    if (isOpen && opportunity) {
      setActiveTab(initialTab);
      loadTeamPosts();
      loadTeammates();
      setIsCreatingPost(false);
      setPostMessage('');
      setPostSkills([]);
      setPostTeamSize(2);
      setCustomSkillInput('');
      setPostFormError(null);
    } else {
      setCandidates([]);
      setTeamPosts([]);
      setCandidatesError(null);
      setPostsError(null);
      setActionError(null);
      setMessages({});
      setJoinMessages({});
    }
  }, [isOpen, opportunity?.id, initialTab]);

  const loadTeammates = async () => {
    if (!opportunity) return;
    setLoadingCandidates(true);
    setCandidatesError(null);
    try {
      const data = await getOpportunityTeammates(opportunity.id);
      setCandidates(data);
    } catch (err: any) {
      console.error('Failed to load teammates:', err);
      setCandidatesError(err?.response?.data?.detail || 'Teammates load karne mein samasya aayi.');
    } finally {
      setLoadingCandidates(false);
    }
  };

  const loadTeamPosts = async () => {
    if (!opportunity) return;
    setLoadingPosts(true);
    setPostsError(null);
    try {
      const data = await getOpportunityTeamPosts(opportunity.id);
      setTeamPosts(data);
    } catch (err: any) {
      console.error('Failed to load team posts:', err);
      setPostsError(err?.response?.data?.detail || 'Team posts load karne mein samasya aayi.');
    } finally {
      setLoadingPosts(false);
    }
  };

  const handleSendCandidateRequest = async (candidate: TeammateCandidate) => {
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

  const handleCreatePostSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!opportunity) return;

    if (!postMessage.trim() || postMessage.trim().length < 5) {
      setPostFormError('Kripya kam se kam 5 characters ka message likhein.');
      return;
    }
    if (postSkills.length === 0) {
      setPostFormError('Kripya kam se kam ek skill select karein.');
      return;
    }

    setSubmittingPost(true);
    setPostFormError(null);
    try {
      const created = await createOpportunityTeamPost(opportunity.id, {
        message: postMessage.trim(),
        needed_skills: postSkills,
        team_size_needed: Number(postTeamSize) || 2,
      });

      // Add new post to list and close form
      setTeamPosts((prev) => [created, ...prev]);
      setIsCreatingPost(false);
      setPostMessage('');
      setPostSkills([]);
      setPostTeamSize(2);
    } catch (err: any) {
      console.error('Failed to create team post:', err);
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 429) {
        setPostFormError(t('team_posts.daily_limit_reached'));
      } else {
        setPostFormError(detail || 'Team post banane mein samasya aayi.');
      }
    } finally {
      setSubmittingPost(false);
    }
  };

  const handleJoinPostSubmit = async (post: TeamPost) => {
    setJoiningPostId(post.id);
    setActionError(null);
    const note = joinMessages[post.id] || '';
    try {
      const res = await joinTeamPost(post.id, note.trim() || undefined);
      // Update local post item
      setTeamPosts((prev) =>
        prev.map((p) =>
          p.id === post.id
            ? { ...p, has_requested: true, my_request_status: 'pending', my_request_id: res.id }
            : p
        )
      );
    } catch (err: any) {
      console.error('Failed to join team post:', err);
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 429) {
        setActionError(t('teammates.spam_warning'));
      } else {
        setActionError(detail || 'Join request bhejne mein samasya aayi.');
      }
    } finally {
      setJoiningPostId(null);
    }
  };

  const handleClosePostSubmit = async (postId: number) => {
    setClosingPostId(postId);
    setActionError(null);
    try {
      await closeTeamPost(postId);
      setTeamPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch (err: any) {
      console.error('Failed to close post:', err);
      setActionError(err?.response?.data?.detail || 'Post band karne mein samasya aayi.');
    } finally {
      setClosingPostId(null);
    }
  };

  const handleRespondCandidateRequest = async (
    candidate: TeammateCandidate,
    newStatus: 'accepted' | 'declined'
  ) => {
    if (!candidate.request_id) return;
    setSendingUserId(candidate.user_id);
    setActionError(null);
    try {
      await updateTeamRequestStatus(candidate.request_id, newStatus);
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

  const toggleSkillSelection = (skillName: string) => {
    if (postSkills.includes(skillName)) {
      setPostSkills(postSkills.filter((s) => s !== skillName));
    } else {
      if (postSkills.length >= 10) return;
      setPostSkills([...postSkills, skillName]);
    }
  };

  const handleAddCustomSkill = () => {
    const trimmed = customSkillInput.trim();
    if (!trimmed) return;
    if (!postSkills.some((s) => s.toLowerCase() === trimmed.toLowerCase())) {
      setPostSkills([...postSkills, trimmed]);
    }
    setCustomSkillInput('');
  };

  if (!isOpen || !opportunity) return null;

  const myOpenPost = teamPosts.find((p) => p.is_creator && p.status === 'open');

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
                    {activeTab === 'board' ? t('team_posts.tab_board') : t('teammates.badge')}
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

        {/* Tab Controls: Team Board vs AI Matches */}
        <div className="px-5 pt-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setActiveTab('board');
                setIsCreatingPost(false);
              }}
              className={cn(
                'pb-3 text-xs font-bold transition-all relative flex items-center gap-2',
                activeTab === 'board'
                  ? 'text-brand-400 border-b-2 border-brand-500'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              <Radio className="w-3.5 h-3.5" />
              <span>{t('team_posts.tab_board')}</span>
              {teamPosts.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {teamPosts.length}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                setActiveTab('suggestions');
                setIsCreatingPost(false);
              }}
              className={cn(
                'pb-3 text-xs font-bold transition-all relative flex items-center gap-2',
                activeTab === 'suggestions'
                  ? 'text-brand-400 border-b-2 border-brand-500'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{t('team_posts.tab_suggestions')}</span>
              {candidates.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {candidates.length}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'board' && !isCreatingPost && !myOpenPost && (
            <button
              onClick={() => setIsCreatingPost(true)}
              className="mb-2.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white flex items-center gap-1.5 shadow-md shadow-brand-500/20 active:scale-95 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{t('team_posts.create_post_btn')}</span>
            </button>
          )}
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

          {/* ======================================================== */}
          {/* TAB 1: TEAM BOARD                                         */}
          {/* ======================================================== */}
          {activeTab === 'board' && (
            <div className="space-y-4">
              {/* Create Team Post Form Accordion */}
              {isCreatingPost && (
                <form
                  onSubmit={handleCreatePostSubmit}
                  className="p-5 rounded-2xl bg-slate-950 border border-brand-500/30 shadow-xl space-y-4 animate-in fade-in duration-200"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Plus className="w-4 h-4 text-brand-400" />
                        <span>{t('team_posts.create_post_title')}</span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {t('team_posts.create_post_desc')}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsCreatingPost(false)}
                      className="p-1 rounded-lg text-slate-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {postFormError && (
                    <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
                      {postFormError}
                    </div>
                  )}

                  {/* Message Field */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs text-slate-300">
                      <label className="font-semibold">{t('team_posts.message_label')}</label>
                      <span className="text-[11px] text-slate-500">
                        {postMessage.length}/300
                      </span>
                    </div>
                    <textarea
                      rows={3}
                      maxLength={300}
                      value={postMessage}
                      onChange={(e) => setPostMessage(e.target.value)}
                      placeholder={t('team_posts.message_placeholder')}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 leading-relaxed"
                      required
                    />
                  </div>

                  {/* Skills Selector */}
                  <div className="space-y-2">
                    <label className="block text-xs font-semibold text-slate-300">
                      {t('team_posts.needed_skills_label')}
                    </label>

                    {/* Pre-fill chips from opportunity required skills */}
                    {opportunity.required_skills && opportunity.required_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {opportunity.required_skills.map((skill, idx) => {
                          const isSelected = postSkills.includes(skill);
                          return (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => toggleSkillSelection(skill)}
                              className={cn(
                                'text-[11px] px-2.5 py-1 rounded-lg border font-mono transition-all',
                                isSelected
                                  ? 'bg-brand-600 text-white border-brand-500 font-bold'
                                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border-slate-800'
                              )}
                            >
                              {isSelected ? '✓ ' : '+ '}
                              {skill}
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Custom skill adder */}
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={customSkillInput}
                        onChange={(e) => setCustomSkillInput(e.target.value)}
                        placeholder={t('team_posts.needed_skills_placeholder')}
                        className="flex-1 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddCustomSkill();
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleAddCustomSkill}
                        className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200"
                      >
                        Add
                      </button>
                    </div>

                    {/* Currently selected skills list */}
                    {postSkills.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {postSkills.map((s, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                          >
                            <span>{s}</span>
                            <button
                              type="button"
                              onClick={() => toggleSkillSelection(s)}
                              className="hover:text-rose-400"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Team Size Needed */}
                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-slate-300">
                      {t('team_posts.team_size_label')}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={postTeamSize}
                      onChange={(e) => setPostTeamSize(Number(e.target.value))}
                      className="w-28 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
                      required
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
                    <button
                      type="button"
                      onClick={() => setIsCreatingPost(false)}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300"
                    >
                      {t('team_posts.cancel')}
                    </button>
                    <button
                      type="submit"
                      disabled={submittingPost}
                      className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-brand-500/20 active:scale-95 transition-all"
                    >
                      {submittingPost ? t('team_posts.submitting') : t('team_posts.submit_post')}
                    </button>
                  </div>
                </form>
              )}

              {/* Loading Posts */}
              {loadingPosts && (
                <div className="py-16 text-center space-y-3">
                  <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs text-slate-400">{t('common.loading')}</p>
                </div>
              )}

              {/* Error Loading Posts */}
              {!loadingPosts && postsError && (
                <div className="py-12 text-center space-y-3">
                  <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
                  <p className="text-xs text-rose-300">{postsError}</p>
                  <button
                    onClick={loadTeamPosts}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white"
                  >
                    {t('common.retry')}
                  </button>
                </div>
              )}

              {/* Empty Team Board */}
              {!loadingPosts && !postsError && teamPosts.length === 0 && !isCreatingPost && (
                <div className="py-14 text-center space-y-4 glass-card rounded-2xl p-6 border border-slate-800">
                  <Radio className="w-10 h-10 text-slate-600 mx-auto" />
                  <div>
                    <h3 className="text-sm font-bold text-slate-300">
                      {t('team_posts.empty_board_title')}
                    </h3>
                    <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                      {t('team_posts.empty_board_subtitle')}
                    </p>
                  </div>
                  <button
                    onClick={() => setIsCreatingPost(true)}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-brand-500/20 transition-all inline-flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{t('team_posts.create_post_btn')}</span>
                  </button>
                </div>
              )}

              {/* Posts List */}
              {!loadingPosts && !postsError && teamPosts.length > 0 && (
                <div className="space-y-4">
                  {teamPosts.map((post) => {
                    const isCreator = post.is_creator;
                    const isJoining = joiningPostId === post.id;
                    const isClosing = closingPostId === post.id;
                    const isAccepted = post.my_request_status === 'accepted';
                    const isPending = post.my_request_status === 'pending';
                    const isDeclined = post.my_request_status === 'declined';

                    return (
                      <div
                        key={post.id}
                        className="p-4 sm:p-5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3.5"
                      >
                        {/* Header: Creator Info & Match Badge */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 to-indigo-600 border border-brand-500/30 flex items-center justify-center text-sm font-bold text-white flex-shrink-0 shadow-sm">
                              {post.creator.full_name
                                ? post.creator.full_name.charAt(0).toUpperCase()
                                : 'U'}
                            </div>
                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="text-sm font-bold text-white">
                                  {post.creator.full_name}
                                </h4>
                                {isCreator && (
                                  <span className="text-[10px] font-bold px-2 py-0.2 rounded-md bg-brand-500/20 text-brand-300 border border-brand-500/30">
                                    You
                                  </span>
                                )}
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                                  Year {post.creator.year || 3} • {post.creator.degree || 'B.Tech'}
                                </span>
                              </div>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {post.creator.college_name ? `${post.creator.college_name} • ` : ''}
                                {post.creator.branch || 'Engineering'}
                              </p>
                            </div>
                          </div>

                          {/* Skill Match Metric Badge */}
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            {post.match_count > 0 ? (
                              <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-bold text-xs">
                                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                                <span>{t('team_posts.match_pct', { pct: post.match_percentage })}</span>
                              </div>
                            ) : (
                              <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-800 text-slate-400 text-[11px]">
                                <span>0% Match</span>
                              </div>
                            )}
                            <span className="text-[10px] text-slate-500 font-mono">
                              {t('team_posts.match_badge', {
                                count: post.match_count,
                                total: post.needed_skills.length,
                              })}
                            </span>
                          </div>
                        </div>

                        {/* Pitch Message Card */}
                        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 text-xs text-slate-200 leading-relaxed font-sans">
                          "{post.message}"
                        </div>

                        {/* Skills Needed Chips with User Match Highlights */}
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span className="font-semibold">{t('team_posts.needed_skills')}</span>
                            <span className="text-indigo-300 font-mono">
                              {t('team_posts.team_size_badge', { count: post.team_size_needed })}
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {post.needed_skills.map((skill, idx) => {
                              const isMatched = post.matched_skills.some(
                                (m) => m.toLowerCase() === skill.toLowerCase()
                              );
                              return (
                                <span
                                  key={idx}
                                  className={cn(
                                    'text-[11px] px-2.5 py-0.5 rounded-lg border font-mono transition-colors',
                                    isMatched
                                      ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/35 font-semibold'
                                      : 'bg-slate-900 text-slate-400 border-slate-800'
                                  )}
                                >
                                  {isMatched ? '✓ ' : ''}
                                  {skill}
                                </span>
                              );
                            })}
                          </div>
                        </div>

                        {/* Sensitive Contact Info (Revealed ONLY if accepted) */}
                        {isAccepted ? (
                          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                              <span>{t('teammates.connected_title', { name: post.creator.full_name })}</span>
                            </div>
                            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                              {post.creator.email && (
                                <a
                                  href={`mailto:${post.creator.email}`}
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                                >
                                  <Mail className="w-3.5 h-3.5 text-brand-400" />
                                  <span>{post.creator.email}</span>
                                </a>
                              )}
                              {post.creator.phone && (
                                <a
                                  href={`tel:${post.creator.phone}`}
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                                >
                                  <Phone className="w-3.5 h-3.5 text-emerald-400" />
                                  <span>{post.creator.phone}</span>
                                </a>
                              )}
                              {post.creator.github_url && (
                                <a
                                  href={post.creator.github_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-200 hover:text-white border border-slate-800 transition-colors"
                                >
                                  <Github className="w-3.5 h-3.5" />
                                  <span>GitHub</span>
                                  <ExternalLink className="w-3 h-3 text-slate-500" />
                                </a>
                              )}
                              {post.creator.linkedin_url && (
                                <a
                                  href={post.creator.linkedin_url}
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
                        ) : !isCreator && (
                          <div className="flex items-center text-[11px] text-slate-500 px-1">
                            <span className="flex items-center gap-1">
                              <Shield className="w-3.5 h-3.5 text-slate-600" />
                              <span>{t('teammates.privacy_hidden')}</span>
                            </span>
                          </div>
                        )}

                        {/* Action Footer */}
                        <div className="pt-2 border-t border-slate-800/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
                          {/* Case 1: Creator view -> Close post button */}
                          {isCreator && (
                            <div className="flex items-center justify-between w-full">
                              <span className="inline-flex items-center gap-1 text-xs text-brand-300 font-semibold">
                                <CheckCircle2 className="w-4 h-4 text-brand-400" />
                                <span>Your recruitment post is active</span>
                              </span>
                              <button
                                onClick={() => handleClosePostSubmit(post.id)}
                                disabled={isClosing}
                                className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors"
                              >
                                {isClosing ? 'Closing...' : t('team_posts.close_post_btn')}
                              </button>
                            </div>
                          )}

                          {/* Case 2: Already Accepted */}
                          {!isCreator && isAccepted && (
                            <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-bold">
                              <CheckCircle2 className="w-4 h-4" />
                              <span>{t('team_posts.joined_accepted')}</span>
                            </div>
                          )}

                          {/* Case 3: Request Pending */}
                          {!isCreator && isPending && (
                            <div className="inline-flex items-center gap-1.5 text-xs text-amber-300 font-semibold">
                              <Clock className="w-4 h-4 text-amber-400" />
                              <span>{t('team_posts.joined_badge')} (Pending)</span>
                            </div>
                          )}

                          {/* Case 4: Request Declined */}
                          {!isCreator && isDeclined && (
                            <span className="text-xs text-slate-500 font-medium">
                              Request was declined.
                            </span>
                          )}

                          {/* Case 5: No request yet -> Show Join input & button */}
                          {!isCreator && !post.has_requested && (
                            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full">
                              <input
                                type="text"
                                placeholder="Add a quick note (e.g. 'I know React, let's connect!')..."
                                value={joinMessages[post.id] || ''}
                                onChange={(e) =>
                                  setJoinMessages({ ...joinMessages, [post.id]: e.target.value })
                                }
                                className="flex-1 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                              />
                              <button
                                onClick={() => handleJoinPostSubmit(post)}
                                disabled={isJoining}
                                className="flex items-center justify-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-md shadow-brand-500/20 active:scale-95 flex-shrink-0"
                              >
                                <Send className="w-3.5 h-3.5" />
                                <span>{isJoining ? t('team_posts.joining') : t('team_posts.join_btn')}</span>
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
          )}

          {/* ======================================================== */}
          {/* TAB 2: AI MATCHES / COMPLEMENTARY MATCHING               */}
          {/* ======================================================== */}
          {activeTab === 'suggestions' && (
            <div className="space-y-4">
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
              {loadingCandidates && (
                <div className="py-16 text-center space-y-3">
                  <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs text-slate-400">{t('teammates.loading')}</p>
                </div>
              )}

              {/* Error State */}
              {!loadingCandidates && candidatesError && (
                <div className="py-12 text-center space-y-3">
                  <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
                  <p className="text-xs text-rose-300">{candidatesError}</p>
                  <button
                    onClick={loadTeammates}
                    className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white"
                  >
                    {t('common.retry')}
                  </button>
                </div>
              )}

              {/* Empty State */}
              {!loadingCandidates && !candidatesError && candidates.length === 0 && (
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
              {!loadingCandidates && !candidatesError && candidates.length > 0 && (
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
                          {isAccepted && (
                            <div className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-bold">
                              <CheckCircle2 className="w-4 h-4" />
                              <span>{t('team_requests.status_accepted')}</span>
                            </div>
                          )}

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

                              {!cand.is_outgoing_request && cand.request_id && (
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => handleRespondCandidateRequest(cand, 'accepted')}
                                    disabled={isSending}
                                    className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm flex items-center gap-1"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                    <span>{t('teammates.accept')}</span>
                                  </button>
                                  <button
                                    onClick={() => handleRespondCandidateRequest(cand, 'declined')}
                                    disabled={isSending}
                                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors"
                                  >
                                    {t('teammates.decline')}
                                  </button>
                                </div>
                              )}
                            </div>
                          )}

                          {isDeclined && (
                            <span className="text-xs text-slate-500 font-medium">
                              {t('team_requests.status_declined')}
                            </span>
                          )}

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
                                onClick={() => handleSendCandidateRequest(cand)}
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
