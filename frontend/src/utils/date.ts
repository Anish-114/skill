/**
 * Formats an ISO 8601 UTC date string into Indian Standard Time (IST):
 * Example: "10 Nov 2026, 11:59 PM IST"
 */
export function formatToIST(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Open / Ongoing';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return 'Open / Ongoing';

  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Kolkata',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };

  const formatted = new Intl.DateTimeFormat('en-IN', options).format(d);
  // Ensure AM/PM is capitalized
  const formattedUpper = formatted.replace(/\b(am|pm)\b/i, (match) => match.toUpperCase());
  return `${formattedUpper} IST`;
}

/**
 * Calculates remaining days/countdown from now until deadline.
 */
export function getDeadlineCountdown(dateStr: string | null | undefined): {
  diffDays: number | null;
  label: string;
  isUrgent: boolean;
} {
  if (!dateStr) {
    return { diffDays: null, label: 'Open / Ongoing', isUrgent: false };
  }
  const deadline = new Date(dateStr);
  if (isNaN(deadline.getTime())) {
    return { diffDays: null, label: 'Open / Ongoing', isUrgent: false };
  }

  const now = new Date();
  const diffMs = deadline.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffMs <= 0) {
    return { diffDays: 0, label: 'Deadline passed', isUrgent: false };
  }
  if (diffDays <= 1) {
    const diffHours = Math.max(1, Math.round(diffMs / (1000 * 60 * 60)));
    return { diffDays, label: `${diffHours}h left`, isUrgent: true };
  }
  return {
    diffDays,
    label: `${diffDays}d left`,
    isUrgent: diffDays <= 7,
  };
}
