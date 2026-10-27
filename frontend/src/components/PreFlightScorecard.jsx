import React, { useState } from 'react';
import { 
  PlaneTakeoff, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Upload, 
  FileText, 
  RotateCcw, 
  ShieldAlert, 
  AlertTriangle, 
  ExternalLink, 
  HelpCircle, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Check,
  RefreshCw,
  Info
} from 'lucide-react';
import { api } from '../services/api';

/**
 * Institution Pre-Flight Scrutiny Self-Assessment Page:
 * - Upload documents (dropzone + simulated instant OCR & hash check)
 * - Traffic-light readiness score (3-lens illuminated signal + circular gauge)
 * - Category checklist with plain-language fix instructions
 * - Re-check compliance audit button with dynamic score recalculation
 * - Adheres strictly to AICTE "Indicator for review" non-punitive governance
 */
export default function PreFlightScorecard({ onNavigateToEvidenceLens }) {
  const [selectedCategory, setSelectedCategory] = useState('Extension of Approval (EoA)');
  const [readinessScore, setReadinessScore] = useState(74.5);
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditFeedback, setAuditFeedback] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState({
    'Fire Safety NOC': { name: 'Fire_Safety_NOC_2025.pdf', size: '2.4 MB', uploadedAt: '18-Oct-2025' },
    'Approved Building Plan': { name: 'Sanctioned_Master_Plan.pdf', size: '14.1 MB', uploadedAt: '12-Oct-2025' },
    'University Affiliation Order': { name: 'VTU_Affiliation_Order.pdf', size: '1.8 MB', uploadedAt: '15-Oct-2025' },
    'Audited Accounts': { name: 'Audited_Balance_Sheet_UDIN.pdf', size: '3.6 MB', uploadedAt: '10-Oct-2025' }
  });

  // Checklist items with plain-language fix instructions
  const [checklist, setChecklist] = useState([
    {
      id: 'CHK-001',
      docType: 'Fire Safety Certificate / NOC',
      clauseRef: 'APH Clause 2.14.3',
      status: 'EXPIRING', // 'EXPIRING' | 'VERIFIED' | 'FLAGGED' | 'MISSING'
      statusLabel: 'Expiring',
      validity: 'Valid till 14-Jun-2025',
      aiWording: 'Indicator for review: Document validity period expires before academic session end',
      fixInstruction: 'Your Fire Safety NOC expires on 14-Jun-2025. AICTE requires coverage through the full 2025-26 academic year. FIX: Upload an acknowledgment receipt of your renewal application filed with Karnataka Fire Services to obtain an interim grace period.',
      actionLabel: 'Upload Renewal Receipt',
      resolved: false,
    },
    {
      id: 'CHK-002',
      docType: 'Faculty Cadre Roster & Form 16',
      clauseRef: 'APH Clause 2.7.4',
      status: 'FLAGGED',
      statusLabel: 'Mismatch Detected',
      validity: 'Dual-Employment Conflict',
      aiWording: 'Indicator for review: Concurrent full-time tenure detected across multiple institutions',
      fixInstruction: 'Dr. R. K. Sharma (HoD) is recorded on the active faculty roster of Royal College of Engineering simultaneously. FIX: Upload IT Form 16 and Aadhaar-enabled biometric attendance logs for the last 6 months to establish exclusive full-time employment.',
      actionLabel: 'Submit Biometric Proof',
      resolved: false,
    },
    {
      id: 'CHK-003',
      docType: 'Campus Built-Up Area & Floor Plans',
      clauseRef: 'APH Clause 2.4.2',
      status: 'FLAGGED',
      statusLabel: 'Deficit Detected',
      validity: '-22% Geospatial Deficit',
      aiWording: 'Indicator for review: Built-up area footprint deficit beyond tolerance threshold',
      fixInstruction: 'Satellite footprint indicates 14,196 sq.m, which is 22% below the claimed 18,200 sq.m. FIX: If your campus has multi-story buildings, upload the Architect-Certified Floor-Wise Completion Certificate showing the vertical plinth area multiplier.',
      actionLabel: 'Upload Floor Plan',
      resolved: false,
    },
    {
      id: 'CHK-004',
      docType: 'Land Title / 30-Year Registered Lease',
      clauseRef: 'APH Clause 2.3.1',
      status: 'MISSING',
      statusLabel: 'Missing Document',
      validity: 'Not Uploaded',
      aiWording: 'Indicator for review: Mandatory land title document missing from dossier',
      fixInstruction: 'Registered Land Deed or 30-Year Government Lease Deed has not been submitted. FIX: Upload a certified digital copy of the registered deed issued by the Sub-Registrar Office.',
      actionLabel: 'Upload Land Deed',
      resolved: false,
    },
    {
      id: 'CHK-005',
      docType: 'Approved Building Plan & Occupancy',
      clauseRef: 'APH Clause 2.4.1',
      status: 'VERIFIED',
      statusLabel: 'Verified',
      validity: 'Sanction No: BMRDA/TP/2021/8821',
      aiWording: 'Verified against municipal planning database',
      fixInstruction: 'Document verified and authentic. Municipal town planning clearance in order.',
      actionLabel: 'View Sanction',
      resolved: true,
    },
    {
      id: 'CHK-006',
      docType: 'University Affiliation Order',
      clauseRef: 'APH Clause 2.8.1',
      status: 'VERIFIED',
      statusLabel: 'Verified',
      validity: 'VTU/ACA/2024-25/A-4/1049',
      aiWording: 'Verified with State Technical University Registry',
      fixInstruction: 'Affiliation order confirmed active for the upcoming academic session.',
      actionLabel: 'View Affiliation',
      resolved: true,
    },
    {
      id: 'CHK-007',
      docType: 'Audited Financial Accounts (UDIN)',
      clauseRef: 'APH Clause 2.11.2',
      status: 'VERIFIED',
      statusLabel: 'Verified',
      validity: 'UDIN: 24089123AAAAA9021',
      aiWording: 'Cryptographically authenticated with ICAI registry',
      fixInstruction: 'Chartered Accountant digital signature and balance sheet verified.',
      actionLabel: 'View UDIN',
      resolved: true,
    },
  ]);

  // Traffic Light Determination
  // Green: >= 85%, Amber: 60 - 84%, Red: < 60%
  const trafficLightState = readinessScore >= 85 ? 'GREEN' : readinessScore >= 60 ? 'AMBER' : 'RED';

  // Handle Dynamic Re-Check
  const handleReCheck = async () => {
    setIsAuditing(true);
    setAuditFeedback(null);

    // Call live preflight API or execute simulated calculation
    try {
      await new Promise((r) => setTimeout(r, 900));
      
      // Calculate score based on resolved items
      const resolvedCount = checklist.filter((c) => c.resolved).length;
      const totalCount = checklist.length;
      const base = 45;
      const computedScore = Number((base + (resolvedCount / totalCount) * 50).toFixed(1));

      setReadinessScore(computedScore);
      setAuditFeedback({
        type: 'SUCCESS',
        message: `Pre-flight audit completed! Readiness score recalculated to ${computedScore}/100.`,
      });
    } catch (err) {
      console.error(err);
    } finally {
      setIsAuditing(false);
    }
  };

  // Handle Quick Fix Action Toggle (Simulates Applicant Uploading Resolution)
  const handleToggleResolve = (id) => {
    setChecklist((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const nextResolved = !item.resolved;
          return {
            ...item,
            resolved: nextResolved,
            status: nextResolved ? 'VERIFIED' : item.status === 'VERIFIED' ? 'EXPIRING' : item.status,
            statusLabel: nextResolved ? 'Resolved' : item.statusLabel,
          };
        }
        return item;
      })
    );
  };

  // Handle Mock File Drop/Upload
  const handleFileUpload = (docType, e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFiles((prev) => ({
      ...prev,
      [docType]: {
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        uploadedAt: 'Just Now',
      },
    }));

    // Auto mark matching checklist item as resolved
    setChecklist((prev) =>
      prev.map((item) => {
        if (item.docType.toLowerCase().includes(docType.toLowerCase())) {
          return {
            ...item,
            resolved: true,
            status: 'VERIFIED',
            statusLabel: 'Uploaded & Resolved',
          };
        }
        return item;
      })
    );
  };

  return (
    <div className="space-y-6 max-w-[1720px] mx-auto">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-50 via-white to-slate-50 border border-sky-200/90 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-sky-700 uppercase tracking-widest mb-1">
              <span>Institution Self-Assessment Engine</span>
              <span>•</span>
              <span>AICTE EoA Scrutiny Readiness</span>
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
              <PlaneTakeoff className="w-6 h-6 text-sky-600 shrink-0" />
              <span>Pre-Flight Scrutiny Readiness & Self-Audit</span>
            </h1>
            <p className="text-xs text-slate-600 mt-1 max-w-3xl">
              Simulates official scrutiny prior to submission. Upload documents, monitor your traffic-light readiness score, 
              and follow plain-language instructions to fix deficiencies before formal committee evaluation.
            </p>
          </div>

          {/* Action: Re-Check Compliance Audit Button */}
          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={handleReCheck}
              disabled={isAuditing}
              id="recheck-preflight-btn"
              className="py-2.5 px-5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-bold shadow-md shadow-sky-500/20 transition-all flex items-center space-x-2 active:scale-95 cursor-pointer"
            >
              <RotateCcw className={`w-4 h-4 ${isAuditing ? 'animate-spin' : ''}`} />
              <span>{isAuditing ? 'Auditing Dossier...' : 'Re-Check Compliance Audit'}</span>
            </button>
          </div>
        </div>

        {/* Dynamic Audit Toast Message */}
        {auditFeedback && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-950 text-xs flex items-center space-x-2 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{auditFeedback.message}</span>
          </div>
        )}

        {/* 
          TRAFFIC-LIGHT READINESS SCORE DECK:
          - Illuminated 3-lens signal (Green / Amber / Red)
          - Circular gauge
          - Executive status
        */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5 mt-6 pt-6 border-t border-slate-200">
          
          {/* Traffic Light Signal Card */}
          <div className="md:col-span-5 bg-white rounded-2xl p-5 border border-slate-200 shadow-2xs flex flex-col sm:flex-row items-center gap-5">
            
            {/* Physical 3-Lens Traffic Light Housing */}
            <div className="bg-slate-900 border-2 border-slate-800 rounded-2xl p-2.5 flex sm:flex-col items-center justify-center gap-2 shadow-inner shrink-0">
              {/* Red Light */}
              <div 
                className={`w-7 h-7 rounded-full border-2 transition-all duration-300 flex items-center justify-center ${
                  trafficLightState === 'RED'
                    ? 'bg-rose-500 border-rose-300 shadow-[0_0_16px_rgba(244,63,94,0.9)] animate-pulse'
                    : 'bg-rose-950/60 border-rose-900 opacity-30'
                }`}
                title="Critical Deficiencies"
              >
                {trafficLightState === 'RED' && <span className="w-2 h-2 rounded-full bg-white" />}
              </div>

              {/* Amber Light */}
              <div 
                className={`w-7 h-7 rounded-full border-2 transition-all duration-300 flex items-center justify-center ${
                  trafficLightState === 'AMBER'
                    ? 'bg-amber-400 border-amber-200 shadow-[0_0_16px_rgba(251,191,36,0.9)] animate-pulse'
                    : 'bg-amber-950/60 border-amber-900 opacity-30'
                }`}
                title="Scrutiny Inquiry Likely"
              >
                {trafficLightState === 'AMBER' && <span className="w-2 h-2 rounded-full bg-white" />}
              </div>

              {/* Green Light */}
              <div 
                className={`w-7 h-7 rounded-full border-2 transition-all duration-300 flex items-center justify-center ${
                  trafficLightState === 'GREEN'
                    ? 'bg-emerald-500 border-emerald-200 shadow-[0_0_16px_rgba(16,185,129,0.9)] animate-pulse'
                    : 'bg-emerald-950/60 border-emerald-900 opacity-30'
                }`}
                title="Ready for Scrutiny Submission"
              >
                {trafficLightState === 'GREEN' && <span className="w-2 h-2 rounded-full bg-white" />}
              </div>
            </div>

            {/* Circular Gauge & Status Headline */}
            <div className="flex items-center space-x-4 min-w-0">
              <div className="relative w-22 h-22 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-slate-100"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className={
                      trafficLightState === 'GREEN'
                        ? 'text-emerald-500'
                        : trafficLightState === 'AMBER'
                        ? 'text-amber-500'
                        : 'text-rose-500'
                    }
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
                  <span className="text-[10px] text-slate-400 block -mt-1">/ 100</span>
                </div>
              </div>

              <div className="min-w-0">
                <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  Traffic-Light Status
                </div>
                <div className={`text-sm font-black mt-0.5 ${
                  trafficLightState === 'GREEN'
                    ? 'text-emerald-700'
                    : trafficLightState === 'AMBER'
                    ? 'text-amber-700'
                    : 'text-rose-700'
                }`}>
                  {trafficLightState === 'GREEN' 
                    ? 'Ready for Submission' 
                    : trafficLightState === 'AMBER' 
                    ? 'Scrutiny Inquiry Likely' 
                    : 'Critical Deficiencies Found'}
                </div>
                <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                  {trafficLightState === 'GREEN'
                    ? 'All mandatory AICTE handbook clauses satisfied with high OCR confidence.'
                    : `${checklist.filter(c => !c.resolved).length} compliance shortfalls detected. Review fix instructions below.`}
                </p>
              </div>
            </div>

          </div>

          {/* Quick Metrics Cards */}
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-2xs">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">Checklist Complete</div>
              <div className="text-xl font-black text-emerald-600 mt-1">
                {checklist.filter((c) => c.resolved).length} of {checklist.length}
              </div>
              <div className="text-[10px] text-slate-500 mt-1 font-mono">
                {((checklist.filter((c) => c.resolved).length / checklist.length) * 100).toFixed(0)}% Satisfied
              </div>
            </div>

            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-2xs">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">Expiring Certs</div>
              <div className="text-xl font-black text-amber-600 mt-1">
                {checklist.filter((c) => c.status === 'EXPIRING' && !c.resolved).length} Notice
              </div>
              <div className="text-[10px] text-slate-500 mt-1">Fire NOC Renewal Due</div>
            </div>

            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-2xs">
              <div className="text-[10px] text-slate-500 uppercase font-semibold">Regulatory AI Flags</div>
              <div className="text-xl font-black text-rose-600 mt-1">
                {checklist.filter((c) => (c.status === 'FLAGGED' || c.status === 'MISSING') && !c.resolved).length} Items
              </div>
              <div className="text-[10px] text-rose-700 font-semibold mt-1">
                Indicator for review
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Main Grid: Left = Document Upload Deck; Right = Checklist with Plain-Language Fixes */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        
        {/* Left Column (5 cols): Upload Documents Section */}
        <div className="xl:col-span-5 space-y-4">
          <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
            <span className="flex items-center space-x-1.5">
              <Upload className="w-4 h-4 text-sky-600" />
              <span>Document Upload & Ingestion Center</span>
            </span>
            <span className="text-[11px] font-normal text-slate-500">
              Drag-and-drop or file picker
            </span>
          </div>

          {/* Primary Upload Dropzone */}
          <div className="bg-white border-2 border-dashed border-sky-300 rounded-2xl p-6 text-center hover:bg-sky-50/30 transition-all group shadow-2xs relative">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Upload className="w-6 h-6" />
            </div>
            <h3 className="text-xs font-bold text-slate-900">
              Upload Compliance Documents or Certificates
            </h3>
            <p className="text-[11px] text-slate-500 mt-1 max-w-xs mx-auto">
              PDF, JPG, or PNG (Max 25MB). Multi-modal OCR extracts fields and checks hash authenticity automatically.
            </p>

            <label className="mt-3 inline-block">
              <span className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer">
                Select Document to Upload
              </span>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => handleFileUpload('Generic Document', e)}
                className="hidden"
              />
            </label>
          </div>

          {/* Uploaded Documents List */}
          <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs space-y-3">
            <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
              <span>Ingested Institutional Files ({Object.keys(uploadedFiles).length})</span>
              <span className="text-[10px] text-emerald-600 font-semibold">✓ SHA-256 Verified</span>
            </div>

            <div className="space-y-2">
              {Object.entries(uploadedFiles).map(([docType, file]) => (
                <div 
                  key={docType}
                  className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center shrink-0">
                      <FileText className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-slate-900 truncate text-xs">{docType}</div>
                      <div className="text-[10px] text-slate-500 flex items-center space-x-2 font-mono">
                        <span className="truncate">{file.name}</span>
                        <span>•</span>
                        <span>{file.size}</span>
                      </div>
                    </div>
                  </div>

                  <label className="text-[10px] font-bold text-sky-700 bg-white border border-slate-200 px-2 py-1 rounded-lg hover:bg-slate-100 cursor-pointer shrink-0 ml-2">
                    <span>Replace</span>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg"
                      onChange={(e) => handleFileUpload(docType, e)}
                      className="hidden"
                    />
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Statutory Caveat Card */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-950 space-y-1">
            <div className="font-bold flex items-center space-x-1.5 text-amber-900">
              <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
              <span>Statutory Non-Rejection Policy</span>
            </div>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              Pre-flight audits are institutional self-improvement instruments. Negative scores NEVER trigger automated rejection or cancel your application.
            </p>
          </div>
        </div>

        {/* Right Column (7 cols): Checklist with Plain-Language Fix Instructions */}
        <div className="xl:col-span-7 space-y-4">
          <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Category Checklist & Plain-Language Fix Guide</span>
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              AICTE APH 2025-26 Specifications
            </span>
          </div>

          {/* Checklist Cards Container */}
          <div className="space-y-3">
            {checklist.map((item) => {
              const isResolved = item.resolved;

              return (
                <div
                  key={item.id}
                  className={`bg-white border rounded-2xl p-4 transition-all shadow-2xs ${
                    isResolved
                      ? 'border-emerald-200 bg-emerald-50/15'
                      : item.status === 'EXPIRING'
                      ? 'border-amber-300'
                      : item.status === 'MISSING'
                      ? 'border-purple-300'
                      : 'border-rose-300'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-slate-900">{item.docType}</span>
                        <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                          {item.clauseRef}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        Recorded Status: <strong className="text-slate-800">{item.validity}</strong>
                      </div>
                    </div>

                    {/* Status Chip */}
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        isResolved
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : item.status === 'EXPIRING'
                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                          : item.status === 'MISSING'
                          ? 'bg-purple-100 text-purple-800 border-purple-300'
                          : 'bg-rose-100 text-rose-800 border-rose-300'
                      }`}>
                        {isResolved ? 'Resolved' : item.statusLabel}
                      </span>
                    </div>
                  </div>

                  {/* AI Advisory Wording Banner (MANDATORY EXACT WORDING) */}
                  {!isResolved && (
                    <div className="mt-2.5 p-2 rounded-lg bg-rose-50/70 border border-rose-200 text-xs flex items-center space-x-2 text-rose-900">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                      <span className="font-semibold text-[11px]">
                        {item.aiWording}
                      </span>
                    </div>
                  )}

                  {/* PLAIN-LANGUAGE FIX INSTRUCTION BOX */}
                  <div className="mt-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                    <div className="font-bold text-slate-900 flex items-center space-x-1.5 text-[11px]">
                      <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                      <span>Plain-Language Fix Guidance:</span>
                    </div>
                    <p className="text-[11px] text-slate-700 leading-relaxed">
                      {item.fixInstruction}
                    </p>
                  </div>

                  {/* Quick Action Bar on each item */}
                  <div className="mt-3 flex items-center justify-between text-xs pt-1">
                    <button
                      onClick={() => handleToggleResolve(item.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer ${
                        isResolved
                          ? 'bg-emerald-600 text-white'
                          : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <Check className="w-3 h-3" />
                      <span>{isResolved ? 'Marked Resolved' : 'Mark as Fixed'}</span>
                    </button>

                    <label className="text-xs font-bold text-sky-700 hover:text-sky-800 flex items-center space-x-1 cursor-pointer">
                      <span>{item.actionLabel}</span>
                      <ArrowRight className="w-3 h-3" />
                      <input
                        type="file"
                        onChange={(e) => handleFileUpload(item.docType, e)}
                        className="hidden"
                      />
                    </label>
                  </div>

                </div>
              );
            })}
          </div>

        </div>

      </div>

    </div>
  );
}
