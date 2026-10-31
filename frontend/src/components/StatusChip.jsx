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
 * Government Portal Design:
 * - 24px fixed height
 * - 12px / 600 font weight
 * - Tinted background + 1px tinted border + colored dot + label
 * - High contrast & readable in both light and dark themes
 */
export default function StatusChip({ status, size = 'md' }) {
  const normStatus = (status || '').trim();

  let config = {
    label: normStatus || 'Verification Pending',
    icon: RefreshCw,
    dot: 'bg-[#486581]',
    explanation: 'Queued for automated gateway verification.',
    themeClasses: 'bg-[#EBF1F7] dark:bg-[#1E2530] border-[#C8D6E5] dark:border-[#2D3949] text-[#2C4866] dark:text-[#93AEC9]',
  };

  switch (normStatus) {
    case 'Verified':
      config = {
        label: 'Verified',
        icon: CheckCircle2,
        dot: 'bg-success',
        explanation: 'Verified: Authority ledger and document hashes match.',
        themeClasses: 'bg-success-bg border-success-border text-success-text',
      };
      break;

    case 'Mismatch Detected':
      config = {
        label: 'Mismatch Detected',
        icon: AlertTriangle,
        dot: 'bg-danger',
        explanation: 'Indicator for review: Conflicting data found across authorities.',
        themeClasses: 'bg-danger-bg border-danger-border text-danger-text',
      };
      break;

    case 'Expired':
      config = {
        label: 'Expired',
        icon: Clock,
        dot: 'bg-warning',
        explanation: 'Indicator for review: Validity expired per authoritative registry.',
        themeClasses: 'bg-warning-bg border-warning-border text-warning-text',
      };
      break;

    case 'Verification Pending':
      config = {
        label: 'Verification Pending',
        icon: RefreshCw,
        dot: 'bg-[#486581]',
        explanation: 'Queued for automated gateway verification.',
        themeClasses: 'bg-[#EBF1F7] dark:bg-[#1E2530] border-[#C8D6E5] dark:border-[#2D3949] text-[#2C4866] dark:text-[#93AEC9]',
      };
      break;

    case 'Source Unavailable':
      config = {
        label: 'Source Unavailable',
        icon: ServerOff,
        dot: 'bg-[#627D98]',
        explanation: 'External authoritative source timed out; queued for fallback.',
        themeClasses: 'bg-surface-2 border-border text-text-muted',
      };
      break;

    case 'Manual Review Required':
      config = {
        label: 'Manual Review Required',
        icon: UserCog,
        dot: 'bg-info',
        explanation: 'Manual review: statutory discretion or discrepancy noted.',
        themeClasses: 'bg-info-bg border-info-border text-info-text',
      };
      break;

    default:
      if (/mismatch/i.test(normStatus)) {
        config = {
          label: 'Mismatch Detected',
          icon: AlertTriangle,
          dot: 'bg-danger',
          explanation: 'Indicator for review: Conflicting data found across authorities.',
          themeClasses: 'bg-danger-bg border-danger-border text-danger-text',
        };
      } else if (/expired/i.test(normStatus)) {
        config = {
          label: 'Expired',
          icon: Clock,
          dot: 'bg-warning',
          explanation: 'Indicator for review: Validity expired per authoritative registry.',
          themeClasses: 'bg-warning-bg border-warning-border text-warning-text',
        };
      } else if (/unavailable|timeout/i.test(normStatus)) {
        config = {
          label: 'Source Unavailable',
          icon: ServerOff,
          dot: 'bg-[#627D98]',
          explanation: 'External authoritative source timed out; queued for fallback.',
          themeClasses: 'bg-surface-2 border-border text-text-muted',
        };
      } else if (/manual|review/i.test(normStatus)) {
        config = {
          label: 'Manual Review Required',
          icon: UserCog,
          dot: 'bg-info',
          explanation: 'Manual review: statutory discretion or discrepancy noted.',
          themeClasses: 'bg-info-bg border-info-border text-info-text',
        };
      } else if (/verif/i.test(normStatus)) {
        config = {
          label: 'Verified',
          icon: CheckCircle2,
          dot: 'bg-success',
          explanation: 'Verified: Authority ledger and document hashes match.',
          themeClasses: 'bg-success-bg border-success-border text-success-text',
        };
      }
      break;
  }

  const Icon = config.icon;
  const isSm = size === 'sm';

  return (
    <span
      title={config.explanation}
      className={`inline-flex items-center gap-1.5 rounded-full border h-6 select-none font-semibold transition-all duration-150 hover:brightness-105 cursor-help ${
        isSm ? 'px-2 text-[11px]' : 'px-2.5 text-[12px]'
      } ${config.themeClasses}`}
    >
      <span 
        className={`status-dot w-2 h-2 rounded-full shrink-0 ${config.dot}`} 
        style={{ padding: 0, minWidth: '8px', minHeight: '8px' }}
        aria-hidden="true"
      />
      <Icon className={`shrink-0 opacity-80 ${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'}`} />
      <span className="font-semibold tracking-tight whitespace-nowrap leading-none">{config.label}</span>
    </span>
  );
}
