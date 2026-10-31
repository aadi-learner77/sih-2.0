import React, { useState, useRef, useEffect } from 'react';
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
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';
import './login.css';

/**
 * AICTE Regulatory Emblem Shield SVG
 * 48px, deep navy, gold accent, and cyan check
 */
function AicteShieldLogo({ className = "w-12 h-12" }) {
  return (
    <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <linearGradient id="shieldNavyGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0B1B45" />
          <stop offset="50%" stopColor="#0A1F3D" />
          <stop offset="100%" stopColor="#14396B" />
        </linearGradient>
        <linearGradient id="shieldGoldGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFC76B" />
          <stop offset="100%" stopColor="#FF9933" />
        </linearGradient>
      </defs>
      <path 
        d="M32 4L10 12V28C10 44.5 19.5 55.5 32 60C44.5 55.5 54 44.5 54 28V12L32 4Z" 
        fill="url(#shieldNavyGrad)" 
        stroke="#FFFFFF" 
        strokeWidth="1.5" 
      />
      <path 
        d="M32 9L15 15.5V28C15 41.5 22.5 50.5 32 54.5C41.5 50.5 49 41.5 49 28V15.5L32 9Z" 
        stroke="url(#shieldGoldGrad)" 
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
 * 5 Demo Accounts Specifications with Tinted Icon Chips
 */
const DEMO_ROLES = [
  {
    role: 'scrutiny_officer',
    title: { en: 'Scrutiny Officer', hi: 'संवीक्षा अधिकारी' },
    desc: { en: 'Desk scrutiny & Evidence Lens', hi: 'डेस्क संवीक्षा और एविडेंस लेंस' },
    email: 'scrutiny.officer@aicte-india.org',
    password: 'AicteOfficer@2025',
    icon: Search,
    chipBg: 'rgba(14, 165, 233, 0.12)',
    chipBorder: 'rgba(14, 165, 233, 0.25)',
    iconColor: '#0284C7',
  },
  {
    role: 'senior_officer',
    title: { en: 'Regional Officer', hi: 'क्षेत्रीय अधिकारी' },
    desc: { en: 'Approvals & What-If dry-runs', hi: 'अनुमोदन और व्हाट-इफ सिमुलेशन' },
    email: 'regional.officer@aicte-india.org',
    password: 'AicteRegional@2025',
    icon: Scale,
    chipBg: 'rgba(20, 57, 107, 0.12)',
    chipBorder: 'rgba(20, 57, 107, 0.25)',
    iconColor: '#14396B',
  },
  {
    role: 'admin',
    title: { en: 'Central Admin', hi: 'केंद्रीय प्रशासक' },
    desc: { en: 'Rule catalog & governance', hi: 'नियम सूची एवं शासन' },
    email: 'admin@aicte-india.org',
    password: 'AicteAdmin@2025',
    icon: SlidersHorizontal,
    chipBg: 'rgba(124, 58, 237, 0.12)',
    chipBorder: 'rgba(124, 58, 237, 0.25)',
    iconColor: '#7C3AED',
  },
  {
    role: 'auditor',
    title: { en: 'Independent Auditor', hi: 'स्वतंत्र लेखा परीक्षक' },
    desc: { en: 'Read-only audit ledger', hi: 'केवल-पठन ऑडिट लेज़र' },
    email: 'auditor@aicte-india.org',
    password: 'AicteAuditor@2025',
    icon: Fingerprint,
    chipBg: 'rgba(16, 185, 129, 0.12)',
    chipBorder: 'rgba(16, 185, 129, 0.25)',
    iconColor: '#059669',
  },
  {
    role: 'institution_user',
    title: { en: 'Institution User (Apex Tech)', hi: 'संस्थान प्रतिनिधि (एपेक्स टेक)' },
    desc: { en: 'Dossier & pre-flight readiness', hi: 'संस्थान डॉसियर और प्री-फ्लाइट तैयारी' },
    email: 'registrar@apextech.edu.in',
    password: 'ApexPass@2025',
    icon: Building2,
    chipBg: 'rgba(245, 158, 11, 0.12)',
    chipBorder: 'rgba(245, 158, 11, 0.25)',
    iconColor: '#D97706',
  },
];

/**
 * Translations Dictionary (EN / HI)
 */
const TRANSLATIONS = {
  en: {
    brandTag: "AICTE Regulatory Scrutiny & Document Verification",
    welcomeBack: "Welcome back",
    subtext: "Sign in to continue to your workspace",
    advisoryPill: "AI Decision-Support • Indicator for review",
    emailLabel: "Official Email Address",
    passwordLabel: "Password",
    signInBtn: "Sign In to PRAMAAN-X",
    verifyingBtn: "Verifying…",
    verifiedBtn: "Authenticated ✓",
    rememberMe: "Remember me",
    needHelp: "Need help signing in?",
    demoSectionTitle: "Quick demo access",
    demoTag: "Demo",
    auditSecured: "Cryptographic Audit Ledger • JWT Secured",
    capsLockOn: "Caps Lock is ON",
    authError: "Authentication Error",
    helpTitle: "AICTE Scrutiny Cell Sign-In Help",
    helpDesc: "PRAMAAN-X is an authorized AICTE institutional scrutiny platform. For evaluation, click any demo account below to fill credentials automatically.",
    helpClose: "Close Window"
  },
  hi: {
    brandTag: "एआईसीटीई विनियामक संवीक्षा एवं दस्तावेज़ सत्यापन",
    welcomeBack: "स्वागत है",
    subtext: "अपने कार्यक्षेत्र में जारी रखने के लिए साइन इन करें",
    advisoryPill: "एआई निर्णय-समर्थन • समीक्षा हेतु संकेतक",
    emailLabel: "आधिकारिक ईमेल पता",
    passwordLabel: "पासवर्ड",
    signInBtn: "PRAMAAN-X में साइन इन करें",
    verifyingBtn: "सत्यापित हो रहा है…",
    verifiedBtn: "प्रमाणित ✓",
    rememberMe: "सत्र याद रखें",
    needHelp: "सहायता चाहिए?",
    demoSectionTitle: "त्वरित डेमो पहुंच",
    demoTag: "डेमो",
    auditSecured: "क्रिप्टोग्राफिक ऑडिट लेज़र • JWT सुरक्षित",
    capsLockOn: "कैप्स लॉक चालू है",
    authError: "प्रमाणीकरण त्रुटि",
    helpTitle: "एआईसीटीई संवीक्षा कक्ष साइन-इन सहायता",
    helpDesc: "PRAMAAN-X एक अधिकृत एआईसीटीई संस्थान संवीक्षा प्लेटफॉर्म है। मूल्यांकन हेतु, क्रेडेंशियल्स स्वतः भरने के लिए नीचे दिए किसी भी डेमो खाते पर क्लिक करें।",
    helpClose: "खिड़की बंद करें"
  }
};

export default function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState('scrutiny.officer@aicte-india.org');
  const [password, setPassword] = useState('AicteOfficer@2025');
  const [selectedRole, setSelectedRole] = useState('scrutiny_officer');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [cardShake, setCardShake] = useState(false);
  const [capsLockOn, setCapsLockOn] = useState(false);
  const [lang, setLang] = useState('en');
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [focusedInput, setFocusedInput] = useState(null);
  const [inputHighlight, setInputHighlight] = useState(false);

  const typingTimerRef = useRef(null);
  const emailInputRef = useRef(null);
  const passwordInputRef = useRef(null);
  const t = TRANSLATIONS[lang] || TRANSLATIONS.en;

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    };
  }, []);

  // Smooth Typewriter Simulation for Demo Roles (~18ms per character)
  const handleSelectPreset = (preset) => {
    setSelectedRole(preset.role);
    setErrorMessage('');
    
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);

    setInputHighlight(true);
    setTimeout(() => setInputHighlight(false), 450);

    const targetEmail = preset.email;
    const targetPassword = preset.password;
    let eIdx = 0;
    let pIdx = 0;

    setEmail('');
    setPassword('');

    const typeStep = () => {
      if (eIdx <= targetEmail.length) {
        setEmail(targetEmail.slice(0, eIdx));
        eIdx++;
        typingTimerRef.current = setTimeout(typeStep, 18);
      } else if (pIdx <= targetPassword.length) {
        setPassword(targetPassword.slice(0, pIdx));
        pIdx++;
        typingTimerRef.current = setTimeout(typeStep, 18);
      }
    };

    typeStep();
  };

  const handleKeyModifier = (e) => {
    if (e.getModifierState) {
      setCapsLockOn(e.getModifierState('CapsLock'));
    }
  };


  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);

    // Ensure we have current values even if typing animation was interrupted
    const currentPreset = DEMO_ROLES.find(r => r.role === selectedRole);
    const submitEmail = (email && email.includes('@')) ? email.trim() : (currentPreset ? currentPreset.email : email.trim());
    const submitPassword = password ? password : (currentPreset ? currentPreset.password : password);

    if (!submitEmail || !submitPassword) {
      setErrorMessage(
        lang === 'hi' 
          ? 'कृपया ईमेल और पासवर्ड दोनों दर्ज करें।' 
          : 'Please enter both email and password.'
      );
      triggerCardShake();
      if (!submitEmail) {
        emailInputRef.current?.focus();
      } else {
        passwordInputRef.current?.focus();
      }
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      // 1. Authenticate with FastAPI backend and obtain JWT
      const loginRes = await api.login(submitEmail, submitPassword);
      const token = loginRes?.access_token;
      if (!token) {
        throw new Error('Access token not returned by authentication service.');
      }

      // 2. Persist JWT token
      localStorage.setItem('pramaan_token', token);

      // 3. Derive current user and role strictly from /auth/me
      const userProfile = await api.getMe();
      localStorage.setItem('pramaan_user', JSON.stringify(userProfile));

      // 4. Success State: Green button with checkmark for ~600ms
      setIsSuccess(true);
      setTimeout(() => {
        onLoginSuccess(userProfile);
      }, 600);
    } catch (err) {
      console.error('Login failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Authentication failed. Please verify credentials.';
      setErrorMessage(detail);
      localStorage.removeItem('pramaan_token');
      localStorage.removeItem('pramaan_user');
      triggerCardShake();
    } finally {
      setIsLoading(false);
    }
  };

  const triggerCardShake = () => {
    setCardShake(true);
    setTimeout(() => setCardShake(false), 380);
  };

  return (
    <div 
      id="login-root" 
      className="login-root relative min-h-screen w-full flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8"
    >
      {/* ========================================================
          BACKGROUND: Deep Navy (#0B1B45 -> #0A1F3D -> #081433)
          Faint White Dot Grid + Rising Soft Blue Glow + Aurora Blobs
          ======================================================== */}
      {/* Faint White Dot Grid (opacity ~0.06) */}
      <div className="absolute inset-0 login-bg-dots pointer-events-none opacity-40" aria-hidden="true" />

      {/* Soft, large, blurred light-blue/silver glow rising from the bottom centre behind the card */}
      <div className="login-bottom-glow" aria-hidden="true" />

      {/* Faint Cyan / Violet Aurora Blobs at sides */}
      <div className="absolute top-1/3 -left-20 w-[480px] h-[480px] bg-[#22D3EE]/[0.10] rounded-full blur-[140px] pointer-events-none login-aurora-blob-1" aria-hidden="true" />
      <div className="absolute bottom-1/4 -right-20 w-[480px] h-[480px] bg-[#8B5CF6]/[0.10] rounded-full blur-[140px] pointer-events-none login-aurora-blob-2" aria-hidden="true" />
      <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-[520px] h-[360px] bg-[#14396B]/[0.18] rounded-full blur-[120px] pointer-events-none login-aurora-blob-3" aria-hidden="true" />

      {/* Decorative Hash-Chain Line with Travelling Dots */}
      <div className="absolute inset-x-0 top-1/5 pointer-events-none opacity-25" aria-hidden="true">
        <div className="hash-dot-line">
          <span className="hash-stream-dot-1" />
        </div>
      </div>
      <div className="absolute inset-x-0 bottom-1/4 pointer-events-none opacity-20" aria-hidden="true">
        <div className="hash-dot-line">
          <span className="hash-stream-dot-2" />
          <span className="hash-stream-dot-3" />
        </div>
      </div>

      {/* ========================================================
          WEB-APP WIDE CARD (max-w-[1040px], Two Columns on Desktop)
          Rotating Conic Border + Moving Gold Comet + Neon Streaks
          ======================================================== */}
      <div className="relative z-20 w-full max-w-[1040px] flex flex-col items-center">
        {/* Ambient Warm Gold Glow Bleeding onto Navy Page */}
        <div className="login-card-ambient-gold-glow" aria-hidden="true" />

        {/* Card Border Wrap (Rotating Conic Border Cyan -> Violet -> Cyan) */}
        <div 
          className={`relative z-20 login-card-border-wrap animate-card-entrance w-full ${
            cardShake ? 'animate-shake' : ''
          }`}
        >
          {/* Moving Gold Light Comet Border (sitting on outer edge of card) */}
          <div className="login-card-gold-comet-border" aria-hidden="true" />

          {/* Top Edge Neon Streak (Cyan -> Violet -> Cyan) */}
          <div className="login-card-scanner-beam" aria-hidden="true" />

          {/* Bottom Edge Neon Streak (Mirrors top, sweeps right to left) */}
          <div className="login-card-bottom-streak" aria-hidden="true" />

          {/* Card Main Surface: Solid White with Rounded-3xl */}
          <div 
            className="w-full login-white-card-surface p-6 sm:p-8 lg:p-10 box-border"
          >
          {/* Subtle Grain / Noise Overlay */}
          <div className="login-noise-overlay" aria-hidden="true" />

          {/* Diagonal Slow Light Sheen Across Card */}
          <div className="login-card-sheen" aria-hidden="true" />

          {/* Inside Card: Two Columns Grid on Desktop (>= 1024px) */}
          <div className="relative z-20 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-stretch pt-1">
            
            {/* ========================================================
                LEFT COLUMN (about 55% -> lg:col-span-7)
                Logo + Wordmark + Welcome Back + Form
                ======================================================== */}
            <div className="lg:col-span-7 flex flex-col justify-between space-y-4 sm:space-y-5">
              
              {/* Brand Logo & Wordmark */}
              <div className="stagger-1 select-none">
                <div className="flex items-center space-x-3.5 mb-1.5">
                  {/* Shield Emblem Tile in Dark Navy */}
                  <div className="login-shield-wrapper p-2 rounded-2xl flex items-center justify-center shrink-0">
                    <AicteShieldLogo className="w-12 h-12" />
                  </div>

                  {/* Wordmark: PRAMAAN in navy Inter 800, -X in saffron gradient */}
                  <div>
                    <div className="flex items-baseline space-x-1.5">
                      <span className="text-2xl sm:text-3xl login-wordmark-pramaan">
                        PRAMAAN
                      </span>
                      <span className="text-2xl sm:text-3xl login-wordmark-x">
                        -X
                      </span>
                      <span className="font-devanagari text-xs login-devanagari-tag font-medium pl-1.5 opacity-90">
                        प्रमाण-X
                      </span>
                    </div>
                    <p className="text-[11px] sm:text-xs font-normal tracking-wide mt-1" style={{ color: '#51607F' }}>
                      {t.brandTag}
                    </p>
                  </div>
                </div>
              </div>

              {/* Welcome Back & Sub-text */}
              <div className="stagger-2 pt-1">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A1F3D] leading-tight">
                  {t.welcomeBack}
                </h1>
                <p className="text-xs mt-1" style={{ color: '#51607F' }}>
                  {t.subtext}
                </p>
              </div>

              {/* AI Decision-Support Indicator Pill (Amber) */}
              <div className="login-advisory-pill stagger-2">
                <ShieldCheck className="w-4 h-4 shrink-0" style={{ color: '#7A4B00' }} />
                <span className="truncate leading-tight">
                  {t.advisoryPill}
                </span>
              </div>

              {/* Inline Error Message */}
              {errorMessage && (
                <div 
                  id="login-error-alert"
                  role="alert" 
                  aria-live="polite"
                  className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2 animate-shake"
                >
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div className="leading-snug">
                    <span className="font-semibold text-rose-900">{t.authError}: </span>
                    <span>{errorMessage}</span>
                  </div>
                </div>
              )}

              {/* Caps Lock Alert */}
              {capsLockOn && (
                <div className="px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>{t.capsLockOn}</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleSubmit} className="space-y-3.5 stagger-3" noValidate>
                {/* Email Field with Floating Focus Highlight & Progress Line */}
                <div>
                  <label 
                    htmlFor="login-email" 
                    className="block text-[11px] font-semibold uppercase tracking-wider mb-1.5"
                    style={{ color: focusedInput === 'email' ? '#14396B' : '#3B4A6B' }}
                  >
                    {t.emailLabel}
                  </label>
                  <div className="relative group">
                    <Mail 
                      className={`login-input-icon absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 pointer-events-none ${
                        focusedInput === 'email' ? 'focused' : ''
                      }`} 
                    />
                    <input
                      ref={emailInputRef}
                      id="login-email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      aria-invalid={!!errorMessage}
                      aria-describedby={errorMessage ? "login-error-alert" : undefined}
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      onFocus={() => setFocusedInput('email')}
                      onBlur={() => setFocusedInput(null)}
                      placeholder="officer@aicte-india.org"
                      className={`${errorMessage ? 'input-error' : ''} ${
                        inputHighlight ? 'ring-2 ring-[#14396B]' : ''
                      }`}
                    />
                    {/* Bottom Growing Progress Line on Focus */}
                    <div className="absolute bottom-0 left-0 right-0 h-[2px] overflow-hidden rounded-b-xl pointer-events-none">
                      <div 
                        className="input-progress-line"
                        style={{ width: focusedInput === 'email' ? '100%' : '0%' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Password Field with Morphing Eye Toggle & Progress Line */}
                <div>
                  <label 
                    htmlFor="login-password" 
                    className="block text-[11px] font-semibold uppercase tracking-wider mb-1.5"
                    style={{ color: focusedInput === 'password' ? '#14396B' : '#3B4A6B' }}
                  >
                    {t.passwordLabel}
                  </label>
                  <div className="relative group">
                    <Lock 
                      className={`login-input-icon absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 pointer-events-none ${
                        focusedInput === 'password' ? 'focused' : ''
                      }`} 
                    />
                    <input
                      ref={passwordInputRef}
                      id="login-password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      aria-invalid={!!errorMessage}
                      aria-describedby={errorMessage ? "login-error-alert" : undefined}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={handleKeyModifier}
                      onKeyUp={handleKeyModifier}
                      onFocus={() => setFocusedInput('password')}
                      onBlur={() => setFocusedInput(null)}
                      placeholder="••••••••••••"
                      className={`${errorMessage ? 'input-error' : ''} ${
                        inputHighlight ? 'ring-2 ring-[#14396B]' : ''
                      }`}
                    />

                    {/* Borderless Eye Toggle Button inside Input */}
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="login-eye-toggle-btn"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      aria-pressed={showPassword}
                    >
                      <div className="transition-transform duration-200 hover:scale-110">
                        {showPassword ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </div>
                    </button>

                    {/* Bottom Growing Progress Line on Focus */}
                    <div className="absolute bottom-0 left-0 right-0 h-[2px] overflow-hidden rounded-b-xl pointer-events-none">
                      <div 
                        className="input-progress-line"
                        style={{ width: focusedInput === 'password' ? '100%' : '0%' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Primary Submit Button with Navy Gradient, Moving Shimmer & Success State */}
                <button
                  id="login-submit-btn"
                  type="submit"
                  disabled={isLoading || isSuccess}
                  className={`login-submit-btn login-submit-btn-primary group mt-2 ${isSuccess ? 'success-state' : ''}`}
                >
                  {/* Shimmer Sweep Effect */}
                  <div className="btn-shimmer-effect" aria-hidden="true" />

                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>{t.verifyingBtn}</span>
                    </div>
                  ) : isSuccess ? (
                    <div className="flex items-center space-x-2">
                      <Check className="w-5 h-5 stroke-[2.5] animate-scale" />
                      <span>{t.verifiedBtn}</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <span>{t.signInBtn}</span>
                      <ArrowRight className="w-4 h-4 transition-transform duration-150 group-hover:translate-x-1" />
                    </div>
                  )}
                </button>
              </form>

              {/* Row below button: Remember Me & Need Help Text Link */}
              <div className="flex items-center justify-between pt-1 pb-1 text-xs stagger-4">
                {/* Custom Checkbox with Animated SVG Check-Draw */}
                <label className="flex items-center space-x-2 cursor-pointer select-none" style={{ color: '#3B4A6B' }}>
                  <div className="relative flex items-center justify-center">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="sr-only"
                    />
                    <div 
                      className="w-4 h-4 rounded border transition-colors flex items-center justify-center"
                      style={{
                        backgroundColor: rememberMe ? '#0A1F3D' : '#FFFFFF',
                        borderColor: rememberMe ? '#0A1F3D' : '#D5DEF5'
                      }}
                    >
                      <svg className="w-3 h-3 text-white pointer-events-none" viewBox="0 0 16 16" fill="none">
                        <path 
                          d="M3.5 8.5L6.5 11.5L12.5 4.5" 
                          stroke="currentColor" 
                          strokeWidth="2.2" 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          style={{
                            strokeDasharray: 18,
                            strokeDashoffset: rememberMe ? 0 : 18,
                            transition: 'stroke-dashoffset 200ms ease'
                          }} 
                        />
                      </svg>
                    </div>
                  </div>
                  <span className="text-xs font-normal" style={{ color: '#3B4A6B' }}>{t.rememberMe}</span>
                </label>

                {/* Plain Text Link: Need help signing in? (#14396B, underline on hover) */}
                <button
                  type="button"
                  onClick={() => setShowHelpModal(true)}
                  className="login-need-help-link"
                >
                  {t.needHelp}
                </button>
              </div>

            </div>

            {/* ========================================================
                RIGHT COLUMN (about 45% -> lg:col-span-5)
                Quick Demo Access: All 5 roles in clean single-column list
                Separated by faint vertical divider (#E3E9FA)
                ======================================================== */}
            <div className="lg:col-span-5 lg:pl-8 relative flex flex-col justify-between stagger-5">
              
              {/* Faint Vertical Divider (Desktop only) */}
              <div 
                className="hidden lg:block absolute left-0 top-0 bottom-0 w-[1px] pointer-events-none" 
                style={{ background: '#E3E9FA' }}
                aria-hidden="true" 
              />

              {/* Horizontal Divider for Mobile (< 1024px) */}
              <div 
                className="lg:hidden h-[1px] w-full my-4" 
                style={{ background: '#E3E9FA' }}
                aria-hidden="true" 
              />

              {/* Demo Section Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: '#3B4A6B' }}>
                  {t.demoSectionTitle}
                </span>
                <span className="login-demo-badge">
                  {t.demoTag}
                </span>
              </div>

              {/* 5 Preset Role Cards in a Clean Single-Column Stack */}
              <div 
                role="radiogroup" 
                aria-label="Preset Demo Accounts"
                className="flex flex-col space-y-2.5 w-full flex-1 justify-between"
              >
                {DEMO_ROLES.map((preset) => {
                  const isSelected = selectedRole === preset.role;
                  const Icon = preset.icon;

                  return (
                    <button
                      key={preset.role}
                      id={`preset-role-${preset.role}`}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      onClick={() => handleSelectPreset(preset)}
                      className={`role-preset-card group ${isSelected ? 'selected' : ''}`}
                    >
                      <div className="flex items-center space-x-3 w-full min-w-0">
                        {/* Colored Icon Chip with Visible Icon */}
                        <div 
                          className="role-chip-container"
                          style={{
                            backgroundColor: preset.chipBg,
                            border: `1px solid ${preset.chipBorder}`
                          }}
                        >
                          <Icon className="w-4 h-4" style={{ stroke: preset.iconColor, color: preset.iconColor }} />
                        </div>

                        {/* Role Title and 1-Line Description (No awkward wrapping) */}
                        <div className="min-w-0 flex-1 text-left">
                          <div className="role-preset-title truncate">
                            {preset.title[lang] || preset.title.en}
                          </div>
                          <p className="role-preset-desc truncate">
                            {preset.desc[lang] || preset.desc.en}
                          </p>
                        </div>

                        {/* Selected Check Pill in Blue (#0B7FD6) */}
                        {isSelected && (
                          <div className="w-5 h-5 rounded-full bg-[#0B7FD6] text-white flex items-center justify-center shrink-0 ml-1.5 shadow-[0_0_8px_rgba(11,127,214,0.4)] animate-scale">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

            </div>

          </div>

          {/* ========================================================
              FOOTER STRIP (Spanning both columns inside the card)
              LEFT: Audit Ledger Pill
              RIGHT: EN | हिं Language Toggle
              ======================================================== */}
          <div 
            className="relative z-20 mt-8 pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 w-full stagger-6"
            style={{ borderTop: '1px solid #E3E9FA' }}
          >
            {/* LEFT: Cryptographic Audit Ledger Pill */}
            <div className="login-footer-pill space-x-2 group cursor-default">
              <Lock className="w-3.5 h-3.5 text-[#14532D] group-hover:rotate-12 transition-transform duration-200" />
              <span className="login-pulse-dot" aria-hidden="true" />
              <span className="text-[11px] font-medium" style={{ color: '#14532D' }}>{t.auditSecured}</span>
            </div>

            {/* RIGHT: Language Segmented Control (EN | हिं) */}
            <div className="login-lang-control">
              {/* Sliding Pill Indicator */}
              <div 
                className="login-lang-slider"
                style={{
                  transform: lang === 'hi' ? 'translateX(calc(100% + 2.5px))' : 'translateX(0)',
                }}
                aria-hidden="true"
              />
              <button
                type="button"
                onClick={() => setLang('en')}
                className={`login-lang-btn ${lang === 'en' ? 'active' : ''}`}
                aria-label="Switch to English"
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setLang('hi')}
                className={`login-lang-btn ${lang === 'hi' ? 'active' : ''}`}
                aria-label="Switch to Hindi"
              >
                हिं
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>

      {/* Team AnomalyX: small centred text below the card on the navy background */}
      <div className="mt-4 text-center text-xs tracking-wider font-medium text-white/70 select-none stagger-6">
        Team AnomalyX
      </div>

      {/* ========================================================
          NEED HELP SIGNING IN MODAL
          ======================================================== */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0A1F3D]/60 backdrop-blur-sm animate-fadeIn">
          <div className="login-modal-glass p-6 max-w-sm w-full space-y-4 box-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-[#0A1F3D] font-bold text-sm">
                <HelpCircle className="w-4 h-4 text-[#14396B]" />
                <span>{t.helpTitle}</span>
              </div>
              <button
                type="button"
                onClick={() => setShowHelpModal(false)}
                className="text-[#51607F] hover:text-[#0A1F3D] text-sm font-bold p-1 cursor-pointer transition-colors"
                aria-label="Close help modal"
              >
                ✕
              </button>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: '#51607F' }}>
              {t.helpDesc}
            </p>
            <button
              type="button"
              onClick={() => setShowHelpModal(false)}
              className="w-full py-2.5 bg-gradient-to-r from-[#0A1F3D] to-[#14396B] hover:from-[#14396B] hover:to-[#1E4F94] text-white rounded-xl text-xs font-semibold transition cursor-pointer shadow-lg shadow-[#0A1F3D]/25 border border-white/10"
            >
              {t.helpClose}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
