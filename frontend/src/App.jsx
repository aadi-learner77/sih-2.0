import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import EvidenceLens from './components/EvidenceLens';
import ImpossibilityGraph from './components/ImpossibilityGraph';
import PhotoReuseRadar from './components/PhotoReuseRadar';
import RuleConfigPage from './pages/RuleConfigPage';
import PreFlightScorecard from './components/PreFlightScorecard';
import AuditLedgerView from './components/AuditLedgerView';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentRole, setCurrentRole] = useState('scrutiny_officer');
  const [applications, setApplications] = useState([]);
  const [activeApplication, setActiveApplication] = useState(null);
  const [evidenceLensData, setEvidenceLensData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const apps = await api.getApplications();
      setApplications(apps);
      if (apps && apps.length > 0) {
        const primary = apps[0];
        setActiveApplication(primary);
        const lens = await api.getEvidenceLens(primary.id);
        setEvidenceLensData(lens);
      }
    } catch (err) {
      console.error('Failed to load application data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectApplication = async (app) => {
    setActiveApplication(app);
    try {
      const lens = await api.getEvidenceLens(app.id);
      setEvidenceLensData(lens);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Top AICTE Navigation */}
      <Navbar 
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        activeApplication={activeApplication}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab}
          counts={{
            impossibilities: 2,
            advisoryFlags: activeApplication?.advisory_flags_count || 4
          }}
        />

        {/* Main Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-slate-50/60">
          {activeTab === 'dashboard' && (
            <Dashboard 
              applications={applications}
              onSelectApplication={handleSelectApplication}
              onNavigateTab={setActiveTab}
              onRefresh={loadData}
            />
          )}

          {activeTab === 'evidence-lens' && (
            <EvidenceLens 
              evidenceLensData={evidenceLensData} 
              onRefresh={loadData}
            />
          )}

          {activeTab === 'impossibility-engine' && (
            <ImpossibilityGraph />
          )}

          {activeTab === 'photo-radar' && (
            <PhotoReuseRadar />
          )}

          {activeTab === 'regulations' && (
            <RuleConfigPage />
          )}

          {activeTab === 'preflight' && (
            <PreFlightScorecard 
              onNavigateToEvidenceLens={() => setActiveTab('evidence-lens')}
            />
          )}

          {activeTab === 'audit-ledger' && (
            <AuditLedgerView />
          )}
        </main>
      </div>

      {/* Statutory Footer */}
      <footer className="bg-white border-t border-slate-200 py-3.5 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 shadow-sm">
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
