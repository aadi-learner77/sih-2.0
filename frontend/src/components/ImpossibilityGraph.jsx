import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Users, 
  MapPin, 
  Building2, 
  AlertTriangle, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle2, 
  Info,
  Maximize2,
  RefreshCw,
  Code2,
  ChevronDown,
  ChevronRight,
  FileText,
  FlaskConical,
  GraduationCap
} from 'lucide-react';
import { api } from '../services/api';

export default function ImpossibilityGraph() {
  const [graphData, setGraphData] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('ALL');
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [showJsonMap, setShowJsonMap] = useState({});

  const fetchGraphAndAnomalies = async () => {
    setLoading(true);
    try {
      const [gData, aData] = await Promise.all([
        api.getKnowledgeGraph(),
        api.getImpossibilities()
      ]);
      setGraphData(gData);
      setAnomalies(aData || []);
      if (aData && aData.length > 0) {
        setSelectedAnomaly(aData[0]);
      }
    } catch (err) {
      console.error('Error fetching graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphAndAnomalies();
  }, []);

  const toggleJson = (idx) => {
    setShowJsonMap(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const filteredAnomalies = filterType === 'ALL' 
    ? anomalies 
    : anomalies.filter(a => {
        const cType = a.conflict_type || a.check_id || '';
        if (filterType === 'DUAL_EMPLOYMENT') {
          return cType.includes('DUAL_EMPLOYMENT');
        }
        if (filterType === 'AREA_DENSITY') {
          return cType.includes('AREA_DENSITY') || cType.includes('DENSITY');
        }
        if (filterType === 'CHRONOLOGY') {
          return cType.includes('DOCUMENT_PREDATES') || cType.includes('DOCUMENT_INVERTED') || cType.includes('CHRONOLOGY');
        }
        if (filterType === 'LAB_EQUIPMENT') {
          return cType.includes('LAB_EQUIPMENT');
        }
        if (filterType === 'SHARED_DOCUMENT') {
          return cType.includes('SHARED_DOCUMENT');
        }
        if (filterType === 'LAND_PARCEL') {
          return cType.includes('LAND_PARCEL');
        }
        return cType === filterType;
      });

  const getNodeIcon = (type) => {
    switch (type) {
      case 'INSTITUTION': return <Building2 className="w-3.5 h-3.5 text-sky-600" />;
      case 'FACULTY': return <Users className="w-3.5 h-3.5 text-rose-600" />;
      case 'PROGRAMME': return <GraduationCap className="w-3.5 h-3.5 text-indigo-600" />;
      case 'DOCUMENT': return <FileText className="w-3.5 h-3.5 text-amber-600" />;
      case 'LAB': return <FlaskConical className="w-3.5 h-3.5 text-emerald-600" />;
      case 'BUILDING': return <Building2 className="w-3.5 h-3.5 text-cyan-600" />;
      case 'LOCATION': return <MapPin className="w-3.5 h-3.5 text-purple-600" />;
      case 'ISSUER': return <ShieldAlert className="w-3.5 h-3.5 text-orange-600" />;
      default: return <Info className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-rose-50 via-white to-slate-50 border border-rose-200/70 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-700 uppercase tracking-widest mb-1">
              <span>NetworkX Institution Twin</span>
              <span>•</span>
              <span>Indicator for Review Radar</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Institution Twin: Multi-College Regulatory Radar
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Constructs an inter-institutional digital twin graph of Institutions, Faculty, Programmes, Documents, Labs, Buildings, Locations, and Issuers to detect mathematically and physically impossible claims across regional colleges.
            </p>
          </div>
          <button
            onClick={fetchGraphAndAnomalies}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-xs shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-run Conflict Queries</span>
          </button>
        </div>

        {/* Graph Metrics */}
        {graphData && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-200/80">
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Institutions</div>
              <div className="text-xl font-bold text-sky-700">{graphData.summary?.total_institutions || 0}</div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Faculty Nodes</div>
              <div className="text-xl font-bold text-indigo-700">{graphData.summary?.total_faculty || 0}</div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Documents & Labs</div>
              <div className="text-xl font-bold text-emerald-700">
                {(graphData.summary?.total_documents || 0) + (graphData.summary?.total_labs || 0)}
              </div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Review Indicators</div>
              <div className="text-xl font-bold text-rose-600">{anomalies.length} Flagged</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-1">
        {[
          { id: 'ALL', label: 'All Indicators' },
          { id: 'DUAL_EMPLOYMENT', label: '1. Dual Full-Time Faculty' },
          { id: 'AREA_DENSITY', label: '2. Built-Up Area Density' },
          { id: 'CHRONOLOGY', label: '3. Document Chronology' },
          { id: 'LAB_EQUIPMENT', label: '4. Lab Equipment Consistency' },
          { id: 'SHARED_DOCUMENT', label: '5. Shared Document Reference' },
          { id: 'LAND_PARCEL', label: 'Land Parcel Collisions' }
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilterType(f.id)}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all shrink-0 ${
              filterType === f.id
                ? 'bg-rose-50 border-rose-300 text-rose-800 shadow-xs'
                : 'bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Grid: Graph Visualizer & Anomaly Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Knowledge Graph Topological Map (SVG) */}
        <div className="lg:col-span-6 bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Network className="w-4 h-4 text-sky-600" />
              <h3 className="text-sm font-semibold text-slate-900">Cross-Institutional Relational Map</h3>
            </div>
            <div className="flex items-center space-x-3 text-[11px]">
              <span className="flex items-center space-x-1 text-sky-700">
                <span className="w-2 h-2 rounded-full bg-sky-600 inline-block" />
                <span>Colleges</span>
              </span>
              <span className="flex items-center space-x-1 text-rose-700">
                <span className="w-2 h-2 rounded-full bg-rose-600 inline-block" />
                <span>Faculty</span>
              </span>
              <span className="flex items-center space-x-1 text-amber-700">
                <span className="w-2 h-2 rounded-full bg-amber-600 inline-block" />
                <span>Documents</span>
              </span>
              <span className="flex items-center space-x-1 text-emerald-700">
                <span className="w-2 h-2 rounded-full bg-emerald-600 inline-block" />
                <span>Labs</span>
              </span>
            </div>
          </div>

          {/* Interactive SVG Graph Rendering */}
          <div className="relative bg-slate-50 border border-slate-200/80 rounded-xl p-4 h-96 flex items-center justify-center overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 600 360">
              {/* Conflict Connection Lines */}
              <line x1="160" y1="100" x2="300" y2="180" stroke="#e11d48" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
              <line x1="440" y1="100" x2="300" y2="180" stroke="#e11d48" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
              
              <line x1="160" y1="100" x2="160" y2="280" stroke="#0284c7" strokeWidth="1.5" />
              <line x1="440" y1="100" x2="440" y2="280" stroke="#059669" strokeWidth="1.5" />

              {/* Edge Labels */}
              <rect x="200" y="130" width="85" height="18" rx="4" fill="#ffffff" stroke="#cbd5e1" />
              <text x="242" y="143" fill="#334155" fontSize="8" textAnchor="middle" fontWeight="bold">employs (Full-Time)</text>

              <rect x="330" y="130" width="85" height="18" rx="4" fill="#ffffff" stroke="#cbd5e1" />
              <text x="372" y="143" fill="#334155" fontSize="8" textAnchor="middle" fontWeight="bold">employs (Full-Time)</text>

              {/* Node 1: Apex Institute */}
              <g transform="translate(160, 100)" className="cursor-pointer">
                <circle r="36" fill="#ffffff" stroke="#0284c7" strokeWidth="2.5" />
                <Building2 x="-12" y="-20" className="w-6 h-6 text-sky-600" />
                <text y="8" fill="#0f172a" fontSize="9" fontWeight="bold" textAnchor="middle">Apex Tech</text>
                <text y="20" fill="#64748b" fontSize="8" textAnchor="middle">Bengaluru</text>
              </g>

              {/* Node 2: Royal College */}
              <g transform="translate(440, 100)" className="cursor-pointer">
                <circle r="36" fill="#ffffff" stroke="#0284c7" strokeWidth="2.5" />
                <Building2 x="-12" y="-20" className="w-6 h-6 text-sky-600" />
                <text y="8" fill="#0f172a" fontSize="9" fontWeight="bold" textAnchor="middle">Royal College</text>
                <text y="20" fill="#64748b" fontSize="8" textAnchor="middle">Mysuru</text>
              </g>

              {/* Center Conflict Node: Faculty */}
              <g transform="translate(300, 180)" className="cursor-pointer">
                <circle r="32" fill="#ffe4e6" stroke="#e11d48" strokeWidth="3" className="animate-pulse" />
                <Users x="-10" y="-16" className="w-5 h-5 text-rose-700" />
                <text y="6" fill="#881337" fontSize="8" fontWeight="bold" textAnchor="middle">Dr. R. K. Sharma</text>
                <text y="16" fill="#be123c" fontSize="7" textAnchor="middle">AB****89C</text>
              </g>

              {/* Document Node */}
              <g transform="translate(160, 280)" className="cursor-pointer">
                <rect x="-35" y="-18" width="70" height="36" rx="6" fill="#fffbeb" stroke="#d97706" strokeWidth="2" />
                <text y="-2" fill="#78350f" fontSize="8" fontWeight="bold" textAnchor="middle">Fire Safety NOC</text>
                <text y="10" fill="#b45309" fontSize="7" textAnchor="middle">FIR/KA/99102</text>
              </g>

              {/* Lab Node */}
              <g transform="translate(440, 280)" className="cursor-pointer">
                <rect x="-35" y="-18" width="70" height="36" rx="6" fill="#ecfdf5" stroke="#059669" strokeWidth="2" />
                <text y="-2" fill="#064e3b" fontSize="8" fontWeight="bold" textAnchor="middle">Mech Workshop</text>
                <text y="10" fill="#047857" fontSize="7" textAnchor="middle">Lathe, Milling, UTM</text>
              </g>
            </svg>

            <div className="absolute bottom-3 left-3 bg-white/95 border border-slate-200 rounded-lg px-2.5 py-1 text-[10px] text-slate-500 shadow-xs">
              Topological projection • NetworkX MultiDiGraph (8 Node Types • 5 Edge Types)
            </div>
          </div>

          {/* Active Subgraph Summary */}
          {selectedAnomaly && selectedAnomaly.conflicting_subgraph && (
            <div className="mt-4 pt-4 border-t border-slate-200 text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-700">Selected Conflicting Subgraph:</span>
                <span className="text-[11px] font-mono text-rose-700">
                  {selectedAnomaly.conflicting_subgraph.nodes?.length || 0} nodes • {selectedAnomaly.conflicting_subgraph.edges?.length || 0} edges
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedAnomaly.conflicting_subgraph.nodes?.map((n, i) => (
                  <span key={i} className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-[11px] text-slate-700">
                    {getNodeIcon(n.type)}
                    <span>{n.label || n.id}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Review Indicator Dossiers */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">
              Indicators for Review ({filteredAnomalies.length})
            </h3>
            <span className="text-xs text-rose-700 font-mono font-medium">Statutory review flags</span>
          </div>

          <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {filteredAnomalies.map((anomaly, idx) => (
              <div 
                key={idx}
                onClick={() => setSelectedAnomaly(anomaly)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  selectedAnomaly === anomaly 
                    ? 'bg-rose-50/80 border-rose-300 shadow-xs' 
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span className="text-xs font-bold text-slate-900 leading-tight">{anomaly.title}</span>
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border shrink-0 ${
                    anomaly.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}>
                    {anomaly.indicator_type || 'INDICATOR_FOR_REVIEW'}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  {anomaly.explanation}
                </p>

                {/* Subgraph Nodes & Edges Preview */}
                {anomaly.conflicting_subgraph && (
                  <div className="mb-3 bg-white p-2.5 rounded-lg border border-slate-200/90 space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                      <span>Conflicting Subgraph Entities:</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleJson(idx);
                        }}
                        className="flex items-center space-x-1 text-sky-700 hover:text-sky-900 font-semibold"
                      >
                        <Code2 className="w-3 h-3" />
                        <span>{showJsonMap[idx] ? 'Hide JSON' : 'View Subgraph JSON'}</span>
                      </button>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {anomaly.conflicting_subgraph.nodes?.map((node, nIdx) => (
                        <span key={nIdx} className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-700">
                          {getNodeIcon(node.type)}
                          <span className="font-medium">{node.label || node.name || node.id}</span>
                          <span className="text-[9px] text-slate-400">({node.type})</span>
                        </span>
                      ))}
                    </div>

                    {showJsonMap[idx] && (
                      <pre className="mt-2 p-2 rounded bg-slate-900 text-slate-200 font-mono text-[10px] overflow-x-auto max-h-40">
                        {JSON.stringify(anomaly.conflicting_subgraph, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-700">
                  <strong className="text-rose-700">Recommended Officer Action:</strong> {anomaly.recommended_action}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
