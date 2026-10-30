import React, { useEffect } from 'react';
import { 
  LayoutDashboard, 
  SearchCode, 
  Network, 
  ScanEye, 
  BookOpenCheck, 
  PlaneTakeoff, 
  FileCheck2,
  Compass,
  Clock,
  FileSearch,
  X
} from 'lucide-react';

/**
 * Clean, Accessible Role-Aware Sidebar Navigation (Theme Tokens)
 * - Desktop: 260px expanded <-> 72px collapsed icon rail (200ms transition)
 * - Mobile: Off-canvas drawer with backdrop, Esc to close
 * - Active item: Cobalt tinted background + 3px cobalt left bar + readable text in both themes
 * - No stray orange dots, clean label/badge hiding
 */
export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  counts = {},
  currentRole = 'scrutiny_officer',
  isOpen = false,
  onClose = () => {},
  isCollapsed = false
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const navSections = [
    {
      title: 'Scrutiny',
      items: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          icon: LayoutDashboard,
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
        },
        {
          id: 'evidence-lens',
          label: 'Evidence Lens',
          icon: SearchCode,
          badge: (counts.advisoryFlags && counts.advisoryFlags > 0) ? `${counts.advisoryFlags}` : null,
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'manual-review-queue',
          label: 'Review Queue',
          icon: Clock,
          badge: (counts.manualReview && counts.manualReview > 0) ? `${counts.manualReview}` : null,
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'preflight',
          label: 'Pre-Flight',
          icon: PlaneTakeoff,
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'institution_user'],
        },
      ]
    },
    {
      title: 'Intelligence',
      items: [
        {
          id: 'document-intelligence',
          label: 'Doc Intelligence',
          icon: FileSearch,
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
        },
        {
          id: 'photo-radar',
          label: 'Photo Radar',
          icon: ScanEye,
          roles: ['scrutiny_officer', 'senior_officer', 'admin'],
        },
        {
          id: 'impossibility-engine',
          label: 'Impossibility Engine',
          icon: Network,
          badge: (counts.impossibilities && counts.impossibilities > 0) ? `${counts.impossibilities}` : null,
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
          roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
        },
        {
          id: 'regulations',
          label: 'Rules Catalog',
          icon: BookOpenCheck,
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
    auditor: 'Independent Auditor',
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

      {/* Main Aside Component */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 bg-sidebar-bg border-r border-border text-text
        flex flex-col justify-between h-full overflow-y-auto p-3 pb-6 gap-4 scrollbar-slim transition-[width] duration-200 ease-in-out select-none
        lg:relative lg:z-0 lg:shrink-0 lg:shadow-none lg:translate-x-0 lg:flex
        ${isOpen ? 'translate-x-0 w-[260px]' : '-translate-x-full lg:translate-x-0'}
        ${isCollapsed ? 'lg:w-[72px] lg:px-2' : 'lg:w-[260px]'}
      `}>
        <div className="flex flex-col gap-4">
          
          {/* Top Role Identity: Expanded = Name + Dot; Collapsed = Dot only */}
          <div className={`px-2.5 py-2 bg-surface-2 rounded-lg border border-border flex items-center shrink-0 transition-all ${
            isCollapsed ? 'lg:justify-center lg:px-1' : 'justify-between'
          }`}>
            {isCollapsed ? (
              <div 
                className="hidden lg:flex items-center justify-center p-1"
                title={`Active Role: ${roleDisplayNames[currentRole] || currentRole}`}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-500/20" />
              </div>
            ) : null}

            <div className={`min-w-0 ${isCollapsed ? 'lg:hidden' : 'block'}`}>
              <div className="text-[10px] uppercase font-bold tracking-wider text-text-subtle">
                Role Context
              </div>
              <div className="text-xs font-bold text-text truncate">
                {roleDisplayNames[currentRole] || currentRole?.replace('_', ' ')}
              </div>
            </div>

            <div className={`flex items-center space-x-1.5 shrink-0 ${isCollapsed ? 'lg:hidden' : 'flex'}`}>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
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

          {/* Grouped Navigation Sections (20px group spacing, 4px item gap, 40px item height) */}
          <nav className="flex flex-col space-y-5">
            {navSections.map((section) => {
              const permittedItems = section.items.filter(item => item.roles.includes(currentRole));
              if (permittedItems.length === 0) return null;

              return (
                <div key={section.title} className="space-y-1">
                  {/* Group Title (11-12px, 600, uppercase with slight tracking, text-subtle) */}
                  <div className={`text-[11px] font-semibold tracking-wider text-text-subtle uppercase px-3 mb-1.5 ${
                    isCollapsed ? 'lg:hidden' : 'block'
                  }`}>
                    {section.title}
                  </div>

                  <div className="flex flex-col gap-1">
                    {permittedItems.map((item) => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;
                      const isAlertBadge = item.id === 'evidence-lens' || item.id === 'manual-review-queue';

                      return (
                        <button
                          key={item.id}
                          id={`sidebar-tab-${item.id}`}
                          onClick={() => handleItemClick(item.id)}
                          title={item.label}
                          className={`w-full flex items-center rounded-lg text-left transition-colors group cursor-pointer relative h-10 ${
                            isCollapsed 
                              ? 'lg:justify-center lg:p-2' 
                              : 'px-3 py-2 justify-between gap-2'
                          } ${
                            isActive
                              ? 'bg-primary/10 border-l-[3px] border-l-primary text-primary dark:text-white font-semibold'
                              : 'text-text-muted hover:text-text hover:bg-surface-2 border-l-[3px] border-l-transparent font-medium'
                          }`}
                        >
                          <div className={`flex items-center min-w-0 ${isCollapsed ? 'lg:justify-center' : 'space-x-2.5 flex-1'}`}>
                            <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                              isActive ? 'text-primary dark:text-white' : 'text-text-muted group-hover:text-text'
                            }`} />
                            
                            {/* Label for expanded mode (14px/400-500) */}
                            <span className={`text-[13px] truncate ${
                              isCollapsed ? 'lg:hidden' : 'block'
                            }`}>
                              {item.label}
                            </span>
                          </div>

                          {/* Badge for expanded mode: small neutral pill (surface-2 background, text-muted), except alerts which use danger tint */}
                          {item.badge && !isCollapsed && (
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono font-medium shrink-0 shadow-2xs ${
                              isAlertBadge
                                ? 'bg-danger/10 text-danger border-danger/25'
                                : 'bg-surface-2 text-text-muted border-border'
                            }`}>
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
          </nav>
        </div>

        {/* Bottom Note: Short single line */}
        <div className="pt-2 border-t border-border shrink-0">
          <div className={`text-[10px] text-text-muted px-2 py-0.5 truncate text-center ${
            isCollapsed ? 'lg:hidden' : 'block'
          }`}>
            Advisory Indicators Only
          </div>
        </div>
      </aside>
    </>
  );
}
