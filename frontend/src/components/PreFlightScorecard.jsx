import React, { useState } from 'react';
import { 
  PlaneTakeoff, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  TrendingUp, 
  ShieldAlert, 
  FileText,
  RotateCcw
} from 'lucide-react';
import { api } from '../services/api';

export default function PreFlightScorecard({ onNavigateToEvidenceLens }) {
  const [selectedCategory, setSelectedCategory] = useState('Extension of Approval (EoA)');
  const [readinessScore, setReadinessScore] = useState(72.4);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const handleRunPreflight = async () => {
    setScanning(true);
    try {
      const res = await api.runPreflight(1, selectedCategory, {
        sanctioned_intake: 480,
        built_up_area_sqm: 8500.0,
        total_faculty: 15,
        fire_noc_expiry_date: '2026-03-31'
      });
      setScanResult(res);
      setReadinessScore(res.readiness_score);
    } catch (err) {
      console.error(err);
      // Demo fallback
      setReadinessScore(74.0);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-50 via-white to-slate-50 border border-sky-200/70 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-sky-700 uppercase tracking-widest mb-1">
              <span>Institution Self-Assessment Engine</span>
              <span>•</span>
              <span>Approval Process Handbook 2025-26</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Pre-Flight Scrutiny Readiness Scorecard
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Provides technical institutions with an instant, pre-submission compliance audit. Uncovers missing documents, expiring certificates, and regulatory clause shortfalls before formal scrutiny submission.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={handleRunPreflight}
              disabled={scanning}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-2"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
              <span>{scanning ? 'Computing Score...' : 'Run Pre-Flight Audit'}</span>
            </button>
          </div>
        </div>

        {/* Readiness Gauge & Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mt-6 pt-6 border-t border-slate-200/80">
          <div className="md:col-span-4 bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center space-x-5">
            <div className="relative w-24 h-24 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-slate-200"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={readinessScore >= 80 ? 'text-emerald-500' : 'text-amber-500'}
                  strokeDasharray={`${readinessScore}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute text-center">
                <span className="text-xl font-black text-slate-900 font-mono">{readinessScore}</span>
                <span className="text-[10px] text-slate-500 block -mt-1">/ 100</span>
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-700">Readiness Status</div>
              <div className="text-sm font-bold text-amber-600 mt-0.5">Scrutiny Inquiry Likely</div>
              <p className="text-[11px] text-slate-500 mt-1">
                4 action items require attention before submitting formal EoA application.
              </p>
            </div>
          </div>

          <div className="md:col-span-8 grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Checklist Complete</div>
              <div className="text-lg font-bold text-emerald-600">85.7%</div>
              <div className="text-[10px] text-slate-500 mt-1">6 of 7 mandatory docs</div>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Expiring Certs</div>
              <div className="text-lg font-bold text-amber-600">1 Document</div>
              <div className="text-[10px] text-slate-500 mt-1">Fire NOC expires March 2026</div>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Regulatory Flags</div>
              <div className="text-lg font-bold text-rose-600">3 Clauses</div>
              <div className="text-[10px] text-slate-500 mt-1">FSR, Carpet Area, Cadre</div>
            </div>
          </div>
        </div>
      </div>

      {/* Actionable Pre-Submission Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Checklist Breakdown */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-sky-600" />
            <span>Category Checklist Breakdown (EoA 2025-26)</span>
          </h2>

          <div className="space-y-2.5">
            {[
              { name: 'Fire Safety Certificate / NOC', status: 'EXPIRING', note: 'Expires on 31-03-2026 (Renewal Required for full session)' },
              { name: 'Land Title / 30-Year Registered Lease', status: 'FLAGGED', note: 'Sy. No. 42/1 subject to dual claim indicator' },
              { name: 'Approved Building Plan & Occupancy', status: 'VERIFIED', note: 'Sanction No: BMRDA/TP/2021/8821' },
              { name: 'Faculty Cadre Roster & Form 16', status: 'FLAGGED', note: 'HOD CSE full-time appointment dispute' },
              { name: 'University Affiliation Order', status: 'VERIFIED', note: 'VTU/ACA/2024-25/A-4/1049 (Active)' },
              { name: 'Audited Financial Accounts (UDIN)', status: 'VERIFIED', note: 'UDIN authenticated with ICAI portal' },
              { name: 'Geo-tagged Campus Photos', status: 'FLAGGED', note: 'Photo Radar match on CS Lab workstations' }
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <div>
                  <div className="font-semibold text-slate-900">{item.name}</div>
                  <div className="text-[11px] text-slate-500">{item.note}</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                  item.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                  item.status === 'EXPIRING' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                  'bg-rose-50 text-rose-700 border border-rose-200'
                }`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Actionable Recommendations to achieve 100/100 */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            <span>Remediation Roadmap (Path to 100% Readiness)</span>
          </h2>

          <div className="space-y-3">
            {[
              {
                step: '1',
                title: 'Renew Fire Safety NOC with State Fire Department',
                desc: 'Apply for NOC renewal covering through at least June 2026 to satisfy Clause 6.3.2 before submission.',
                points: '+12 Points'
              },
              {
                step: '2',
                title: 'Resolve Faculty Dual Employment with Dr. R. K. Sharma',
                desc: 'Submit formal resignation & relieving order from Royal College of Engineering along with bank salary credit statements.',
                points: '+10 Points'
              },
              {
                step: '3',
                title: 'Augment Instructional Built-up Area or Adjust Intake',
                desc: 'Reported 8,500 sq.m is below the 10.5 sqm/student statutory norm for 480 intake. Upload recent wing expansion certificate.',
                points: '+6 Points'
              }
            ].map((rec, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-start space-x-3 text-xs">
                <span className="w-6 h-6 rounded-lg bg-sky-50 text-sky-700 font-bold flex items-center justify-center shrink-0 border border-sky-200">
                  {rec.step}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{rec.title}</span>
                    <span className="text-emerald-700 font-mono font-bold text-[11px]">{rec.points}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{rec.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={onNavigateToEvidenceLens}
              className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200 transition-colors"
            >
              Inspect Active Evidence Lens for Full Clause Diffs
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
