import React from 'react';
import { ShieldCheck, AlertTriangle, UserCheck, Bell, Building2 } from 'lucide-react';

export default function Navbar({ currentRole, onRoleChange, activeApplication }) {
  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50 px-6 py-3 shadow-xs">
      <div className="flex items-center justify-between">
        {/* Brand & AICTE Identity */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
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
              <p className="text-xs text-slate-500">
                AI Regulatory Decision-Support & Document Intelligence Platform
              </p>
            </div>
          </div>

          <div className="hidden lg:flex items-center ml-6 pl-6 border-l border-slate-200">
            <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>AI Advisory Only • Indicators for Review • No Auto-Rejection</span>
            </div>
          </div>
        </div>

        {/* Action Controls & User */}
        <div className="flex items-center space-x-4">
          {/* Active Ledger Status Badge */}
          <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Audit Ledger: INTACT (7 Blocks)</span>
          </div>

          {/* Active Application Selector */}
          {activeApplication && (
            <div className="hidden xl:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
              <Building2 className="w-3.5 h-3.5 text-sky-600" />
              <span className="font-semibold text-slate-900">{activeApplication.application_no}</span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600 truncate max-w-[180px]">{activeApplication.institution_name}</span>
            </div>
          )}

          {/* Role Switcher for Demo */}
          <div className="flex items-center space-x-2 bg-slate-50 p-1 rounded-xl border border-slate-200">
            <UserCheck className="w-4 h-4 ml-2 text-sky-600" />
            <select
              value={currentRole}
              onChange={(e) => onRoleChange(e.target.value)}
              className="bg-transparent text-xs text-slate-700 font-medium px-2 py-1 outline-none cursor-pointer"
            >
              <option value="scrutiny_officer">Scrutiny Officer (Deshmukh)</option>
              <option value="regional_officer">Regional Officer (Kulkarni)</option>
              <option value="admin">Central Admin (AICTE HQ)</option>
              <option value="institution_user">Institution Registrar (Apex)</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
}
