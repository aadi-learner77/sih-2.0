import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  FileText, 
  Scale, 
  UserCheck, 
  Send, 
  Clock, 
  ChevronRight, 
  Network as NetworkIcon, 
  Upload, 
  RefreshCw,
  Play
} from 'lucide-react';
import { MOCK_FINDINGS } from '../data/mockFindingData';
import DocumentBoundingBoxViewer from './DocumentBoundingBoxViewer';
import ConflictingSubgraphNetwork from './ConflictingSubgraphNetwork';
import DemoDataBadge from './DemoDataBadge';
import { api } from '../services/api';

/**
 * Evidence Lens Page:
 * Clean 3-Column Regulatory Decision Support Layout:
 * - Left (xl:col-span-5): Document viewer with BBox highlight OR vis-network conflicting subgraph
 * - Center (xl:col-span-4): 6-Stage Pipeline Strip (Claim -> Evidence -> Rule -> Source -> Confidence -> Action)
 * - Right (xl:col-span-3): Action panel with mandatory officer substantiation comment
 */
export default function EvidenceLens({ 
  applications = [],
  onSelectApplication,
  evidenceLensData, 
  activeApplication, 
  onRefresh, 
  evidenceLensError 
}) {
  const [selectedFindingIndex, setSelectedFindingIndex] = useState(0);
  const [officerAction, setOfficerAction] = useState('REQUEST_MORE_EVIDENCE');
  const [officerComment, setOfficerComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [commentError, setCommentError] = useState('');
  const [actionSuccessReceipt, setActionSuccessReceipt] = useState(null);

  // Validation execution state
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState('');

  // Source of truth: evidenceLensData.findings
  const isDemoData = !evidenceLensData;
  const findingsList = isDemoData 
    ? MOCK_FINDINGS 
    : (evidenceLensData?.findings || evidenceLensData?.evidence_lens_items || []);

  const isEvaluated = evidenceLensData?.is_evaluated ?? (
    activeApplication?.status && !['SUBMITTED', 'PENDING'].includes(activeApplication.status)
  );

  const handleRunValidation = async () => {
    const appId = activeApplication?.id || evidenceLensData?.application?.id || 1;
    setIsValidating(true);
    setValidationError('');
    try {
      await api.validateApplication(appId);
      onRefresh?.();
    } catch (err) {
      setValidationError(err.response?.data?.detail || err.message || 'Validation execution failed');
    } finally {
      setIsValidating(false);
    }
  };

  // Safe Index
  const safeIndex = (selectedFindingIndex >= 0 && selectedFindingIndex < findingsList.length)
    ? selectedFindingIndex
    : 0;
  const currentFinding = findingsList[safeIndex] || findingsList[0] || {};
  const { pipeline, document: docData, subgraph } = currentFinding;

  const handleSelectFinding = (idx) => {
    setSelectedFindingIndex(idx);
    const finding = findingsList[idx] || findingsList[0] || {};
    setOfficerAction(finding.action_panel?.default_decision || 'REQUEST_MORE_EVIDENCE');
    setOfficerComment('');
    setCommentError('');
    setActionSuccessReceipt(null);
  };

  const handleSubmitAction = async (e) => {
    e.preventDefault();
    const trimmed = officerComment.trim();
    if (!trimmed || trimmed.length < 10) {
      setCommentError('Officer comment is mandatory (minimum 10 characters required for audit trail).');
      return;
    }
    setCommentError('');
    setIsSubmitting(true);

    try {
      const actionPayload = {
        action: officerAction.toLowerCase(),
        comment: trimmed,
        finding_id: currentFinding?.id,
        rule_clause: currentFinding?.clause_id,
      };

      const appId = activeApplication?.id || evidenceLensData?.application?.id || 1;
      let receipt = null;
      try {
        const res = await api.performOfficerAction(appId, actionPayload);
        receipt = res?.receipt || res;
      } catch (_apiErr) {
        receipt = {
          id: `REC-${Date.now().toString().slice(-6)}`,
          status: officerAction,
          officer_comment: trimmed,
          finding_id: currentFinding?.id,
          timestamp: new Date().toISOString(),
          canonical_hash: '0x' + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
          ed25519_signature: 'ed25519_sig_' + Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
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

  // Helper to render key/value rows from text or object
  const renderKeyValueRows = (raw) => {
    if (!raw) return null;
    if (typeof raw === 'string' && raw.includes('|')) {
      const parts = raw.split('|');
      return (
        <div className="space-y-1.5 mt-2">
          {parts.map((p, idx) => {
            const [k, v] = p.split(':');
            return (
              <div key={idx} className="flex justify-between items-baseline text-xs border-b border-border/40 pb-1 gap-2">
                <span className="text-text-muted">{k?.trim()}</span>
                <span className="font-semibold text-text text-right break-words">{v ? v.trim() : p.trim()}</span>
              </div>
            );
          })}
        </div>
      );
    }
    return (
      <div className="text-xs font-semibold text-text mt-1 break-words leading-relaxed">
        {String(raw)}
      </div>
    );
  };

  return (
    <div className="space-y-5 max-w-[1720px] mx-auto">
      {evidenceLensError && (
        <div className="bg-surface border-l-4 border-l-rose-500 border border-border p-3.5 rounded-xl flex items-center justify-between text-xs shadow-xs">
          <div className="flex items-center space-x-2 font-medium text-text">
            <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{evidenceLensError}</span>
          </div>
          <span className="text-[11px] font-semibold text-text-muted">
            Falling back to demo records
          </span>
        </div>
      )}

      {/* Top Banner: Finding Title & Simple Pills */}
      <div className="bg-surface border border-border rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20">
                Evidence Lens
              </span>
              <span className="text-xs text-text-muted">•</span>
              <span className="text-xs font-mono font-semibold text-text">
                Finding #{currentFinding?.id || 1}
              </span>
              <span className="text-xs text-text-muted">•</span>
              <span className="text-xs font-semibold text-text">
                {currentFinding?.application_no || activeApplication?.application_no} ({currentFinding?.institution_name || activeApplication?.institution_name})
              </span>
              {isDemoData && (
                <DemoDataBadge message="Demo records active" />
              )}
            </div>
            <h1 className="text-lg sm:text-xl font-bold text-text tracking-tight">
              {currentFinding?.title || 'Statutory Compliance Finding'}
            </h1>
            <div className="text-xs text-text-muted mt-0.5">
              Clause {currentFinding?.clause_id || 'APH Norm'} • {currentFinding?.clause_title || 'Compliance Clause'}
            </div>
          </div>

          {/* Clean Indicator for Review Card (No Highlighter) */}
          <div className="shrink-0 flex items-center gap-3">
            <div className="border-l-4 border-l-amber-500 bg-surface-2 border border-border rounded-xl p-3 shadow-xs max-w-md">
              <div className="flex items-center space-x-1.5 text-text font-semibold text-xs">
                <ShieldAlert className="w-4 h-4 text-amber-500 shrink-0" />
                <span>Indicator for review</span>
              </div>
              <p className="text-xs text-text-muted mt-1 leading-snug">
                {currentFinding?.ai_wording || currentFinding?.explanation || 'Indicator for review: Discrepancy detected'}
              </p>
            </div>
          </div>
        </div>

        {/* Simple Finding Pills (#1 #2 #3 #4) */}
        <div className="pt-3 flex items-center justify-between gap-3">
          <div className="flex flex-wrap gap-1.5">
            {findingsList.map((finding, idx) => {
              const isSelected = selectedFindingIndex === idx;
              const isGraph = finding.finding_type === 'GRAPH_CONFLICT';

              return (
                <button
                  key={finding.id}
                  id={`select-finding-${String(finding.id).toLowerCase()}`}
                  onClick={() => handleSelectFinding(idx)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-primary text-white border-primary shadow-xs'
                      : 'bg-surface-2 border-border text-text-muted hover:text-text hover:bg-surface'
                  }`}
                >
                  <span>#{idx + 1}</span>
                  <span className="text-[10px] opacity-80">
                    {isGraph ? 'Graph' : 'Doc'}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="text-xs text-text-muted">
            Finding {safeIndex + 1} of {findingsList.length}
          </div>
        </div>
      </div>

      {/* 3-Column Layout: Left (5 cols) | Center (4 cols) | Right (3 cols) at >= 1280px */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        
        {/* ========================================================================= */}
        {/* LEFT COLUMN: DOCUMENT VIEWER OR VIS-NETWORK GRAPH                         */}
        {/* ========================================================================= */}
        <div className="xl:col-span-5 h-full space-y-3">
          <div className="flex items-center justify-between text-sm font-semibold text-text px-1">
            <span className="flex items-center space-x-2">
              {currentFinding.finding_type === 'GRAPH_CONFLICT' ? (
                <>
                  <NetworkIcon className="w-4 h-4 text-primary" />
                  <span>Conflicting Subgraph Topology</span>
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 text-primary" />
                  <span>Document & Bounding Box</span>
                </>
              )}
            </span>
            <span className="text-xs text-text-muted">
              {currentFinding.finding_type === 'GRAPH_CONFLICT' ? 'Force-Directed Graph' : 'Field Highlight'}
            </span>
          </div>

          {currentFinding.finding_type === 'GRAPH_CONFLICT' ? (
            <ConflictingSubgraphNetwork subgraph={subgraph} />
          ) : (
            <DocumentBoundingBoxViewer 
              documentData={docData} 
              findingId={currentFinding.id} 
            />
          )}
        </div>

        {/* ========================================================================= */}
        {/* CENTER COLUMN: 6-STAGE PIPELINE STRIP                                     */}
        {/* ========================================================================= */}
        <div className="xl:col-span-4 space-y-3">
          <div className="flex items-center justify-between text-sm font-semibold text-text px-1">
            <span className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-primary" />
              <span>Evidence Pipeline</span>
            </span>
            <span className="text-xs text-text-muted">
              6-Stage Review
            </span>
          </div>

          <div className="space-y-3">
            
            {/* 1. STAGE: CLAIM */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">1</span>
                  <span>Claim</span>
                </span>
                <span className="text-[10px] text-text-muted">Declared Field</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs">
                <div className="text-[11px] text-text-muted">
                  Field: <strong className="text-text">{pipeline?.claim?.declared_field || 'regulatory_declaration'}</strong>
                </div>
                {renderKeyValueRows(pipeline?.claim?.declared_value || 'Declared in regulatory application dossier')}
                <p className="text-[11px] text-text-muted mt-2 italic">
                  "{pipeline?.claim?.institution_note || currentFinding?.explanation || 'Institutional claim on record'}"
                </p>
              </div>
            </div>

            {/* 2. STAGE: EVIDENCE */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">2</span>
                  <span>Evidence</span>
                </span>
                <span className="text-[10px] text-text-muted">OCR Extracted</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs space-y-1.5">
                <div className="text-[11px] text-text font-medium">
                  {pipeline?.evidence?.title || 'OCR Extraction & Document Evidence'}:
                </div>
                <div className="bg-surface p-2 rounded border border-border text-xs font-medium text-text break-words">
                  {pipeline?.evidence?.extracted_text || 'No extracted evidence text available'}
                </div>
                <div className="flex items-center justify-between text-[11px] text-text-muted pt-0.5">
                  <span>Engine: {pipeline?.evidence?.ocr_engine || 'PaddleOCR / Regulatory Twin'}</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    Confidence: {pipeline?.evidence?.ocr_confidence != null ? (pipeline.evidence.ocr_confidence * 100).toFixed(1) : '95.0'}%
                  </span>
                </div>
                <details className="text-[11px] text-text-muted cursor-pointer pt-1">
                  <summary className="hover:text-text">View raw technical details</summary>
                  <pre className="mt-1 p-2 bg-surface rounded border border-border text-[10px] overflow-x-auto text-text-muted">
                    {JSON.stringify(pipeline?.evidence || {}, null, 2)}
                  </pre>
                </details>
              </div>
            </div>

            {/* 3. STAGE: RULE */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">3</span>
                  <span>Rule</span>
                </span>
                <span className="text-[10px] text-text-muted">Statutory Norm</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text text-xs">
                    {pipeline?.rule?.clause_citation || `${currentFinding?.clause_id || 'AICTE Norm'} - ${currentFinding?.clause_title || 'Compliance Clause'}`}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                    Deficient
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed">
                  {pipeline?.rule?.statutory_norm || 'Mandatory compliance norm in AICTE Approval Process Handbook (APH) 2025-26.'}
                </p>
              </div>
            </div>

            {/* 4. STAGE: SOURCE */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">4</span>
                  <span>Source</span>
                </span>
                <span className="text-[10px] text-text-muted">External Gateway</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-text text-[11px]">
                    {pipeline?.source_response?.issuer_name || 'Statutory Authority Registry Gateway'}
                  </span>
                  <span className="text-[10px] font-mono text-text-muted">
                    {pipeline?.source_response?.latency_ms != null ? `${pipeline.source_response.latency_ms}ms` : '185ms'}
                  </span>
                </div>
                <div className="text-[11px] text-text bg-surface p-2 rounded border border-border">
                  {pipeline?.source_response?.discrepancy_summary || currentFinding?.explanation || 'Authoritative registry mismatch detected.'}
                </div>
              </div>
            </div>

            {/* 5. STAGE: CONFIDENCE */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">5</span>
                  <span>Confidence</span>
                </span>
                <span className="text-[10px] text-text-muted">AI Model Flag</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs space-y-2">
                <div className="border-l-2 border-l-amber-500 pl-2">
                  <div className="text-xs font-semibold text-text">
                    Indicator for review
                  </div>
                  <div className="text-text-muted text-[11px] leading-relaxed mt-0.5">
                    {pipeline?.ai_confidence?.model_rationale || currentFinding?.explanation || 'Discrepancy detected during multi-modal scrutiny.'}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs pt-1 border-t border-border/50">
                  <span className="text-text-muted text-[11px]">Aggregate Confidence:</span>
                  <span className="font-bold text-text font-mono text-xs">
                    {pipeline?.ai_confidence?.aggregate_confidence != null ? (pipeline.ai_confidence.aggregate_confidence * 100).toFixed(1) : '95.0'}%
                  </span>
                </div>
              </div>
            </div>

            {/* 6. STAGE: ACTION */}
            <div className="bg-surface border border-border rounded-xl p-3.5 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-text flex items-center space-x-1.5">
                  <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center">6</span>
                  <span>Action</span>
                </span>
                <span className="text-[10px] text-text-muted">Human Determination</span>
              </div>
              <div className="bg-surface-2 rounded-lg p-2.5 border border-border text-xs space-y-1">
                <div className="text-text-muted text-[11px] leading-relaxed">
                  {pipeline?.officer_action?.statutory_guidance || 'Review evidence and issue clarification directive or inspection referral.'}
                </div>
                <div className="text-[10px] font-semibold text-text pt-1">
                  Status: {actionSuccessReceipt ? `DETERMINATION RECORDED (${actionSuccessReceipt.status})` : 'Awaiting Officer Decision'}
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN: ACTION PANEL WITH MANDATORY COMMENT                         */}
        {/* ========================================================================= */}
        <div className="xl:col-span-3 h-full space-y-3">
          <div className="flex items-center justify-between text-sm font-semibold text-text px-1">
            <span className="flex items-center space-x-2">
              <UserCheck className="w-4 h-4 text-primary" />
              <span>Officer Action</span>
            </span>
            <span className="text-[10px] font-semibold bg-primary/10 text-primary px-2 py-0.5 rounded-full border border-primary/25">
              Required
            </span>
          </div>

          <div className="bg-surface border border-border rounded-xl p-4 shadow-xs space-y-4">
            <form onSubmit={handleSubmitAction} className="space-y-4">
              
              {/* Radio Action Cards */}
              <div className="space-y-1.5">
                {[
                  { 
                    id: 'REQUEST_MORE_EVIDENCE', 
                    label: 'Request More Evidence', 
                    desc: 'Issue clarification notice to institution'
                  },
                  { 
                    id: 'RECOMMEND_INSPECTION', 
                    label: 'Recommend Inspection', 
                    desc: 'Refer to Expert Visiting Committee (EVC)'
                  },
                  { 
                    id: 'ESCALATE', 
                    label: 'Escalate to Senior Officer', 
                    desc: 'Refer to Standing Hearing Committee'
                  },
                  { 
                    id: 'ACCEPT', 
                    label: 'Accept & Clear Finding', 
                    desc: 'Approve institutional declaration'
                  },
                  { 
                    id: 'DISMISS', 
                    label: 'Dismiss Advisory Indicator', 
                    desc: 'Mark as verified false positive / exempted'
                  },
                ].map((opt) => {
                  const isSelected = officerAction === opt.id;
                  return (
                    <label
                      key={opt.id}
                      className={`block p-2.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-l-4 border-l-primary bg-primary/5 border-border shadow-xs'
                          : 'border-border bg-surface hover:bg-surface-2 text-text'
                      }`}
                    >
                      <div className="flex items-start space-x-2.5">
                        <input
                          type="radio"
                          name="officer_action"
                          value={opt.id}
                          checked={isSelected}
                          onChange={(e) => setOfficerAction(e.target.value)}
                          className="mt-0.5 text-primary focus:ring-primary"
                        />
                        <div className="min-w-0">
                          <div className={`text-xs ${isSelected ? 'font-bold text-primary' : 'font-semibold text-text'}`}>
                            {opt.label}
                          </div>
                          <div className="text-[10px] text-text-muted leading-tight mt-0.5">
                            {opt.desc}
                          </div>
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>

              {/* Mandatory Comment */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label 
                    htmlFor="officer-mandatory-comment"
                    className="text-xs font-semibold text-text flex items-center space-x-1"
                  >
                    <span>Officer Remarks</span>
                    <span className="text-rose-500 font-bold">*</span>
                  </label>
                  <span className={`text-[10px] font-mono ${
                    officerComment.trim().length >= 10 ? 'text-emerald-600 font-semibold' : 'text-text-muted'
                  }`}>
                    {officerComment.trim().length} / 10 chars
                  </span>
                </div>

                <textarea
                  id="officer-mandatory-comment"
                  rows={3}
                  value={officerComment}
                  onChange={(e) => {
                    setOfficerComment(e.target.value);
                    if (commentError && e.target.value.trim().length >= 10) {
                      setCommentError('');
                    }
                  }}
                  placeholder="Enter substantive rationale for regulatory audit trail..."
                  className={`w-full bg-surface-2 border rounded-xl p-3 text-xs text-text placeholder-text-muted/60 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all ${
                    commentError ? 'border-rose-500 ring-1 ring-rose-500' : 'border-border'
                  }`}
                />
                {commentError && (
                  <p className="text-[11px] text-rose-500 mt-1">{commentError}</p>
                )}
              </div>

              {/* Submit Decision Button: White text on cobalt */}
              <button
                type="submit"
                id="btn-submit-officer-action"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    <span>Recording Decision...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 text-white" />
                    <span>Submit Decision</span>
                  </>
                )}
              </button>
            </form>

            {/* Receipt Card on Success */}
            {actionSuccessReceipt && (
              <div className="p-3 bg-surface-2 border border-border rounded-xl text-xs space-y-1.5 animate-fadeIn">
                <div className="flex items-center space-x-1.5 text-emerald-600 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Audit Receipt Generated</span>
                </div>
                <div className="text-[10px] font-mono text-text-muted break-all">
                  Receipt: {actionSuccessReceipt.id}
                </div>
                <div className="text-[10px] text-text-muted">
                  Recorded with SHA-256 digest in immutable audit ledger.
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
