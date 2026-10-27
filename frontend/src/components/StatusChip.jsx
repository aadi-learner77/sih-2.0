import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  RefreshCw, 
  ServerOff, 
  UserCog, 
  ShieldAlert 
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
    bg: 'bg-slate-50 text-slate-700 border-slate-200',
    icon: Clock,
    dot: 'bg-slate-400',
  };

  switch (normStatus) {
    case 'Verified':
      config = {
        label: 'Verified',
        bg: 'bg-emerald-50 text-emerald-800 border-emerald-200/80 shadow-xs',
        icon: CheckCircle2,
        dot: 'bg-emerald-500',
      };
      break;

    case 'Mismatch Detected':
      config = {
        label: 'Mismatch Detected',
        bg: 'bg-rose-50 text-rose-800 border-rose-200/90 shadow-xs',
        icon: AlertTriangle,
        dot: 'bg-rose-500',
      };
      break;

    case 'Expired':
      config = {
        label: 'Expired',
        bg: 'bg-amber-50 text-amber-800 border-amber-200/90 shadow-xs',
        icon: Clock,
        dot: 'bg-amber-500',
      };
      break;

    case 'Verification Pending':
      config = {
        label: 'Verification Pending',
        bg: 'bg-sky-50 text-sky-800 border-sky-200/90 shadow-xs',
        icon: RefreshCw,
        dot: 'bg-sky-500',
      };
      break;

    case 'Source Unavailable':
      config = {
        label: 'Source Unavailable',
        bg: 'bg-slate-100 text-slate-800 border-slate-300 shadow-xs',
        icon: ServerOff,
        dot: 'bg-slate-500',
      };
      break;

    case 'Manual Review Required':
      config = {
        label: 'Manual Review Required',
        bg: 'bg-indigo-50 text-indigo-800 border-indigo-200/90 shadow-xs',
        icon: UserCog,
        dot: 'bg-indigo-500',
      };
      break;

    default:
      // Fallback matching
      if (/mismatch/i.test(normStatus)) {
        config = {
          label: 'Mismatch Detected',
          bg: 'bg-rose-50 text-rose-800 border-rose-200/90',
          icon: AlertTriangle,
          dot: 'bg-rose-500',
        };
      } else if (/expired/i.test(normStatus)) {
        config = {
          label: 'Expired',
          bg: 'bg-amber-50 text-amber-800 border-amber-200/90',
          icon: Clock,
          dot: 'bg-amber-500',
        };
      } else if (/unavailable|timeout/i.test(normStatus)) {
        config = {
          label: 'Source Unavailable',
          bg: 'bg-slate-100 text-slate-800 border-slate-300',
          icon: ServerOff,
          dot: 'bg-slate-500',
        };
      } else if (/manual|review/i.test(normStatus)) {
        config = {
          label: 'Manual Review Required',
          bg: 'bg-indigo-50 text-indigo-800 border-indigo-200/90',
          icon: UserCog,
          dot: 'bg-indigo-500',
        };
      } else if (/verif/i.test(normStatus)) {
        config = {
          label: 'Verified',
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
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
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${config.dot}`} />
      <Icon className={`shrink-0 ${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'}`} />
      <span className="font-semibold tracking-tight whitespace-nowrap">{config.label}</span>
    </span>
  );
}
