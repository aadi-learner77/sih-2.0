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
 * 
 * Clean, modern glassmorphism design: NO marker-highlighter backgrounds.
 * High-contrast text (black in light mode, white in dark mode), 
 * subtle neutral surface, and a precise status dot.
 */
export default function StatusChip({ status, size = 'md' }) {
  const normStatus = (status || '').trim();

  let config = {
    label: normStatus || 'Verification Pending',
    icon: RefreshCw,
    dot: 'bg-sky-500',
  };

  switch (normStatus) {
    case 'Verified':
      config = {
        label: 'Verified',
        icon: CheckCircle2,
        dot: 'bg-emerald-500',
      };
      break;

    case 'Mismatch Detected':
      config = {
        label: 'Mismatch Detected',
        icon: AlertTriangle,
        dot: 'bg-rose-500',
      };
      break;

    case 'Expired':
      config = {
        label: 'Expired',
        icon: Clock,
        dot: 'bg-amber-500',
      };
      break;

    case 'Verification Pending':
      config = {
        label: 'Verification Pending',
        icon: RefreshCw,
        dot: 'bg-sky-500',
      };
      break;

    case 'Source Unavailable':
      config = {
        label: 'Source Unavailable',
        icon: ServerOff,
        dot: 'bg-slate-400',
      };
      break;

    case 'Manual Review Required':
      config = {
        label: 'Manual Review Required',
        icon: UserCog,
        dot: 'bg-primary',
      };
      break;

    default:
      if (/mismatch/i.test(normStatus)) {
        config = {
          label: 'Mismatch Detected',
          icon: AlertTriangle,
          dot: 'bg-rose-500',
        };
      } else if (/expired/i.test(normStatus)) {
        config = {
          label: 'Expired',
          icon: Clock,
          dot: 'bg-amber-500',
        };
      } else if (/unavailable|timeout/i.test(normStatus)) {
        config = {
          label: 'Source Unavailable',
          icon: ServerOff,
          dot: 'bg-slate-400',
        };
      } else if (/manual|review/i.test(normStatus)) {
        config = {
          label: 'Manual Review Required',
          icon: UserCog,
          dot: 'bg-primary',
        };
      } else if (/verif/i.test(normStatus)) {
        config = {
          label: 'Verified',
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
      className={`inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-2/90 backdrop-blur-md text-text font-medium shadow-2xs transition-all ${
        isSm ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      }`}
    >
      <span 
        className={`status-dot w-2 h-2 rounded-full shrink-0 ${config.dot}`} 
        style={{ padding: 0, minWidth: '8px', minHeight: '8px' }}
        aria-hidden="true"
      />
      <Icon className={`shrink-0 text-text-muted ${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'}`} />
      <span className="font-semibold tracking-tight whitespace-nowrap text-text">{config.label}</span>
    </span>
  );
}
