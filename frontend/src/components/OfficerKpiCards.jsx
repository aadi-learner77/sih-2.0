import React from 'react';
import { 
  Inbox, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  ShieldAlert
} from 'lucide-react';

/**
 * KPI Cards Component for Officer Dashboard:
 * Visualizes the 5 core operational metrics:
 * 1. Applications in queue
 * 2. Verified %
 * 3. Expired
 * 4. Mismatches
 * 5. Pending verification
 */
export default function OfficerKpiCards({ 
  kpis,
  selectedStatusFilter,
  onStatusFilterClick 
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
      color: 'sky',
      accentBg: 'bg-sky-50 text-sky-700 border-sky-200/80',
      iconBg: 'bg-sky-600 text-white shadow-sky-500/20',
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
      color: 'emerald',
      accentBg: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
      iconBg: 'bg-emerald-600 text-white shadow-emerald-500/20',
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
      color: 'amber',
      accentBg: 'bg-amber-50 text-amber-800 border-amber-200/80',
      iconBg: 'bg-amber-600 text-white shadow-amber-500/20',
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
      color: 'rose',
      accentBg: 'bg-rose-50 text-rose-800 border-rose-200/80',
      iconBg: 'bg-rose-600 text-white shadow-rose-500/20',
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
      color: 'indigo',
      accentBg: 'bg-indigo-50 text-indigo-800 border-indigo-200/80',
      iconBg: 'bg-indigo-600 text-white shadow-indigo-500/20',
      filterTarget: 'Verification Pending',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-stretch">
      {cards.map((card) => {
        const Icon = card.icon;
        const isSelected = selectedStatusFilter === card.filterTarget;

        return (
          <div
            key={card.id}
            onClick={() => onStatusFilterClick && card.filterTarget && onStatusFilterClick(card.filterTarget)}
            className={`bg-white rounded-2xl p-6 border transition-all duration-200 cursor-pointer group hover:-translate-y-0.5 hover:shadow-md relative overflow-hidden flex flex-col justify-between h-full ${
              isSelected
                ? 'border-sky-500 ring-2 ring-sky-500/20 shadow-sm'
                : 'border-slate-200/90 hover:border-slate-300 shadow-xs'
            }`}
          >
            {/* Top Row: Icon & Trend */}
            <div className="flex items-center justify-between">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-xs transition-transform group-hover:scale-105 ${card.iconBg}`}>
                <Icon className="w-5 h-5 shrink-0" />
              </div>
              <span className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border flex items-center gap-1.5 ${card.accentBg}`}>
                {card.trendPositive === true && <TrendingUp className="w-2.5 h-2.5 shrink-0" />}
                {card.trendPositive === false && <ShieldAlert className="w-2.5 h-2.5 shrink-0" />}
                <span>{card.trend}</span>
              </span>
            </div>

            {/* Metric Value: icon row, label, value, and caption separated by 8px */}
            <div className="flex flex-col gap-2 mt-2">
              <div className="text-[11px] font-semibold text-slate-500 tracking-wide uppercase">
                {card.title}
              </div>
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span>{card.value}</span>
                {card.unit && <span className="text-xs font-normal text-slate-500">{card.unit}</span>}
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                {card.subtitle}
              </p>
            </div>

            {/* Bottom Glow Bar */}
            <div className={`h-1 w-full absolute bottom-0 left-0 transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} ${
              card.color === 'emerald' ? 'bg-emerald-500' :
              card.color === 'rose' ? 'bg-rose-500' :
              card.color === 'amber' ? 'bg-amber-500' :
              card.color === 'indigo' ? 'bg-indigo-500' : 'bg-sky-500'
            }`} />
          </div>
        );
      })}
    </div>
  );
}
