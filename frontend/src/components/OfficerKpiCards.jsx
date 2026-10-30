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
 * Circular Progress Ring for Verified % (Cyan to Cobalt Gradient Stroke)
 */
function CircularProgressRing({ percentage, size = 38, strokeWidth = 3.5 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const val = Math.min(Math.max(parseFloat(percentage) || 0, 0), 100);
  const strokeDashoffset = circumference - (val / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <defs>
          <linearGradient id="kpiProgressGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#22D3EE" />
            <stop offset="100%" stopColor="#1F4BFF" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-border/40"
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#kpiProgressGrad)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
          fill="transparent"
        />
      </svg>
      <span className="absolute text-[9px] font-mono font-bold text-primary dark:text-cyan-300">
        {Math.round(val)}%
      </span>
    </div>
  );
}

/**
 * Metric Card Inner with Count-Up and Single Gold Sweep on Hover
 */
function KpiCardItem({ card, isSelected, onClick, loading }) {
  const Icon = card.icon;
  const animatedValue = useCountUp(card.value, 700);

  if (loading) {
    return (
      <div className="kpi-glass-card rounded-2xl p-5 border border-border animate-pulse flex flex-col justify-between h-36">
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
      className={`kpi-glass-card rounded-2xl p-5 border cursor-pointer group flex flex-col justify-between h-full border-t-[3px] ${
        card.topAccent
      } ${
        isSelected
          ? 'ring-2 ring-primary/40 border-primary shadow-card'
          : 'border-border shadow-card'
      }`}
    >
      {/* Single Gold Sweep on Hover */}
      <div className="gold-hover-sweep" aria-hidden="true" />

      {/* Top Row: Icon Chip & Trend / Circular Ring */}
      <div className="flex items-center justify-between relative z-10">
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

      {/* Metric Value: label, tabular-nums value, and caption */}
      <div className="flex flex-col gap-1.5 mt-3 relative z-10">
        <div className="text-[11px] font-semibold text-text-muted tracking-wide uppercase">
          {card.title}
        </div>
        <div className="text-2xl font-black text-text tracking-tight flex items-baseline gap-1 font-mono tabular-nums">
          <span>{animatedValue}</span>
          {card.unit && <span className="text-xs font-normal text-text-muted">{card.unit}</span>}
        </div>
        <p className="text-[11px] text-text-muted leading-snug truncate" title={card.subtitle}>
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
      trend: kpis?.trends?.queue || '+4 today',
      trendPositive: true,
      subtitle: 'EoA & New Inst Triage',
      icon: Inbox,
      topAccent: 'border-t-primary',
      iconBg: 'bg-primary/20 text-primary dark:text-cyan-300 border border-primary/30',
      trendBadge: 'bg-primary/10 text-primary dark:text-cobalt-light border-primary/30',
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
      iconBg: 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border border-emerald-500/30',
      trendBadge: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30',
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
      iconBg: 'bg-amber-500/20 text-amber-600 dark:text-amber-300 border border-amber-500/30',
      trendBadge: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30',
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
      iconBg: 'bg-rose-500/20 text-rose-600 dark:text-rose-300 border border-rose-500/30',
      trendBadge: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30',
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
      iconBg: 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 border border-indigo-500/30',
      trendBadge: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/30',
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
