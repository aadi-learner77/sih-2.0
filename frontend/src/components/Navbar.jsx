import React, { useState, useEffect, useRef } from 'react';
import { 
  AlertTriangle, 
  Sun, 
  Moon, 
  LogOut, 
  Menu, 
  X,
  ChevronDown,
  UserCheck,
  Monitor,
  Search
} from 'lucide-react';
import AlertBellDrawer from './AlertBellDrawer';
import ConfirmModal from './ui/ConfirmModal';
import SiteSearchModal from './ui/SiteSearchModal';
import { api } from '../services/api';

/**
 * AICTE Regulatory Emblem Shield SVG
 */
function AicteShieldLogo({ className = "w-7 h-7" }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="navShieldCobaltGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0B1B45" />
          <stop offset="50%" stopColor="#1F4BFF" />
          <stop offset="100%" stopColor="#14396B" />
        </linearGradient>
        <linearGradient id="navShieldGoldGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFC76B" />
          <stop offset="100%" stopColor="#FF9933" />
        </linearGradient>
      </defs>
      <path 
        d="M32 4L10 12V28C10 44.5 19.5 55.5 32 60C44.5 55.5 54 44.5 54 28V12L32 4Z" 
        fill="url(#navShieldCobaltGrad)" 
        stroke="#FFFFFF" 
        strokeWidth="1.5" 
      />
      <path 
        d="M32 9L15 15.5V28C15 41.5 22.5 50.5 32 54.5C41.5 50.5 49 41.5 49 28V15.5L32 9Z" 
        stroke="url(#navShieldGoldGrad)" 
        strokeWidth="1.5" 
        opacity="0.9" 
      />
      <circle cx="30" cy="30" r="10" stroke="#FFFFFF" strokeWidth="2.2" fill="none" />
      <path 
        d="M26 30L29 33L36 26" 
        stroke="#22D3EE" 
        strokeWidth="2.5" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
      />
      <line x1="37" y1="37" x2="44" y2="44" stroke="#FF9933" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Clean 64px Command Center Header (Theme Tokens, High Readability)
 */
export default function Navbar({ 
  currentUser,
  currentRole = 'scrutiny_officer', 
  isAdmin = false,
  adminPreviewRole = null,
  onAdminSwitchRole,
  onReturnToAdmin,
  onLogout, 
  activeApplication, 
  isLiveMode = false,
  isMobileMenuOpen = false,
  onToggleMobileMenu,
  onToggleSidebarCollapse,
  isScrolled = false,
  scrollProgress = 0,
  onSelectTab
}) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || saved === 'light') return saved;
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      return prefersDark ? 'dark' : 'light';
    }
    return 'light';
  });

  const [themePref, setThemePref] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme_preference') || 'auto';
    }
    return 'auto';
  });

  const [ledgerStatus, setLedgerStatus] = useState({ intact: true, blocks: 7 });
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isAdvisoryDismissed, setIsAdvisoryDismissed] = useState(() => {
    return typeof window !== 'undefined' && sessionStorage.getItem('pramaan_advisory_dismissed') === 'true';
  });

  const userMenuRef = useRef(null);

  // Global Ctrl/Cmd + K shortcut for Site Search palette
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsSearchOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const applyTheme = (targetTheme) => {
    setTheme(targetTheme);
    document.documentElement.setAttribute('data-theme', targetTheme);
    if (targetTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    try {
      localStorage.setItem('theme', targetTheme);
      localStorage.setItem('pramaan_theme', targetTheme);
    } catch (_e) {}
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: targetTheme } }));
  };

  useEffect(() => {
    const activeTheme = document.documentElement.getAttribute('data-theme') || localStorage.getItem('theme') || 'light';
    applyTheme(activeTheme);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setIsUserMenuOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    const checkLedger = async () => {
      try {
        const res = await api.verifyAuditChain(activeApplication?.id || 1);
        if (isMounted && res) {
          setLedgerStatus({
            intact: res.is_intact ?? res.is_valid ?? true,
            blocks: res.chain_length ?? res.total_receipts ?? 7
          });
        }
      } catch (_err) {}
    };
    checkLedger();
    const interval = setInterval(checkLedger, 8000);
    return () => { isMounted = false; clearInterval(interval); };
  }, [activeApplication?.id]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    applyTheme(nextTheme);
    setThemePref(nextTheme);
    localStorage.setItem('theme_preference', nextTheme);
  };

  const handleSelectThemeMode = (mode) => {
    setThemePref(mode);
    localStorage.setItem('theme_preference', mode);
    if (mode === 'system') {
      const isSystemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      applyTheme(isSystemDark ? 'dark' : 'light');
    } else {
      applyTheme(mode);
    }
  };

  const handleDismissAdvisory = () => {
    setIsAdvisoryDismissed(true);
    try {
      sessionStorage.setItem('pramaan_advisory_dismissed', 'true');
    } catch (_e) {}
  };

  const roleLabels = {
    scrutiny_officer: 'Scrutiny Officer',
    senior_officer: 'Regional Officer',
    admin: 'Central Admin',
    auditor: 'Auditor (Read-Only)',
    institution_user: 'Institution User'
  };

  const roleColors = {
    scrutiny_officer: 'bg-surface-2 text-text border-border',
    senior_officer: 'bg-surface-2 text-text border-border',
    admin: 'bg-surface-2 text-text border-border',
    auditor: 'bg-surface-2 text-text border-border',
    institution_user: 'bg-surface-2 text-text border-border'
  };

  const userName = currentUser?.full_name || (
    currentRole === 'institution_user' 
      ? 'Apex Institute of Technology' 
      : 'Shri R. K. Sharma, Scrutiny Cell'
  );

  const userInitial = userName.trim().charAt(0).toUpperCase();

  return (
    <>
      {/* 3px National Tricolour Accent Stripe (Static, Full Width) */}
      <div className="h-[3px] w-full shrink-0 grid grid-cols-3 z-50 relative select-none" aria-hidden="true">
        <div className="bg-[#FF9933] h-full" />
        <div className="bg-[#FFFFFF] h-full" />
        <div className="bg-[#138808] h-full" />
      </div>

      {/* Dynamic Glass / Sticky Header (64px shrinks to 56px when scrolled) */}
      <header 
        id="app-header-bar"
        className={`shrink-0 z-40 relative select-none border-b border-border text-text transition-all duration-200 ${
          isScrolled 
            ? 'h-14 glass-surface shadow-md border-border/80' 
            : 'h-16 bg-header-bg shadow-xs border-border'
        }`}
      >
        {/* 2px Cobalt Scroll Progress Line */}
        <div 
          className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary origin-left pointer-events-none transition-transform duration-75 z-50"
          style={{ transform: `scaleX(${scrollProgress})` }}
          aria-hidden="true"
        />
        <div className="h-full px-4 sm:px-6 flex items-center justify-between gap-3">
          
          {/* LEFT: Single Hamburger Toggle + PRAMAAN-X Wordmark + AICTE EoA Chip */}
          <div className="flex items-center space-x-2.5 min-w-0">
            {/* Single Toggle Button for Desktop Rail & Mobile Drawer */}
            <button
              type="button"
              id="sidebar-toggle-btn"
              onClick={() => {
                if (typeof window !== 'undefined' && window.innerWidth >= 1024) {
                  onToggleSidebarCollapse && onToggleSidebarCollapse();
                } else {
                  onToggleMobileMenu && onToggleMobileMenu();
                }
              }}
              aria-label="Toggle navigation sidebar"
              aria-expanded={isMobileMenuOpen}
              aria-controls="sidebar-nav"
              title="Toggle sidebar"
              className="p-2 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Logo Emblem & Brand Wordmark */}
            <div className="flex items-center space-x-2.5 min-w-0">
              <div className="p-1 rounded-lg bg-surface-2 border border-border shrink-0 flex items-center justify-center shadow-xs">
                <AicteShieldLogo className="w-7 h-7" />
              </div>

              <div className="flex items-center space-x-2">
                <div id="header-wordmark" className="flex items-baseline tracking-tight font-black font-sans text-xl">
                  <span className="text-[#0B3D91] dark:text-white font-black tracking-tight">PRAMAAN</span>
                  <span className="text-[#FF9933] font-black ml-0.5">
                    -X
                  </span>
                </div>
                
                {/* AICTE EoA Chip: neutral official capsule */}
                <span 
                  className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-surface-2 text-text-muted border border-border shadow-xs"
                  title="Approval Process Handbook (APH 2025-26) Regulatory Scrutiny"
                >
                  AICTE EoA
                </span>
              </div>
            </div>

            {/* Admin Viewing As Chip */}
            {adminPreviewRole && (
              <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-full bg-surface-2 border border-border text-text text-xs font-medium shadow-xs">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>Viewing as <strong className="text-text capitalize">{adminPreviewRole.replace('_', ' ')}</strong></span>
                <button
                  type="button"
                  id="return-to-admin-btn"
                  onClick={onReturnToAdmin}
                  className="ml-1 px-2.5 py-0.5 rounded-md bg-surface border border-border hover:bg-surface-2 text-text text-[11px] font-semibold cursor-pointer transition-colors"
                  title="Return to your Central Admin session"
                >
                  Return to Admin
                </button>
              </div>
            )}
          </div>

          {/* RIGHT: Compact Status Pill + Bell + 36px Theme Toggle + User Menu */}
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            
            {/* Single Compact Status Pill with Two Small Dots */}
            <div id="header-status-pill" className="hidden md:flex items-center space-x-2.5 px-3 py-1.5 rounded-full border border-border bg-surface-2 text-xs font-medium text-text-muted shadow-xs">
              <div className="flex items-center space-x-1.5">
                <span 
                  className={`w-2 h-2 rounded-full ${
                    isLiveMode ? 'bg-emerald-500' : 'bg-amber-500'
                  }`} 
                />
                <span className="text-[11px] font-semibold text-text">
                  {isLiveMode ? 'API Live' : 'Demo API'}
                </span>
              </div>

              <span className="w-px h-3 bg-border" />

              <div className="flex items-center space-x-1.5">
                <span 
                  className={`w-2 h-2 rounded-full ${
                    ledgerStatus.intact ? 'bg-emerald-500' : 'bg-rose-500'
                  }`} 
                />
                <span className="text-[11px] font-semibold text-text">
                  {ledgerStatus.intact ? 'Ledger Intact' : 'Ledger Flagged'}
                </span>
              </div>
            </div>

            {/* Operational Alert Bell with Drawer */}
            <AlertBellDrawer currentRole={currentRole} />

            {/* Quick Site Search Button (Ctrl+K) */}
            <button
              type="button"
              id="site-search-btn"
              onClick={() => setIsSearchOpen(true)}
              aria-label="Search navigation modules (Ctrl+K)"
              title="Search modules (Ctrl+K)"
              className="w-9 h-9 rounded-lg border border-border bg-surface-2 hover:bg-surface text-text flex items-center justify-center transition-colors cursor-pointer shrink-0 shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <Search className="w-4 h-4 text-text-muted hover:text-text" />
            </button>

            {/* Compact 36px Icon Theme Toggle with Sun/Moon 18px morph */}
            <button
              type="button"
              id="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label="Switch theme"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="w-9 h-9 rounded-lg border border-border bg-surface-2 hover:bg-surface text-text flex items-center justify-center transition-colors cursor-pointer shrink-0 shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 relative overflow-hidden group"
            >
              <div className="relative w-[18px] h-[18px] flex items-center justify-center">
                <Sun 
                  className={`w-[18px] h-[18px] text-[#FBBF24] absolute transition-all duration-250 ease-out ${
                    theme === 'dark' ? 'rotate-0 scale-100 opacity-100' : 'rotate-90 scale-50 opacity-0 pointer-events-none'
                  }`} 
                  id="theme-toggle-light" 
                />
                <Moon 
                  className={`w-[18px] h-[18px] text-text absolute transition-all duration-250 ease-out ${
                    theme === 'light' ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-50 opacity-0 pointer-events-none'
                  }`} 
                  id="theme-toggle-dark" 
                />
              </div>
            </button>

            {/* USER MENU (Solid Surface, High Contrast) */}
            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                id="user-menu-btn"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-2 pl-2 pr-2.5 py-1.5 rounded-lg border border-border bg-surface-2 hover:bg-surface transition-all cursor-pointer shadow-xs group"
                aria-expanded={isUserMenuOpen}
                aria-haspopup="true"
              >
                <div className="w-7 h-7 rounded-md bg-primary text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-xs">
                  {userInitial}
                </div>

                <div className="text-left hidden sm:flex flex-col items-start min-w-0 max-w-[160px]">
                  <span className="text-xs font-bold text-text leading-tight truncate w-full">
                    {userName}
                  </span>
                  <span className="text-[10px] font-medium text-text-muted truncate max-w-full leading-none mt-0.5">
                    {roleLabels[currentRole] || currentRole}
                  </span>
                </div>

                <ChevronDown className={`w-3.5 h-3.5 text-text-muted transition-transform duration-200 ${
                  isUserMenuOpen ? 'rotate-180' : ''
                }`} />
              </button>

              {/* User Dropdown Menu: Solid Surface, 280px, Right Aligned, High Z-Index */}
              {isUserMenuOpen && (
                <div 
                  id="user-menu-dropdown"
                  className="absolute right-0 mt-2 w-[280px] rounded-xl border border-border bg-surface p-2 shadow-xl z-50 animate-fadeIn text-xs text-text space-y-2"
                  role="menu"
                  aria-orientation="vertical"
                >
                  {/* User Profile Header */}
                  <div className="p-3 bg-surface-2 rounded-lg border border-border space-y-1">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-text-subtle">
                      Signed In As
                    </div>
                    <div className="font-bold text-text truncate text-xs">
                      {userName}
                    </div>
                    <div className="text-[11px] text-text-muted font-mono truncate">
                      {currentUser?.email || 'scrutiny.officer@aicte-india.org'}
                    </div>
                    <div className="pt-1">
                      <span className="inline-block text-[10px] font-medium px-2 py-0.5 rounded-full border border-border bg-surface text-text-muted">
                        {roleLabels[currentRole] || currentRole}
                      </span>
                    </div>
                  </div>

                  {/* Theme Option Row */}
                  <div className="p-2 border-t border-border">
                    <div className="text-[10px] font-bold text-text-subtle uppercase tracking-wider mb-1.5 flex items-center justify-between">
                      <span>Interface Theme</span>
                      <span className="text-primary font-mono capitalize">{theme}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1">
                      {[
                        { id: 'light', label: 'Light', icon: Sun },
                        { id: 'dark', label: 'Dark', icon: Moon },
                        { id: 'system', label: 'System', icon: Monitor }
                      ].map((tOpt) => {
                        const Icon = tOpt.icon;
                        const isSelected = themePref === tOpt.id;
                        return (
                          <button
                            key={tOpt.id}
                            type="button"
                            onClick={() => handleSelectThemeMode(tOpt.id)}
                            className={`py-1 rounded-lg text-xs font-semibold capitalize border flex items-center justify-center space-x-1 transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-primary text-white border-primary shadow-xs'
                                : 'bg-surface-2 text-text-muted hover:text-text border-border'
                            }`}
                          >
                            <Icon className="w-3 h-3" />
                            <span>{tOpt.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Switch Demo Role: Visible ONLY when logged-in role is admin */}
                  {isAdmin && onAdminSwitchRole && (
                    <div className="p-2 space-y-1 border-t border-border">
                      <label htmlFor="user-menu-role-select" className="text-[10px] font-bold text-text-subtle uppercase tracking-wider flex items-center space-x-1">
                        <UserCheck className="w-3 h-3 text-primary" />
                        <span>Switch Demo Role (Admin Only)</span>
                      </label>
                      <select
                        id="user-menu-role-select"
                        value={adminPreviewRole || 'admin'}
                        onChange={(e) => {
                          onAdminSwitchRole(e.target.value);
                          setIsUserMenuOpen(false);
                        }}
                        className="w-full bg-surface-2 border border-border rounded-lg px-2 py-1.5 text-xs text-text font-medium outline-none cursor-pointer"
                      >
                        <option value="admin">Central Admin</option>
                        <option value="scrutiny_officer">Scrutiny Officer</option>
                        <option value="senior_officer">Regional Officer</option>
                        <option value="auditor">Independent Auditor</option>
                        <option value="institution_user">Institution User</option>
                      </select>
                    </div>
                  )}

                  {/* Sign Out Action: Full Width, Danger-tinted */}
                  {onLogout && (
                    <div className="border-t border-border pt-1">
                      <button
                        type="button"
                        id="user-menu-signout-btn"
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          setShowLogoutConfirm(true);
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg text-danger hover:bg-danger/10 transition-colors font-semibold cursor-pointer"
                      >
                        <LogOut className="w-4 h-4 text-danger" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>
        </div>
      </header>

      {/* Reusable Accessible Confirmation Modal for Sign Out */}
      <ConfirmModal
        isOpen={showLogoutConfirm}
        onClose={() => setShowLogoutConfirm(false)}
        onConfirm={() => {
          setShowLogoutConfirm(false);
          onLogout && onLogout();
        }}
        title="Sign Out of PRAMAAN-X"
        description="Are you sure you wish to end your active AICTE scrutiny session? Any unsaved edits will be discarded."
        confirmText="Sign Out"
        variant="danger"
      />

      {/* Accessible Command Palette Site Search (Ctrl+K) */}
      <SiteSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectTab={onSelectTab}
        currentRole={currentRole}
      />

      {/* Single Line Advisory Notice (Clean, No Highlighter) */}
      {!isAdvisoryDismissed && (
        <div 
          role="status"
          className="h-7 shrink-0 bg-surface-2 border-b border-border px-4 sm:px-6 flex items-center justify-between text-xs font-medium text-text-muted z-30 transition-all select-none"
        >
          <div className="flex items-center space-x-2 min-w-0">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span className="text-text font-normal">Advisory only. No auto-rejection.</span>
          </div>

          <button
            type="button"
            onClick={handleDismissAdvisory}
            className="text-text-muted hover:text-text p-0.5 rounded cursor-pointer"
            aria-label="Dismiss advisory note"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </>
  );
}
