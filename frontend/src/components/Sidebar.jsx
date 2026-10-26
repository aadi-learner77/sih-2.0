import React from 'react';
import { 
  LayoutDashboard, 
  SearchCode, 
  Network, 
  ScanEye, 
  BookOpenCheck, 
  PlaneTakeoff, 
  FileCheck2,
  Lock,
  Layers
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, counts = {} }) {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Scrutiny Dashboard',
      icon: LayoutDashboard,
      badge: null,
      desc: 'Applications overview'
    },
    {
      id: 'evidence-lens',
      label: 'Evidence Lens',
      icon: SearchCode,
      badge: 'Flagship',
      badgeColor: 'bg-sky-50 text-sky-700 border-sky-200',
      desc: 'Claim-to-Evidence pipeline'
    },
    {
      id: 'impossibility-engine',
      label: 'Impossibility Engine',
      icon: Network,
      badge: counts.impossibilities ? `${counts.impossibilities} Flags` : '2 Flags',
      badgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
      desc: 'Multi-college graph conflicts'
    },
    {
      id: 'photo-radar',
      label: 'Photo Radar & Forensics',
      icon: ScanEye,
      badge: '98.4% Match',
      badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
      desc: 'Perceptual hash & ELA lab'
    },
    {
      id: 'regulations',
      label: 'Regulation-as-Code',
      icon: BookOpenCheck,
      badge: 'APH 2025',
      badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
      desc: 'Configurable YAML clauses'
    },
    {
      id: 'preflight',
      label: 'Pre-Flight Readiness',
      icon: PlaneTakeoff,
      badge: '72.4/100',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      desc: 'Self-assessment simulator'
    },
    {
      id: 'audit-ledger',
      label: 'Audit Ledger & Receipts',
      icon: FileCheck2,
      badge: 'SHA-256',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      desc: 'Tamper-evident hash chain'
    }
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 min-h-[calc(100vh-61px)]">
      <div className="p-4 space-y-1">
        <div className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase px-3 py-2">
          Regulatory Scrutiny
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-all group ${
                isActive
                  ? 'bg-sky-50 text-sky-700 font-semibold border border-sky-200 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                <div className="truncate">
                  <div className="text-xs truncate">{item.label}</div>
                  <div className="text-[10px] text-slate-500 font-normal truncate">{item.desc}</div>
                </div>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono font-medium shrink-0 ml-2 ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-auto p-4 border-t border-slate-200">
        <div className="bg-amber-50/70 rounded-xl p-3 border border-amber-200/70 text-xs space-y-1.5">
          <div className="flex items-center space-x-2 text-amber-900 font-medium">
            <Lock className="w-3.5 h-3.5 text-amber-600" />
            <span>Statutory Safeguard</span>
          </div>
          <p className="text-[11px] text-amber-800/90 leading-relaxed">
            All AI decision indicators require explicit scrutiny officer sign-off before formal order generation.
          </p>
        </div>
      </div>
    </aside>
  );
}
