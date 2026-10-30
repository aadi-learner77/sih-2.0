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
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

/**
 * Role-Aware Grouped Sidebar Navigation:
 * - Desktop: 264px expanded <-> 72px icon rail
 * - Responsive mobile drawer (<1024px)
 * - Persisted collapse state
 * - One-row items with tooltips
 * - Active accent bar with soft cobalt tint
 */
export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  counts = {},
  currentRole = 'scrutiny_officer',
  isOpen = false,
  onClose = () => {},
  isCollapsed = false,
  onToggleCollapse = () => {}
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
          badgeColor: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
          desc: 'Risk-ranked triage queue',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
        },
        {
          id: 'evidence-lens',
          label: 'Evidence Lens',
          icon: SearchCode,
          badge: (counts.advisoryFlags && counts.advisoryFlags > 0) ? `${counts.advisoryFlags}` : null,
          badgeColor: 'bg-primary/10 text-primary dark:text-cobalt-light border-primary/30',
          desc: 'Claim-to-evidence pipeline',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'manual-review-queue',
          label: 'Manual Review Queue',
          icon: Clock,
          badge: (counts.manualReview && counts.manualReview > 0) ? `${counts.manualReview}` : null,
          badgeColor: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30',
          desc: 'Authoritative fallback queue',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'preflight',
          label: 'Pre-Flight Readiness',
          icon: PlaneTakeoff,
          badge: 'Sim',
          badgeColor: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
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
          badge: 'OCR',
          badgeColor: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30',
          desc: 'Field extraction & OCR bbox',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'photo-radar',
          label: 'Photo Radar & Forensics',
          icon: ScanEye,
          badge: 'ELA',
          badgeColor: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30',
          desc: 'Radar, Forensics & Reality',
          roles: ['scrutiny_officer', 'senior_officer', 'admin'],
        },
        {
          id: 'impossibility-engine',
          label: 'Impossibility Engine',
          icon: Network,
          badge: (counts.impossibilities && counts.impossibilities > 0) ? `${counts.impossibilities}` : null,
          badgeColor: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30',
          desc: 'Multi-college graph conflicts',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
      ]
    },
    {
      title: 'Audit & Rules',
      items: [
        {
          id: 'audit-ledger',
          label: 'Audit & Receipts',
          icon: FileCheck2,
          badge: 'SHA-256',
          badgeColor: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30',
          desc: 'Timeline of receipts & tamper check',
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
        },
        {
          id: 'regulations',
          label: 'Regulation-as-Code',
          icon: BookOpenCheck,
          badge: 'APH',
          badgeColor: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30',
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
          badge: 'GIS',
          badgeColor: 'bg-teal-500/10 text-teal-600 dark:text-teal-400 border-teal-500/30',
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

  const roleDisplayNames = {
    scrutiny_officer: 'Scrutiny Officer',
    senior_officer: 'Regional Officer',
    admin: 'Central Admin',
    auditor: 'Auditor (Read-Only)',
    institution_user: 'Institution User'
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-40 lg:hidden transition-opacity animate-fadeIn" 
          onClick={onClose} 
          aria-hidden="true"
        />
      )}

      <aside className={`
        fixed inset-y-0 left-0 z-50 bg-surface border-r border-border 
        flex flex-col justify-between h-full overflow-y-auto p-3 pb-6 gap-4 scrollbar-slim shadow-2xl transition-all duration-200 ease-in-out
        lg:relative lg:z-0 lg:shrink-0 lg:shadow-none lg:translate-x-0 lg:flex
        ${isOpen ? 'translate-x-0 w-64 max-w-[85vw]' : '-translate-x-full lg:translate-x-0'}
        ${isCollapsed ? 'lg:w-[72px] lg:px-2' : 'lg:w-[264px]'}
      `}>
        <div className="flex flex-col gap-4">
          
          {/* Top Role Identity / Rail Indicator */}
          <div className={`px-2.5 py-2 bg-surface-2 rounded-xl border border-border flex items-center justify-between shrink-0 transition-all ${
            isCollapsed ? 'lg:justify-center lg:px-1.5' : ''
          }`}>
            {isCollapsed ? (
              <div 
                className="hidden lg:flex items-center justify-center relative cursor-default"
                title={`Active Role: ${roleDisplayNames[currentRole] || currentRole}`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-500/20 animate-pulse" />
              </div>
            ) : null}

            <div className={`min-w-0 ${isCollapsed ? 'lg:hidden' : 'block'}`}>
              <div className="text-[10px] uppercase font-bold tracking-wider text-text-muted">
                Active Role
              </div>
              <div className="text-xs font-bold text-text truncate">
                {roleDisplayNames[currentRole] || currentRole?.replace('_', ' ')}
              </div>
            </div>

            <div className="flex items-center space-x-1.5 shrink-0">
              <span className={`w-2 h-2 rounded-full bg-emerald-500 shrink-0 ${isCollapsed ? 'lg:hidden' : 'block'}`} />
              
              {/* Desktop quick collapse toggle */}
              <button
                type="button"
                onClick={onToggleCollapse}
                className="hidden lg:flex p-1 rounded-lg text-text-muted hover:text-text hover:bg-surface transition cursor-pointer"
                title={isCollapsed ? "Expand Sidebar (264px)" : "Collapse Sidebar (72px)"}
                aria-label="Toggle sidebar collapse"
              >
                {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
              </button>

              {/* Mobile Close Button */}
              <button
                type="button"
                onClick={onClose}
                className="lg:hidden p-1 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition cursor-pointer"
                aria-label="Close sidebar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Grouped Navigation Sections */}
          <nav className="flex flex-col gap-4">
            {navSections.map((section) => {
              const permittedItems = section.items.filter(item => item.roles.includes(currentRole));
              if (permittedItems.length === 0) return null;

              return (
                <div key={section.title} className="space-y-1">
                  {/* Section Title (hidden on collapsed desktop) */}
                  <div className={`text-[10px] font-bold tracking-wider text-text-muted uppercase px-2 mb-1 ${
                    isCollapsed ? 'lg:hidden' : 'block'
                  }`}>
                    {section.title}
                  </div>

                  <div className="flex flex-col gap-0.5">
                    {permittedItems.map((item) => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;
                      const tooltipText = `${item.label}${item.desc ? ` — ${item.desc}` : ''}${item.badge ? ` [${item.badge}]` : ''}`;

                      return (
                        <button
                          key={item.id}
                          id={`sidebar-tab-${item.id}`}
                          onClick={() => handleItemClick(item.id)}
                          title={tooltipText}
                          className={`w-full flex items-center rounded-xl text-left transition-all group cursor-pointer relative ${
                            isCollapsed 
                              ? 'lg:justify-center lg:p-2.5 lg:h-11' 
                              : 'px-3 py-2 justify-between gap-2 h-10'
                          } ${
                            isActive
                              ? 'bg-primary/10 text-primary dark:text-cobalt-light font-bold border-l-4 border-primary shadow-xs'
                              : 'text-text-muted hover:text-text hover:bg-surface-2 border-l-4 border-transparent'
                          }`}
                        >
                          <div className={`flex items-center min-w-0 ${isCollapsed ? 'lg:justify-center' : 'space-x-2.5 flex-1'}`}>
                            <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                              isActive ? 'text-primary dark:text-cobalt-light' : 'text-text-muted group-hover:text-text'
                            }`} />
                            
                            {/* Label for expanded mode */}
                            <span className={`text-xs font-medium truncate ${
                              isCollapsed ? 'lg:hidden' : 'block'
                            } ${isActive ? 'font-bold text-text' : ''}`}>
                              {item.label}
                            </span>
                          </div>

                          {/* Badge for expanded mode */}
                          {item.badge && (
                            <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-mono font-medium shrink-0 ${
                              isCollapsed ? 'lg:hidden' : 'block'
                            } ${item.badgeColor}`}>
                              {item.badge}
                            </span>
                          )}

                          {/* Collapsed dot indicator when badge exists */}
                          {item.badge && isCollapsed && (
                            <span className="hidden lg:block absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </nav>
        </div>

        {/* Statutory Legal Safe-Harbor Box */}
        <div className="pt-3 border-t border-border shrink-0 mt-2">
          {isCollapsed ? (
            <div 
              className="hidden lg:flex items-center justify-center p-2 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 cursor-pointer hover:bg-amber-500/20 transition-colors"
              title="Statutory Safeguard: All AI outputs represent advisory indicators for review. Autonomous determinations are prohibited; committee inquiry required."
            >
              <Lock className="w-4 h-4" />
            </div>
          ) : null}

          <div className={isCollapsed ? 'lg:hidden' : 'block'}>
            <details className="group bg-amber-500/10 dark:bg-amber-950/20 rounded-xl border border-amber-500/20 text-xs overflow-hidden transition-all">
              <summary className="flex items-center justify-between p-2 cursor-pointer list-none select-none text-amber-900 dark:text-amber-300 font-semibold text-[11px]">
                <div className="flex items-center space-x-1.5 min-w-0">
                  <Lock className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                  <span className="truncate">Statutory Safeguard</span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-amber-600/70 dark:text-amber-400/70 group-open:rotate-180 transition-transform shrink-0" />
              </summary>
              <div className="px-2 pb-2 text-[10px] text-amber-800/90 dark:text-amber-300/80 leading-relaxed border-t border-amber-500/10">
                All AI outputs represent advisory indicators for committee inquiry. Autonomous rejections are prohibited under regulatory guidelines.
              </div>
            </details>
          </div>
        </div>
      </aside>
    </>
  );
}
