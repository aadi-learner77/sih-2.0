import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Sun, 
  Moon, 
  LogOut, 
  Menu, 
  X,
  ChevronDown,
  UserCheck,
  PanelLeftClose,
  PanelLeftOpen,
  HelpCircle,
  Database,
  Cpu
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
 * Compact 64px Regulatory Command Center Header
 */
export default function Navbar({ 
  currentUser,
  currentRole = 'scrutiny_officer', 
  onRoleChange,
  onLogout, 
  activeApplication, 
  isLiveMode = false,
  onToggleLiveMode,
  isMobileMenuOpen = false,
  onToggleMobileMenu,
  isSidebarCollapsed = false,
  onToggleSidebarCollapse
}) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') || localStorage.getItem('theme') || 'light';
    }
    return 'light';
  });

  const [ledgerStatus, setLedgerStatus] = useState({ intact: true, blocks: 7, loading: true });
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isStatusPopoverOpen, setIsStatusPopoverOpen] = useState(false);
  const [isAdvisoryDismissed, setIsAdvisoryDismissed] = useState(() => {
    return typeof window !== 'undefined' && sessionStorage.getItem('pramaan_advisory_dismissed') === 'true';
  });

  const userMenuRef = useRef(null);
  const statusClusterRef = useRef(null);

  // Sync theme on mount
  useEffect(() => {
    const activeTheme = document.documentElement.getAttribute('data-theme') || localStorage.getItem('theme') || 'light';
    setTheme(activeTheme);
    document.documentElement.setAttribute('data-theme', activeTheme);
    if (activeTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  // Close menus on click outside or Escape
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setIsUserMenuOpen(false);
      }
      if (statusClusterRef.current && !statusClusterRef.current.contains(e.target)) {
        setIsStatusPopoverOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsUserMenuOpen(false);
        setIsStatusPopoverOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Poll Audit Ledger status
  useEffect(() => {
    let isMounted = true;
    const checkLedger = async () => {
      try {
        const res = await api.verifyAuditChain(activeApplication?.id || 1);
        if (isMounted && res) {
          setLedgerStatus({
            intact: res.is_intact ?? res.is_valid ?? true,
            blocks: res.chain_length ?? res.total_receipts ?? 7,
            loading: false
          });
        }
      } catch (_err) {
        if (isMounted) setLedgerStatus(prev => ({ ...prev, loading: false }));
      }
    };
    checkLedger();
    const interval = setInterval(checkLedger, 6000);
    return () => { isMounted = false; clearInterval(interval); };
  }, [activeApplication?.id]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    try {
      localStorage.setItem('theme', nextTheme);
    } catch (_e) {}
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: nextTheme } }));
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
    auditor: 'Independent Auditor',
    institution_user: 'Institution User'
  };

  const roleColors = {
    scrutiny_officer: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border-cyan-500/20',
    senior_officer: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20',
    admin: 'bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20',
    auditor: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20',
    institution_user: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20'
  };

  const userInitial = (currentUser?.full_name || currentUser?.email || 'Dr. Deshmukh')[0].toUpperCase();
  const userName = currentUser?.full_name || currentUser?.email?.split('@')[0] || 'Dr. Deshmukh';

  return (
    <>
      {/* 64px Compact Header */}
      <header className="h-16 shrink-0 bg-surface/90 backdrop-blur-md border-b border-border sticky top-0 z-40 px-3 sm:px-5 lg:px-6 shadow-xs w-full transition-colors duration-150">
        <div className="flex items-center justify-between h-full w-full gap-2 sm:gap-4">
          
          {/* LEFT: Sidebar Toggle + Brand Identity + AICTE Chip */}
          <div className="flex items-center space-x-2.5 sm:space-x-3.5 shrink-0 min-w-0">
            {/* Desktop Hamburger / Collapse Sidebar Button */}
            <button
              type="button"
              id="desktop-sidebar-collapse-btn"
              onClick={onToggleSidebarCollapse}
              aria-label={isSidebarCollapsed ? "Expand sidebar rail" : "Collapse sidebar to icon rail"}
              title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="hidden lg:flex p-1.5 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 border border-transparent hover:border-border transition-colors cursor-pointer"
            >
              {isSidebarCollapsed ? (
                <PanelLeftOpen className="w-5 h-5 text-text-muted" />
              ) : (
                <PanelLeftClose className="w-5 h-5 text-text-muted" />
              )}
            </button>

            {/* Mobile Drawer Toggle Button */}
            <button
              type="button"
              id="mobile-drawer-toggle-btn"
              onClick={onToggleMobileMenu}
              aria-label="Toggle navigation drawer"
              className="lg:hidden p-1.5 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5 text-text" />
              ) : (
                <Menu className="w-5 h-5 text-text" />
              )}
            </button>

            {/* Brand Logo & Wordmark with saffron-gradient -X */}
            <div 
              className="flex items-center space-x-2 sm:space-x-2.5 cursor-pointer select-none group"
              title="PRAMAAN-X • AICTE Regulatory Scrutiny & Multi-Modal Document Intelligence"
            >
              <div className="p-1 rounded-xl bg-navy/5 dark:bg-white/5 border border-border shrink-0 flex items-center justify-center shadow-2xs">
                <AicteShieldLogo className="w-7 h-7" />
              </div>

              <div className="flex items-center space-x-2">
                <div className="flex items-baseline tracking-tight font-black font-sans text-lg sm:text-xl">
                  <span className="text-text font-black">PRAMAAN</span>
                  <span className="bg-gradient-to-r from-[#FFC76B] via-[#FF9933] to-[#FF7A00] bg-clip-text text-transparent font-black ml-0.5">
                    -X
                  </span>
                </div>
                
                {/* AICTE EoA Chip with Tooltip */}
                <span 
                  className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/25"
                  title="Approval Process Handbook (APH 2025-26) Regulatory Scrutiny"
                >
                  AICTE EoA
                </span>
              </div>
            </div>
          </div>

          {/* RIGHT: System Status Cluster + Notification Bell + Theme Toggle + User Menu */}
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            
            {/* Single System Status Cluster Pill */}
            <div className="relative" ref={statusClusterRef}>
              <button
                type="button"
                id="system-status-cluster-btn"
                onClick={() => setIsStatusPopoverOpen(!isStatusPopoverOpen)}
                className="hidden md:flex items-center space-x-2.5 px-3 py-1.5 rounded-full border border-border bg-surface-2 hover:bg-surface-muted text-xs font-medium text-text transition-all cursor-pointer shadow-2xs"
                title="Click for System Status details"
              >
                {/* Live Backend Dot */}
                <div className="flex items-center space-x-1.5">
                  <span 
                    className={`w-2 h-2 rounded-full ${
                      isLiveMode ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
                    }`} 
                  />
                  <span className="text-[11px] font-semibold text-text-muted">
                    {isLiveMode ? 'API Live' : 'Demo Mode'}
                  </span>
                </div>

                <span className="w-px h-3 bg-border" />

                {/* Ledger Dot */}
                <div className="flex items-center space-x-1.5">
                  <span 
                    className={`w-2 h-2 rounded-full ${
                      ledgerStatus.intact 
                        ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)] animate-pulse' 
                        : 'bg-rose-500 animate-bounce'
                    }`} 
                  />
                  <span className="text-[11px] font-semibold text-text-muted">
                    {ledgerStatus.intact ? 'Ledger Intact' : 'Ledger Flagged'}
                  </span>
                </div>
              </button>

              {/* Status Details Popover */}
              {isStatusPopoverOpen && (
                <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-border bg-surface p-4 shadow-xl z-50 text-xs animate-fadeIn space-y-3">
                  <div className="flex items-center justify-between font-bold text-text border-b border-border pb-2">
                    <span className="flex items-center space-x-1.5">
                      <Cpu className="w-4 h-4 text-primary" />
                      <span>System Architecture Status</span>
                    </span>
                    <button 
                      type="button" 
                      onClick={() => setIsStatusPopoverOpen(false)}
                      className="text-text-muted hover:text-text cursor-pointer"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="space-y-2">
                    <div className="p-2.5 rounded-xl bg-surface-2 border border-border flex items-start justify-between">
                      <div>
                        <div className="font-semibold text-text">FastAPI Backend Connector</div>
                        <div className="text-[11px] text-text-muted">
                          {isLiveMode ? 'Connected on :8000 (Live mode)' : 'Simulated offline / mock fallback'}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={onToggleLiveMode}
                        className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary text-white hover:bg-primary-hover cursor-pointer"
                      >
                        Toggle
                      </button>
                    </div>

                    <div className="p-2.5 rounded-xl bg-surface-2 border border-border space-y-1">
                      <div className="flex items-center justify-between font-semibold text-text">
                        <span className="flex items-center space-x-1.5">
                          <ShieldCheck className="w-4 h-4 text-emerald-500" />
                          <span>SHA-256 Audit Ledger</span>
                        </span>
                        <span className="font-mono text-emerald-600 dark:text-emerald-400 text-[11px]">
                          {ledgerStatus.intact ? 'SECURED' : 'FLAGGED'}
                        </span>
                      </div>
                      <div className="text-[11px] text-text-muted">
                        Merkle root verified across {ledgerStatus.blocks} chronological blocks.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Operational Alert Bell with Drawer */}
            <AlertBellDrawer currentRole={currentRole} />

            {/* Animated Sun / Moon Theme Toggle */}
            <button
              type="button"
              id="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              className="w-9 h-9 rounded-xl border border-border bg-surface-2 hover:bg-surface-muted text-text flex items-center justify-center cursor-pointer transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/40 shrink-0 shadow-2xs"
            >
              <div className="relative w-4 h-4 sm:w-[18px] sm:h-[18px]">
                <Sun 
                  className={`w-full h-full text-amber-500 absolute inset-0 transition-all duration-300 transform ${
                    theme === 'dark' ? 'rotate-0 scale-100 opacity-100' : 'rotate-90 scale-0 opacity-0'
                  }`} 
                />
                <Moon 
                  className={`w-full h-full text-slate-700 dark:text-slate-300 absolute inset-0 transition-all duration-300 transform ${
                    theme === 'dark' ? '-rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'
                  }`} 
                />
              </div>
            </button>

            {/* USER MENU: Avatar + Name + Role Badge with Dropdown */}
            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                id="user-menu-btn"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-2 pl-2 pr-2.5 py-1 rounded-xl border border-border bg-surface-2 hover:bg-surface-muted transition-all cursor-pointer shadow-2xs group"
                aria-expanded={isUserMenuOpen}
                aria-haspopup="true"
              >
                {/* Avatar initial chip */}
                <div className="w-7 h-7 rounded-lg bg-primary/15 text-primary font-bold text-xs flex items-center justify-center border border-primary/25 shrink-0 shadow-2xs">
                  {userInitial}
                </div>

                {/* Name & Role Pill (Desktop) */}
                <div className="text-left hidden sm:flex flex-col items-start min-w-0 max-w-[120px] lg:max-w-[150px]">
                  <span className="text-xs font-bold text-text leading-tight truncate w-full">
                    {userName}
                  </span>
                  <span className={`text-[9px] font-semibold px-1.5 py-0 rounded-md border truncate max-w-full ${
                    roleColors[currentRole] || 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}>
                    {roleLabels[currentRole] || currentRole}
                  </span>
                </div>

                <ChevronDown className={`w-3.5 h-3.5 text-text-muted transition-transform duration-200 ${
                  isUserMenuOpen ? 'rotate-180' : ''
                }`} />
              </button>

              {/* User Dropdown Menu */}
              {isUserMenuOpen && (
                <div 
                  className="absolute right-0 mt-2 w-64 rounded-2xl border border-border bg-surface p-2 shadow-2xl z-50 animate-fadeIn text-xs text-text space-y-1.5"
                  role="menu"
                  aria-orientation="vertical"
                >
                  {/* User Profile Header in Dropdown */}
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
                      <span className={`inline-block text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                        roleColors[currentRole] || 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {roleLabels[currentRole] || currentRole}
                      </span>
                    </div>
                  </div>

                  {/* Switch Role Quick Select for Evaluation / Demo */}
                  {onRoleChange && (
                    <div className="p-2 space-y-1 border-t border-border mt-1">
                      <label htmlFor="user-menu-role-select" className="text-[10px] font-bold text-text-muted uppercase tracking-wider flex items-center space-x-1">
                        <UserCheck className="w-3 h-3 text-primary" />
                        <span>Switch Demo Role</span>
                      </label>
                      <select
                        id="user-menu-role-select"
                        value={currentRole}
                        onChange={(e) => {
                          onRoleChange(e.target.value);
                          setIsUserMenuOpen(false);
                        }}
                        className="w-full bg-surface-2 border border-border rounded-lg px-2 py-1.5 text-xs text-text font-medium outline-none cursor-pointer"
                      >
                        <option value="scrutiny_officer">Scrutiny Officer</option>
                        <option value="senior_officer">Regional Officer</option>
                        <option value="admin">Central Admin</option>
                        <option value="auditor">Independent Auditor</option>
                        <option value="institution_user">Institution User</option>
                      </select>
                    </div>
                  )}

                  {/* Sign Out Action */}
                  {onLogout && (
                    <div className="border-t border-border pt-1">
                      <button
                        type="button"
                        id="user-menu-signout-btn"
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          onLogout();
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors font-semibold cursor-pointer"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out of Session</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>
        </div>
      </header>

      {/* 32px Slim Statutory Advisory Notice (Dismissible per session) */}
      {!isAdvisoryDismissed && (
        <div 
          role="status"
          className="h-8 shrink-0 bg-amber-500/10 dark:bg-amber-950/30 backdrop-blur-md border-b border-amber-500/20 px-3 sm:px-6 flex items-center justify-between text-[11px] font-medium text-amber-900 dark:text-amber-200 z-30 transition-all select-none"
        >
          <div className="flex items-center space-x-2 min-w-0">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
            <span className="truncate">
              Advisory indicators only • Non-punitive review • No auto-rejection
            </span>
          </div>

          <button
            type="button"
            id="dismiss-advisory-strip-btn"
            onClick={handleDismissAdvisory}
            title="Dismiss notice for this session"
            aria-label="Dismiss advisory banner"
            className="p-1 rounded text-amber-800/70 dark:text-amber-300/70 hover:text-amber-950 dark:hover:text-amber-100 hover:bg-amber-500/15 transition-colors cursor-pointer shrink-0 ml-2"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </>
  );
}
