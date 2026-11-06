import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';
import { TeamRequestItem } from '../types';
import { getMyTeamRequests, updateTeamRequestStatus } from '../api/client';
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
  const [activeTab, setActiveTab] = useState<'received' | 'sent'>('received');
  const [requests, setRequests] = useState<TeamRequestItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadRequests();
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

  const handleRespond = async (requestId: number, newStatus: 'accepted' | 'declined') => {
    setUpdatingId(requestId);
    try {
      const updated = await updateTeamRequestStatus(requestId, newStatus);
      setRequests((prev) =>
        prev.map((r) => (r.id === requestId ? updated : r))
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
                <span>Meri Team Requests</span>
                {pendingIncomingCount > 0 && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-brand-500 text-white animate-pulse">
                    {pendingIncomingCount} New
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400">
                Hackathon collaboration invites aur incoming team matching requests
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

        {/* Tab Controls */}
        <div className="px-5 pt-3 border-b border-slate-800/80 bg-slate-950/30 flex items-center gap-3">
          <button
            onClick={() => setActiveTab('received')}
            className={cn(
              'pb-3 text-xs font-bold transition-all relative flex items-center gap-2',
              activeTab === 'received'
                ? 'text-brand-400 border-b-2 border-brand-500'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Inbox className="w-4 h-4" />
            <span>Aaye Huye Requests (Incoming)</span>
            {pendingIncomingCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-brand-500 text-white">
                {pendingIncomingCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('sent')}
            className={cn(
              'pb-3 text-xs font-bold transition-all relative flex items-center gap-2',
              activeTab === 'sent'
                ? 'text-brand-400 border-b-2 border-brand-500'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            <Send className="w-4 h-4" />
            <span>Bheje Huye Requests (Sent)</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
              {outgoingRequests.length}
            </span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4 flex-1">
          {loading && (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Loading your team collaboration requests...</p>
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
                Retry
              </button>
            </div>
          )}

          {!loading && !error && currentList.length === 0 && (
            <div className="py-16 text-center space-y-3 glass-card rounded-2xl p-6 border border-slate-800">
              <MessageSquare className="w-10 h-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-300">
                {activeTab === 'received'
                  ? 'Abhi koi incoming team requests nahi hain'
                  : 'Aapne abhi tak koi team request nahi bheji'}
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {activeTab === 'received'
                  ? 'Jab doosre students aapki profile dekh kar collaborate karna chahenge, unki requests yahan dikhengi.'
                  : 'Hackathons explore karein aur "Teammates dhundho" button se compatible teammates ko invite karein.'}
              </p>
            </div>
          )}

          {!loading && !error && currentList.length > 0 && (
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
                            <span>Accepted</span>
                          </span>
                        )}
                        {isPending && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 font-semibold text-xs">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Pending</span>
                          </span>
                        )}
                        {isDeclined && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 font-semibold text-xs">
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Declined</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Opportunity reference */}
                    <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
                      <span className="text-slate-400">Event:</span>
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
                          <span>Connected! Contact Details:</span>
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
                        <span>Contact info protected until request is accepted</span>
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
                          Decline
                        </button>
                        <button
                          onClick={() => handleRespond(req.id, 'accepted')}
                          disabled={isUpdating}
                          className="px-4 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-500/20 active:scale-95 flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Accept Request</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
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
            Band Karein
          </button>
        </div>
      </div>
    </div>
  );
};
