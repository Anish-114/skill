import React, { useState } from 'react';
import {
  Bookmark,
  ExternalLink,
  Trash2,
  Zap,
  Calendar,
  Building2,
  FileEdit,
  Check,
  X,
  AlertCircle,
  Plus,
} from 'lucide-react';
import { SavedOpportunityItem } from '../types';
import { cn } from '../utils/cn';
import { formatToIST, getDeadlineCountdown } from '../utils/date';
import { updateSavedOpportunity } from '../api/client';

export const STATUS_CONFIG: Record<
  string,
  { label: string; badgeClass: string; dotClass: string }
> = {
  saved: {
    label: 'Saved',
    badgeClass: 'bg-slate-800/90 text-slate-300 border-slate-700',
    dotClass: 'bg-slate-400',
  },
  applied: {
    label: 'Applied',
    badgeClass: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    dotClass: 'bg-indigo-400',
  },
  in_progress: {
    label: 'In Progress',
    badgeClass: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    dotClass: 'bg-amber-400',
  },
  shortlisted: {
    label: 'Shortlisted',
    badgeClass: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
    dotClass: 'bg-cyan-400',
  },
  selected: {
    label: 'Selected',
    badgeClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    dotClass: 'bg-emerald-400',
  },
  rejected: {
    label: 'Rejected',
    badgeClass: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    dotClass: 'bg-rose-400',
  },
  archived: {
    label: 'Archived',
    badgeClass: 'bg-slate-900 text-slate-500 border-slate-800',
    dotClass: 'bg-slate-600',
  },
};

const ALL_STATUSES = [
  'all',
  'saved',
  'applied',
  'in_progress',
  'shortlisted',
  'selected',
  'rejected',
  'archived',
];

interface SavedViewProps {
  savedList: SavedOpportunityItem[];
  loading: boolean;
  onEvaluate: (oppId: number) => void;
  onRemoveSave: (oppId: number) => void;
  onItemUpdated?: (updatedItem: SavedOpportunityItem) => void;
}

export const SavedView: React.FC<SavedViewProps> = ({
  savedList,
  loading,
  onEvaluate,
  onRemoveSave,
  onItemUpdated,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  // Inline notes editor state: mapping oppId -> text being edited
  const [editingNotesId, setEditingNotesId] = useState<number | null>(null);
  const [notesInput, setNotesInput] = useState<string>('');
  const [savingNoteId, setSavingNoteId] = useState<number | null>(null);
  const [statusUpdatingId, setStatusUpdatingId] = useState<number | null>(null);

  // Status counts
  const statusCounts = ALL_STATUSES.reduce((acc, st) => {
    if (st === 'all') {
      acc[st] = savedList.length;
    } else {
      acc[st] = savedList.filter(
        (item) => item.status.toLowerCase() === st.toLowerCase()
      ).length;
    }
    return acc;
  }, {} as Record<string, number>);

  const filtered = savedList.filter((item) => {
    if (selectedStatus === 'all') return true;
    return item.status.toLowerCase() === selectedStatus.toLowerCase();
  });

  const handleStatusChange = async (
    item: SavedOpportunityItem,
    newStatus: string
  ) => {
    if (item.status.toLowerCase() === newStatus.toLowerCase()) return;
    const oldStatus = item.status;
    const oppId = item.opportunity_id;

    // Optimistic UI update
    setStatusUpdatingId(oppId);
    item.status = newStatus;
    if (onItemUpdated) {
      onItemUpdated({ ...item, status: newStatus });
    }

    try {
      const updated = await updateSavedOpportunity(oppId, { status: newStatus });
      if (onItemUpdated) {
        onItemUpdated(updated);
      }
    } catch (err) {
      console.error('Failed to update status, rolling back:', err);
      // Rollback on failure
      item.status = oldStatus;
      if (onItemUpdated) {
        onItemUpdated({ ...item, status: oldStatus });
      }
    } finally {
      setStatusUpdatingId(null);
    }
  };

  const handleStartEditNotes = (item: SavedOpportunityItem) => {
    setEditingNotesId(item.opportunity_id);
    setNotesInput(item.notes || '');
  };

  const handleCancelEditNotes = () => {
    setEditingNotesId(null);
    setNotesInput('');
  };

  const handleSaveNotes = async (item: SavedOpportunityItem) => {
    const oppId = item.opportunity_id;
    const oldNotes = item.notes;
    const newNotes = notesInput.trim();

    setSavingNoteId(oppId);
    // Optimistic update
    item.notes = newNotes;
    if (onItemUpdated) {
      onItemUpdated({ ...item, notes: newNotes });
    }

    try {
      const updated = await updateSavedOpportunity(oppId, { notes: newNotes });
      if (onItemUpdated) {
        onItemUpdated(updated);
      }
      setEditingNotesId(null);
    } catch (err) {
      console.error('Failed to save notes, rolling back:', err);
      item.notes = oldNotes;
      if (onItemUpdated) {
        onItemUpdated({ ...item, notes: oldNotes });
      }
    } finally {
      setSavingNoteId(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Bookmark className="w-6 h-6 text-brand-400 fill-brand-400" />
            Application Tracker & Saved Opportunities
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Track submissions, manage preparation notes, and monitor application milestones.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 p-1.5 rounded-xl glass-panel bg-slate-900/60 overflow-x-auto max-w-full">
          {ALL_STATUSES.map((s) => {
            const count = statusCounts[s] || 0;
            const cfg = STATUS_CONFIG[s];
            const label = s === 'all' ? 'All' : cfg?.label || s;

            return (
              <button
                key={s}
                onClick={() => setSelectedStatus(s)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5',
                  selectedStatus === s
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                )}
              >
                <span>{label}</span>
                <span
                  className={cn(
                    'text-[10px] px-1.5 py-0.2 rounded-full font-bold',
                    selectedStatus === s
                      ? 'bg-brand-800 text-brand-100'
                      : 'bg-slate-800 text-slate-400'
                  )}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bookmarks Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-5 h-64 animate-pulse" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((item) => {
            const opp = item.opportunity;
            const isEditingNotes = editingNotesId === item.opportunity_id;
            const isSavingNote = savingNoteId === item.opportunity_id;
            const isStatusUpdating = statusUpdatingId === item.opportunity_id;

            // Check if deadline has passed or event is marked inactive
            const now = new Date();
            const isExpired =
              !opp.is_active ||
              (opp.deadline ? new Date(opp.deadline).getTime() < now.getTime() : false);

            const { label: countdownLabel, isUrgent } = getDeadlineCountdown(opp.deadline);
            const formattedIST = formatToIST(opp.deadline);
            const statusKey = item.status.toLowerCase();
            const currentStatusCfg = STATUS_CONFIG[statusKey] || STATUS_CONFIG.saved;

            return (
              <div
                key={item.id}
                className={cn(
                  'glass-card rounded-2xl p-5 flex flex-col justify-between border transition-colors relative',
                  isExpired ? 'border-slate-800/80 bg-slate-950/60' : 'border-slate-800'
                )}
              >
                <div>
                  {/* Top Badges Row: Category + Expired / Active + Status Dropdown */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-brand-500/10 text-brand-300 border border-brand-500/20 capitalize">
                        {opp.category.replace(/_/g, ' ')}
                      </span>

                      {/* Expired Label (Requirement 5) */}
                      {isExpired && (
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1"
                          title="Event deadline has passed. Historical record preserved."
                        >
                          <AlertCircle className="w-3 h-3 text-rose-400" />
                          Expired
                        </span>
                      )}
                    </div>

                    {/* Status Dropdown (Requirement 2 & 3) */}
                    <div className="relative flex items-center">
                      <select
                        value={statusKey}
                        disabled={isStatusUpdating}
                        onChange={(e) => handleStatusChange(item, e.target.value)}
                        className={cn(
                          'text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border focus:outline-none cursor-pointer transition-all',
                          currentStatusCfg.badgeClass,
                          isStatusUpdating && 'opacity-50 pointer-events-none'
                        )}
                        title="Update application status"
                      >
                        <option value="saved" className="bg-slate-900 text-slate-200">
                          Saved
                        </option>
                        <option value="applied" className="bg-slate-900 text-indigo-300">
                          Applied
                        </option>
                        <option value="in_progress" className="bg-slate-900 text-amber-300">
                          In Progress
                        </option>
                        <option value="shortlisted" className="bg-slate-900 text-cyan-300">
                          Shortlisted
                        </option>
                        <option value="selected" className="bg-slate-900 text-emerald-300">
                          Selected
                        </option>
                        <option value="rejected" className="bg-slate-900 text-rose-300">
                          Rejected
                        </option>
                        <option value="archived" className="bg-slate-900 text-slate-400">
                          Archived
                        </option>
                      </select>
                    </div>
                  </div>

                  {/* Opportunity Title */}
                  <h3 className="font-semibold text-lg text-white mb-1 line-clamp-2">
                    {opp.title}
                  </h3>

                  {/* Organizer */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-3">
                    <Building2 className="w-3.5 h-3.5 text-slate-500" />
                    <span className="truncate">{opp.organizer}</span>
                  </div>

                  {/* Inline Notes Editor (Requirement 2) */}
                  <div className="mb-4">
                    {isEditingNotes ? (
                      <div className="p-3 rounded-xl bg-slate-900 border border-brand-500/30 space-y-2 animate-in fade-in">
                        <textarea
                          rows={2}
                          value={notesInput}
                          onChange={(e) => setNotesInput(e.target.value)}
                          placeholder="Add tracking notes (e.g. Round 1 submitted, interview link, team ideas)..."
                          className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 resize-none leading-relaxed"
                          autoFocus
                        />
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={handleCancelEditNotes}
                            disabled={isSavingNote}
                            className="px-2 py-1 rounded-md text-[11px] font-medium text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSaveNotes(item)}
                            disabled={isSavingNote}
                            className="px-2.5 py-1 rounded-md text-[11px] font-bold text-white bg-brand-600 hover:bg-brand-500 flex items-center gap-1 transition-colors"
                          >
                            <Check className="w-3 h-3" />
                            <span>{isSavingNote ? 'Saving...' : 'Save Note'}</span>
                          </button>
                        </div>
                      </div>
                    ) : item.notes ? (
                      <div
                        onClick={() => handleStartEditNotes(item)}
                        className="group p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-all flex items-start justify-between gap-2"
                        title="Click to edit notes"
                      >
                        <div className="text-xs text-slate-300 italic leading-relaxed line-clamp-3">
                          "{item.notes}"
                        </div>
                        <FileEdit className="w-3.5 h-3.5 text-slate-500 group-hover:text-brand-400 flex-shrink-0 mt-0.5 transition-colors" />
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleStartEditNotes(item)}
                        className="text-[11px] text-slate-400 hover:text-brand-300 font-medium flex items-center gap-1 transition-colors py-1 px-2 rounded-lg hover:bg-slate-900/60 border border-dashed border-slate-800 hover:border-slate-700 w-full justify-center"
                      >
                        <Plus className="w-3 h-3" />
                        <span>Add Tracking Notes</span>
                      </button>
                    )}
                  </div>

                  {/* Skills tags */}
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

                {/* Card Footer: Deadline & Action Buttons */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <div className="flex flex-col gap-0.5 text-xs text-slate-400 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                      <span
                        className={cn(
                          'font-medium',
                          isExpired
                            ? 'text-rose-400'
                            : isUrgent
                            ? 'text-amber-400'
                            : 'text-slate-300'
                        )}
                      >
                        {isExpired ? 'Deadline passed' : countdownLabel}
                      </span>
                    </div>
                    {opp.deadline && (
                      <span
                        className="text-[10px] text-slate-400 truncate max-w-[170px]"
                        title={formattedIST}
                      >
                        {formattedIST}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => onEvaluate(opp.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white transition-all shadow-sm active:scale-95"
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
                      title="Open official site"
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
          <h3 className="text-lg font-bold text-white mb-1">
            {selectedStatus === 'all'
              ? 'No Bookmarked Opportunities'
              : `No Opportunities with status "${selectedStatus}"`}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {selectedStatus === 'all'
              ? 'Browse the AI Recommendations or Explore catalog to bookmark events you want to prepare for.'
              : `Change the filter tab above or update the status on your saved opportunities.`}
          </p>
        </div>
      )}
    </div>
  );
};
