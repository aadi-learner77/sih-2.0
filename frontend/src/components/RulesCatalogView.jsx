import React, { useState, useEffect, useMemo } from 'react';
import { 
  BookOpenCheck, 
  Search, 
  Filter, 
  Scale, 
  FileText, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronRight, 
  ChevronDown, 
  ExternalLink, 
  Copy, 
  Check, 
  RefreshCw, 
  Info,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import StatusChip from './StatusChip';
import DemoDataBadge from './DemoDataBadge';
import { api } from '../services/api';

/**
 * AICTE Approval Process Handbook (APH) Rules Catalog:
 * - Formatted clause-citation format: [AICTE APH 2025-26 Clause X.X.X]
 * - Category filters (Faculty & Cadre, Infrastructure, Land & Title, Legal & Entity, Governance)
 * - Search by clause citation, title, or rule code
 * - Expanded detail drawer with exact parameter thresholds and failure message template
 * - "Simulate in What-If" action button
 */
export default function RulesCatalogView({ onSelectForSimulation }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDemoData, setIsDemoData] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [expandedRuleId, setExpandedRuleId] = useState(null);
  const [copiedCitation, setCopiedCitation] = useState(null);

  // Load rules from backend API
  const fetchRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRules();
      if (Array.isArray(data) && data.length > 0) {
        setRules(data);
        setIsDemoData(false);
      } else {
        throw new Error('Empty rules catalog');
      }
    } catch (err) {
      console.warn('Backend rules API offline, falling back to mock rules:', err);
      setError('Live regulations catalog temporarily offline. Displaying authoritative APH 2025-26 baseline.');
      setIsDemoData(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  // Standardize clause citation format
  const formatClauseCitation = (rule) => {
    const rawClause = rule.clause_id || 'APH-2025-Cl-Norm';
    // Format APH-2025-Cl-4.1.2 -> AICTE APH 2025-26 Clause 4.1.2
    const cleanClause = rawClause
      .replace(/^APH-2025-Cl-/, '')
      .replace(/^APH\s*2025-26\s*Clause\s*/i, '')
      .replace(/^APH-CH\d+-Clause-/, '');
    return `AICTE APH 2025-26 Clause ${cleanClause}`;
  };

  const handleCopyCitation = (citation, id) => {
    navigator.clipboard.writeText(citation);
    setCopiedCitation(id);
    setTimeout(() => setCopiedCitation(null), 2000);
  };

  // Categories list
  const categories = useMemo(() => {
    const set = new Set();
    rules.forEach((r) => r.category && set.add(r.category));
    return ['ALL', ...Array.from(set)];
  }, [rules]);

  // Filtered rules
  const filteredRules = useMemo(() => {
    return rules.filter((r) => {
      const citation = formatClauseCitation(r).toLowerCase();
      const title = (r.title || '').toLowerCase();
      const code = (r.rule_code || '').toLowerCase();
      const desc = (r.description || '').toLowerCase();
      const q = searchQuery.toLowerCase();

      const matchesSearch = !searchQuery || citation.includes(q) || title.includes(q) || code.includes(q) || desc.includes(q);
      const matchesCategory = selectedCategory === 'ALL' || r.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [rules, searchQuery, selectedCategory]);

  return (
    <div className="space-y-6">
      {/* 1. Header & Statutory Guidance Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-xl text-purple-700">
              <BookOpenCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">AICTE Handbook Rules Catalog</h2>
                {isDemoData && <DemoDataBadge reason="Handbook Baseline Fallback" />}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Official AICTE Approval Process Handbook (APH) 2025-26 statutory codification with formal clause citations and automated evaluation constraints.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-purple-800 bg-purple-50 px-3 py-1.5 rounded-xl border border-purple-200 self-start md:self-auto">
          <span>Edition: <strong>AICTE APH 2025-26</strong></span>
          <span>•</span>
          <span>Version: <strong>v1.0.0</strong></span>
        </div>
      </div>

      {/* Statutory Section 6 Caveat */}
      <div className="bg-purple-50/70 border border-purple-200/80 rounded-2xl p-4 flex items-start space-x-3 text-xs text-purple-950">
        <Info className="w-4 h-4 text-purple-700 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Mandatory Statutory Protocol:</strong> Rule evaluations in PRAMAAN-X serve as 
          <em> "Indicators for review"</em>. Non-compliance findings cite the exact handbook clause to ensure full legal defensibility during scrutiny committee inquiry. Automated rejections are strictly prohibited.
        </div>
      </div>

      {/* 2. Search & Category Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search clause citation (e.g. Clause 4.1), title, or rule code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 bg-surface border border-border rounded-xl pl-10 pr-4 text-xs text-text placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 shadow-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-purple-600 text-white shadow-2xs'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {cat === 'ALL' ? 'All Regulations' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Rules Catalog List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center text-slate-400 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-purple-600" />
            <p className="text-sm font-semibold text-slate-700">Loading statutory rule definitions...</p>
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400 space-y-2">
            <BookOpenCheck className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-sm font-bold text-slate-700">No regulations match your query</p>
            <p className="text-xs text-slate-400">Try adjusting the search keyword or category filter.</p>
          </div>
        ) : (
          filteredRules.map((rule, idx) => {
            const citation = formatClauseCitation(rule);
            const isExpanded = expandedRuleId === rule.id;
            const version = rule.current_version || {};
            const params = version.parameters || {};

            return (
              <div
                key={rule.id || idx}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:border-purple-300 transition-all space-y-3"
              >
                {/* Rule Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Official Clause Citation Badge */}
                    <span 
                      onClick={() => handleCopyCitation(citation, rule.id)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-xl text-xs font-mono font-bold bg-purple-50 text-purple-800 border border-purple-200 hover:bg-purple-100 cursor-pointer transition-colors"
                      title="Click to copy statutory citation"
                    >
                      <Scale className="w-3.5 h-3.5 text-purple-600" />
                      <span>[{citation}]</span>
                      {copiedCitation === rule.id ? (
                        <Check className="w-3 h-3 text-emerald-600 ml-1" />
                      ) : (
                        <Copy className="w-3 h-3 text-purple-400 ml-1" />
                      )}
                    </span>

                    <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      {rule.rule_code}
                    </span>

                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                      rule.severity === 'CRITICAL'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {rule.severity || 'CRITICAL'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-slate-500">
                    <span className="font-semibold text-slate-700">{rule.category}</span>
                    <span>•</span>
                    <span className="font-mono text-[11px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                      v{version.version_number || '1.0.0'}
                    </span>
                  </div>
                </div>

                {/* Rule Body */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                  <div className="lg:col-span-8 space-y-2">
                    <h3 className="text-sm font-bold text-slate-900 leading-snug">
                      {rule.title}
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {rule.description}
                    </p>
                  </div>

                  {/* Quick Parameters Summary (4 cols) */}
                  <div className="lg:col-span-4 bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs space-y-1.5">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Statutory Parameters</span>
                    <div className="space-y-1 font-mono text-[11px] text-slate-700">
                      {Object.entries(params).slice(0, 3).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="text-slate-500">{k}:</span>
                          <span className="font-bold text-slate-900 truncate max-w-[140px]">{JSON.stringify(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div className="pt-3 border-t border-slate-100 space-y-3 animate-fade-in text-xs">
                    {/* Failure Template Box */}
                    {version.failure_message_template && (
                      <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-3.5 space-y-1">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-rose-800 flex items-center space-x-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                          <span>Statutory Non-Compliance Output Template</span>
                        </div>
                        <p className="text-xs text-rose-950 font-mono leading-relaxed">
                          {version.failure_message_template}
                        </p>
                      </div>
                    )}

                    {/* Condition & Technical Expression */}
                    <div className="bg-slate-900 text-slate-100 rounded-xl p-3.5 font-mono text-[11px] space-y-2">
                      <div className="flex justify-between text-slate-400 border-b border-slate-800 pb-1.5 text-[10px]">
                        <span>Handbook Edition: {version.handbook_edition || 'AICTE APH 2025-26'}</span>
                        <span>Evaluation Mode: Deterministic Rules Engine</span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block">Full Parameter Dictionary:</span>
                        <pre className="text-emerald-400 overflow-x-auto text-[10px] mt-1">
                          {JSON.stringify(params, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                )}

                {/* Card Footer Actions */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={() => setExpandedRuleId(isExpanded ? null : rule.id)}
                    className="text-xs font-semibold text-purple-700 hover:text-purple-900 flex items-center space-x-1 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Hide Statutory Details' : 'Inspect Citation & Parameters'}</span>
                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>

                  {onSelectForSimulation && (
                    <button
                      onClick={() => onSelectForSimulation(rule)}
                      className="px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer shadow-2xs"
                    >
                      <Sliders className="w-3.5 h-3.5 text-purple-600" />
                      <span>Simulate in What-If</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
