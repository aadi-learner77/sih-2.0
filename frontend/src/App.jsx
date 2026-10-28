import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EvidenceLens from './components/EvidenceLens';
import ImpossibilityGraph from './components/ImpossibilityGraph';
import PhotoReuseRadar from './components/PhotoReuseRadar';
import RuleConfigPage from './pages/RuleConfigPage';
import PreFlightScorecard from './components/PreFlightScorecard';
import AuditAndReceiptsPage from './pages/AuditAndReceiptsPage';
import InspectionPlannerPage from './pages/InspectionPlannerPage';
import ManualReviewQueuePage from './pages/ManualReviewQueuePage';
import DocumentIntelligencePage from './pages/DocumentIntelligencePage';
import LoginPage from './pages/LoginPage';
import { ShieldAlert } from 'lucide-react';
import { api } from './services/api';

const ROLE_PERMITTED_TABS = {
  institution_user: ['dashboard', 'preflight', 'audit-ledger'],
  auditor: ['dashboard', 'evidence-lens', 'impossibility-engine', 'manual-review-queue', 'document-intelligence', 'audit-ledger'],
  scrutiny_officer: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'inspection-planner', 'audit-ledger'],
  senior_officer: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'regulations', 'inspection-planner', 'audit-ledger'],
  admin: ['dashboard', 'evidence-lens', 'manual-review-queue', 'preflight', 'document-intelligence', 'photo-radar', 'impossibility-engine', 'regulations', 'inspection-planner', 'audit-ledger'],
};

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentRole, setCurrentRole] = useState('scrutiny_officer');
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

  const handleLogout = () => {
    localStorage.removeItem('pramaan_token');
    localStorage.removeItem('pramaan_user');
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentRole('scrutiny_officer');
    setApplications([]);
    setActiveApplication(null);
    setEvidenceLensData(null);
    setEvidenceLensError(null);
    setSidebarCounts({ impossibilities: 0, advisoryFlags: 0 });
  };

  const loadData = async (role = currentRole) => {
    setLoading(true);
    try {
      const apps = await api.getApplications();
      if (apps && Array.isArray(apps) && apps.length > 0) {
        setApplications(apps);
        setIsLiveMode(true);

        // Select the application with the most findings or the highest regulatory risk
        const sortedApps = [...apps].sort((a, b) => {
          const findingsA = (a.advisory_flags_count || 0) + (a.impossibility_flags_count || 0) + (a.forensic_flags_count || 0);
          const findingsB = (b.advisory_flags_count || 0) + (b.impossibility_flags_count || 0) + (b.forensic_flags_count || 0);
          if (findingsB !== findingsA) {
            return findingsB - findingsA; // Most findings first
          }
          const scoreA = a.preflight_readiness_score !== undefined ? a.preflight_readiness_score : 100;
          const scoreB = b.preflight_readiness_score !== undefined ? b.preflight_readiness_score : 100;
          return scoreA - scoreB; // Lowest readiness first (highest risk)
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

        // Fetch dynamic counts from API for sidebar badges (/graph/impossibilities, /applications/findings/all, /verification/connector/manual-review-queue)
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
        } catch (_cntErr) {
          // ignore count fetch error
        }
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
        // Switch tab if not permitted for role
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

    // Listen for 401 unauthorized events from Axios interceptor
    const handleUnauthorized = () => {
      console.warn('Session expired or unauthorized: redirecting to login');
      handleLogout();
    };
    window.addEventListener('pramaan_unauthorized', handleUnauthorized);

    // Periodic health check to keep Live Backend API status truthful
    let isMounted = true;
    const checkBackendHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
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

  // If verifying authentication on startup, show elegant loading screen
  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-3 border-orange-500/30 border-t-orange-500 rounded-full animate-spin mb-4" />
        <div className="text-sm font-semibold tracking-wide text-slate-300">
          Loading PRAMAAN-X Scrutiny Protocol...
        </div>
      </div>
    );
  }

  // If not authenticated, render Login Page
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const permittedTabs = ROLE_PERMITTED_TABS[currentUser?.role || currentRole] || ROLE_PERMITTED_TABS.scrutiny_officer;
  const isTabAllowed = permittedTabs.includes(activeTab);

  return (
    <div className="h-screen w-full max-w-full bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-sky-500 selection:text-white overflow-hidden">
      {/* Top AICTE Navigation */}
      <Navbar 
        currentUser={currentUser}
        currentRole={currentRole}
        onLogout={handleLogout}
        activeApplication={activeApplication}
        isLiveMode={isLiveMode}
        onToggleLiveMode={() => setIsLiveMode(!isLiveMode)}
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      />

      <div className="flex-1 min-h-0 flex overflow-hidden relative">
        {/* Left Navigation Sidebar (Role-Aware & Responsive Mobile Drawer) */}
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={(tab) => {
            setActiveTab(tab);
            setIsMobileMenuOpen(false);
          }}
          currentRole={currentRole}
          counts={sidebarCounts}
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        />

        {/* Main Content Workspace */}
        <main className="flex-1 overflow-y-auto min-h-0 bg-slate-50/60 p-3 sm:p-5 lg:p-6 pb-20 w-full min-w-0">
          <div className="w-full max-w-[1600px] mx-auto flex flex-col gap-4 sm:gap-6 min-w-0">
            {!isTabAllowed ? (
              <div 
                id="access-restricted-card"
                className="bg-white rounded-2xl border border-rose-200 p-8 text-center flex flex-col items-center justify-center gap-4 my-8 shadow-sm"
              >
                <div className="w-14 h-14 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center">
                  <ShieldAlert className="w-7 h-7" />
                </div>
                <h2 className="text-xl font-bold text-slate-800">Access Restricted</h2>
                <p className="text-sm text-slate-600 max-w-md">
                  Your active role (<span className="font-semibold text-rose-700 capitalize">{currentRole?.replace('_', ' ')}</span>) is not authorized to access the <strong>{activeTab}</strong> regulatory module directly.
                </p>
                <button
                  id="return-to-dashboard-btn"
                  onClick={() => setActiveTab('dashboard')}
                  className="mt-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors cursor-pointer"
                >
                  Return to Dashboard
                </button>
              </div>
            ) : (
              <>
                {activeTab === 'dashboard' && (
                  <Dashboard 
                    applications={isLiveMode ? applications : []}
                    onSelectApplication={handleSelectApplication}
                    onNavigateTab={setActiveTab}
                    onRefresh={() => loadData(currentRole)}
                    isLiveMode={isLiveMode}
                    currentRole={currentRole}
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
                        loadData(currentRole);
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
              </>
            )}
          </div>
        </main>
      </div>

      {/* Statutory Footer */}
      <footer className="flex-none bg-white border-t border-slate-200 py-2.5 px-4 sm:px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 shadow-sm z-30">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-slate-700">PRAMAAN-X v1.0.0</span>
          <span>•</span>
          <span>Regulatory Decision-Support System for AICTE India</span>
        </div>
        <div className="text-[11px] text-slate-500">
          Statutory Constraint: AI outputs are advisory indicators for committee inquiry. Automated rejections are prohibited under regulatory guidelines.
        </div>
      </footer>
    </div>
  );
}
