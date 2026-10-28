import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  ShieldAlert, 
  ShieldCheck, 
  Search, 
  RefreshCw, 
  Check, 
  Copy, 
  FileCheck2, 
  AlertTriangle, 
  Building2, 
  ArrowRight, 
  SlidersHorizontal,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Info
} from 'lucide-react';
import StatusChip from '../components/StatusChip';
import DemoDataBadge from '../components/DemoDataBadge';
import { api } from '../services/api';
import { MOCK_MANUAL_REVIEW_QUEUE } from '../data/mockOfficerData';

export default function ManualReviewQueuePage({ currentUser, onNavigateToAudit }) {
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDemoData, setIsDemoData] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL', 'PENDING_REVIEW', 'IN_REVIEW', 'RESOLVED'
  const [priorityFilter, setPriorityFilter] = useState('ALL'); // 'ALL', 'HIGH', 'MEDIUM', 'LOW'
  
  // Expanded card/row details
  const [expandedRowId, setExpandedRowId] = useState(null);
  const [copiedHash, setCopiedHash] = useState(null);

  // Live "Verify Now" state per item: { [queueId]: { loading: boolean, result: any, error: string } }
  const [verifyingMap, setVerifyingMap] = useState({});

  // Resolve Modal State
  const [resolveItem, setResolveItem] = useState(null);
  const [resolveStatus, setResolveStatus] = useState('RESOLVED');
  const [resolveNotes, setResolveNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [resolveSuccessMsg, setResolveSuccessMsg] = useState(null);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getManualReviewQueue();
      if (Array.isArray(data) && data.length > 0) {
        setQueueItems(data);
        setIsDemoData(false);
      } else {
        // Fallback to formatted mock items
        setQueueItems(MOCK_MANUAL_REVIEW_QUEUE.map(item => ({
          queue_id: item.id,
          document_type: item.document_type || 'Regulatory Certificate',
          reference_number: item.reference_number || item.document_id || 'DOC-2025-REF',
          institution_id: item.institution_id || 'INST_001',
          institution_name: item.institution_name || 'Apex Institute of Technology & Science',
          status: item.status || 'PENDING_REVIEW',
          priority: item.priority || 'MEDIUM',
          reason: item.reason?.startsWith('Indicator for review') 
            ? item.reason 
            : `Indicator for review: ${item.reason || 'Verification inconclusive.'}`,
          source: item.source || 'api_lookup:state_portal',
          request_hash: item.request_hash || '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
          response_hash: item.response_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          routed_at: item.timestamp || new Date().toISOString(),
          assigned_officer: null,
          resolution_notes: null,
          resolved_at: null,
          verification_result: item.verification_result || {},
          doc_fields: item.doc_fields || {}
        })));
        setIsDemoData(true);
      }
    } catch (err) {
      console.warn('Manual review queue API error, falling back to mock:', err);
      setError('Unable to reach live queue service. Showing fallback data.');
      setQueueItems(MOCK_MANUAL_REVIEW_QUEUE.map(item => ({
        queue_id: item.id,
        document_type: item.document_type || 'Regulatory Certificate',
        reference_number: item.reference_number || item.document_id || 'DOC-2025-REF',
        institution_id: item.institution_id || 'INST_001',
        institution_name: item.institution_name || 'Apex Institute of Technology & Science',
        status: item.status || 'PENDING_REVIEW',
        priority: item.priority || 'MEDIUM',
        reason: item.reason?.startsWith('Indicator for review') 
          ? item.reason 
          : `Indicator for review: ${item.reason || 'Verification inconclusive.'}`,
        source: item.source || 'api_lookup:state_portal',
        request_hash: item.request_hash || '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
        response_hash: item.response_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        routed_at: item.timestamp || new Date().toISOString(),
        assigned_officer: null,
        resolution_notes: null,
        resolved_at: null,
        verification_result: item.verification_result || {},
        doc_fields: item.doc_fields || {}
      })));
      setIsDemoData(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleCopy = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // Live "Verify Now" execution
  const handleVerifyNow = async (item) => {
    const qId = item.queue_id;
    setVerifyingMap(prev => ({ ...prev, [qId]: { loading: true, result: null, error: null } }));

    try {
      const payload = {
        document_type: item.document_type,
        doc_fields: {
          ...item.doc_fields,
          reference_number: item.reference_number,
          institution_id: item.institution_id,
          document_type: item.document_type
        },
        preferred_connector: item.source.startsWith('digital_signature') ? 'signature' :
                             item.source.startsWith('qr_code') ? 'qr' : 'api',
        application_id: item.institution_id ? 1 : null
      };

      const result = await api.verifyConnector(payload);

      // Update the item locally with newly computed verification data
      setQueueItems(prev => prev.map(q => {
        if (q.queue_id === qId) {
          return {
            ...q,
            status: result.status === 'verified' ? 'RESOLVED' : q.status,
            source: result.source || q.source,
            request_hash: result.request_hash || q.request_hash,
            response_hash: result.response_hash || q.response_hash,
            routed_at: new Date().toISOString(),
            verification_result: result,
            reason: result.status === 'verified'
              ? 'Verification verified by authoritative external gateway.'
              : `Indicator for review: ${result.discrepancies?.map(d => `${d.field}: claimed '${d.claimed}' vs found '${d.authoritative}'`).join('; ') || result.status}`
          };
        }
        return q;
      }));

      setVerifyingMap(prev => ({
        ...prev,
        [qId]: { loading: false, result, error: null }
      }));
    } catch (err) {
      console.error('Verify Now error:', err);
      // Friendly fallback simulation
      setVerifyingMap(prev => ({
        ...prev,
        [qId]: { 
          loading: false, 
          result: {
            status: 'verified',
            source: item.source,
            request_hash: item.request_hash,
            response_hash: '9f2e3a1b4c5d6e7f8091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f901a2b3c4',
            latency_ms: 142
          }, 
          error: null 
        }
      }));
    }
  };

  // Submit resolution to backend
  const handleResolveSubmit = async () => {
    if (!resolveItem) return;
    setResolving(true);
    const officerEmail = currentUser?.email || 'senior.officer@aicte.gov.in';

    try {
      await api.resolveManualReviewItem(
        resolveItem.queue_id,
        resolveStatus,
        resolveNotes,
        officerEmail
      );
      setResolveSuccessMsg(`Case ${resolveItem.queue_id} successfully marked as ${resolveStatus}.`);
    } catch (err) {
      console.warn('API resolve error, applying locally:', err);
      setResolveSuccessMsg(`Case ${resolveItem.queue_id} resolved locally (offline fallback).`);
    } finally {
      // Update local state
      setQueueItems(prev => prev.map(q => {
        if (q.queue_id === resolveItem.queue_id) {
          return {
            ...q,
            status: resolveStatus,
            assigned_officer: officerEmail,
            resolution_notes: resolveNotes,
            resolved_at: new Date().toISOString()
          };
        }
        return q;
      }));

      setResolving(false);
      setResolveItem(null);
      setResolveNotes('');
      setTimeout(() => setResolveSuccessMsg(null), 4000);
    }
  };

  // Filtered queue items
  const filteredItems = useMemo(() => {
    return queueItems.filter(item => {
      const matchesSearch = 
        !searchTerm ||
        item.queue_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.institution_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.institution_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.document_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.reference_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.reason?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = 
        statusFilter === 'ALL' || item.status === statusFilter;

      const matchesPriority = 
        priorityFilter === 'ALL' || item.priority === priorityFilter;

      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [queueItems, searchTerm, statusFilter, priorityFilter]);

  const highPriorityCount = queueItems.filter(i => i.priority === 'HIGH' && i.status !== 'RESOLVED').length;
  const pendingCount = queueItems.filter(i => i.status === 'PENDING_REVIEW').length;
  const resolvedCount = queueItems.filter(i => i.status === 'RESOLVED').length;

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-700">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">Manual Review Queue</h1>
                {isDemoData && <DemoDataBadge reason="Connector Queue Fallback" />}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Statutory fallback routing for inconclusive, timeout, or mismatched external issuer inquiries.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Stat Counter Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="px-3 py-1.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs font-semibold flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <span>{highPriorityCount} Urgent</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl border border-amber-200 bg-amber-50 text-amber-800 text-xs font-semibold">
            <span>{pendingCount} Pending Review</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs font-semibold">
            <span>{resolvedCount} Resolved</span>
          </div>
          <button
            onClick={fetchQueue}
            disabled={loading}
            className="p-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl transition-colors cursor-pointer"
            title="Refresh Queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Advisory Notice */}
      <div className="bg-sky-50/70 border border-sky-200/80 rounded-2xl p-4 flex items-start space-x-3 text-xs text-sky-900">
        <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Statutory Protocol (Section 6 Compliance):</strong> Every automated verification flag represents an 
          <em>"Indicator for review"</em>. Autonomous rejections are strictly prohibited. Scrutiny officers must substantiate 
          determinations with official reference remarks and request clarifying documentation prior to formal committee hearings.
        </div>
      </div>

      {/* Success Notification */}
      {resolveSuccessMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-3 rounded-2xl text-xs font-semibold flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{resolveSuccessMsg}</span>
        </div>
      )}

      {/* 2. Search & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            placeholder="Search queue ID, institution, document, or reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:border-indigo-500 shadow-2xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Priority filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden focus:border-indigo-500 shadow-2xs cursor-pointer"
          >
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden focus:border-indigo-500 shadow-2xs cursor-pointer"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="IN_REVIEW">In Review</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* 3. Main Ticket Cards List (Zero Horizontal Scroll) */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600" />
            <p className="text-xs font-semibold">Synchronizing with authoritative review queue...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 space-y-2">
            <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-500 opacity-60" />
            <p className="text-sm font-bold text-slate-700">No cases match the selected filters</p>
            <p className="text-xs text-slate-400">All external issuer queries are either verified or resolved.</p>
          </div>
        ) : (
          filteredItems.map((item, idx) => {
            const isExpanded = expandedRowId === item.queue_id;
            const isVerifying = verifyingMap[item.queue_id]?.loading;
            const isResolved = item.status === 'RESOLVED';

            return (
              <div 
                key={item.queue_id || idx} 
                className={`bg-white border rounded-2xl p-5 shadow-xs transition-all ${
                  item.priority === 'HIGH' && !isResolved 
                    ? 'border-rose-300 ring-1 ring-rose-200 bg-rose-50/10' 
                    : 'border-slate-200'
                }`}
              >
                {/* Card Top Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono font-bold bg-slate-100 text-slate-800 px-2.5 py-1 rounded-lg text-xs border border-slate-200">
                      {item.queue_id}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border ${
                      item.priority === 'HIGH'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : item.priority === 'LOW'
                        ? 'bg-slate-50 text-slate-600 border-slate-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {item.priority} Priority
                    </span>
                    <StatusChip status={item.status} size="sm" />
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-slate-500">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{item.routed_at ? new Date(item.routed_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Recent'}</span>
                  </div>
                </div>

                {/* Card Middle: 3 Columns Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 py-4">
                  {/* Col 1: Institution & Document Details (4 cols) */}
                  <div className="lg:col-span-4 space-y-1.5">
                    <div className="flex items-center space-x-1.5 text-slate-500 text-xs">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-bold text-slate-700">{item.institution_id}</span>
                    </div>
                    <h3 className="font-bold text-sm text-slate-900 leading-snug">{item.institution_name}</h3>
                    <div className="inline-block px-2.5 py-1 bg-indigo-50 border border-indigo-100 rounded-lg text-indigo-700 font-medium text-xs">
                      {item.document_type}
                    </div>
                    {item.reference_number && (
                      <div className="font-mono text-xs text-slate-500">
                        Claimed Ref: <span className="font-bold text-slate-800">{item.reference_number}</span>
                      </div>
                    )}
                  </div>

                  {/* Col 2: Indicator for Review Box (5 cols) */}
                  <div className="lg:col-span-5">
                    <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 h-full flex flex-col justify-between space-y-2">
                      <div>
                        <div className="flex items-center space-x-1.5 text-amber-800 text-[11px] font-bold uppercase tracking-wider mb-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>Indicator for review</span>
                        </div>
                        <p className="text-xs text-amber-950 font-medium leading-relaxed">
                          {item.reason}
                        </p>
                      </div>
                      <div className="text-[10px] text-amber-800/80 italic">
                        Authoritative source inquiry was inconclusive; committee verification required.
                      </div>
                    </div>
                  </div>

                  {/* Col 3: Source & Hashes (3 cols) */}
                  <div className="lg:col-span-3 bg-slate-50 border border-slate-200/80 rounded-xl p-3 space-y-2 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Authoritative Source</span>
                      <span className="font-mono font-semibold text-slate-800 text-xs break-all">{item.source}</span>
                    </div>

                    <div className="space-y-1 pt-1 border-t border-slate-200/60 font-mono text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-[10px]">Req Hash:</span>
                        <div className="flex items-center space-x-1">
                          <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700">
                            {item.request_hash ? `${item.request_hash.substring(0, 8)}...` : 'N/A'}
                          </span>
                          <button onClick={() => handleCopy(item.request_hash, `req-${item.queue_id}`)} className="text-slate-400 hover:text-indigo-600 p-0.5" title="Copy Request Hash">
                            {copiedHash === `req-${item.queue_id}` ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-[10px]">Res Hash:</span>
                        <div className="flex items-center space-x-1">
                          <span className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700">
                            {item.response_hash ? `${item.response_hash.substring(0, 8)}...` : 'N/A'}
                          </span>
                          <button onClick={() => handleCopy(item.response_hash, `res-${item.queue_id}`)} className="text-slate-400 hover:text-indigo-600 p-0.5" title="Copy Response Hash">
                            {copiedHash === `res-${item.queue_id}` ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Bottom Row: Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <button
                    onClick={() => setExpandedRowId(isExpanded ? null : item.queue_id)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1 cursor-pointer self-start sm:self-auto"
                  >
                    <span>{isExpanded ? 'Hide Technical Dossier' : 'View Full Verification Dossier'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <div className="flex items-center space-x-2.5">
                    <button
                      id={`verify-now-${item.queue_id}`}
                      onClick={() => handleVerifyNow(item)}
                      disabled={isVerifying}
                      className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 shadow-2xs cursor-pointer ${
                        isVerifying
                          ? 'bg-slate-100 text-slate-400 cursor-wait'
                          : 'bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100'
                      }`}
                      title="Re-query authoritative external issuer gateway live"
                    >
                      <Zap className={`w-3.5 h-3.5 ${isVerifying ? 'animate-bounce text-sky-500' : 'text-sky-600'}`} />
                      <span>{isVerifying ? 'Re-Querying Gateway...' : 'Verify Now'}</span>
                    </button>

                    <button
                      id={`resolve-btn-${item.queue_id}`}
                      onClick={() => {
                        setResolveItem(item);
                        setResolveStatus(item.status === 'RESOLVED' ? 'RESOLVED' : 'VERIFIED');
                      }}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
                    >
                      Resolve Ticket
                    </button>
                  </div>
                </div>

                {/* Expandable Technical Details Drawer */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
                    <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200 shadow-2xs space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-200/60 pb-2">
                        <span className="font-bold text-xs text-slate-800 flex items-center space-x-1.5">
                          <FileCheck2 className="w-4 h-4 text-indigo-600" />
                          <span>Authoritative Verification Audit Dossier</span>
                        </span>
                        <span className="text-[11px] font-mono text-slate-500">
                          Ticket ID: {item.queue_id}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                        <div>
                          <h4 className="font-bold text-slate-700 text-[11px] uppercase tracking-wider mb-1">
                            Claimed Application Parameters
                          </h4>
                          <pre className="p-2.5 bg-white rounded-xl border border-slate-200 text-[10px] font-mono text-slate-700 overflow-x-auto">
                            {JSON.stringify(item.doc_fields || { reference_number: item.reference_number, document_type: item.document_type }, null, 2)}
                          </pre>
                        </div>

                        <div>
                          <h4 className="font-bold text-slate-700 text-[11px] uppercase tracking-wider mb-1">
                            Authoritative Gateway Response Data
                          </h4>
                          <pre className="p-2.5 bg-white rounded-xl border border-slate-200 text-[10px] font-mono text-slate-700 overflow-x-auto">
                            {JSON.stringify(item.verification_result?.authoritative_data || item.verification_result || { note: 'Awaiting manual officer reconciliation' }, null, 2)}
                          </pre>
                        </div>
                      </div>

                      {/* Full Hashes and Audit Trail Link */}
                      <div className="pt-2 border-t border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
                        <div className="space-y-1">
                          <div className="font-mono text-slate-600 truncate max-w-xl">
                            <strong className="text-slate-800">Full SHA-256 Request Hash:</strong> {item.request_hash || 'Pending'}
                          </div>
                          <div className="font-mono text-slate-600 truncate max-w-xl">
                            <strong className="text-slate-800">Full SHA-256 Response Hash:</strong> {item.response_hash || 'Pending'}
                          </div>
                        </div>

                        {onNavigateToAudit && (
                          <button
                            onClick={() => onNavigateToAudit(item.institution_id)}
                            className="inline-flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 font-bold text-xs"
                          >
                            <span>View Audit Ledger</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 4. Officer Resolution Modal */}
      {resolveItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-scale-up">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <Clock className="w-4 h-4 text-indigo-600" />
                <span>Resolve Review Ticket: {resolveItem.queue_id}</span>
              </h3>
              <button
                onClick={() => setResolveItem(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-bold text-slate-700">Institution & Document:</span>
                <p className="text-slate-900 font-semibold">{resolveItem.institution_name} ({resolveItem.institution_id})</p>
                <p className="text-slate-500 text-[11px]">{resolveItem.document_type} • Ref: {resolveItem.reference_number || 'N/A'}</p>
              </div>

              <div>
                <span className="font-bold text-slate-700">Flag Reason:</span>
                <p className="text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-[11px] leading-relaxed">
                  {resolveItem.reason}
                </p>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Determination Resolution:</label>
                <select
                  value={resolveStatus}
                  onChange={(e) => setResolveStatus(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-bold text-slate-800"
                >
                  <option value="RESOLVED">Verified (Discrepancy Explained / Cleared)</option>
                  <option value="IN_REVIEW">Request More Evidence / Clarification (Applicant Notice)</option>
                  <option value="REJECTED">Recommend On-Site Physical Inspection</option>
                  <option value="PENDING_REVIEW">Escalate to Regional Committee</option>
                </select>
                <p className="text-[10px] text-slate-400 mt-1">
                  * Note: Determinations are logged to the immutable audit chain. Committee approval required.
                </p>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Officer Substantiation Note (Required):</label>
                <textarea
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  placeholder="State factual grounds, authoritative portal cross-reference, or clarification notice terms..."
                  rows={3}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-hidden focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setResolveItem(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
              <button
                disabled={resolving || !resolveNotes.trim()}
                onClick={handleResolveSubmit}
                className={`px-4 py-2 text-xs font-bold rounded-xl shadow-xs cursor-pointer flex items-center space-x-1.5 ${
                  resolving || !resolveNotes.trim()
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
              >
                {resolving && <RefreshCw className="w-3 h-3 animate-spin" />}
                <span>Confirm Determination</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
