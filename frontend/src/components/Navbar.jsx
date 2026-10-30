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
  Monitor
} from 'lucide-react';
import AlertBellDrawer from './AlertBellDrawer';
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
  onToggleMobileMenu,
  onToggleSidebarCollapse
}) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') || localStorage.getItem('theme') || 'light';
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
  const [isAdvisoryDismissed, setIsAdvisoryDismissed] = useState(() => {
    return typeof window !== 'undefined' && sessionStorage.getItem('pramaan_advisory_dismissed') === 'true';
  });

  const userMenuRef = useRef(null);

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
    scrutiny_officer: 'bg-primary/10 text-primary border-primary/25',
    senior_officer: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/25',
    admin: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25',
    auditor: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25',
    institution_user: 'bg-teal-500/10 text-teal-700 dark:text-teal-300 border-teal-500/25'
  };

  const userName = currentUser?.full_name || (
    currentRole === 'institution_user' 
      ? 'Apex Institute of Technology' 
      : 'Shri R. K. Sharma, Scrutiny Cell'
  );

  const userInitial = userName.trim().charAt(0).toUpperCase();

  return (
    <>
      {/* 64px Fixed Height Semantic Token Header */}
      <header className="h-16 shrink-0 z-40 relative select-none bg-surface border-b border-border text-text shadow-xs">
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
              title="Toggle sidebar"
              className="p-2 rounded-xl text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Logo Emblem & Brand Wordmark */}
            <div className="flex items-center space-x-2.5 min-w-0">
              <div className="p-1 rounded-xl bg-surface-2 border border-border shrink-0 flex items-center justify-center shadow-xs">
                <AicteShieldLogo className="w-7 h-7" />
              </div>

              <div className="flex items-center space-x-2">
                <div className="flex items-baseline tracking-tight font-black font-sans text-xl">
                  <span className="text-text font-black tracking-tight">PRAMAAN</span>
                  <span className="bg-gradient-to-r from-[#FFC76B] via-[#FF9933] to-[#FF7A00] bg-clip-text text-transparent font-black ml-0.5">
                    -X
                  </span>
                </div>
                
                {/* AICTE EoA Chip: cobalt text on tinted background with 1px border */}
                <span 
                  className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-primary/10 text-primary border border-primary/25 shadow-xs"
                  title="Approval Process Handbook (APH 2025-26) Regulatory Scrutiny"
                >
                  AICTE EoA
                </span>
              </div>
            </div>

            {/* Admin Viewing As Chip */}
            {adminPreviewRole && (
              <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-800 dark:text-amber-200 text-xs font-semibold shadow-xs">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>Viewing as <strong className="text-text capitalize">{adminPreviewRole.replace('_', ' ')}</strong></span>
                <button
                  type="button"
                  id="return-to-admin-btn"
                  onClick={onReturnToAdmin}
                  className="ml-1 px-2.5 py-0.5 rounded-md bg-amber-500/20 hover:bg-amber-500/30 text-amber-900 dark:text-amber-100 text-[11px] font-bold cursor-pointer transition-colors"
                  title="Return to your Central Admin session"
                >
                  Return to Admin
                </button>
              </div>
            )}
          </div>

          {/* RIGHT: Compact Status Pill + Bell + 40px Theme Toggle + User Menu */}
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            
            {/* Single Compact Status Pill with Two Small Dots */}
            <div className="hidden md:flex items-center space-x-2.5 px-3 py-1.5 rounded-full border border-border bg-surface-2 text-xs font-medium text-text-muted shadow-xs">
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

            {/* 40px Visible Sun / Moon Theme Toggle */}
            <button
              type="button"
              id="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              className="w-10 h-10 rounded-xl border border-border bg-surface-2 hover:bg-surface text-text flex items-center justify-center cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/60 shrink-0 shadow-xs"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5 text-amber-400" />
              ) : (
                <Moon className="w-5 h-5 text-text" />
              )}
            </button>

            {/* USER MENU (Solid Surface, High Contrast) */}
            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                id="user-menu-btn"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-2 pl-2 pr-2.5 py-1.5 rounded-xl border border-border bg-surface-2 hover:bg-surface transition-all cursor-pointer shadow-xs group"
                aria-expanded={isUserMenuOpen}
                aria-haspopup="true"
              >
                <div className="w-7 h-7 rounded-lg bg-primary text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-xs">
                  {userInitial}
                </div>

                <div className="text-left hidden sm:flex flex-col items-start min-w-0 max-w-[130px]">
                  <span className="text-xs font-bold text-text leading-tight truncate w-full">
                    {userName}
                  </span>
                  <span className={`text-[9px] font-semibold px-1.5 py-0 rounded-md border truncate max-w-full ${
                    roleColors[currentRole] || 'bg-surface text-text-muted border-border'
                  }`}>
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
                  className="absolute right-0 mt-2 w-[280px] rounded-2xl border border-border bg-surface p-2 shadow-2xl z-50 animate-fadeIn text-xs text-text space-y-2"
                  role="menu"
                  aria-orientation="vertical"
                >
                  {/* User Profile Header */}
                  <div className="p-3 bg-surface-2 rounded-xl border border-border space-y-1">
                    <div className="text-[10px] uppercase font-bold tracking-wider text-text-muted">
                      Signed In As
                    </div>
                    <div className="font-bold text-text truncate text-xs">
                      {userName}
                    </div>
                    <div className="text-[11px] text-text-muted font-mono truncate">
                      {currentUser?.email || 'scrutiny.officer@aicte-india.org'}
                    </div>
                    <div className="pt-1">
                      <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        roleColors[currentRole] || 'bg-surface text-text-muted border-border'
                      }`}>
                        {roleLabels[currentRole] || currentRole}
                      </span>
                    </div>
                  </div>

                  {/* Theme Option Row */}
                  <div className="p-2 border-t border-border">
                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1.5 flex items-center justify-between">
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
                      <label htmlFor="user-menu-role-select" className="text-[10px] font-bold text-text-muted uppercase tracking-wider flex items-center space-x-1">
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
                          onLogout();
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-[#DC2626] hover:bg-rose-500/10 transition-colors font-semibold cursor-pointer"
                      >
                        <LogOut className="w-4 h-4 text-[#DC2626]" />
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

      {/* Single Line Advisory Notice (Dismissible) */}
      {!isAdvisoryDismissed && (
        <div 
          role="status"
          className="h-7 shrink-0 bg-amber-500/10 border-b border-amber-500/25 px-4 sm:px-6 flex items-center justify-between text-xs font-medium text-amber-800 dark:text-amber-200 z-30 transition-all select-none"
        >
          <div className="flex items-center space-x-2 min-w-0">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>Advisory only. No auto-rejection.</span>
          </div>

          <button
            type="button"
            onClick={handleDismissAdvisory}
            className="text-amber-700 dark:text-amber-300 hover:text-amber-900 dark:hover:text-amber-100 p-0.5 rounded cursor-pointer"
            aria-label="Dismiss advisory note"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </>
  );
}
