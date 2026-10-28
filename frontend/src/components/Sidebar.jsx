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
  History,
  ShieldCheck,
  UserCheck,
  Compass
} from 'lucide-react';

/**
 * Role-Aware Sidebar Navigation:
 * Dynamically adjusts available modules, badges, and permissions based on active officer role:
 * - Scrutiny Officer: Operational Triage & Evidence Lens
 * - Senior Officer: Escalations, Approvals & Impossibility Graph
 * - Central Admin: Full access + Regulation-as-Code YAML catalog
 * - Auditor: Read-only compliance trail & Audit Receipts
 * - Institution User: Application submission & self-assessment
 */
export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  counts = {},
  currentRole = 'scrutiny_officer' 
}) {
  const allNavItems = [
    {
      id: 'dashboard',
      label: 'Scrutiny Dashboard',
      icon: LayoutDashboard,
      badge: 'Live',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      desc: 'Risk-ranked triage queue',
      roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
    },
    {
      id: 'evidence-lens',
      label: 'Evidence Lens',
      icon: SearchCode,
      badge: (counts.advisoryFlags && counts.advisoryFlags > 0) ? `${counts.advisoryFlags} Findings` : null,
      badgeColor: 'bg-sky-50 text-sky-700 border-sky-200',
      desc: 'Claim-to-evidence pipeline',
      roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
    },
    {
      id: 'impossibility-engine',
      label: 'Impossibility Engine',
      icon: Network,
      badge: (counts.impossibilities && counts.impossibilities > 0) ? `${counts.impossibilities} Flags` : null,
      badgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
      desc: 'Multi-college graph conflicts',
      roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
    },
    {
      id: 'photo-radar',
      label: 'Photo Radar & Forensics',
      icon: ScanEye,
      badge: 'pHash + ELA',
      badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
      desc: 'Cross-college image reuse',
      roles: ['scrutiny_officer', 'senior_officer', 'admin'],
    },
    {
      id: 'regulations',
      label: 'Regulation-as-Code',
      icon: BookOpenCheck,
      badge: 'APH 2025',
      badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
      desc: 'Handbook rule catalog & versions',
      roles: ['senior_officer', 'admin'],
    },
    {
      id: 'inspection-planner',
      label: 'Inspection Planner',
      icon: Compass,
      badge: 'GIS Cluster',
      badgeColor: 'bg-teal-50 text-teal-700 border-teal-200',
      desc: 'District clusters & visit order',
      roles: ['scrutiny_officer', 'senior_officer', 'admin'],
    },
    {
      id: 'preflight',
      label: 'Pre-Flight Readiness',
      icon: PlaneTakeoff,
      badge: 'Simulator',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      desc: 'Self-assessment readiness',
      roles: ['scrutiny_officer', 'senior_officer', 'admin', 'institution_user'],
    },
    {
      id: 'audit-ledger',
      label: 'Audit and Receipts',
      icon: FileCheck2,
      badge: 'SHA-256',
      badgeColor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      desc: 'Timeline of receipts & tamper verification',
      roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
    },
  ];

  // Filter items visible to current role
  const visibleNavItems = allNavItems.filter((item) => item.roles.includes(currentRole));

  return (
    <aside className="w-[285px] bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 min-h-[calc(100vh-61px)] p-4 gap-6">
      <div className="flex flex-col gap-6">
        
        {/* Role Identity Header */}
        <div className="px-3.5 py-2.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
          <div className="min-w-0">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
              Active Role
            </div>
            <div className="text-xs font-bold text-slate-800 capitalize">
              {currentRole?.replace('_', ' ')}
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
        </div>

        {/* Navigation Group */}
        <div>
          <div className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase px-3 mb-2">
            Regulatory Modules
          </div>

          <div className="flex flex-col gap-2">
            {visibleNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`sidebar-tab-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-start justify-between px-3 py-2.5 rounded-xl text-left transition-all group cursor-pointer gap-2 ${
                    isActive
                      ? 'bg-sky-50 text-sky-800 font-semibold border border-sky-200/90 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                    <Icon className={`w-4 h-4 shrink-0 mt-0.5 transition-colors ${
                      isActive ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`} />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-semibold leading-snug">{item.label}</div>
                      <div className="text-[11px] text-slate-500 font-normal leading-snug mt-0.5">{item.desc}</div>
                    </div>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono font-medium shrink-0 self-start mt-0.5 ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Statutory Legal Safe-Harbor Box */}
      <div className="pt-4 border-t border-slate-200 mt-auto">
        <div className="bg-amber-50/70 rounded-xl p-4 border border-amber-200/70 text-xs space-y-2">
          <div className="flex items-center space-x-2 text-amber-900 font-bold">
            <Lock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Statutory Safeguard</span>
          </div>
          <p className="text-[11px] text-amber-800/90 leading-relaxed">
            All AI outputs represent advisory indicators for review. Autonomous determinations are prohibited; committee inquiry required.
          </p>
        </div>
      </div>
    </aside>
  );
}
