import React, { useState, useEffect } from 'react';
import { 
  Inbox, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RefreshCw, 
  TrendingUp, 
  ShieldAlert
} from 'lucide-react';

/**
 * Animated Count-Up Hook (700ms ease-out)
 */
function useCountUp(target, duration = 700) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = 0;
    // Check if percentage string like '72.5%'
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
      // Ease out cubic
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
 * Circular Progress Ring for Verified %
 */
function CircularProgressRing({ percentage, size = 36, strokeWidth = 3 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const val = Math.min(Math.max(parseFloat(percentage) || 0, 0), 100);
  const strokeDashoffset = circumference - (val / 100) * circumference;

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
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-emerald-500 transition-all duration-700 ease-out"
          fill="transparent"
        />
      </svg>
      <span className="absolute text-[9px] font-mono font-bold text-emerald-600 dark:text-emerald-400">
        {Math.round(val)}%
      </span>
    </div>
  );
}

/**
 * Metric Card Inner with Count-Up
 */
function KpiCardItem({ card, isSelected, onClick, loading }) {
  const Icon = card.icon;
  const animatedValue = useCountUp(card.value, 700);

  if (loading) {
    return (
      <div className="bg-surface rounded-2xl p-5 border border-border animate-pulse flex flex-col justify-between h-36">
        <div className="flex justify-between items-center">
          <div className="w-9 h-9 rounded-xl bg-surface-2" />
          <div className="w-16 h-5 rounded-full bg-surface-2" />
        </div>
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
      className={`bg-surface rounded-2xl p-5 border transition-all duration-200 cursor-pointer group hover:-translate-y-1 hover:shadow-card-hover relative overflow-hidden flex flex-col justify-between h-full border-t-2 ${
        card.topAccent
      } ${
        isSelected
          ? 'border-primary ring-2 ring-primary/20 shadow-card'
          : 'border-border shadow-card'
      }`}
    >
      {/* Top Row: Icon Chip & Trend / Ring */}
      <div className="flex items-center justify-between">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center transition-transform group-hover:scale-105 shadow-xs ${card.iconBg}`}>
          <Icon className="w-4 h-4 shrink-0" />
        </div>

        {card.id === 'verified' ? (
          <CircularProgressRing percentage={card.value} />
        ) : (
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1 shrink-0 ${card.trendBadge}`}>
            {card.trendPositive === true && <TrendingUp className="w-2.5 h-2.5 shrink-0" />}
            {card.trendPositive === false && <ShieldAlert className="w-2.5 h-2.5 shrink-0" />}
            <span>{card.trend}</span>
          </span>
        )}
      </div>

      {/* Metric Value: label, value, and caption */}
      <div className="flex flex-col gap-1.5 mt-3">
        <div className="text-[11px] font-semibold text-text-muted tracking-wide uppercase">
          {card.title}
        </div>
        <div className="text-2xl font-black text-text tracking-tight flex items-baseline gap-1 font-mono">
          <span>{animatedValue}</span>
          {card.unit && <span className="text-xs font-normal text-text-muted">{card.unit}</span>}
        </div>
        <p className="text-[11px] text-text-muted leading-snug truncate" title={card.subtitle}>
          {card.subtitle}
        </p>
      </div>

      {/* Bottom subtle accent line on hover */}
      <div className={`h-0.5 w-full absolute bottom-0 left-0 transition-opacity ${
        isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
      } ${card.bottomLine}`} />
    </div>
  );
}

/**
 * KPI Cards Component for Officer Dashboard:
 * Visualizes the 5 core operational metrics with:
 * - Top accent line
 * - Icon chips
 * - 700ms count-up animation
 * - Circular progress ring on Verified %
 * - Hover lift
 * - Skeleton loaders
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
      trend: kpis?.trends?.queue || '+4 today',
      trendPositive: true,
      subtitle: 'EoA & New Inst Triage',
      icon: Inbox,
      topAccent: 'border-t-primary',
      bottomLine: 'bg-primary',
      iconBg: 'bg-primary text-white shadow-primary/20',
      trendBadge: 'bg-primary/10 text-primary dark:text-cobalt-light border-primary/20',
      filterTarget: 'ALL',
    },
    {
      id: 'verified',
      title: 'Verified %',
      value: kpis?.verifiedPercentage !== undefined ? `${kpis.verifiedPercentage}%` : '72.5%',
      unit: '',
      trend: kpis?.trends?.verified || '+5.2% this week',
      trendPositive: true,
      subtitle: 'Authoritative Gateway Checked',
      icon: CheckCircle2,
      topAccent: 'border-t-emerald-500',
      bottomLine: 'bg-emerald-500',
      iconBg: 'bg-emerald-600 text-white shadow-emerald-500/20',
      trendBadge: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20',
      filterTarget: 'Verified',
    },
    {
      id: 'expired',
      title: 'Expired Documents',
      value: kpis?.expiredCount ?? 9,
      unit: '',
      trend: kpis?.trends?.expired || '3 urgent renewals',
      trendPositive: false,
      subtitle: 'Fire, Land & PWD NOCs',
      icon: Clock,
      topAccent: 'border-t-amber-500',
      bottomLine: 'bg-amber-500',
      iconBg: 'bg-amber-600 text-white shadow-amber-500/20',
      trendBadge: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20',
      filterTarget: 'Expired',
    },
    {
      id: 'mismatches',
      title: 'Mismatches Detected',
      value: kpis?.mismatchCount ?? 6,
      unit: '',
      trend: kpis?.trends?.mismatches || '2 high critical',
      trendPositive: false,
      subtitle: 'Bhoomi / AISHE / CBDT',
      icon: AlertTriangle,
      topAccent: 'border-t-rose-500',
      bottomLine: 'bg-rose-500',
      iconBg: 'bg-rose-600 text-white shadow-rose-500/20',
      trendBadge: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20',
      filterTarget: 'Mismatch Detected',
    },
    {
      id: 'pending',
      title: 'Pending Verification',
      value: kpis?.pendingVerificationCount ?? 14,
      unit: '',
      trend: kpis?.trends?.pending || 'Awaiting state gateway',
      trendPositive: null,
      subtitle: 'Queued with Backoff Retry',
      icon: RefreshCw,
      topAccent: 'border-t-indigo-500',
      bottomLine: 'bg-indigo-500',
      iconBg: 'bg-indigo-600 text-white shadow-indigo-500/20',
      trendBadge: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/20',
      filterTarget: 'Verification Pending',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 items-stretch">
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
