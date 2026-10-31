import React, { useState, useEffect } from 'react';
import { 
  Inbox, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RefreshCw 
} from 'lucide-react';

/**
 * Animated Count-Up Hook (700ms ease-out)
 */
function useCountUp(target, duration = 700) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = 0;
    const isPercent = typeof target === 'string' && target.endsWith('%');
    const numericTarget = isPercent ? parseFloat(target) : Number(target);

    if (isNaN(numericTarget)) {
      setDisplayValue(target);
      return;
    }

    let startTime = null;
    let animationFrame;

    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (numericTarget - start) * eased;

      if (isPercent) {
        setDisplayValue(`${current.toFixed(1)}%`);
      } else {
        setDisplayValue(Math.round(current));
      }

      if (progress < 1) {
        animationFrame = requestAnimationFrame(step);
      }
    };

    animationFrame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animationFrame);
  }, [target, duration]);

  return displayValue;
}

/**
 * Circular Progress Ring for Verified % (Clean, Legible Text)
 */
function CircularProgressRing({ percentage, size = 36, strokeWidth = 3 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const val = Math.min(Math.max(parseFloat(percentage) || 0, 0), 100);
  const targetOffset = circumference - (val / 100) * circumference;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(targetOffset);
    }, 50);
    return () => clearTimeout(timer);
  }, [targetOffset]);

  return (
    <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-border"
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-success transition-all duration-700 ease-out"
          fill="transparent"
        />
      </svg>
      <span className="absolute text-[10px] font-mono font-bold text-text">
        {Math.round(val)}%
      </span>
    </div>
  );
}

/**
 * Government Portal Metric Card:
 * - Glass surface, soft spotlight tracking cursor via --mx/--my
 * - 2px hover lift, gentle 1.06 icon scale
 * - :focus-visible only (never :focus on mouse click)
 */
function KpiCardItem({ card, isSelected, onClick, loading }) {
  const Icon = card.icon;
  const animatedValue = useCountUp(card.value, 700);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty('--mx', `${e.clientX - rect.left}px`);
    e.currentTarget.style.setProperty('--my', `${e.clientY - rect.top}px`);
  };

  if (loading) {
    return (
      <div className="bg-surface rounded-lg p-5 border border-border animate-pulse flex flex-col justify-between h-36">
        <div className="w-8 h-8 rounded-md bg-surface-2" />
        <div className="space-y-2 mt-4">
          <div className="w-24 h-3 bg-surface-2 rounded" />
          <div className="w-16 h-7 bg-surface-2 rounded" />
          <div className="w-32 h-2.5 bg-surface-2 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } }}
      onMouseMove={handleMouseMove}
      className={`kpi-glass-card rounded-lg p-4 sm:p-5 border cursor-pointer group flex flex-col justify-between h-full select-none relative overflow-hidden outline-none focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 transition-all duration-200 ${
        isSelected
          ? 'border-primary bg-primary/5 shadow-xs'
          : 'border-border hover:border-border-strong shadow-card'
      }`}
    >
      {/* Top Row: Icon in a Tinted Square + Verified Progress Ring (if verified card) */}
      <div className="flex items-center justify-between relative z-10">
        <div className={`w-8 h-8 rounded-md flex items-center justify-center border transition-transform duration-200 group-hover:scale-[1.06] ${card.iconSquare}`}>
          <Icon className="w-4 h-4 shrink-0" />
        </div>

        {card.id === 'verified' && (
          <CircularProgressRing percentage={card.value} />
        )}
      </div>

      {/* Metric Content */}
      <div className="flex flex-col gap-1 mt-3 relative z-10">
        <div className="text-sm font-medium text-text-muted">
          {card.title}
        </div>
        <div className="text-[28px] leading-tight font-bold text-text tracking-tight font-sans tabular-nums">
          {animatedValue}{card.unit}
        </div>
        <p className="text-xs text-text-muted truncate mt-0.5" title={card.subtitle}>
          {card.subtitle}
        </p>
      </div>
    </div>
  );
}

/**
 * KPI Cards Component for Officer Dashboard
 */
export default function OfficerKpiCards({ 
  kpis,
  selectedStatusFilter,
  onStatusFilterClick,
  loading = false
}) {
  const cards = [
    {
      id: 'queue',
      title: 'Applications in Queue',
      value: kpis?.applicationsInQueue ?? 48,
      unit: '',
      subtitle: 'EoA & New Inst Triage',
      icon: Inbox,
      iconSquare: 'bg-primary/10 border-primary/20 text-primary',
      filterTarget: 'ALL',
    },
    {
      id: 'verified',
      title: 'Verified %',
      value: kpis?.verifiedPercentage !== undefined ? `${kpis.verifiedPercentage}%` : '72.5%',
      unit: '',
      subtitle: 'Authoritative Gateway Checked',
      icon: CheckCircle2,
      iconSquare: 'bg-success-bg border-success-border text-success-text',
      filterTarget: 'Verified',
    },
    {
      id: 'expired',
      title: 'Expired Documents',
      value: kpis?.expiredCount ?? 9,
      unit: '',
      subtitle: 'Fire, Land & PWD NOCs',
      icon: Clock,
      iconSquare: 'bg-warning-bg border-warning-border text-warning-text',
      filterTarget: 'Expired',
    },
    {
      id: 'mismatches',
      title: 'Mismatches Detected',
      value: kpis?.mismatchCount ?? 6,
      unit: '',
      subtitle: 'Bhoomi / AISHE / CBDT',
      icon: AlertTriangle,
      iconSquare: 'bg-danger-bg border-danger-border text-danger-text',
      filterTarget: 'Mismatch Detected',
    },
    {
      id: 'pending',
      title: 'Pending Verification',
      value: kpis?.pendingVerificationCount ?? 14,
      unit: '',
      subtitle: 'Queued with Backoff Retry',
      icon: RefreshCw,
      iconSquare: 'bg-info-bg border-info-border text-info-text',
      filterTarget: 'Verification Pending',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 sm:gap-4 items-stretch">
      {cards.map((card) => {
        const isSelected = selectedStatusFilter === card.filterTarget;

        return (
          <KpiCardItem
            key={card.id}
            card={card}
            isSelected={isSelected}
            loading={loading}
            onClick={() => onStatusFilterClick && card.filterTarget && onStatusFilterClick(card.filterTarget)}
          />
        );
      })}
    </div>
  );
}
