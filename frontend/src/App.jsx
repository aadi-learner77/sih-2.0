import React, { useState, useEffect, useRef, lazy, Suspense } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import Spinner from './components/ui/Spinner';
import FloatingContactButton from './components/ui/FloatingContactButton';
import StorageConsentBanner from './components/ui/StorageConsentBanner';
import { useUtm } from './hooks/useUtm';
import { ShieldAlert, ArrowUp } from 'lucide-react';
import { api } from './services/api';

// Code-split dynamic page imports for optimal bundle size
const Dashboard = lazy(() => import('./pages/Dashboard'));
const EvidenceLens = lazy(() => import('./components/EvidenceLens'));
const ImpossibilityGraph = lazy(() => import('./components/ImpossibilityGraph'));
const PhotoReuseRadar = lazy(() => import('./components/PhotoReuseRadar'));
const RuleConfigPage = lazy(() => import('./pages/RuleConfigPage'));
const PreFlightScorecard = lazy(() => import('./components/PreFlightScorecard'));
const AuditAndReceiptsPage = lazy(() => import('./pages/AuditAndReceiptsPage'));
const InspectionPlannerPage = lazy(() => import('./pages/InspectionPlannerPage'));
const ManualReviewQueuePage = lazy(() => import('./pages/ManualReviewQueuePage'));
const DocumentIntelligencePage = lazy(() => import('./pages/DocumentIntelligencePage'));

const ROLE_PERMITTED_TABS = {
  institution_user: ['dashboard', 'preflight', 'audit-ledger'],
  auditor: ['dashboard', 'evidence-lens', 'impossibility-engine', 'manual-review-queue', 'document-intelligence', 'audit-ledger'],
  scrutiny_officer: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'inspection-planner', 'audit-ledger'],
  senior_officer: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'regulations', 'inspection-planner', 'audit-ledger'],
  admin: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'regulations', 'inspection-planner', 'audit-ledger'],
};

export default function App() {
  useUtm();

  // All state declarations first to avoid temporal dead zone
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentRole, setCurrentRole] = useState('scrutiny_officer');
  const [adminPreviewRole, setAdminPreviewRole] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [applications, setApplications] = useState([]);
  const [activeApplication, setActiveApplication] = useState(null);
  const [evidenceLensData, setEvidenceLensData] = useState(null);
  const [evidenceLensError, setEvidenceLensError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [sidebarCounts, setSidebarCounts] = useState({ impossibilities: 0, advisoryFlags: 0 });
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem('pramaan_sidebar_collapsed') === 'true';
    } catch (e) {
      return false;
    }
  });
  const [isScrolled, setIsScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const mainScrollRef = useRef(null);

  // Passive rAF-throttled scroll listener on <main> container (Item 4 & 5)
  useEffect(() => {
    const el = mainScrollRef.current;
    if (!el) return;

    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          if (!el) return;
          const scrollTop = el.scrollTop;
          const scrollHeight = el.scrollHeight - el.clientHeight;

          setIsScrolled(scrollTop > 8);
          setShowBackToTop(scrollTop > 400);
          setScrollProgress(scrollHeight > 0 ? Math.min(Math.max(scrollTop / scrollHeight, 0), 1) : 0);
          ticking = false;
        });
        ticking = true;
      }
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [isAuthenticated, activeTab]);

  const scrollToTop = () => {
    if (mainScrollRef.current) {
      const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      mainScrollRef.current.scrollTo({ 
        top: 0, 
        behavior: prefersReducedMotion ? 'auto' : 'smooth' 
      });
    }
  };

  // Liquid hover effect coordinate tracker (Part 2.2 & Part 3.1)
  useEffect(() => {
    const handlePointerMove = (e) => {
      const el = e.target?.closest?.('.btn-liquid, .kpi-glass-card, button.bg-primary');
      if (el) {
        const rect = el.getBoundingClientRect();
        el.style.setProperty('--mx', `${e.clientX - rect.left}px`);
        el.style.setProperty('--my', `${e.clientY - rect.top}px`);
      }
    };
    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    return () => window.removeEventListener('pointermove', handlePointerMove);
  }, []);

  // Calculate actual authenticated role vs active preview role
  const actualUserRole = currentUser?.role || currentRole;
  const isAdmin = actualUserRole === 'admin';
  const effectiveRole = adminPreviewRole || actualUserRole;

  const handleToggleSidebarCollapse = () => {
    setIsSidebarCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('pramaan_sidebar_collapsed', String(next));
      } catch (e) {}
      return next;
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('pramaan_token');
    localStorage.removeItem('pramaan_user');
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentRole('scrutiny_officer');
    setAdminPreviewRole(null);
    setApplications([]);
    setActiveApplication(null);
    setEvidenceLensData(null);
    setEvidenceLensError(null);
    setSidebarCounts({ impossibilities: 0, advisoryFlags: 0 });
  };

  // Only Admin can switch demo preview roles (A1)
  const handleAdminSwitchRole = (newRole) => {
    if (isAdmin) {
      setAdminPreviewRole(newRole);
      const allowed = ROLE_PERMITTED_TABS[newRole] || ROLE_PERMITTED_TABS.scrutiny_officer;
      if (!allowed.includes(activeTab)) {
        setActiveTab('dashboard');
      }
      loadData(newRole);
    }
  };

  const handleReturnToAdmin = () => {
    setAdminPreviewRole(null);
    const allowed = ROLE_PERMITTED_TABS.admin;
    if (!allowed.includes(activeTab)) {
      setActiveTab('dashboard');
    }
    loadData('admin');
  };

  const loadData = async (role = effectiveRole) => {
    setLoading(true);
    try {
      const apps = await api.getApplications();
      if (apps && Array.isArray(apps) && apps.length > 0) {
        setApplications(apps);
        setIsLiveMode(true);

        const sortedApps = [...apps].sort((a, b) => {
          const findingsA = (a.advisory_flags_count || 0) + (a.impossibility_flags_count || 0) + (a.forensic_flags_count || 0);
          const findingsB = (b.advisory_flags_count || 0) + (b.impossibility_flags_count || 0) + (b.forensic_flags_count || 0);
          if (findingsB !== findingsA) {
            return findingsB - findingsA;
          }
          const scoreA = a.preflight_readiness_score !== undefined ? a.preflight_readiness_score : 100;
          const scoreB = b.preflight_readiness_score !== undefined ? b.preflight_readiness_score : 100;
          return scoreA - scoreB;
        });

        const primary = sortedApps[0] || apps[0];
        setActiveApplication(primary);
        try {
          setEvidenceLensError(null);
          const lens = await api.getEvidenceLens(primary.id);
          setEvidenceLensData(lens);
        } catch (lensErr) {
          const detail = lensErr.response?.data?.detail || lensErr.message || 'Error fetching evidence lens';
          console.warn('Evidence lens fetch fallback:', detail);
          setEvidenceLensError(`Evidence lens request failed for ${primary.application_no || `App #${primary.id}`}: ${detail}`);
          setEvidenceLensData(null);
        }

        try {
          const [impRes, findingsRes, queueRes] = await Promise.allSettled([
            api.getImpossibilities(),
            api.getAllFindings(),
            api.getManualReviewQueue()
          ]);
          const impCount = impRes.status === 'fulfilled' && Array.isArray(impRes.value) ? impRes.value.length : 0;
          const advCount = findingsRes.status === 'fulfilled' && Array.isArray(findingsRes.value) 
            ? findingsRes.value.length 
            : (primary?.advisory_flags_count || 0);
          const queueCount = queueRes.status === 'fulfilled' && Array.isArray(queueRes.value) ? queueRes.value.length : 0;
          setSidebarCounts({
            impossibilities: impCount,
            advisoryFlags: advCount,
            manualReview: queueCount
          });
        } catch (_cntErr) {}
      } else {
        setApplications([]);
        setIsLiveMode(false);
      }
    } catch (err) {
      console.warn('Backend applications offline or empty, falling back to mock mode:', err.message);
      setIsLiveMode(false);
    } finally {
      setLoading(false);
    }
  };

  const checkAuth = async () => {
    const token = localStorage.getItem('pramaan_token');
    if (!token) {
      setIsAuthenticated(false);
      setAuthLoading(false);
      return;
    }

    try {
      const user = await api.getMe();
      if (user && user.role) {
        setCurrentUser(user);
        setCurrentRole(user.role);
        setIsAuthenticated(true);
        const allowed = ROLE_PERMITTED_TABS[user.role] || ROLE_PERMITTED_TABS.scrutiny_officer;
        if (!allowed.includes(activeTab)) {
          setActiveTab('dashboard');
        }
        await loadData(user.role);
      } else {
        handleLogout();
      }
    } catch (err) {
      console.warn('Stored token invalid or session expired:', err.message);
      handleLogout();
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();

    const handleUnauthorized = () => {
      console.warn('Session expired or unauthorized: redirecting to login');
      handleLogout();
    };
    window.addEventListener('pramaan_unauthorized', handleUnauthorized);

    let isMounted = true;
    const checkBackendHealth = async () => {
      try {
        const h = (typeof window !== 'undefined' && window.location.hostname === '127.0.0.1') ? '127.0.0.1' : 'localhost';
        const res = await fetch(`http://${h}:8000/health`).catch(() => fetch('http://127.0.0.1:8000/health'));
        if (isMounted) setIsLiveMode(res.ok);
      } catch (e) {
        if (isMounted) setIsLiveMode(false);
      }
    };
    checkBackendHealth();
    const healthInterval = setInterval(checkBackendHealth, 5000);

    return () => {
      window.removeEventListener('pramaan_unauthorized', handleUnauthorized);
      isMounted = false;
      clearInterval(healthInterval);
    };
  }, []);

  const handleLoginSuccess = async (userProfile) => {
    setCurrentUser(userProfile);
    setCurrentRole(userProfile.role);
    setAdminPreviewRole(null);
    setIsAuthenticated(true);

    const allowed = ROLE_PERMITTED_TABS[userProfile.role] || ROLE_PERMITTED_TABS.scrutiny_officer;
    if (!allowed.includes(activeTab)) {
      setActiveTab('dashboard');
    }

    await loadData(userProfile.role);
  };

  const handleSelectApplication = async (app) => {
    setActiveApplication(app);
    setEvidenceLensError(null);
    try {
      const lens = await api.getEvidenceLens(app.id);
      setEvidenceLensData(lens);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Error fetching evidence lens';
      console.error('Could not fetch evidence lens for selected app:', detail);
      setEvidenceLensError(`Evidence lens request failed for ${app.application_no || `App #${app.id}`}: ${detail}`);
      setEvidenceLensData(null);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen app-shell-bg flex flex-col items-center justify-center text-text">
        <div className="w-12 h-12 border-3 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
        <div className="text-sm font-semibold tracking-wide text-text-muted">
          Loading PRAMAAN-X Scrutiny Protocol...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const permittedTabs = ROLE_PERMITTED_TABS[effectiveRole] || ROLE_PERMITTED_TABS.scrutiny_officer;
  const isTabAllowed = permittedTabs.includes(activeTab);

  return (
    <div className="h-screen w-full max-w-full bg-bg text-text flex flex-col font-sans selection:bg-primary selection:text-white overflow-hidden relative">
      {/* Ambient background layer (Part 1) */}
      <div className="ambient-background" aria-hidden="true" />

      {/* Skip-to-content accessible link (Item 10) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-accent font-semibold text-xs transition"
      >
        Skip to main content
      </a>

      {/* Top AICTE Navigation */}
      <Navbar 
        currentUser={currentUser}
        currentRole={effectiveRole}
        isAdmin={isAdmin}
        adminPreviewRole={adminPreviewRole}
        onAdminSwitchRole={handleAdminSwitchRole}
        onReturnToAdmin={handleReturnToAdmin}
        onLogout={handleLogout}
        activeApplication={activeApplication}
        isLiveMode={isLiveMode}
        onToggleLiveMode={() => setIsLiveMode(!isLiveMode)}
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        isSidebarCollapsed={isSidebarCollapsed}
        onToggleSidebarCollapse={handleToggleSidebarCollapse}
        isScrolled={isScrolled}
        scrollProgress={scrollProgress}
        onSelectTab={setActiveTab}
      />

      <div className="flex-1 min-h-0 flex overflow-hidden relative z-10">
        {/* Left Navigation Sidebar */}
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={(tab) => {
            setActiveTab(tab);
            setIsMobileMenuOpen(false);
          }}
          currentRole={effectiveRole}
          counts={sidebarCounts}
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={handleToggleSidebarCollapse}
        />

        {/* Main Content Workspace */}
        <main 
          ref={mainScrollRef}
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto min-h-0 bg-transparent p-3 sm:p-5 lg:p-6 pb-12 w-full min-w-0 scrollbar-slim relative z-10 focus:outline-none"
        >
          <div className="w-full max-w-[1600px] mx-auto flex flex-col gap-4 sm:gap-6 min-w-0">
            {!isTabAllowed ? (
              <div 
                id="access-restricted-card"
                className="bg-surface rounded-2xl border border-rose-500/30 p-8 text-center flex flex-col items-center justify-center gap-4 my-8 shadow-card"
              >
                <div className="w-14 h-14 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center">
                  <ShieldAlert className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-text">Access Restricted</h2>
                <p className="text-sm text-text-muted max-w-md">
                  Your active role (<span className="font-semibold text-rose-500 capitalize">{effectiveRole?.replace('_', ' ')}</span>) is not authorized to access the <strong>{activeTab}</strong> regulatory module directly.
                </p>
                <button
                  id="return-to-dashboard-btn"
                  onClick={() => setActiveTab('dashboard')}
                  className="mt-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-semibold hover:bg-primary/90 transition-colors cursor-pointer"
                >
                  Return to Dashboard
                </button>
              </div>
            ) : (
              <Suspense fallback={
                <div className="p-12 flex flex-col items-center justify-center gap-3">
                  <Spinner size="lg" label="Loading regulatory module..." />
                  <span className="text-xs font-semibold text-text-muted">Loading scrutiny module...</span>
                </div>
              }>
                {activeTab === 'dashboard' && (
                  <Dashboard 
                    applications={isLiveMode ? applications : []}
                    onSelectApplication={handleSelectApplication}
                    onNavigateTab={setActiveTab}
                    onRefresh={() => loadData(effectiveRole)}
                    isLiveMode={isLiveMode}
                    currentRole={effectiveRole}
                    currentUser={currentUser}
                  />
                )}

                {activeTab === 'evidence-lens' && (
                  <EvidenceLens 
                    applications={applications}
                    onSelectApplication={handleSelectApplication}
                    evidenceLensData={evidenceLensData} 
                    activeApplication={activeApplication}
                    evidenceLensError={evidenceLensError}
                    onRefresh={() => {
                      if (activeApplication) {
                        handleSelectApplication(activeApplication);
                      } else {
                        loadData(effectiveRole);
                      }
                    }}
                  />
                )}

                {activeTab === 'manual-review-queue' && (
                  <ManualReviewQueuePage 
                    currentUser={currentUser}
                    onNavigateToAudit={() => setActiveTab('audit-ledger')}
                  />
                )}

                {activeTab === 'impossibility-engine' && (
                  <ImpossibilityGraph />
                )}

                {activeTab === 'document-intelligence' && (
                  <DocumentIntelligencePage 
                    onNavigateTab={setActiveTab}
                    onSelectApplication={handleSelectApplication}
                  />
                )}

                {activeTab === 'photo-radar' && (
                  <PhotoReuseRadar 
                    onNavigateTab={setActiveTab}
                    onSelectApplication={handleSelectApplication}
                  />
                )}

                {activeTab === 'regulations' && (
                  <RuleConfigPage />
                )}

                {activeTab === 'preflight' && (
                  <PreFlightScorecard 
                    currentUser={currentUser}
                    onNavigateToEvidenceLens={() => setActiveTab('evidence-lens')}
                  />
                )}

                {activeTab === 'inspection-planner' && (
                  <InspectionPlannerPage />
                )}

                {activeTab === 'audit-ledger' && (
                  <AuditAndReceiptsPage activeApplicationId={activeApplication?.id || 1} />
                )}
              </Suspense>
            )}
          </div>
        </main>
      </div>

      {/* Back-to-Top Floating Glass Button (Item 4) */}
      <button
        type="button"
        id="back-to-top-btn"
        onClick={scrollToTop}
        aria-label="Back to top"
        title="Back to top"
        className={`fixed bottom-16 right-4 sm:right-6 z-40 w-10 h-10 rounded-full glass-surface flex items-center justify-center text-text hover:text-primary transition-all duration-200 cursor-pointer shadow-lg outline-none focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
          showBackToTop 
            ? 'opacity-100 translate-y-0 pointer-events-auto' 
            : 'opacity-0 translate-y-2 pointer-events-none'
        }`}
      >
        <ArrowUp className="w-4 h-4" />
      </button>

      {/* Floating Regulatory Support Contact Button (Item 20) */}
      <FloatingContactButton />

      {/* Dismissible Local Storage / Session Consent Notice (Item 13) */}
      <StorageConsentBanner />

      {/* Clean Single Line Footer */}
      <footer className="h-8 shrink-0 bg-surface border-t border-border px-4 sm:px-6 flex items-center justify-between text-xs text-text-muted z-30 select-none">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-text">PRAMAAN-X v1.0.0</span>
          <span>•</span>
          <span>Advisory decision support</span>
        </div>
      </footer>
    </div>
  );
}
