import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Mail, 
  ArrowRight, 
  AlertCircle, 
  Scale, 
  Eye, 
  EyeOff, 
  Search, 
  SlidersHorizontal, 
  Fingerprint, 
  Building2, 
  Check,
  FileCheck,
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';

/**
 * AICTE Regulatory Emblem Shield SVG
 */
function AicteShieldLogo({ className = "w-9 h-9" }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="shieldNavyGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0A1F3D" />
          <stop offset="55%" stopColor="#14396B" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>
        <linearGradient id="shieldGoldGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFC76B" />
          <stop offset="100%" stopColor="#FF7A00" />
        </linearGradient>
      </defs>
      <path 
        d="M32 4L10 12V28C10 44.5 19.5 55.5 32 60C44.5 55.5 54 44.5 54 28V12L32 4Z" 
        fill="url(#shieldNavyGrad)" 
        stroke="#FFFFFF" 
        strokeWidth="2.5" 
      />
      <path 
        d="M32 9L15 15.5V28C15 41.5 22.5 50.5 32 54.5C41.5 50.5 49 41.5 49 28V15.5L32 9Z" 
        stroke="url(#shieldGoldGrad)" 
        strokeWidth="1.5" 
        opacity="0.9" 
      />
      <circle cx="30" cy="30" r="10" stroke="#FFFFFF" strokeWidth="2.5" fill="none" />
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
 * 5 Demo Accounts Specifications
 */
const DEMO_ROLES = [
  {
    role: 'scrutiny_officer',
    title: { en: 'Scrutiny Officer', hi: 'संवीक्षा अधिकारी' },
    desc: { en: 'Desk scrutiny & Evidence Lens', hi: 'डेस्क संवीक्षा और एविडेंस लेंस' },
    email: 'scrutiny.officer@aicte-india.org',
    password: 'AicteOfficer@2025',
    icon: Search,
    color: '#0284C7',
    chipClass: 'bg-sky-50 text-sky-600 border border-sky-200',
  },
  {
    role: 'senior_officer',
    title: { en: 'Regional Officer', hi: 'क्षेत्रीय अधिकारी' },
    desc: { en: 'Approvals & What-If dry-runs', hi: 'अनुमोदन और व्हाट-इफ सिमुलेशन' },
    email: 'regional.officer@aicte-india.org',
    password: 'AicteRegional@2025',
    icon: Scale,
    color: '#6366F1',
    chipClass: 'bg-indigo-50 text-indigo-600 border border-indigo-200',
  },
  {
    role: 'admin',
    title: { en: 'Central Admin', hi: 'केंद्रीय प्रशासक' },
    desc: { en: 'Rule catalog & governance', hi: 'नियम सूची एवं शासन' },
    email: 'admin@aicte-india.org',
    password: 'AicteAdmin@2025',
    icon: SlidersHorizontal,
    color: '#9333EA',
    chipClass: 'bg-purple-50 text-purple-600 border border-purple-200',
  },
  {
    role: 'auditor',
    title: { en: 'Independent Auditor', hi: 'स्वतंत्र लेखा परीक्षक' },
    desc: { en: 'Read-only audit ledger', hi: 'केवल-पठन ऑडिट लेज़र' },
    email: 'auditor@aicte-india.org',
    password: 'AicteAuditor@2025',
    icon: Fingerprint,
    color: '#059669',
    chipClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
  },
  {
    role: 'institution_user',
    title: { en: 'Institution User (Apex Tech)', hi: 'संस्थान प्रतिनिधि (एपेक्स टेक)' },
    desc: { en: 'Dossier & pre-flight readiness', hi: 'संस्थान डॉसियर और प्री-फ्लाइट तैयारी' },
    email: 'registrar@apextech.edu.in',
    password: 'ApexPass@2025',
    icon: Building2,
    color: '#D97706',
    chipClass: 'bg-amber-50 text-amber-600 border border-amber-200',
  },
];

/**
 * Linked Hash Chain Blocks
 */
const HASH_CHAIN_BLOCKS = [
  { id: 'b1', name: 'dossier', hash: 'a3f9…c21', glowClass: 'hash-glow-0' },
  { id: 'b2', name: 'ocr_ingest', hash: '7b4e…91f', glowClass: 'hash-glow-1' },
  { id: 'b3', name: 'rule_check', hash: 'e12d…58a', glowClass: 'hash-glow-2' },
  { id: 'b4', name: 'gateway', hash: '84c0…37b', glowClass: 'hash-glow-3' },
  { id: 'b5', name: 'ed25519', hash: '9fa2…140', glowClass: 'hash-glow-4' },
];

/**
 * Translations Dictionary (EN / HI)
 */
const TRANSLATIONS = {
  en: {
    brandTag: "AICTE Regulatory Scrutiny & Document Verification",
    headline: "Every claim checked. Every decision human.",
    badge1: "Advisory only: no auto-rejection",
    badge2: "Tamper-evident audit ledger",
    badge3: "PII masked by role",
    teamFooter: "Team AnomalyX",
    welcomeBack: "Welcome back",
    subtext: "Sign in to continue to your workspace",
    advisoryPill: "AI Decision-Support • Indicator for review",
    emailLabel: "Official Email Address",
    passwordLabel: "Password",
    signInBtn: "Sign In to PRAMAAN-X",
    signingIn: "Verifying credentials...",
    rememberMe: "Remember me",
    needHelp: "Need help signing in?",
    demoSectionTitle: "Quick demo access",
    demoTag: "Demo",
    auditSecured: "Cryptographic Audit Ledger • JWT Secured",
    capsLockOn: "Caps Lock is ON",
    authError: "Authentication Error",
    helpTitle: "AICTE Scrutiny Cell Sign-In Help",
    helpDesc: "PRAMAAN-X is an authorized AICTE institutional scrutiny platform. For evaluation, click any demo account below to fill credentials.",
    helpClose: "Close Window"
  },
  hi: {
    brandTag: "एआईसीटीई विनियामक संवीक्षा एवं दस्तावेज़ सत्यापन",
    headline: "प्रत्येक दावे की जांच। प्रत्येक निर्णय मानवीय।",
    badge1: "केवल परामर्श: स्वतः अस्वीकृति नहीं",
    badge2: "छेड़छाड़-रोधी ऑडिट लेज़र",
    badge3: "भूमिका अनुसार पीआईआई छुपाया गया",
    teamFooter: "टीम अनोमली-एक्स (Team AnomalyX)",
    welcomeBack: "स्वागत है",
    subtext: "अपने कार्यक्षेत्र में जारी रखने के लिए साइन इन करें",
    advisoryPill: "एआई निर्णय-समर्थन • समीक्षा हेतु संकेतक",
    emailLabel: "आधिकारिक ईमेल पता",
    passwordLabel: "पासवर्ड",
    signInBtn: "PRAMAAN-X में साइन इन करें",
    signingIn: "क्रेडेंशियल्स सत्यापित हो रहे हैं...",
    rememberMe: "सत्र याद रखें",
    needHelp: "सहायता चाहिए?",
    demoSectionTitle: "त्वरित डेमो पहुंच",
    demoTag: "डेमो",
    auditSecured: "क्रिप्टोग्राफिक ऑडिट लेज़र • JWT सुरक्षित",
    capsLockOn: "कैप्स लॉक चालू है",
    authError: "प्रमाणीकरण त्रुटि",
    helpTitle: "एआईसीटीई संवीक्षा कक्ष साइन-इन सहायता",
    helpDesc: "PRAMAAN-X एक अधिकृत एआईसीटीई संस्थान संवीक्षा प्लेटफॉर्म है। मूल्यांकन हेतु, नीचे दिए किसी भी डेमो खाते पर क्लिक करें।",
    helpClose: "खिड़की बंद करें"
  }
};

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('scrutiny.officer@aicte-india.org');
  const [password, setPassword] = useState('AicteOfficer@2025');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [lang, setLang] = useState('en');
  const [showHelpModal, setShowHelpModal] = useState(false);

  const t = TRANSLATIONS[lang] || TRANSLATIONS.en;

  const handleSelectPreset = (preset) => {
    setEmail(preset.email);
    setPassword(preset.password);
    setErrorMessage('');
  };

  const handleKeyModifier = (e) => {
    if (e.getModifierState) {
      setCapsLockOn(e.getModifierState('CapsLock'));
    }
  };

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!email || !password) {
      setErrorMessage(
        lang === 'hi' 
          ? 'कृपया ईमेल और पासवर्ड दोनों दर्ज करें।' 
          : 'Please enter both email and password.'
      );
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      // 1. Authenticate with FastAPI backend and obtain JWT
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

  const firstFourRoles = DEMO_ROLES.slice(0, 4);
  const fifthRole = DEMO_ROLES[4];

  return (
    <div id="login-root" className="min-h-screen w-full flex flex-col lg:flex-row bg-[#F6F8FB] text-slate-900 selection:bg-cyan-500 selection:text-white">
      
      {/* ========================================================
          LEFT PANEL: Brand, Story & Trust (>=1024px)
          ======================================================== */}
      <section className="relative w-full lg:w-[48%] xl:w-[45%] bg-gradient-to-br from-[#0A1F3D] to-[#14396B] text-white p-6 sm:p-10 lg:p-12 flex flex-col justify-between overflow-hidden shrink-0 border-b lg:border-b-0 lg:border-r border-slate-800">
        {/* Subtle Background Dot Grid */}
        <div className="absolute inset-0 brand-dot-grid pointer-events-none opacity-40" aria-hidden="true" />
        
        {/* Soft Ambient Cyan/Blue Light Glows */}
        <div className="absolute top-1/4 -left-12 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" aria-hidden="true" />
        <div className="absolute bottom-1/4 right-0 w-80 h-80 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" aria-hidden="true" />

        <div className="relative z-10">
          {/* Tricolor Accent Rule */}
          <div className="flex h-1 w-20 rounded-full overflow-hidden mb-6" aria-hidden="true">
            <span className="w-1/3 bg-[#FF9933]" />
            <span className="w-1/3 bg-[#FFFFFF]" />
            <span className="w-1/3 bg-[#138808]" />
          </div>

          {/* Logo & Header Wordmark */}
          <div className="flex items-center space-x-3.5 mb-6">
            <div className="shrink-0 p-1.5 rounded-xl bg-slate-950/80 border border-slate-700/80 shadow-md">
              <AicteShieldLogo className="w-8 h-8 sm:w-9 sm:h-9" />
            </div>
            <div>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl sm:text-2xl font-bold tracking-tight text-white font-serif">
                  PRAMAAN
                </span>
                <span className="text-xl sm:text-2xl font-bold tracking-tight bg-gradient-to-r from-[#FFC76B] to-[#FF7A00] bg-clip-text text-transparent font-serif">
                  -X
                </span>
                <span className="font-devanagari text-xs text-amber-200/90 font-medium pl-1">
                  प्रमाण-X
                </span>
              </div>
              <p className="text-[11px] sm:text-xs text-slate-300 font-medium leading-tight mt-0.5">
                {t.brandTag}
              </p>
            </div>
          </div>

          {/* Headline */}
          <div className="mt-8 lg:mt-12 max-w-lg">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-bold text-white tracking-tight leading-snug">
              {t.headline}
            </h2>
          </div>

          {/* Animated Horizontal Hash-Chain Visual */}
          <div className="mt-8 lg:mt-12 pt-6 border-t border-slate-700/60 max-w-lg">
            <div className="flex items-center justify-between text-[11px] font-mono text-cyan-300 mb-3">
              <span className="flex items-center space-x-1.5 font-semibold">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span>SHA-256 Chained Verification Flow</span>
              </span>
              <span className="text-slate-400 text-[10px]">Ed25519 Signed</span>
            </div>

            {/* Blocks Row */}
            <div className="flex items-center justify-between gap-1 sm:gap-1.5">
              {HASH_CHAIN_BLOCKS.map((blk, idx) => (
                <React.Fragment key={blk.id}>
                  <div className={`flex-1 rounded-lg border p-1.5 sm:p-2 text-center transition-all ${blk.glowClass}`}>
                    <div className="text-[9px] font-mono text-cyan-200 font-semibold truncate">
                      {blk.name}
                    </div>
                    <div className="text-[9px] font-mono text-slate-300 truncate mt-0.5">
                      {blk.hash}
                    </div>
                  </div>
                  {idx < HASH_CHAIN_BLOCKS.length - 1 && (
                    <div className="w-1.5 sm:w-2 h-0.5 bg-cyan-400/50 shrink-0" aria-hidden="true" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Three Trust Badges */}
          <div className="mt-8 lg:mt-10 space-y-2.5 max-w-md">
            <div className="flex items-center space-x-3 text-xs sm:text-[13px] text-slate-200">
              <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-400/25 flex items-center justify-center shrink-0 text-cyan-300">
                <Scale className="w-3.5 h-3.5" />
              </div>
              <span>{t.badge1}</span>
            </div>

            <div className="flex items-center space-x-3 text-xs sm:text-[13px] text-slate-200">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-400/25 flex items-center justify-center shrink-0 text-emerald-300">
                <FileCheck className="w-3.5 h-3.5" />
              </div>
              <span>{t.badge2}</span>
            </div>

            <div className="flex items-center space-x-3 text-xs sm:text-[13px] text-slate-200">
              <div className="w-7 h-7 rounded-lg bg-violet-500/10 border border-violet-400/25 flex items-center justify-center shrink-0 text-violet-300">
                <EyeOff className="w-3.5 h-3.5" />
              </div>
              <span>{t.badge3}</span>
            </div>
          </div>
        </div>

        {/* Left Footer */}
        <div className="relative z-10 mt-8 pt-4 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>{t.teamFooter}</span>
          <span>APH 2025-26</span>
        </div>
      </section>

      {/* ========================================================
          RIGHT PANEL: Clean Centered Card Form
          ======================================================== */}
      <section className="relative flex-1 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-10 min-h-screen overflow-y-auto">
        {/* Soft Radial Light & Form Dot Grid */}
        <div className="absolute inset-0 form-dot-grid pointer-events-none opacity-40" aria-hidden="true" />
        <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-blue-500/[0.04] rounded-full blur-3xl pointer-events-none" aria-hidden="true" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-amber-500/[0.03] rounded-full blur-3xl pointer-events-none" aria-hidden="true" />

        {/* Clean White Card (Max Width 440px) */}
        <div className="relative z-10 w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200/90 p-5 sm:p-6 my-auto box-border">
          
          {/* Card Top Row: Heading + Language Segmented Pill */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight leading-tight">
                {t.welcomeBack}
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                {t.subtext}
              </p>
            </div>

            {/* Segmented Control Language Switcher */}
            <div className="shrink-0 flex items-center p-0.5 bg-slate-100 rounded-full border border-slate-200/80">
              <button
                type="button"
                onClick={() => setLang('en')}
                className={`lang-segment-btn ${lang === 'en' ? 'active' : ''}`}
                aria-label="Switch to English"
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setLang('hi')}
                className={`lang-segment-btn ${lang === 'hi' ? 'active' : ''}`}
                aria-label="Switch to Hindi"
              >
                हिं
              </button>
            </div>
          </div>

          {/* Statutory Safeguard Pill */}
          <div className="mb-4 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200/80 text-amber-900 text-xs flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="truncate font-medium">
              {t.advisoryPill}
            </span>
          </div>

          {/* Authentication Error Alert */}
          {errorMessage && (
            <div 
              role="alert" 
              aria-live="polite"
              className="mb-3.5 p-3 rounded-xl bg-rose-50 border border-rose-300 text-rose-800 text-xs flex items-start space-x-2 animate-shake"
            >
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="leading-snug">
                <span className="font-semibold">{t.authError}: </span>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          {/* Caps Lock Alert */}
          {capsLockOn && (
            <div className="mb-2 px-3 py-1 rounded-lg bg-amber-100 border border-amber-300 text-amber-900 text-[11px] flex items-center space-x-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>{t.capsLockOn}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3" noValidate>
            {/* Email Field */}
            <div>
              <label 
                htmlFor="login-email" 
                className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1"
              >
                {t.emailLabel}
              </label>
              <div className="relative group">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none group-focus-within:text-cyan-500 transition-colors" />
                <input
                  id="login-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@aicte-india.org"
                  className={`w-full ${errorMessage ? 'input-error' : ''}`}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label 
                htmlFor="login-password" 
                className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1"
              >
                {t.passwordLabel}
              </label>
              <div className="relative group">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none group-focus-within:text-cyan-500 transition-colors" />
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={handleKeyModifier}
                  onKeyUp={handleKeyModifier}
                  placeholder="••••••••••••"
                  className={`w-full ${errorMessage ? 'input-error' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="eye-toggle-btn absolute right-2 top-1/2 -translate-y-1/2"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              id="login-submit-btn"
              type="submit"
              disabled={isLoading}
              className="login-submit-btn mt-1"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>{t.signingIn}</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1.5">
                  <span>{t.signInBtn}</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </div>
              )}
            </button>
          </form>

          {/* Row below button: Remember Me & Need Help */}
          <div className="flex items-center justify-between pt-2.5 pb-1 text-xs">
            <label className="flex items-center space-x-2 cursor-pointer select-none text-slate-600">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-3.5 h-3.5 rounded text-[#14396B] focus:ring-cyan-500 border-slate-300"
              />
              <span className="text-xs">{t.rememberMe}</span>
            </label>

            <button
              type="button"
              onClick={() => setShowHelpModal(true)}
              className="link-text-btn"
            >
              {t.needHelp}
            </button>
          </div>

          {/* Demo Accounts Section */}
          <div className="mt-3.5 pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                {t.demoSectionTitle}
              </span>
              <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-semibold text-[10px]">
                {t.demoTag}
              </span>
            </div>

            {/* 2x2 Grid for first 4 roles */}
            <div 
              role="radiogroup" 
              aria-label="Preset Demo Accounts"
              className="space-y-1.5"
            >
              <div className="grid grid-cols-2 gap-1.5">
                {firstFourRoles.map((preset) => {
                  const isSelected = email === preset.email;
                  const Icon = preset.icon;

                  return (
                    <button
                      key={preset.role}
                      id={`preset-role-${preset.role}`}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      onClick={() => handleSelectPreset(preset)}
                      className={`role-card-btn ${isSelected ? 'selected' : ''}`}
                    >
                      <div className="flex items-center space-x-2 w-full min-w-0">
                        <div 
                          className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${preset.chipClass}`}
                          style={{ color: preset.color }}
                        >
                          <Icon className="w-3.5 h-3.5" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="text-[11px] font-semibold text-slate-800 truncate leading-tight">
                            {preset.title[lang] || preset.title.en}
                          </div>
                          <p className="text-[9.5px] text-slate-400 truncate leading-tight mt-0.5">
                            {preset.desc[lang] || preset.desc.en}
                          </p>
                        </div>

                        {isSelected && (
                          <div className="w-4 h-4 rounded-full bg-[#0284C7] text-white flex items-center justify-center shrink-0 ml-1">
                            <Check className="w-2.5 h-2.5 stroke-[3]" />
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* 5th Role: Institution User (Apex Tech) Full Width */}
              <button
                key={fifthRole.role}
                id={`preset-role-${fifthRole.role}`}
                type="button"
                role="radio"
                aria-checked={email === fifthRole.email}
                onClick={() => handleSelectPreset(fifthRole)}
                className={`role-card-btn ${email === fifthRole.email ? 'selected' : ''}`}
              >
                <div className="flex items-center space-x-2.5 w-full min-w-0">
                  <div 
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${fifthRole.chipClass}`}
                    style={{ color: fifthRole.color }}
                  >
                    <fifthRole.icon className="w-4 h-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="text-[11.5px] font-semibold text-slate-800 truncate leading-tight">
                      {fifthRole.title[lang] || fifthRole.title.en}
                    </div>
                    <p className="text-[10px] text-slate-400 truncate leading-tight mt-0.5">
                      {fifthRole.desc[lang] || fifthRole.desc.en}
                    </p>
                  </div>

                  {email === fifthRole.email && (
                    <div className="w-4 h-4 rounded-full bg-[#0284C7] text-white flex items-center justify-center shrink-0 ml-1">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </div>
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Footer inside the card: Real Pill with Lock icon and Pulse Dot */}
          <div className="mt-3.5 pt-2 text-center">
            <div className="audit-footer-pill space-x-1.5">
              <Lock className="w-3 h-3 text-slate-500" />
              <span className="pulse-dot" aria-hidden="true" />
              <span>{t.auditSecured}</span>
            </div>
          </div>
        </div>

        {/* Need Help Modal */}
        {showHelpModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fadeIn">
            <div className="bg-white rounded-2xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 space-y-3 box-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-xs">
                  <HelpCircle className="w-4 h-4 text-[#14396B]" />
                  <span>{t.helpTitle}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowHelpModal(false)}
                  className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1 cursor-pointer"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {t.helpDesc}
              </p>
              <button
                type="button"
                onClick={() => setShowHelpModal(false)}
                className="w-full py-2 bg-[#0A1F3D] text-white rounded-xl text-xs font-semibold hover:bg-[#14396B] transition cursor-pointer"
              >
                {t.helpClose}
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
