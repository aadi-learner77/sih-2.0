import React, { useState } from 'react';
import { 
  Building2, 
  SearchCode, 
  Network, 
  ScanEye, 
  FileCheck2, 
  AlertTriangle, 
  CheckCircle2, 
  Upload, 
  FileText, 
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  FileSearch
} from 'lucide-react';
import { api } from '../services/api';

export default function Dashboard({ 
  applications = [], 
  onSelectApplication, 
  onNavigateTab,
  onRefresh
}) {
  const [uploadFile, setUploadFile] = useState(null);
  const [docType, setDocType] = useState('Auto-Detect');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  const activeApp = applications[0] || null;

  const handleDocumentUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !activeApp) return;

    setUploading(true);
    setUploadSuccess(null);
    try {
      const res = await api.uploadDocument(activeApp.id, uploadFile, docType);
      setUploadSuccess(res);
      setUploadFile(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-sky-50 via-indigo-50/30 to-slate-50 border border-slate-200/90 rounded-2xl p-6 shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-orange-700 uppercase tracking-widest mb-1.5">
              <span>All India Council for Technical Education (AICTE)</span>
              <span>•</span>
              <span>Approval Year 2025-26</span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              PRAMAAN-X: EoA AI Scrutiny & Regulatory Intelligence
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
              AI decision-support system analyzing Extension of Approval applications, OCR field extraction, knowledge-graph impossibility detection, and tamper-evident audit receipts.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigateTab('evidence-lens')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-bold transition-all shadow-sm shadow-sky-600/20 flex items-center space-x-2"
            >
              <SearchCode className="w-4 h-4" />
              <span>Launch Evidence Lens</span>
            </button>
            <button
              onClick={() => onNavigateTab('impossibility-engine')}
              className="px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold transition-all shadow-xs flex items-center space-x-2"
            >
              <Network className="w-4 h-4 text-rose-600" />
              <span>View Impossibility Graph</span>
            </button>
          </div>
        </div>

        {/* Quick Statutory Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-200/80">
          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Scrutiny Queue</div>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {applications.length} Applications
            </div>
            <div className="text-[10px] text-sky-700 font-medium mt-0.5">Engineering & Management</div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Advisory Review Flags</div>
            <div className="text-2xl font-black text-amber-600 mt-1">4 Indicators</div>
            <div className="text-[10px] text-amber-700/90 font-medium mt-0.5">Decision-support flags</div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Impossibility Conflicts</div>
            <div className="text-2xl font-black text-rose-600 mt-1">2 Anomalies</div>
            <div className="text-[10px] text-rose-700/90 font-medium mt-0.5">Dual-faculty & shared land</div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs">
            <div className="text-[11px] text-slate-500 uppercase font-medium">Audit Receipts</div>
            <div className="text-2xl font-black text-emerald-600 mt-1">7 Blocks</div>
            <div className="text-[10px] text-emerald-700/90 font-medium mt-0.5">SHA-256 chain verified</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Applications List & Live Document Uploader */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Applications Scrutiny Table */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Building2 className="w-5 h-5 text-sky-600" />
              <span>Applications Under Regulatory Review ({applications.length})</span>
            </h2>
            <span className="text-xs text-slate-500">Click to inspect dossier</span>
          </div>

          <div className="space-y-3">
            {applications.map((app) => (
              <div 
                key={app.id}
                className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-sky-300 hover:shadow-md transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded border border-sky-200">
                      {app.application_no}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">AY {app.academic_year}</span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                      {app.status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 truncate">
                    {app.institution_name}
                  </h3>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
                    <span>Category: <strong className="text-slate-800">{app.category}</strong></span>
                    <span>•</span>
                    <span>Pre-Flight Score: <strong className="text-amber-600">{app.preflight_readiness_score}%</strong></span>
                    <span>•</span>
                    <span className="text-rose-600 font-semibold">{app.advisory_flags_count} Review Flags</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <button
                    onClick={() => {
                      onSelectApplication(app);
                      onNavigateTab('evidence-lens');
                    }}
                    className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5"
                  >
                    <span>Open Evidence Lens</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Document Uploader & Forensics Scanner */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
            <div className="flex items-center space-x-2 mb-2">
              <Upload className="w-5 h-5 text-sky-600" />
              <h2 className="text-base font-bold text-slate-900">Document Scrutiny Uploader</h2>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Upload compliance documents to test PaddleOCR extraction, classification, Error-Level Analysis (ELA), and cryptographic receipt creation.
            </p>

            <form onSubmit={handleDocumentUpload} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Document Type:</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-sky-500 focus:bg-white transition-colors"
                >
                  <option value="Auto-Detect">Auto-Detect via ML Classifier</option>
                  <option value="Fire Safety Certificate">Fire Safety Certificate / NOC</option>
                  <option value="Land Title Deed">Land Title Deed / Lease Deed</option>
                  <option value="Building Plan Approval">Approved Building Plan & Occupancy</option>
                  <option value="Faculty Roster">Faculty Cadre Roster</option>
                  <option value="University Affiliation Order">University Affiliation Order</option>
                  <option value="Campus/Lab Geo-tagged Photo">Campus/Lab Geo-tagged Photo</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Select File:</label>
                <div className="border border-dashed border-slate-300 hover:border-sky-400 rounded-xl p-4 text-center bg-slate-50/60 relative cursor-pointer transition-colors">
                  <input
                    type="file"
                    required
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <FileSearch className="w-6 h-6 text-sky-600 mx-auto mb-1 opacity-80" />
                  <div className="text-xs text-slate-700 truncate font-medium">
                    {uploadFile ? uploadFile.name : 'Choose PDF, Scan or Image'}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">PDF, PNG, JPG (Max 25MB)</div>
                </div>
              </div>

              <button
                type="submit"
                disabled={uploading || !uploadFile}
                className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all shadow-sm disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <span>{uploading ? 'Processing OCR & Forensics...' : 'Upload & Analyze Document'}</span>
              </button>
            </form>

            {uploadSuccess && (
              <div className="mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs space-y-1.5">
                <div className="text-emerald-800 font-bold flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Document Analyzed & Chained!</span>
                </div>
                <div className="text-[11px] text-slate-600">
                  • Classification: <strong>{uploadSuccess.document_type}</strong> (Confidence: {(uploadSuccess.classification_confidence * 100).toFixed(0)}%)<br />
                  • SHA-256: <span className="font-mono text-emerald-700">{uploadSuccess.file_hash.substring(0, 16)}...</span><br />
                  • ELA Score: {uploadSuccess.ela_score} | Flagged: {uploadSuccess.is_flagged_for_review ? 'Yes (Review Flag)' : 'No'}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
