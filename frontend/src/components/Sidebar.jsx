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
  Compass,
  Clock,
  FileSearch,
  X
} from 'lucide-react';

/**
 * Role-Aware Grouped Sidebar Navigation:
 * Organized under 4 statutory sections:
 * - Scrutiny (Dashboard, Evidence Lens, Manual Review Queue, Pre-Flight Readiness)
 * - Intelligence (Document Intelligence, Photo Radar & Forensics, Impossibility Engine)
 * - Verification and Audit (Audit and Receipts, Regulation-as-Code)
 * - Planning (Inspection Planner)
 * Fully scrollable, responsive mobile drawer, and respects active officer role permissions.
 */
export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  counts = {},
  currentRole = 'scrutiny_officer',
  isOpen = false,
  onClose = () => {}
}) {
  const navSections = [
    {
      title: 'Scrutiny',
      items: [
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
          id: 'manual-review-queue',
          label: 'Manual Review Queue',
          icon: Clock,
          badge: (counts.manualReview && counts.manualReview > 0) ? `${counts.manualReview} Cases` : 'Fallback',
          badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
          desc: 'Authoritative fallback queue',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
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
      ]
    },
    {
      title: 'Intelligence',
      items: [
        {
          id: 'document-intelligence',
          label: 'Document Intelligence',
          icon: FileSearch,
          badge: 'OCR + Schema',
          badgeColor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
          desc: 'Field extraction & OCR bbox',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'photo-radar',
          label: 'Photo Radar & Forensics',
          icon: ScanEye,
          badge: 'pHash + ELA',
          badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
          desc: 'Radar, Forensics & Reality',
          roles: ['scrutiny_officer', 'senior_officer', 'admin'],
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
      ]
    },
    {
      title: 'Verification and Audit',
      items: [
        {
          id: 'audit-ledger',
          label: 'Audit and Receipts',
          icon: FileCheck2,
          badge: 'SHA-256',
          badgeColor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
          desc: 'Timeline of receipts & tamper check',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
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
      ]
    },
    {
      title: 'Planning',
      items: [
        {
          id: 'inspection-planner',
          label: 'Inspection Planner',
          icon: Compass,
          badge: 'GIS Cluster',
          badgeColor: 'bg-teal-50 text-teal-700 border-teal-200',
          desc: 'District clusters & visit order',
          roles: ['scrutiny_officer', 'senior_officer', 'admin'],
        },
      ]
    }
  ];

  const handleItemClick = (id) => {
    setActiveTab(id);
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 lg:hidden transition-opacity animate-fadeIn" 
          onClick={onClose} 
          aria-hidden="true"
        />
      )}

      <aside className={`
        fixed inset-y-0 left-0 z-50 w-[280px] max-w-[85vw] bg-white border-r border-slate-200 
        flex flex-col justify-between h-full overflow-y-auto p-4 gap-6 scrollbar-thin shadow-2xl transition-transform duration-250 ease-in-out
        lg:static lg:z-auto lg:w-[280px] lg:shadow-none lg:translate-x-0 lg:flex
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col gap-5">
          
          {/* Role Identity Header */}
          <div className="px-3.5 py-2.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between shrink-0">
            <div className="min-w-0">
              <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                Active Role
              </div>
              <div className="text-xs font-bold text-slate-800 capitalize truncate">
                {currentRole?.replace('_', ' ')}
              </div>
            </div>
            <div className="flex items-center space-x-2 shrink-0">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
              <button
                type="button"
                onClick={onClose}
                className="lg:hidden p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition cursor-pointer"
                aria-label="Close sidebar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Grouped Navigation Sections */}
          {navSections.map((section) => {
            const permittedItems = section.items.filter(item => item.roles.includes(currentRole));
            if (permittedItems.length === 0) return null;

            return (
              <div key={section.title} className="space-y-1.5">
                <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase px-3 mb-1">
                  {section.title}
                </div>

                <div className="flex flex-col gap-1">
                  {permittedItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        id={`sidebar-tab-${item.id}`}
                        onClick={() => handleItemClick(item.id)}
                      className={`w-full flex items-start justify-between px-3 py-2 rounded-xl text-left transition-all group cursor-pointer gap-2 ${
                        isActive
                          ? 'bg-sky-50 text-sky-800 font-semibold border border-sky-200/90 shadow-2xs'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                        <Icon className={`w-4 h-4 shrink-0 mt-0.5 transition-colors ${
                          isActive ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600'
                        }`} />
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-semibold leading-snug">{item.label}</div>
                          <div className="text-[10px] text-slate-500 font-normal leading-snug truncate mt-0.5">{item.desc}</div>
                        </div>
                      </div>
                      {item.badge && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-mono font-medium shrink-0 self-start mt-0.5 ${item.badgeColor}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Statutory Legal Safe-Harbor Box */}
      <div className="pt-4 border-t border-slate-200 shrink-0 mt-4">
        <div className="bg-amber-50/70 rounded-xl p-3 border border-amber-200/70 text-xs space-y-1.5">
          <div className="flex items-center space-x-1.5 text-amber-900 font-bold">
            <Lock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="text-[11px]">Statutory Safeguard</span>
          </div>
          <p className="text-[10px] text-amber-800/90 leading-relaxed">
            All AI outputs represent advisory indicators for review. Autonomous determinations are prohibited; committee inquiry required.
          </p>
        </div>
      </div>
    </aside>
    </>
  );
}

