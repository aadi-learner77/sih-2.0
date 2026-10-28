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
    <header className="shrink-0 bg-white border-b border-slate-200 sticky top-0 z-40 px-3 sm:px-6 py-2 sm:py-2.5 shadow-xs w-full">
      <div className="flex items-center justify-between gap-2 sm:gap-3 w-full">
        
        {/* Brand & AICTE Identity */}
        <div className="flex items-center space-x-2 sm:space-x-3 shrink-0 min-w-0">
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
              <p className="hidden 2xl:block text-[11px] text-slate-500 leading-tight">
                Regulatory Decision-Support & Multi-Modal Document Intelligence
              </p>
            </div>
          </div>

          <div className="hidden lg:flex items-center ml-2 pl-3 border-l border-slate-200 shrink-0">
            <div className="flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium whitespace-nowrap">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Advisory Indicators Only • Non-Punitive Review • No Auto-Rejection</span>
            </div>
          </div>
        </div>

        {/* Action Controls, Alert Bell & Role Switcher */}
        <div className="flex items-center space-x-2.5 shrink-0">
          
          {/* Data Source Mode Badge / Toggle */}
          <button
            onClick={onToggleLiveMode}
            id="data-source-mode-btn"
            className={`hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all ${
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
            className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono font-medium whitespace-nowrap transition-colors ${
              ledgerStatus.intact
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${ledgerStatus.intact ? 'text-emerald-600' : 'text-rose-600'}`} />
            <span>Ledger: {ledgerStatus.intact ? 'INTACT' : 'TAMPERED'} ({ledgerStatus.blocks} Blocks)</span>
          </div>

          {/* Active Application Selector */}
          {activeApplication && (
            <div className="hidden 2xl:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
              <Building2 className="w-3.5 h-3.5 text-sky-600" />
              <span className="font-semibold text-slate-900">{activeApplication.application_no}</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600 font-medium">{activeApplication.institution_name}</span>
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
            className="w-10 h-10 min-w-[40px] rounded-[8px] border border-[var(--btn-secondary-border)] bg-[var(--btn-secondary-bg)] hover:bg-[var(--btn-secondary-hover)] text-[var(--text)] flex items-center justify-center cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:ring-offset-2 shrink-0 shadow-2xs"
          >
            {theme === 'dark' ? (
              <Sun className="w-[18px] h-[18px] shrink-0 text-[var(--text)]" />
            ) : (
              <Moon className="w-[18px] h-[18px] shrink-0 text-[var(--text)]" />
            )}
          </button>

          {/* Role-Aware Switcher (if onRoleChange prop provided) */}
          {onRoleChange && (
            <div className="flex items-center space-x-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200 shadow-2xs">
              <UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />
              <select
                id="header-role-select"
                value={currentRole}
                onChange={(e) => onRoleChange(e.target.value)}
                className="bg-transparent text-xs text-slate-800 font-semibold px-2 py-1 outline-none cursor-pointer"
              >
                <option value="scrutiny_officer">Scrutiny Officer (Primary Triage)</option>
                <option value="senior_officer">Senior Officer (Escalation & Approvals)</option>
                <option value="admin">Central Admin (System Controls)</option>
                <option value="auditor">Auditor (Read-Only Ledger)</option>
                <option value="institution_user">Institution User (Apex Tech)</option>
              </select>
            </div>
          )}

          {/* Authenticated User Profile & Role Badge */}
          <div className="flex items-center space-x-2.5 bg-slate-50 pl-3 pr-2 py-1.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="flex items-center space-x-2">
              <UserCheck className="w-4 h-4 text-sky-600 shrink-0" />
              <div className="text-left hidden sm:flex flex-col items-start gap-0.5">
                <div className="text-xs font-bold text-slate-800 leading-tight">
                  {currentUser?.full_name || currentUser?.email || 'Dr. Sunita Deshmukh'}
                </div>
                <span id="header-role-badge" className="role-badge-pill">
                  {currentRole ? currentRole.replace('_', ' ') : 'Scrutiny Officer'}
                </span>
              </div>
            </div>

            {/* Logout Action */}
            {onLogout && (
              <button
                id="header-signout-btn"
                onClick={onLogout}
                className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer text-xs flex items-center space-x-1"
                title="Sign out of PRAMAAN-X session"
              >
                <span className="text-[11px] font-medium hidden md:inline">Sign Out</span>
              </button>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}
