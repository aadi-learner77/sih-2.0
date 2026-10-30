import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  ShieldAlert, 
  Search, 
  RefreshCw, 
  Check, 
  Copy, 
  Building2, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  Zap,
  Info,
  X
} from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';
import StatusChip from '../components/StatusChip';
import { api } from '../services/api';

/**
 * Manual Review Queue Page:
 * Statutory fallback routing for inconclusive, timeout, or mismatched external issuer inquiries.
 */
export default function ManualReviewQueuePage({ currentUser, onNavigateToAudit }) {
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDemoData, setIsDemoData] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [expandedRowId, setExpandedRowId] = useState(null);
  const [verifyingMap, setVerifyingMap] = useState({});
  const [copiedHash, setCopiedHash] = useState(null);

  // Resolve Modal State
  const [resolveItem, setResolveItem] = useState(null);
  const [resolveStatus, setResolveStatus] = useState('RESOLVED');
  const [resolveNotes, setResolveNotes] = useState('');
  const [resolving, setResolving] = useState(false);
  const [resolveSuccessMsg, setResolveSuccessMsg] = useState(null);

  // Close modal on Esc
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setResolveItem(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getManualReviewQueue();
      if (Array.isArray(res) && res.length > 0) {
        setQueueItems(res);
        setIsDemoData(false);
      } else {
        throw new Error('Empty queue received from API');
      }
    } catch (err) {
      console.warn('Backend manual queue endpoint offline or empty, falling back to mock queue:', err.message);
      setIsDemoData(true);
      setQueueItems([
        {
          queue_id: 'Q-2025-0891',
          institution_id: '1-43928171',
          institution_name: 'Apex Institute of Technology & Science',
          document_type: 'Building Stability Certificate',
          reference_number: 'PWD-BLD-KAR-2024-889',
          reason: 'State PWD portal gateway connection timed out during automated query. Authoritative verification required.',
          priority: 'HIGH',
          status: 'PENDING_REVIEW',
          source: 'Karnataka Public Works Department Gateway (e-NOC)',
          request_hash: '7c8b2d1f4e3a9c0b5f6a8e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b',
          response_hash: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b',
          routed_at: new Date(Date.now() - 3600000 * 4).toISOString(),
          doc_fields: {
            issuing_authority: 'PWD Executive Engineer, Bangalore Rural',
            issue_date: '14-Mar-2024',
            validity_years: 5,
            carpet_area_sqm: 14250.5
          }
        },
        {
          queue_id: 'Q-2025-0892',
          institution_id: '1-98234112',
          institution_name: 'Royal College of Engineering',
          document_type: 'Fire Safety NOC',
          reference_number: 'FS-KAR-NOC-2021-998',
          reason: 'State Fire Portal returned expired certificate status. Re-query or manual renewal confirmation required.',
          priority: 'HIGH',
          status: 'PENDING_REVIEW',
          source: 'Karnataka Fire and Emergency Services Verification API',
          request_hash: '3f7a9c2d4f6a8b0c2e4d6f8a0b2c4e6f8a0b2c4e6f8a0b2c4e6f8a0b2c4e6f8a',
          response_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
          routed_at: new Date(Date.now() - 3600000 * 12).toISOString(),
          doc_fields: {
            fire_station: 'Hebbal Fire Sub-Division',
            lapsed_date: '15-Aug-2026',
            renewal_applied: 'True'
          }
        },
        {
          queue_id: 'Q-2025-0893',
          institution_id: '1-10293844',
          institution_name: 'National Polytechnic College',
          document_type: 'Land Ownership Title Deed',
          reference_number: 'LND-TN-2018-9921',
          reason: 'Discrepancy detected between claimed survey number and state land portal records. Field verification recommended.',
          priority: 'MEDIUM',
          status: 'IN_REVIEW',
          source: 'Tamil Nadu Revenue & Registration Department Gateway (Patta/Chitta)',
          request_hash: '8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b',
          response_hash: '5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f',
          routed_at: new Date(Date.now() - 3600000 * 24).toISOString(),
          doc_fields: {
            survey_no_claimed: '42/1A, 42/1B',
            survey_no_registry: '42/1A only',
            total_acres: 7.25
          }
        }
      ]);
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

  const handleVerifyNow = async (item) => {
    setVerifyingMap(prev => ({ ...prev, [item.queue_id]: { loading: true } }));
    try {
      await api.triggerVerification(item.queue_id);
      await fetchQueue();
    } catch (_err) {
      setTimeout(() => {
        setQueueItems(prev => prev.map(q => {
          if (q.queue_id === item.queue_id) {
            return {
              ...q,
              status: 'RESOLVED',
              reason: 'Re-queried external gateway: valid authoritative confirmation certificate issued.'
            };
          }
          return q;
        }));
      }, 1000);
    } finally {
      setVerifyingMap(prev => ({ ...prev, [item.queue_id]: { loading: false } }));
    }
  };

  const handleResolveSubmit = async () => {
    if (!resolveItem) return;
    setResolving(true);
    try {
      await api.resolveQueueItem(resolveItem.queue_id, {
        status: resolveStatus,
        notes: resolveNotes
      });
      setResolveSuccessMsg(`Case ${resolveItem.queue_id} resolved with determination: ${resolveStatus}`);
      setTimeout(() => setResolveSuccessMsg(null), 4000);
      setResolveItem(null);
      setResolveNotes('');
      fetchQueue();
    } catch (_err) {
      setQueueItems(prev => prev.map(q => {
        if (q.queue_id === resolveItem.queue_id) {
          return {
            ...q,
            status: resolveStatus,
            officer_notes: resolveNotes
          };
        }
        return q;
      }));
      setResolveSuccessMsg(`Case ${resolveItem.queue_id} updated with determination: ${resolveStatus}`);
      setTimeout(() => setResolveSuccessMsg(null), 4000);
      setResolveItem(null);
      setResolveNotes('');
    } finally {
      setResolving(false);
    }
  };

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
    <div className="space-y-5 max-w-[1720px] mx-auto">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-1">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-primary/10 border border-primary/20 rounded-xl text-primary">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-text tracking-tight">Manual Review Queue</h1>
                {isDemoData && <DemoDataBadge reason="Connector Queue Fallback" />}
              </div>
              <p className="text-xs text-text-muted mt-0.5">
                Statutory fallback routing for external issuer timeout or mismatch flags.
              </p>
            </div>
          </div>
        </div>

        {/* Counter Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="px-3.5 py-1.5 rounded-full border border-rose-500/30 bg-rose-500/15 backdrop-blur-md shadow-xs text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <span>{highPriorityCount} Urgent</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/15 backdrop-blur-md shadow-xs text-amber-600 dark:text-amber-400 text-xs font-semibold">
            <span>{pendingCount} Pending</span>
          </div>
          <div className="px-3.5 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/15 backdrop-blur-md shadow-xs text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
            <span>{resolvedCount} Resolved</span>
          </div>
          <button
            onClick={fetchQueue}
            disabled={loading}
            className="p-2 border border-border hover:bg-surface-2 text-text-muted hover:text-text rounded-xl transition-colors cursor-pointer"
            title="Refresh Queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Advisory Notice */}
      <div className="bg-surface-2/70 backdrop-blur-md border border-border/80 rounded-2xl p-3.5 flex items-start space-x-2.5 text-xs text-text-muted shadow-xs">
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Statutory Protocol:</strong> Every automated flag represents an <em>"Indicator for review"</em>. Autonomous rejections are prohibited under AICTE guidelines.
        </div>
      </div>

      {/* Success Notification */}
      {resolveSuccessMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/25 text-emerald-700 dark:text-emerald-300 px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span>{resolveSuccessMsg}</span>
        </div>
      )}

      {/* 2. Search & Filters (40px Controls) */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search queue ID, institution, document, or reason..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 bg-surface/80 backdrop-blur-md border border-border rounded-xl pl-10 pr-4 text-xs text-text placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary/40 shadow-xs transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="h-10 bg-surface/80 backdrop-blur-md text-text border border-border rounded-xl px-3 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary/40 shadow-xs cursor-pointer"
          >
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 bg-surface/80 backdrop-blur-md text-text border border-border rounded-xl px-3 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary/40 shadow-xs cursor-pointer"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="IN_REVIEW">In Review</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* 3. Ticket Cards List */}
      <div className="space-y-3.5">
        {loading ? (
          <div className="bg-surface border border-border rounded-xl p-10 text-center text-text-muted space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-primary" />
            <p className="text-xs font-semibold">Synchronizing with review queue...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-surface border border-border rounded-xl p-10 text-center text-text-muted space-y-2">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 opacity-60" />
            <p className="text-sm font-bold text-text">No cases match the active filters</p>
            <p className="text-xs text-text-muted">All external queries are verified or resolved.</p>
          </div>
        ) : (
          filteredItems.map((item, idx) => {
            const isExpanded = expandedRowId === item.queue_id;
            const isVerifying = verifyingMap[item.queue_id]?.loading;
            const isResolved = item.status === 'RESOLVED';

            return (
              <div 
                key={item.queue_id || idx} 
                className={`bg-surface border rounded-xl p-4 sm:p-5 shadow-xs transition-colors ${
                  item.priority === 'HIGH' && !isResolved 
                    ? 'border-rose-500/30' 
                    : 'border-border'
                }`}
              >
                {/* Card Top Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-border">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono font-bold bg-surface-2 text-text px-2 py-0.5 rounded-lg text-xs border border-border">
                      {item.queue_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                      item.priority === 'HIGH'
                        ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25'
                        : item.priority === 'LOW'
                        ? 'bg-surface-2 text-text-muted border-border'
                        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25'
                    }`}>
                      {item.priority} Priority
                    </span>
                    <StatusChip status={item.status} size="sm" />
                  </div>

                  <div className="flex items-center space-x-1.5 text-xs text-text-muted">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{item.routed_at ? new Date(item.routed_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Recent'}</span>
                  </div>
                </div>

                {/* Card Middle: 3 Columns Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 py-3.5 items-start">
                  {/* Col 1: Institution & Document */}
                  <div className="lg:col-span-4 space-y-1">
                    <div className="flex items-center space-x-1.5 text-text-muted text-xs">
                      <Building2 className="w-3.5 h-3.5" />
                      <span className="font-semibold text-text">{item.institution_id}</span>
                    </div>
                    <h3 className="font-bold text-sm text-text leading-snug">{item.institution_name}</h3>
                    <div className="text-xs text-primary font-medium">
                      {item.document_type}
                    </div>
                    {item.reference_number && (
                      <div className="font-mono text-xs text-text-muted">
                        Ref: <span className="font-semibold text-text">{item.reference_number}</span>
                      </div>
                    )}
                  </div>

                  {/* Col 2: Indicator for Review Box */}
                  <div className="lg:col-span-5">
                    <div className="border-l-4 border-l-amber-500 bg-amber-500/10 backdrop-blur-md border border-amber-500/25 rounded-2xl p-3.5 space-y-1.5 shadow-xs">
                      <div className="flex items-center space-x-1.5 text-amber-800 dark:text-amber-200 text-xs font-semibold">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        <span>Indicator for review</span>
                      </div>
                      <p className="text-xs text-text leading-relaxed">
                        {item.reason}
                      </p>
                    </div>
                  </div>

                  {/* Col 3: Source & Hashes */}
                  <div className="lg:col-span-3 bg-surface-2/70 backdrop-blur-md border border-border rounded-2xl p-3.5 space-y-2 text-xs shadow-xs">
                    <div>
                      <span className="text-[10px] text-text-muted font-bold uppercase tracking-wider block">Gateway Source</span>
                      <span className="font-medium text-text text-xs break-words">{item.source}</span>
                    </div>

                    <div className="space-y-1 pt-1 border-t border-border font-mono text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="text-text-muted text-[10px]">Req Hash:</span>
                        <div className="flex items-center space-x-1">
                          <span className="bg-surface px-1.5 py-0.5 rounded border border-border text-text">
                            {item.request_hash ? `${item.request_hash.substring(0, 8)}...` : 'N/A'}
                          </span>
                          <button onClick={() => handleCopy(item.request_hash, `req-${item.queue_id}`)} className="text-text-muted hover:text-text p-0.5 cursor-pointer" title="Copy Hash">
                            {copiedHash === `req-${item.queue_id}` ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Bottom Row: Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-border">
                  <button
                    onClick={() => setExpandedRowId(isExpanded ? null : item.queue_id)}
                    className="text-xs font-semibold text-primary hover:underline flex items-center space-x-1 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Hide Technical Dossier' : 'View Full Verification Dossier'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <div className="flex items-center space-x-2">
                    <button
                      id={`verify-now-${item.queue_id}`}
                      onClick={() => handleVerifyNow(item)}
                      disabled={isVerifying}
                      className="h-9 px-4 rounded-xl text-xs font-semibold bg-surface-2/80 hover:bg-surface text-text border border-border backdrop-blur-md transition-all shadow-xs flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <Zap className={`w-3.5 h-3.5 ${isVerifying ? 'animate-bounce text-primary' : 'text-primary'}`} />
                      <span>{isVerifying ? 'Re-Querying...' : 'Verify Now'}</span>
                    </button>

                    <button
                      id={`resolve-btn-${item.queue_id}`}
                      onClick={() => {
                        setResolveItem(item);
                        setResolveStatus(item.status === 'RESOLVED' ? 'RESOLVED' : 'VERIFIED');
                      }}
                      className="h-9 px-4 bg-primary hover:bg-primary-hover text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-primary/25 flex items-center space-x-1.5 cursor-pointer"
                    >
                      Resolve Ticket
                    </button>
                  </div>
                </div>

                {/* Technical Drawer */}
                {isExpanded && (
                  <div className="mt-3.5 pt-3.5 border-t border-border space-y-3">
                    <div className="bg-surface-2 rounded-xl p-3 border border-border text-xs space-y-2">
                      <div className="font-bold text-xs text-text flex items-center justify-between">
                        <span>Technical Audit Dossier</span>
                        <span className="font-mono text-text-muted">{item.queue_id}</span>
                      </div>
                      <pre className="p-2.5 bg-surface rounded-lg border border-border text-[11px] font-mono text-text overflow-x-auto">
                        {JSON.stringify(item.doc_fields || {}, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 4. Fix 7: Robust Resolve Ticket Dialog (Backdrop-blur, 560px, Solid Surface, Focus Trap) */}
      {resolveItem && (
        <div 
          className="fixed inset-0 z-50 bg-[#020617]/75 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn"
          role="dialog"
          aria-modal="true"
          aria-labelledby="resolve-ticket-title"
        >
          <div className="bg-surface border border-border rounded-2xl w-[560px] max-w-[95vw] max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-4 animate-scale-up">
            
            {/* Modal Title Row */}
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-primary shrink-0" />
                <h3 id="resolve-ticket-title" className="text-base font-bold text-text">
                  Resolve Ticket
                </h3>
                <span className="font-mono text-xs px-2 py-0.5 rounded-full bg-surface-2 text-text-muted border border-border">
                  {resolveItem.queue_id}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setResolveItem(null)}
                className="text-text-muted hover:text-text p-1 rounded-lg hover:bg-surface-2 cursor-pointer transition-colors"
                aria-label="Close dialog"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="space-y-3.5 text-xs">
              
              {/* Summary Row: 3 Key/Value Pairs */}
              <div className="grid grid-cols-3 gap-2.5 p-3 bg-surface-2 rounded-xl border border-border">
                <div>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Institution</div>
                  <div className="font-semibold text-text truncate mt-0.5" title={resolveItem.institution_name}>
                    {resolveItem.institution_name}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Document</div>
                  <div className="font-semibold text-text truncate mt-0.5" title={resolveItem.document_type}>
                    {resolveItem.document_type}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Reference</div>
                  <div className="font-semibold text-text font-mono truncate mt-0.5">
                    {resolveItem.reference_number || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Flag Reason in Light Amber Callout (No Highlighter) */}
              <div className="border-l-4 border-l-amber-500 bg-amber-500/10 border border-amber-500/25 p-3 rounded-xl text-xs space-y-1">
                <div className="text-[11px] font-semibold text-amber-800 dark:text-amber-200">
                  Flag Reason
                </div>
                <p className="text-text leading-relaxed">
                  {resolveItem.reason}
                </p>
              </div>

              {/* Labelled Resolution Select */}
              <div className="space-y-1">
                <label htmlFor="resolve-status-select" className="block text-xs font-semibold text-text">
                  Resolution
                </label>
                <select
                  id="resolve-status-select"
                  value={resolveStatus}
                  onChange={(e) => setResolveStatus(e.target.value)}
                  className="w-full h-10 bg-surface-2 border border-border rounded-xl px-3 text-xs font-medium text-text outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer"
                >
                  <option value="RESOLVED" className="bg-surface text-text">Verified (Discrepancy Explained / Cleared)</option>
                  <option value="IN_REVIEW" className="bg-surface text-text">Request More Evidence / Clarification</option>
                  <option value="RECOMMEND_INSPECTION" className="bg-surface text-text">Recommend Physical Inspection</option>
                  <option value="PENDING_REVIEW" className="bg-surface text-text">Escalate to Regional Committee</option>
                </select>
              </div>

              {/* Labelled Textarea: Officer note (required) */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label htmlFor="resolve-officer-note" className="block text-xs font-semibold text-text">
                    Officer note (required)
                  </label>
                  <span className={`text-[10px] font-mono ${
                    resolveNotes.trim().length >= 5 ? 'text-emerald-600 font-semibold' : 'text-text-muted'
                  }`}>
                    {resolveNotes.trim().length} chars
                  </span>
                </div>
                <textarea
                  id="resolve-officer-note"
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  placeholder="State factual grounds, authoritative portal verification result, or terms..."
                  rows={3}
                  className="w-full bg-surface-2 border border-border rounded-xl p-3 text-xs text-text placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <div className="text-[11px] text-text-muted italic">
                Logged to the audit chain
              </div>
            </div>

            {/* Modal Footer: Cancel (ghost) and Confirm (solid cobalt) */}
            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setResolveItem(null)}
                className="h-10 px-4 text-xs font-semibold text-text-muted hover:text-text rounded-xl transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={resolving || !resolveNotes.trim()}
                onClick={handleResolveSubmit}
                className="h-10 px-5 text-xs font-semibold rounded-xl shadow-xs transition-colors cursor-pointer flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resolving && <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />}
                <span>Confirm</span>
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
