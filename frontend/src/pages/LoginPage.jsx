import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Mail, 
  ArrowRight, 
  UserCheck, 
  AlertCircle, 
  Building2, 
  Scale, 
  Sparkles,
  KeyRound
} from 'lucide-react';
import { api } from '../services/api';

const PRESET_ACCOUNTS = [
  {
    role: 'scrutiny_officer',
    title: 'Scrutiny Officer',
    desc: 'Desk scrutiny, OCR inspection, and Evidence Lens',
    email: 'scrutiny.officer@aicte-india.org',
    password: 'AicteOfficer@2025',
    badgeColor: 'bg-sky-50 text-sky-700 border-sky-200',
  },
  {
    role: 'senior_officer',
    title: 'Senior / Regional Officer',
    desc: 'Escalations, approvals, and What-If dry-runs',
    email: 'regional.officer@aicte-india.org',
    password: 'AicteRegional@2025',
    badgeColor: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  },
  {
    role: 'admin',
    title: 'Central Administrator',
    desc: 'Full regulatory rule catalog & multi-versioning',
    email: 'admin@aicte-india.org',
    password: 'AicteAdmin@2025',
    badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
  },
  {
    role: 'auditor',
    title: 'Independent Auditor',
    desc: 'Read-only access to tamper-evident audit ledger',
    email: 'auditor@aicte-india.org',
    password: 'AicteAuditor@2025',
    badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  {
    role: 'institution_user',
    title: 'Institution User',
    desc: 'Apex Institute: own dossier and pre-flight readiness',
    email: 'registrar@apextech.edu.in',
    password: 'ApexPass@2025',
    badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
  },
];

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('scrutiny.officer@aicte-india.org');
  const [password, setPassword] = useState('AicteOfficer@2025');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSelectPreset = (preset) => {
    setEmail(preset.email);
    setPassword(preset.password);
    setErrorMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      // 1. Authenticate with backend and obtain JWT
      const loginRes = await api.login(email.trim(), password);
      const token = loginRes?.access_token;
      if (!token) {
        throw new Error('Access token not returned by authentication service.');
      }

      // 2. Persist JWT token
      localStorage.setItem('pramaan_token', token);

      // 3. Derive current user and role strictly from /auth/me
      const userProfile = await api.getMe();
      localStorage.setItem('pramaan_user', JSON.stringify(userProfile));

      // 4. Notify App component
      onLoginSuccess(userProfile);
    } catch (err) {
      console.error('Login failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Authentication failed. Please verify credentials.';
      setErrorMessage(detail);
      localStorage.removeItem('pramaan_token');
      localStorage.removeItem('pramaan_user');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-slate-100 font-sans selection:bg-orange-500 selection:text-white relative overflow-x-hidden">
      {/* Background Decorative Gradient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Brand Logo & Header */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500 via-orange-600 to-sky-600 flex items-center justify-center shadow-xl shadow-orange-500/20 text-white font-black text-3xl tracking-wider">
            PX
          </div>
        </div>

        <h2 className="text-center text-3xl font-black tracking-tight text-white">
          PRAMAAN-X
        </h2>
        <p className="mt-1.5 text-center text-xs font-semibold uppercase tracking-widest text-orange-400">
          All India Council for Technical Education (AICTE)
        </p>
        <p className="mt-1 text-center text-sm text-slate-400">
          Regulatory Scrutiny & Multi-Modal Document Intelligence
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl relative z-10">
        <div className="bg-slate-900/80 backdrop-blur-xl py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-800">
          
          {/* Statutory Disclaimer Pill */}
          <div className="mb-6 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
            <Scale className="w-4 h-4 text-amber-400 shrink-0" />
            <span>AI Decision-Support System • Non-Punitive Advisory Review • Role-Based Access</span>
          </div>

          {errorMessage && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Authentication Error: </span>
                {errorMessage}
              </div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Official Email Address
              </label>
              <div className="mt-1.5 relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 z-10">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@aicte-india.org"
                  className="block w-full !pl-12 pr-3.5 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition box-border"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Password
              </label>
              <div className="mt-1.5 relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 z-10">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full !pl-12 pr-3.5 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition box-border"
                />
              </div>
            </div>

            <button
              id="login-submit-btn"
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-60 transition cursor-pointer"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Authenticating & Verifying Role...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <span>Sign In to PRAMAAN-X</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </button>
          </form>

          {/* Preset Roles Quick Selector */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Demo Accounts Quick-Fill
              </span>
              <span className="text-[11px] text-slate-500">
                Click to load role credentials
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 auto-rows-fr w-full box-border">
              {PRESET_ACCOUNTS.map((preset, index) => {
                const isSelected = email === preset.email;
                const isLastOdd = index === PRESET_ACCOUNTS.length - 1 && PRESET_ACCOUNTS.length % 2 !== 0;
                return (
                  <button
                    key={preset.role}
                    id={`preset-role-${preset.role}`}
                    type="button"
                    onClick={() => handleSelectPreset(preset)}
                    className={`w-full h-full min-w-0 text-left p-3 rounded-xl border transition flex flex-col justify-start items-stretch box-border cursor-pointer select-none ${
                      isLastOdd ? 'sm:col-span-2' : ''
                    } ${
                      isSelected
                        ? 'bg-orange-500/15 border-orange-500/50 ring-1 ring-orange-500/30'
                        : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/80 hover:border-slate-700'
                    } focus:outline-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900`}
                  >
                    <div className="w-full min-w-0 flex flex-wrap items-center justify-between gap-1.5 mb-1.5">
                      <span className="text-xs font-bold text-white tracking-tight min-w-0">
                        {preset.title}
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 max-w-full ${preset.badgeColor}`}>
                        {preset.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed m-0 p-0 text-left w-full min-w-0 [overflow-wrap:anywhere] break-words whitespace-normal">
                      {preset.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-slate-500">
          Protected by Statutory Cryptographic Audit Ledger • JWT Signed with HS256
        </p>
      </div>
    </div>
  );
}
