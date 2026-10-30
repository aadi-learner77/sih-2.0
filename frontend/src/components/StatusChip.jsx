import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  ServerOff, 
  UserCog 
} from 'lucide-react';

/**
 * Statutory Status Chip Component:
 * Strictly renders EXACTLY the labels specified by the AICTE PRAMAAN-X specification:
 * - Verified
 * - Mismatch Detected
 * - Expired
 * - Verification Pending
 * - Source Unavailable
 * - Manual Review Required
 */
export default function StatusChip({ status, size = 'md' }) {
  const normStatus = (status || '').trim();

  let config = {
    label: normStatus || 'Verification Pending',
    bg: 'bg-sky-500/10 text-sky-700 dark:text-sky-300 border-sky-500/30',
    icon: RefreshCw,
    dot: 'bg-sky-500',
  };

  switch (normStatus) {
    case 'Verified':
      config = {
        label: 'Verified',
        bg: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30',
        icon: CheckCircle2,
        dot: 'bg-emerald-500',
      };
      break;

    case 'Mismatch Detected':
      config = {
        label: 'Mismatch Detected',
        bg: 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30',
        icon: AlertTriangle,
        dot: 'bg-rose-500',
      };
      break;

    case 'Expired':
      config = {
        label: 'Expired',
        bg: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30',
        icon: Clock,
        dot: 'bg-amber-500',
      };
      break;

    case 'Verification Pending':
      config = {
        label: 'Verification Pending',
        bg: 'bg-sky-500/10 text-sky-700 dark:text-sky-300 border-sky-500/30',
        icon: RefreshCw,
        dot: 'bg-sky-500',
      };
      break;

    case 'Source Unavailable':
      config = {
        label: 'Source Unavailable',
        bg: 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border-slate-500/30',
        icon: ServerOff,
        dot: 'bg-slate-400',
      };
      break;

    case 'Manual Review Required':
      config = {
        label: 'Manual Review Required',
        bg: 'bg-primary/10 text-primary dark:text-cobalt-light border-primary/30',
        icon: UserCog,
        dot: 'bg-primary',
      };
      break;

    default:
      if (/mismatch/i.test(normStatus)) {
        config = {
          label: 'Mismatch Detected',
          bg: 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30',
          icon: AlertTriangle,
          dot: 'bg-rose-500',
        };
      } else if (/expired/i.test(normStatus)) {
        config = {
          label: 'Expired',
          bg: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30',
          icon: Clock,
          dot: 'bg-amber-500',
        };
      } else if (/unavailable|timeout/i.test(normStatus)) {
        config = {
          label: 'Source Unavailable',
          bg: 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border-slate-500/30',
          icon: ServerOff,
          dot: 'bg-slate-400',
        };
      } else if (/manual|review/i.test(normStatus)) {
        config = {
          label: 'Manual Review Required',
          bg: 'bg-primary/10 text-primary dark:text-cobalt-light border-primary/30',
          icon: UserCog,
          dot: 'bg-primary',
        };
      } else if (/verif/i.test(normStatus)) {
        config = {
          label: 'Verified',
          bg: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30',
          icon: CheckCircle2,
          dot: 'bg-emerald-500',
        };
      }
      break;
  }

  const Icon = config.icon;
  const isSm = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium transition-all ${
        isSm ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      } ${config.bg}`}
    >
      <span 
        className={`status-dot w-2 h-2 rounded-full shrink-0 ${config.dot}`} 
        style={{ padding: 0, minWidth: '8px', minHeight: '8px' }}
        aria-hidden="true"
      />
      <Icon className={`shrink-0 ${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'}`} />
      <span className="font-semibold tracking-tight whitespace-nowrap">{config.label}</span>
    </span>
  );
}
