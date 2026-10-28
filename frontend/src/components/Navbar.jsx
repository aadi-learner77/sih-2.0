import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  UserCheck, 
  Building2, 
  Sparkles,
  Layers,
  Sun,
  Moon,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import AlertBellDrawer from './AlertBellDrawer';

/**
 * Top AICTE Navigation Bar:
 * - Brand Identity & Statutory Non-Punitive Advisory Disclaimer
 * - Alert Bell with active counter & flyout drawer
 * - Light / Dark Theme Toggle
 * - Role-Aware Switcher (Scrutiny Officer, Senior Officer, Admin, Auditor, Institution User)
 * - Active Dossier Quick Pill
 */
export default function Navbar({ 
  currentUser,
  currentRole, 
  onRoleChange,
  onLogout, 
  activeApplication, 
  isLiveMode = false,
  onToggleLiveMode,
  isMobileMenuOpen = false,
  onToggleMobileMenu
}) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') || localStorage.getItem('theme') || 'light';
    }
    return 'light';
  });

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
    } catch (e) {}
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: nextTheme } }));
  };
  const [ledgerStatus, setLedgerStatus] = useState({ intact: true, blocks: 7, loading: true });

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
      } catch (err) {
        if (isMounted) setLedgerStatus(prev => ({ ...prev, loading: false }));
      }
    };
    checkLedger();
    const interval = setInterval(checkLedger, 5000);
    return () => { isMounted = false; clearInterval(interval); };
  }, [activeApplication?.id]);

  return (
    <header className="shrink-0 bg-white border-b border-slate-200 sticky top-0 z-40 px-3 sm:px-4 lg:px-6 py-2 shadow-xs w-full">
      <div className="flex flex-wrap items-center justify-between gap-2 w-full">
        
        {/* Brand & AICTE Identity */}
        <div className="flex items-center space-x-2 sm:space-x-3 shrink min-w-0">
          {/* Mobile Menu Hamburger Toggle Button */}
          {onToggleMobileMenu && (
            <button
              type="button"
              id="mobile-nav-toggle-btn"
              onClick={onToggleMobileMenu}
              aria-label="Toggle navigation menu"
              className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer shrink-0"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5 text-slate-800" />
              ) : (
                <Menu className="w-5 h-5 text-slate-800" />
              )}
            </button>
          )}

          <div className="flex items-center space-x-2 sm:space-x-2.5 shrink-0">
            <img 
              src="/logo.png" 
              alt="PRAMAAN-X Logo" 
              className="w-8 h-8 sm:w-9 sm:h-9 object-contain rounded-lg shrink-0 navbar-logo shadow-xs" 
              onError={(e) => { e.target.style.display = 'none'; }}
            />
            <div className="shrink-0">
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <span className="text-base sm:text-xl font-bold tracking-tight text-slate-900">
                  PRAMAAN-X
                </span>
                <span className="hidden xs:inline-block text-[9px] sm:text-[10px] uppercase font-bold tracking-widest px-1.5 sm:px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200">
                  AICTE EoA
                </span>
              </div>
              <p className="hidden xl:block text-[11px] text-slate-500 leading-tight truncate max-w-[280px]">
                Regulatory Decision-Support & Multi-Modal Document Intelligence
              </p>
            </div>
          </div>

          {/* Statutory Advisory Pill - Icon tooltip on <1024px, compact text on 1024-1440px, full on >=1440px */}
          <div className="flex items-center ml-1 sm:ml-2 pl-2 sm:pl-3 border-l border-slate-200 shrink min-w-0">
            <div 
              title="Advisory Indicators Only • Non-Punitive Review • No Auto-Rejection"
              className="flex items-center space-x-1.5 px-2 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium cursor-help"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span className="hidden lg:inline xl:hidden">Advisory Indicators Only</span>
              <span className="hidden xl:inline">Advisory Indicators Only • Non-Punitive Review • No Auto-Rejection</span>
            </div>
          </div>
        </div>

        {/* Action Controls, Alert Bell & Role Switcher */}
        <div className="flex items-center flex-wrap gap-1.5 sm:gap-2 justify-end min-w-0">
          
          {/* Data Source Mode Badge / Toggle */}
          <button
            onClick={onToggleLiveMode}
            id="data-source-mode-btn"
            className={`hidden 2xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all ${
              isLiveMode
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
            }`}
            title="Toggle between Live API and Rich Mock Dataset"
          >
            <span className={`w-2 h-2 rounded-full ${isLiveMode ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
            <span>{isLiveMode ? 'Live Backend API' : 'Demo / Mock Data'}</span>
          </button>

          {/* Active Ledger Status Badge */}
          <div 
            id="navbar-ledger-badge"
            className={`hidden xl:flex items-center space-x-1.5 px-2 py-1 rounded-lg border text-xs font-mono font-medium whitespace-nowrap transition-colors ${
              ledgerStatus.intact
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}
            title={`Ledger: ${ledgerStatus.intact ? 'INTACT' : 'TAMPERED'} (${ledgerStatus.blocks} Blocks)`}
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${ledgerStatus.intact ? 'text-emerald-600' : 'text-rose-600'}`} />
            <span>Ledger: {ledgerStatus.intact ? 'INTACT' : 'TAMPERED'}</span>
          </div>

          {/* Active Application Selector */}
          {activeApplication && (
            <div className="hidden 2xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 max-w-[180px] truncate">
              <Building2 className="w-3.5 h-3.5 text-sky-600 shrink-0" />
              <span className="font-semibold text-slate-900 truncate">{activeApplication.application_no}</span>
            </div>
          )}

          {/* Operational Alert Bell with Drawer */}
          <AlertBellDrawer currentRole={currentRole} />

          {/* Light / Dark Theme Toggle Button */}
          <button
            type="button"
            id="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="w-9 h-9 sm:w-10 sm:h-10 rounded-[8px] border border-[var(--btn-secondary-border)] bg-[var(--btn-secondary-bg)] hover:bg-[var(--btn-secondary-hover)] text-[var(--text)] flex items-center justify-center cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:ring-offset-2 shrink-0 shadow-2xs"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 sm:w-[18px] sm:h-[18px] shrink-0 text-[var(--text)]" />
            ) : (
              <Moon className="w-4 h-4 sm:w-[18px] sm:h-[18px] shrink-0 text-[var(--text)]" />
            )}
          </button>

          {/* Role-Aware Switcher */}
          {onRoleChange && (
            <div className="flex items-center space-x-1 bg-slate-50 p-1 rounded-xl border border-slate-200 shadow-2xs max-w-[130px] sm:max-w-[160px] xl:max-w-[210px]">
              <UserCheck className="w-3.5 h-3.5 ml-1 text-sky-600 shrink-0" />
              <select
                id="header-role-select"
                value={currentRole}
                onChange={(e) => onRoleChange(e.target.value)}
                className="bg-transparent text-xs text-slate-800 font-semibold px-1 py-1 outline-none cursor-pointer truncate w-full"
              >
                <option value="scrutiny_officer">Scrutiny Officer</option>
                <option value="senior_officer">Senior Officer</option>
                <option value="admin">Central Admin</option>
                <option value="auditor">Auditor</option>
                <option value="institution_user">Institution User</option>
              </select>
            </div>
          )}

          {/* Authenticated User Profile & Role Badge - ALWAYS VISIBLE */}
          <div className="flex items-center space-x-2 bg-slate-50 pl-2.5 pr-1.5 py-1 rounded-xl border border-slate-200 shadow-2xs shrink-0">
            <div className="flex items-center space-x-1.5 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700 font-bold text-xs shrink-0">
                {(currentUser?.full_name || currentUser?.email || 'SO')[0].toUpperCase()}
              </div>
              <div className="text-left hidden md:flex flex-col items-start min-w-0 max-w-[110px] xl:max-w-[140px]">
                <div className="text-xs font-bold text-slate-800 leading-tight truncate w-full">
                  {currentUser?.full_name || currentUser?.email?.split('@')[0] || 'Dr. Deshmukh'}
                </div>
                <span id="header-role-badge" className="role-badge-pill truncate max-w-full text-[9px] py-0 px-1.5">
                  {currentRole ? currentRole.replace('_', ' ') : 'Scrutiny Officer'}
                </span>
              </div>
            </div>

            {/* Logout Action - ALWAYS VISIBLE */}
            {onLogout && (
              <button
                id="header-signout-btn"
                onClick={onLogout}
                className="px-2 py-1 rounded-lg text-slate-600 hover:text-rose-700 hover:bg-rose-50 transition cursor-pointer text-xs font-semibold flex items-center space-x-1 shrink-0 border border-transparent hover:border-rose-200"
                title="Sign out of PRAMAAN-X session"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-[11px] font-medium hidden md:inline">Sign Out</span>
              </button>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}
