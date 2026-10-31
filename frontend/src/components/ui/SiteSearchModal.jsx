import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
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
  X,
  CornerDownLeft
} from 'lucide-react';

const ALL_SEARCHABLE_TABS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    description: 'Executive overview, application triage, and key performance indicators',
    category: 'Scrutiny',
    icon: LayoutDashboard,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
  },
  {
    id: 'evidence-lens',
    label: 'Evidence Lens',
    description: 'Multi-modal discrepancy verification, document-photo cross references',
    category: 'Scrutiny',
    icon: SearchCode,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
  },
  {
    id: 'manual-review-queue',
    label: 'Review Queue',
    description: 'Manual verification tickets, land deeds, and pending officer escalations',
    category: 'Scrutiny',
    icon: Clock,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
  },
  {
    id: 'preflight',
    label: 'Pre-Flight Scorecard',
    description: 'Institutional readiness self-check and deficiency diagnostics',
    category: 'Scrutiny',
    icon: PlaneTakeoff,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'institution_user'],
  },
  {
    id: 'document-intelligence',
    label: 'Document Intelligence',
    description: 'OCR coordinate extraction, digital tampering detection, and land deed forensics',
    category: 'Intelligence',
    icon: FileSearch,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
  },
  {
    id: 'photo-radar',
    label: 'Photo Radar',
    description: 'Perceptual hash clustering and geo-spatial photo reuse detection',
    category: 'Intelligence',
    icon: ScanEye,
    roles: ['scrutiny_officer', 'senior_officer', 'admin'],
  },
  {
    id: 'impossibility-engine',
    label: 'Impossibility Engine',
    description: 'Knowledge graph spatio-temporal validation and faculty overlap detection',
    category: 'Intelligence',
    icon: Network,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor'],
  },
  {
    id: 'audit-ledger',
    label: 'Audit & Receipts',
    description: 'Cryptographic SHA-256 hash chain and immutable officer actions ledger',
    category: 'Audit & Rules',
    icon: FileCheck2,
    roles: ['scrutiny_officer', 'senior_officer', 'admin', 'auditor', 'institution_user'],
  },
  {
    id: 'regulations',
    label: 'Rules Catalog',
    description: 'AICTE Approval Process Handbook (APH 2025-26) statutory clauses and What-If simulator',
    category: 'Audit & Rules',
    icon: BookOpenCheck,
    roles: ['senior_officer', 'admin'],
  },
  {
    id: 'inspection-planner',
    label: 'Inspection Planner',
    description: 'Surprise inspection route optimization and surveyor itinerary planning',
    category: 'Planning',
    icon: Compass,
    roles: ['scrutiny_officer', 'senior_officer', 'admin'],
  },
];

export default function SiteSearchModal({
  isOpen,
  onClose,
  onSelectTab,
  currentRole = 'scrutiny_officer'
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  // Filter tabs strictly by permitted role
  const permittedTabs = ALL_SEARCHABLE_TABS.filter(item => 
    item.roles.includes(currentRole)
  );

  const filteredTabs = permittedTabs.filter(item => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      item.label.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filteredTabs.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + (filteredTabs.length || 1)) % (filteredTabs.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredTabs[selectedIndex]) {
        onSelectTab(filteredTabs[selectedIndex].id);
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-start justify-center p-4 pt-16 sm:pt-24 animate-fadeIn"
      onClick={onClose}
      aria-hidden="true"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Search navigation tabs"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden animate-scaleUp text-text flex flex-col"
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-border bg-surface-2/40 gap-3">
          <Search className="w-5 h-5 text-text-muted shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a module name or keyword (e.g. Evidence, Audit, Pre-Flight)..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-text placeholder-text-muted"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="text-text-muted hover:text-text p-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 text-[10px] font-mono font-semibold text-text-muted bg-surface rounded border border-border">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-[380px] overflow-y-auto p-2 space-y-1">
          {filteredTabs.length === 0 ? (
            <div className="p-8 text-center text-text-muted text-xs">
              No modules found matching &ldquo;<span className="text-text font-semibold">{query}</span>&rdquo; for your current role.
            </div>
          ) : (
            filteredTabs.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;

              return (
                <div
                  key={item.id}
                  id={`search-tab-item-${item.id}`}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onSelectTab(item.id);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors text-left ${
                    isSelected 
                      ? 'bg-primary/10 text-primary dark:text-white border border-primary/20' 
                      : 'hover:bg-surface-2 text-text border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-primary text-white' : 'bg-surface-2 text-text-muted'} shrink-0`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold truncate">{item.label}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-2 text-text-muted border border-border uppercase font-semibold">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-text-muted truncate mt-0.5">
                        {item.description}
                      </p>
                    </div>
                  </div>
                  {isSelected && (
                    <CornerDownLeft className="w-3.5 h-3.5 text-primary shrink-0 ml-2" />
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 bg-surface-2/60 border-t border-border flex items-center justify-between text-[11px] text-text-muted select-none">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1.5 py-0.5 bg-surface border border-border rounded text-[10px]">↑</kbd> <kbd className="px-1.5 py-0.5 bg-surface border border-border rounded text-[10px]">↓</kbd> to navigate</span>
            <span><kbd className="px-1.5 py-0.5 bg-surface border border-border rounded text-[10px]">↵</kbd> to select</span>
          </div>
          <span>Allowed modules for active role</span>
        </div>
      </div>
    </div>
  );
}

