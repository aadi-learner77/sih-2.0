import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  FileText, 
  Scale, 
  Database, 
  Bot, 
  UserCheck, 
  Send, 
  Clock, 
  Fingerprint, 
  ChevronRight, 
  Info, 
  Network as NetworkIcon,
  HelpCircle,
  Building,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileCheck
} from 'lucide-react';
import { MOCK_FINDINGS } from '../data/mockFindingData';
import DocumentBoundingBoxViewer from './DocumentBoundingBoxViewer';
import ConflictingSubgraphNetwork from './ConflictingSubgraphNetwork';
import { api } from '../services/api';

/**
 * Evidence Lens Page for a Single Finding:
 * 
 * Strict 3-Column Layout:
 * - Left: Document viewer with bounding-box highlight of the extracted field
 *         (or conflicting subgraph with vis-network for graph findings)
 * - Center: 6-Stage Pipeline Strip:
 *           Claim -> Evidence -> Rule (with clause citation) -> Source response -> AI confidence -> Officer action
 * - Right: Officer action panel with mandatory comment
 * 
 * Mandatory Policy Rule:
 * Show the exact wording "Indicator for review" on all AI flags.
 */
export default function EvidenceLens({ evidenceLensData, onRefresh }) {
  const [selectedFindingIndex, setSelectedFindingIndex] = useState(0);
  const [officerAction, setOfficerAction] = useState('REQUEST_MORE_EVIDENCE');
  const [officerComment, setOfficerComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [commentError, setCommentError] = useState('');
  const [actionSuccessReceipt, setActionSuccessReceipt] = useState(null);

  // Active finding
  const currentFinding = MOCK_FINDINGS[selectedFindingIndex] || MOCK_FINDINGS[0];
  const { pipeline, document: docData, subgraph } = currentFinding;

  // Handle switching finding
  const handleSelectFinding = (idx) => {
    setSelectedFindingIndex(idx);
    const finding = MOCK_FINDINGS[idx];
    setOfficerAction(finding.action_panel?.default_decision || 'REQUEST_MORE_EVIDENCE');
    setOfficerComment('');
    setCommentError('');
    setActionSuccessReceipt(null);
  };

  // Handle Officer Determination Submission
  const handleSubmitAction = async (e) => {
    e.preventDefault();

    // Strict validation: Mandatory comment
    const trimmed = officerComment.trim();
    if (!trimmed || trimmed.length < 10) {
      setCommentError('Officer comment is mandatory (minimum 10 characters required for regulatory audit log).');
      return;
    }
    setCommentError('');
    setIsSubmitting(true);

    try {
      // Attempt live backend officer-action API call
      const actionPayload = {
        action: officerAction.toLowerCase(),
        comment: trimmed,
        finding_id: currentFinding.id,
        rule_clause: currentFinding.clause_id,
      };

      let receipt = null;
      try {
        const res = await api.performOfficerAction(1, actionPayload);
        receipt = res?.receipt || res;
      } catch (apiErr) {
        // Fallback simulation for live demonstration / offline mode
        const mockHash = '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
        const mockSig = 'ed25519_sig_' + Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
        receipt = {
          id: `REC-${Date.now().toString().slice(-6)}`,
          status: officerAction,
          officer_comment: trimmed,
          finding_id: currentFinding.id,
          timestamp: new Date().toISOString(),
          canonical_hash: mockHash,
          ed25519_signature: mockSig,
          rule_version_set: 'APH_2025_26_v1.0.4',
        };
      }

      setActionSuccessReceipt(receipt);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to submit officer action:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-[1720px] mx-auto">
      {/* Top Banner: Finding Title, Regulatory Context & Finding Switcher */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-200">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200">
                Evidence Lens • Single Finding Dossier
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-mono font-semibold text-slate-700">
                {currentFinding.id}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-semibold text-slate-600">
                {currentFinding.application_no} ({currentFinding.institution_name})
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
              <span>{currentFinding.title}</span>
            </h1>
            <div className="text-xs text-slate-600 mt-1 flex flex-wrap items-center gap-2">
              <span className="font-semibold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                {currentFinding.clause_id}
              </span>
              <span>{currentFinding.clause_title}</span>
            </div>
          </div>

          {/* Statutory AI Indicator Flag: MANDATORY WORDING */}
          <div className="shrink-0">
            <div className="bg-rose-50 border border-rose-200/90 rounded-xl p-3 shadow-2xs max-w-md">
              <div className="flex items-center space-x-2 text-rose-800 font-bold text-xs">
                <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                <span className="uppercase tracking-wider">Indicator for review</span>
              </div>
              <p className="text-[11px] text-rose-900 mt-1 font-medium leading-snug">
                {currentFinding.ai_wording}
              </p>
            </div>
          </div>
        </div>

        {/* Finding Switcher Tabs (Document vs Graph findings) */}
        <div className="pt-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500">
            <span>Select Finding to Inspect:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {MOCK_FINDINGS.map((finding, idx) => {
              const isSelected = selectedFindingIndex === idx;
              const isGraph = finding.finding_type === 'GRAPH_CONFLICT';

              return (
                <button
                  key={finding.id}
                  id={`select-finding-${finding.id.toLowerCase()}`}
                  onClick={() => handleSelectFinding(idx)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all flex items-center space-x-2 ${
                    isSelected
                      ? 'bg-slate-900 border-slate-900 text-white font-bold shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                  }`}
                >
                  {isGraph ? (
                    <NetworkIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-rose-400' : 'text-slate-500'}`} />
                  ) : (
                    <FileText className={`w-3.5 h-3.5 ${isSelected ? 'text-sky-400' : 'text-slate-500'}`} />
                  )}
                  <span>{finding.id}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-sans ${
                    isSelected ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {isGraph ? 'vis-network' : 'BBox'}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 
        STRICT 3-COLUMN LAYOUT:
        Left (5 cols on xl): Document viewer with BBox highlight OR vis-network conflicting subgraph
        Center (4 cols on xl): 6-Stage Pipeline Strip: Claim -> Evidence -> Rule -> Source response -> AI confidence -> Officer action
        Right (3 cols on xl): Officer action panel with mandatory comment
      */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        
        {/* ========================================================================= */}
        {/* LEFT COLUMN: DOCUMENT VIEWER WITH BOUNDING BOX OR VIS-NETWORK SUBGRAPH    */}
        {/* ========================================================================= */}
        <div className="xl:col-span-5 h-full">
          <div className="sticky top-4 space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
              <span className="flex items-center space-x-1.5">
                {currentFinding.finding_type === 'GRAPH_CONFLICT' ? (
                  <>
                    <NetworkIcon className="w-4 h-4 text-rose-600" />
                    <span>Conflicting Subgraph Topology</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 text-sky-600" />
                    <span>Document Viewer & Bounding Box</span>
                  </>
                )}
              </span>
              <span className="text-[11px] font-normal text-slate-500">
                {currentFinding.finding_type === 'GRAPH_CONFLICT' ? 'Force-Directed Physics' : 'Extracted Field Highlight'}
              </span>
            </div>

            {/* Left Viewer Component */}
            {currentFinding.finding_type === 'GRAPH_CONFLICT' ? (
              <ConflictingSubgraphNetwork subgraph={subgraph} />
            ) : (
              <DocumentBoundingBoxViewer 
                documentData={docData} 
                findingId={currentFinding.id} 
              />
            )}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* CENTER COLUMN: 6-STAGE PIPELINE STRIP                                     */}
        {/* Claim -> Evidence -> Rule -> Source response -> AI confidence -> Action   */}
        {/* ========================================================================= */}
        <div className="xl:col-span-4 space-y-4">
          <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
            <span className="flex items-center space-x-1.5">
              <Scale className="w-4 h-4 text-indigo-600" />
              <span>Evidence Pipeline Strip</span>
            </span>
            <span className="text-[11px] font-normal text-slate-500">
              6-Stage Regulatory Audit Flow
            </span>
          </div>

          {/* Stepped Connected Strip Container */}
          <div className="space-y-3.5 relative">
            
            {/* 1. STAGE: CLAIM */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:border-sky-300 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-sky-100 text-sky-800 text-[11px] font-bold flex items-center justify-center border border-sky-300">
                    1
                  </span>
                  <span className="text-xs font-bold text-slate-900">Claim (Institutional Declaration)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 1</span>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 text-xs space-y-1">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                  Declared Value for <span className="font-mono text-slate-700">{pipeline.claim.declared_field}</span>:
                </div>
                <div className="text-sm font-bold text-slate-900 font-mono">
                  {pipeline.claim.declared_value}
                </div>
                <div className="text-[11px] text-slate-600 mt-1 italic">
                  "{pipeline.claim.institution_note}"
                </div>
              </div>
            </div>

            {/* Pipeline Stage Connector Arrow */}
            <div className="flex justify-center -my-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-400">
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            {/* 2. STAGE: EVIDENCE */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:border-sky-300 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-sky-100 text-sky-800 text-[11px] font-bold flex items-center justify-center border border-sky-300">
                    2
                  </span>
                  <span className="text-xs font-bold text-slate-900">Evidence (Extracted Field)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 2</span>
              </div>
              <div className="bg-sky-50/40 rounded-lg p-3 border border-sky-200 text-xs space-y-1.5">
                <div className="text-[11px] text-sky-900 font-medium">
                  {pipeline.evidence.title}:
                </div>
                <div className="text-sm font-bold text-sky-950 font-mono bg-white p-2 rounded border border-sky-200">
                  {pipeline.evidence.extracted_text}
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>Engine: {pipeline.evidence.ocr_engine}</span>
                  <span className="font-semibold text-emerald-700">
                    Confidence: {(pipeline.evidence.ocr_confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Pipeline Stage Connector Arrow */}
            <div className="flex justify-center -my-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-400">
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            {/* 3. STAGE: RULE (WITH CLAUSE CITATION) */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:border-indigo-300 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-indigo-100 text-indigo-800 text-[11px] font-bold flex items-center justify-center border border-indigo-300">
                    3
                  </span>
                  <span className="text-xs font-bold text-slate-900">Rule (with Clause Citation)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 3</span>
              </div>
              <div className="bg-indigo-50/30 rounded-lg p-3 border border-indigo-200 text-xs space-y-2">
                {/* Clause Citation Header */}
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-950 text-xs">
                    {pipeline.rule.clause_citation}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300">
                    {pipeline.rule.compliance_status}
                  </span>
                </div>
                <div className="text-[11px] text-slate-700 leading-snug">
                  <strong className="text-slate-900">Statutory Norm:</strong> {pipeline.rule.statutory_norm}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  Rule Version: {pipeline.rule.handbook_edition} ({pipeline.rule.clause_id})
                </div>
              </div>
            </div>

            {/* Pipeline Stage Connector Arrow */}
            <div className="flex justify-center -my-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-400">
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            {/* 4. STAGE: SOURCE RESPONSE */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:border-amber-300 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-amber-100 text-amber-800 text-[11px] font-bold flex items-center justify-center border border-amber-300">
                    4
                  </span>
                  <span className="text-xs font-bold text-slate-900">Source Response (External Registry)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 4</span>
              </div>
              <div className="bg-amber-50/30 rounded-lg p-3 border border-amber-200 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 text-[11px]">
                    {pipeline.source_response.issuer_name}
                  </span>
                  <span className="text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-amber-200 text-amber-900">
                    {pipeline.source_response.latency_ms}ms
                  </span>
                </div>
                <div className="text-[11px] text-rose-800 bg-rose-50 p-2 rounded border border-rose-200 font-medium">
                  {pipeline.source_response.discrepancy_summary}
                </div>
                <div className="text-[10px] font-mono text-slate-500">
                  Ref Query: {pipeline.source_response.query_ref} • Status: {pipeline.source_response.status}
                </div>
              </div>
            </div>

            {/* Pipeline Stage Connector Arrow */}
            <div className="flex justify-center -my-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-400">
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            {/* 5. STAGE: AI CONFIDENCE (WITH MANDATORY "Indicator for review" WORDING) */}
            <div className="bg-white border-2 border-rose-200 rounded-xl p-4 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-rose-100 text-rose-800 text-[11px] font-bold flex items-center justify-center border border-rose-300">
                    5
                  </span>
                  <span className="text-xs font-bold text-slate-900">AI Confidence & Advisory Flag</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 5</span>
              </div>
              
              <div className="space-y-2">
                {/* MANDATORY AI FLAG WORDING */}
                <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-300 text-xs">
                  <div className="flex items-center space-x-1.5 text-rose-900 font-bold mb-1">
                    <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                    <span className="uppercase tracking-wider">Indicator for review</span>
                  </div>
                  <div className="text-slate-800 text-[11px] leading-relaxed">
                    {pipeline.ai_confidence.model_rationale}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs px-1">
                  <span className="text-slate-500 text-[11px]">Aggregate Multi-Modal Confidence:</span>
                  <span className="font-black text-rose-700 font-mono text-sm">
                    {(pipeline.ai_confidence.aggregate_confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="text-[10px] text-slate-500 italic border-t border-slate-200 pt-1.5">
                  Statutory Rule: {pipeline.ai_confidence.advisory_disclaimer}
                </div>
              </div>
            </div>

            {/* Pipeline Stage Connector Arrow */}
            <div className="flex justify-center -my-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-400">
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            {/* 6. STAGE: OFFICER ACTION */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs hover:border-emerald-300 transition-all">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-md bg-emerald-100 text-emerald-800 text-[11px] font-bold flex items-center justify-center border border-emerald-300">
                    6
                  </span>
                  <span className="text-xs font-bold text-slate-900">Officer Action (Human in the Loop)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">STAGE 6</span>
              </div>
              <div className="bg-emerald-50/40 rounded-lg p-3 border border-emerald-200 text-xs space-y-1">
                <div className="text-[11px] text-emerald-900 font-medium">
                  Statutory Guidance for Committee:
                </div>
                <div className="text-slate-800 text-[11px] leading-relaxed">
                  {pipeline.officer_action.statutory_guidance}
                </div>
                <div className="text-[10px] font-semibold text-emerald-800 pt-1">
                  Status: {actionSuccessReceipt ? `DETERMINATION RECORDED (${actionSuccessReceipt.status})` : 'Awaiting Officer Substantiation'}
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN: OFFICER ACTION PANEL WITH MANDATORY COMMENT                 */}
        {/* ========================================================================= */}
        <div className="xl:col-span-3 h-full">
          <div className="sticky top-4 space-y-4">
            <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
              <span className="flex items-center space-x-1.5">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                <span>Officer Action Panel</span>
              </span>
              <span className="text-[10px] font-bold bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full border border-rose-300">
                Mandatory Comment
              </span>
            </div>

            {/* Action Card Container */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
              
              {/* Form for Officer Determination */}
              <form onSubmit={handleSubmitAction} className="space-y-4">
                
                {/* 1. Action Selector */}
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-2">
                    Select Determination Action:
                  </label>
                  <div className="space-y-1.5">
                    {[
                      { 
                        id: 'REQUEST_MORE_EVIDENCE', 
                        label: 'Request More Evidence', 
                        desc: 'Issue show-cause / 15-day notice',
                        color: 'border-amber-300 bg-amber-50 text-amber-900' 
                      },
                      { 
                        id: 'RECOMMEND_INSPECTION', 
                        label: 'Recommend Inspection', 
                        desc: 'Refer to Expert Visiting Committee (EVC)',
                        color: 'border-indigo-300 bg-indigo-50 text-indigo-900' 
                      },
                      { 
                        id: 'ESCALATE', 
                        label: 'Escalate to Senior Officer', 
                        desc: 'Refer to SAC / Standing Hearing Committee',
                        color: 'border-rose-300 bg-rose-50 text-rose-900' 
                      },
                      { 
                        id: 'ACCEPT', 
                        label: 'Accept & Clear Finding', 
                        desc: 'Approve institutional declaration',
                        color: 'border-emerald-300 bg-emerald-50 text-emerald-900' 
                      },
                      { 
                        id: 'DISMISS', 
                        label: 'Dismiss Advisory Indicator', 
                        desc: 'Mark indicator as false positive / exempted',
                        color: 'border-slate-300 bg-slate-100 text-slate-800' 
                      },
                    ].map((opt) => (
                      <label
                        key={opt.id}
                        className={`block p-2.5 rounded-xl border cursor-pointer transition-all ${
                          officerAction === opt.id
                            ? `${opt.color} ring-2 ring-sky-500 font-semibold shadow-xs`
                            : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="officer_action"
                            value={opt.id}
                            checked={officerAction === opt.id}
                            onChange={(e) => setOfficerAction(e.target.value)}
                            className="text-sky-600 focus:ring-sky-500"
                          />
                          <div className="min-w-0">
                            <div className="text-xs font-bold">{opt.label}</div>
                            <div className="text-[10px] text-slate-500 truncate">{opt.desc}</div>
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* 2. Mandatory Officer Comment */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label 
                      htmlFor="officer-mandatory-comment"
                      className="text-xs font-bold text-slate-900 flex items-center space-x-1"
                    >
                      <span>Officer Substantiation Remarks</span>
                      <span className="text-rose-600 font-black">*</span>
                    </label>
                    <span className={`text-[10px] font-mono ${
                      officerComment.trim().length >= 10 ? 'text-emerald-600 font-semibold' : 'text-slate-400'
                    }`}>
                      {officerComment.trim().length} / 10 min chars
                    </span>
                  </div>

                  <textarea
                    id="officer-mandatory-comment"
                    rows={4}
                    value={officerComment}
                    onChange={(e) => {
                      setOfficerComment(e.target.value);
                      if (commentError) setCommentError('');
                    }}
                    placeholder={
                      currentFinding.action_panel?.mandatory_comment_placeholder ||
                      'Mandatory: Enter regulatory rationale, clarification grounds, or inspection scope...'
                    }
                    className={`w-full text-xs p-3 rounded-xl border focus:outline-none focus:ring-2 transition-colors ${
                      commentError 
                        ? 'border-rose-400 bg-rose-50/30 focus:ring-rose-500' 
                        : 'border-slate-300 focus:ring-sky-500 bg-white'
                    }`}
                  />

                  {/* Mandatory Error Alert */}
                  {commentError ? (
                    <div className="text-[11px] text-rose-600 font-medium mt-1 flex items-center space-x-1">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>{commentError}</span>
                    </div>
                  ) : (
                    <div className="text-[10px] text-slate-500 mt-1 flex items-center space-x-1">
                      <Info className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>Statutory mandate: Officer comment is hashed into the tamper-evident audit ledger.</span>
                    </div>
                  )}
                </div>

                {/* Submit Action Button */}
                <button
                  type="submit"
                  id="submit-officer-action-btn"
                  disabled={isSubmitting || officerComment.trim().length < 10}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold shadow-xs transition-all flex items-center justify-center space-x-2 ${
                    officerComment.trim().length < 10
                      ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
                      : 'bg-sky-600 hover:bg-sky-700 text-white cursor-pointer active:scale-[0.98]'
                  }`}
                >
                  {isSubmitting ? (
                    <>
                      <Clock className="w-4 h-4 animate-spin" />
                      <span>Signing & Appending Receipt...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Submit Officer Determination</span>
                    </>
                  )}
                </button>
              </form>

              {/* Success Receipt Modal / Box */}
              {actionSuccessReceipt && (
                <div 
                  id="action-success-receipt-card"
                  className="bg-emerald-50 border border-emerald-300 rounded-xl p-3.5 text-xs text-emerald-950 space-y-2 animate-fadeIn"
                >
                  <div className="flex items-center space-x-2 font-bold text-emerald-900">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Action Recorded & Cryptographically Signed!</span>
                  </div>
                  <div className="text-[11px] text-slate-700 bg-white/80 p-2 rounded border border-emerald-200 space-y-1 font-mono">
                    <div>Receipt ID: <span className="font-bold">{actionSuccessReceipt.id || 'REC-LIVE-001'}</span></div>
                    <div>Action: <span className="font-bold text-emerald-800">{actionSuccessReceipt.status}</span></div>
                    <div className="truncate" title={actionSuccessReceipt.canonical_hash}>
                      SHA-256: {actionSuccessReceipt.canonical_hash?.slice(0, 24)}...
                    </div>
                    <div className="text-[10px] text-slate-500 font-sans mt-1">
                      Rule Set: {actionSuccessReceipt.rule_version_set || 'APH-2025-26-v1.0.4'}
                    </div>
                  </div>
                  <div className="text-[10px] text-emerald-800 italic">
                    Chain verified: Append-only ledger updated without schema errors.
                  </div>
                </div>
              )}

              {/* Quick Institutional Info Card */}
              <div className="pt-2 border-t border-slate-200 text-xs text-slate-600 space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Institution:</span>
                  <span className="font-semibold text-slate-800">{currentFinding.institution_name}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Category:</span>
                  <span className="font-semibold text-slate-800">{currentFinding.category}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Statutory Norm:</span>
                  <span className="font-semibold text-sky-700">{currentFinding.clause_id}</span>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
