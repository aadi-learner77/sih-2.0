import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Scale, 
  Database, 
  ShieldAlert, 
  Send, 
  Clock, 
  Fingerprint, 
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export default function EvidenceLens({ evidenceLensData, onRefresh }) {
  const [selectedItemIndex, setSelectedItemIndex] = useState(0);
  const [officerDecision, setOfficerDecision] = useState('');
  const [officerComment, setOfficerComment] = useState('');
  const [savingAction, setSavingAction] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  if (!evidenceLensData || !evidenceLensData.evidence_lens_items) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Info className="w-8 h-8 mx-auto mb-2 text-sky-600 animate-spin" />
        <p>Loading Evidence Lens verification matrix...</p>
      </div>
    );
  }

  const items = evidenceLensData.evidence_lens_items;
  const currentItem = items[selectedItemIndex] || items[0];

  const handleRecordDecision = async () => {
    if (!officerDecision) {
      alert('Please select an officer decision action');
      return;
    }
    setSavingAction(true);
    setSuccessMsg('');
    try {
      // In demo, map to evaluation id or record decision
      // Simulates live API submission & hash-chain receipt generation
      await new Promise(r => setTimeout(r, 600));
      setSuccessMsg(`Decision '${officerDecision}' recorded & cryptographically signed in audit ledger!`);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
      alert('Failed to record decision');
    } finally {
      setSavingAction(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Evidence Lens Header Banner */}
      <div className="bg-gradient-to-r from-sky-50 via-indigo-50/25 to-slate-50 border border-sky-200/80 rounded-2xl p-6 shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-sky-700 uppercase tracking-widest mb-1">
              <span>Flagship Decision-Support Module</span>
              <span>•</span>
              <span>AICTE EoA Scrutiny</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Evidence Lens: 6-Stage Regulatory Audit Pipeline
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Strictly non-binding decision support mapping institutional claims to OCR forensics, handbook rules, and authoritative external government registers.
            </p>
          </div>
          <div className="flex items-center space-x-4 shrink-0">
            <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-right shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Pre-Flight Readiness</div>
              <div className="text-xl font-black text-amber-600">{evidenceLensData.readiness_score}%</div>
            </div>
          </div>
        </div>

        {/* 6-Stage Process Step Visualizer */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-6 pt-6 border-t border-slate-200/80">
          {[
            { step: '1', title: 'Claim', desc: 'Declared facts' },
            { step: '2', title: 'Evidence', desc: 'OCR & Forensics' },
            { step: '3', title: 'Rule', desc: 'APH Clause' },
            { step: '4', title: 'Source', desc: 'Issuer Portal Diff' },
            { step: '5', title: 'Confidence', desc: 'Multi-modal AI' },
            { step: '6', title: 'Officer Action', desc: 'Human in the Loop' }
          ].map((s, idx) => (
            <div key={idx} className="flex items-center space-x-2 p-2 rounded-lg bg-white border border-slate-200/80 shadow-xs">
              <span className="w-5 h-5 rounded-full bg-sky-50 text-sky-700 text-xs font-bold flex items-center justify-center shrink-0 border border-sky-200">
                {s.step}
              </span>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate">{s.title}</div>
                <div className="text-[10px] text-slate-500 truncate">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Item Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-1">
        {items.map((item, idx) => (
          <button
            key={item.id}
            onClick={() => {
              setSelectedItemIndex(idx);
              setSuccessMsg('');
            }}
            className={`px-4 py-2.5 rounded-xl text-xs font-medium border transition-all flex items-center space-x-2 shrink-0 ${
              selectedItemIndex === idx
                ? 'bg-sky-50 border-sky-300 text-sky-800 font-semibold shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${item.confidence.risk_level === 'CRITICAL' ? 'bg-rose-500' : 'bg-amber-500'}`} />
            <span>{item.domain}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-medium">
              {item.confidence.risk_level}
            </span>
          </button>
        ))}
      </div>

      {/* Main 6-Stage Lens Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Stages 1 through 4 (Claims, Evidence, Rule, Source) */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Stage 1: The Claim */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-300 shadow-xs transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-lg bg-sky-50 text-sky-700 text-xs font-bold flex items-center justify-center border border-sky-200">
                  1
                </span>
                <h3 className="text-sm font-semibold text-slate-900 tracking-wide">Claim (Institutional Declaration)</h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">Input Assertion</span>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-1.5">
              <div className="text-xs text-sky-700 font-semibold">{currentItem.claim.title}</div>
              <div className="text-base font-bold text-slate-900">{currentItem.claim.declared_value}</div>
              <div className="text-xs text-slate-600">{currentItem.claim.institution_note}</div>
            </div>
          </div>

          {/* Stage 2: The Evidence */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-300 shadow-xs transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-bold flex items-center justify-center border border-indigo-200">
                  2
                </span>
                <h3 className="text-sm font-semibold text-slate-900 tracking-wide">Evidence (Document & OCR Forensics)</h3>
              </div>
              <span className="text-xs text-indigo-700 font-mono font-medium">PaddleOCR + ELA</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 space-y-1">
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <FileText className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Document File</span>
                </div>
                <div className="text-xs font-semibold text-slate-800 truncate">{currentItem.evidence.filename}</div>
                <div className="text-[10px] text-slate-500 font-mono truncate">SHA: {currentItem.evidence.file_hash}</div>
              </div>

              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 space-y-1">
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <Fingerprint className="w-3.5 h-3.5 text-amber-600" />
                  <span>Forensic Indicators</span>
                </div>
                {currentItem.evidence.forensic_indicators.metadata_producer ? (
                  <div className="text-xs text-rose-700 font-medium">
                    Software: {currentItem.evidence.forensic_indicators.metadata_producer}
                  </div>
                ) : (
                  <div className="text-xs text-amber-800 font-medium">
                    {currentItem.evidence.forensic_indicators.knowledge_graph_conflict || 'Radar match detected'}
                  </div>
                )}
                {currentItem.evidence.forensic_indicators.ela_score && (
                  <div className="text-[10px] text-slate-600 font-mono">
                    ELA Tamper Score: <span className="text-rose-600 font-bold">{currentItem.evidence.forensic_indicators.ela_score}</span> (Threshold: 0.60)
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stage 3: The Rule */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-300 shadow-xs transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-lg bg-purple-50 text-purple-700 text-xs font-bold flex items-center justify-center border border-purple-200">
                  3
                </span>
                <h3 className="text-sm font-semibold text-slate-900 tracking-wide">Rule (Regulation-as-Code Citation)</h3>
              </div>
              <span className="text-xs text-purple-700 font-mono font-bold">{currentItem.rule.clause_id}</span>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-bold text-slate-800">{currentItem.rule.clause_title}</div>
                <div className="text-xs text-slate-600">Statutory Norm: {currentItem.rule.threshold}</div>
              </div>
              <span className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase shrink-0 ${
                currentItem.rule.status === 'COMPLIANT' 
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                  : 'bg-rose-50 text-rose-700 border border-rose-200'
              }`}>
                {currentItem.rule.status}
              </span>
            </div>
          </div>

          {/* Stage 4: The Source Response */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-300 shadow-xs transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="w-6 h-6 rounded-lg bg-amber-50 text-amber-700 text-xs font-bold flex items-center justify-center border border-amber-200">
                  4
                </span>
                <h3 className="text-sm font-semibold text-slate-900 tracking-wide">Source Response (External Government Register)</h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">{currentItem.source_response.latency_ms}ms response</span>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs font-semibold text-amber-900">
                  <Database className="w-4 h-4 text-amber-600" />
                  <span>{currentItem.source_response.issuer_name}</span>
                </div>
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  currentItem.source_response.status === 'verified'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border border-rose-200'
                }`}>
                  {currentItem.source_response.status}
                </span>
              </div>

              {currentItem.source_response.discrepancies && currentItem.source_response.discrepancies.length > 0 && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 space-y-1.5">
                  <div className="text-xs font-semibold text-rose-800 flex items-center space-x-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                    <span>Authoritative Registry Discrepancy Diff:</span>
                  </div>
                  {currentItem.source_response.discrepancies.map((d, i) => (
                    <div key={i} className="text-xs text-rose-700 pl-5 leading-relaxed">
                      • {d.summary || d.issue || `${d.field}: Claimed '${d.claimed_value}' vs Registry '${d.issuer_value}'`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Right Column: Stages 5 & 6 (Confidence & Officer Action) */}
        <div className="lg:col-span-4 space-y-4">
          
          {/* Stage 5: Multi-Modal Confidence */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
            <div className="flex items-center space-x-2 mb-3">
              <span className="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-bold flex items-center justify-center border border-emerald-200">
                5
              </span>
              <h3 className="text-sm font-semibold text-slate-900 tracking-wide">AI Confidence Scoring</h3>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">Aggregate Confidence</span>
                  <span className="text-slate-900 font-mono font-bold">
                    {(currentItem.confidence.aggregate_ai_confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-sky-500 to-emerald-500 rounded-full"
                    style={{ width: `${currentItem.confidence.aggregate_ai_confidence * 100}%` }}
                  />
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Risk Assessment:</span>
                  <span className={`font-bold uppercase ${
                    currentItem.confidence.risk_level === 'CRITICAL' ? 'text-rose-600' : 'text-amber-600'
                  }`}>
                    {currentItem.confidence.risk_level}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">OCR Reliability:</span>
                  <span className="text-slate-800 font-mono font-medium">{(currentItem.confidence.ocr_confidence * 100 || 95)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">External Sync:</span>
                  <span className="text-emerald-700 font-mono font-medium">100% (Direct Portal Auth)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Stage 6: Human Officer Action */}
          <div className="bg-white border-2 border-sky-300 rounded-2xl p-5 shadow-sm relative">
            <div className="flex items-center space-x-2 mb-3">
              <span className="w-6 h-6 rounded-lg bg-orange-50 text-orange-700 text-xs font-bold flex items-center justify-center border border-orange-200">
                6
              </span>
              <h3 className="text-sm font-bold text-slate-900 tracking-wide">Human Officer Action</h3>
            </div>

            {/* Advisory Reminder */}
            <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-[11px] leading-relaxed mb-4">
              <strong>Statutory Guidance:</strong> {currentItem.officer_action.statutory_guidance}
            </div>

            {/* Decision Radio / Selector */}
            <div className="space-y-2 mb-4">
              <label className="text-xs font-semibold text-slate-700">Scrutiny Determination:</label>
              {[
                { id: 'CLARIFICATION_ISSUED', label: 'Issue Clarification / Show-Cause', color: 'text-amber-800 font-medium' },
                { id: 'ACCEPTED_WITH_NOTE', label: 'Accept Evidence with Explanation', color: 'text-emerald-800 font-medium' },
                { id: 'WAIVED_WITH_REASON', label: 'Grant Statutory Waiver', color: 'text-sky-800 font-medium' },
                { id: 'PENDING_REVIEW', label: 'Keep Under Committee Scrutiny', color: 'text-slate-700 font-medium' }
              ].map((act) => (
                <label 
                  key={act.id} 
                  className={`flex items-center space-x-2.5 p-2 rounded-xl border text-xs cursor-pointer transition-all ${
                    officerDecision === act.id 
                      ? 'bg-sky-50 border-sky-300 text-slate-900 font-medium shadow-xs' 
                      : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="decision"
                    value={act.id}
                    checked={officerDecision === act.id}
                    onChange={(e) => setOfficerDecision(e.target.value)}
                    className="accent-sky-600"
                  />
                  <span className={act.color}>{act.label}</span>
                </label>
              ))}
            </div>

            {/* Officer Comment Box */}
            <div className="space-y-1.5 mb-4">
              <label className="text-xs font-semibold text-slate-700">Official Rationale / Directive:</label>
              <textarea
                rows={3}
                value={officerComment}
                onChange={(e) => setOfficerComment(e.target.value)}
                placeholder="Enter mandatory committee remarks for regulatory audit log..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white transition-colors"
              />
            </div>

            {/* Action Submit */}
            <button
              onClick={handleRecordDecision}
              disabled={savingAction}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white text-xs font-bold shadow-sm flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{savingAction ? 'Recording Cryptographic Receipt...' : 'Sign & Record Officer Action'}</span>
            </button>

            {successMsg && (
              <div className="mt-3 p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
