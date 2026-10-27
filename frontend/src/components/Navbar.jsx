import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  UserCheck, 
  Building2, 
  Sparkles,
  Layers
} from 'lucide-react';
import AlertBellDrawer from './AlertBellDrawer';

/**
 * Top AICTE Navigation Bar:
 * - Brand Identity & Statutory Non-Punitive Advisory Disclaimer
 * - Alert Bell with active counter & flyout drawer
 * - Role-Aware Switcher (Scrutiny Officer, Senior Officer, Admin, Auditor, Institution User)
 * - Active Dossier Quick Pill
 */
export default function Navbar({ 
  currentRole, 
  onRoleChange, 
  activeApplication, 
  isLiveMode = false,
  onToggleLiveMode 
}) {
  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 px-6 py-2.5 shadow-xs">
      <div className="flex items-center justify-between gap-4">
        
        {/* Brand & AICTE Identity */}
        <div className="flex items-center space-x-4 min-w-0">
          <div className="flex items-center space-x-3 shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-600 to-sky-600 flex items-center justify-center shadow-md shadow-orange-500/20 text-white font-black text-xl tracking-wider">
              PX
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-slate-900">
                  PRAMAAN-X
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200">
                  AICTE EoA Scrutiny
                </span>
              </div>
              <p className="text-[11px] text-slate-500 truncate max-w-xs sm:max-w-md">
                Regulatory Decision-Support & Multi-Modal Document Intelligence
              </p>
            </div>
          </div>

          <div className="hidden xl:flex items-center ml-4 pl-4 border-l border-slate-200">
            <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Advisory Indicators Only • Non-Punitive Review • No Auto-Rejection</span>
            </div>
          </div>
        </div>

        {/* Action Controls, Alert Bell & Role Switcher */}
        <div className="flex items-center space-x-3 shrink-0">
          
          {/* Data Source Mode Badge / Toggle */}
          <button
            onClick={onToggleLiveMode}
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
          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Ledger: INTACT (7 Blocks)</span>
          </div>

          {/* Active Application Selector */}
          {activeApplication && (
            <div className="hidden 2xl:flex items-center space-x-2 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
              <Building2 className="w-3.5 h-3.5 text-sky-600" />
              <span className="font-semibold text-slate-900">{activeApplication.application_no}</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600 truncate max-w-[140px]">{activeApplication.institution_name}</span>
            </div>
          )}

          {/* Operational Alert Bell with Drawer */}
          <AlertBellDrawer currentRole={currentRole} />

          {/* Role-Aware Switcher */}
          <div className="flex items-center space-x-1.5 bg-slate-50 p-1 rounded-xl border border-slate-200 shadow-2xs">
            <UserCheck className="w-4 h-4 ml-2 text-sky-600 shrink-0" />
            <select
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

        </div>
      </div>
    </header>
  );
}
