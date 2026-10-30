import React, { useState, useEffect } from 'react';
import { 
  Network, 
  Users, 
  MapPin, 
  Building2, 
  AlertTriangle, 
  ShieldAlert, 
  RefreshCw, 
  Code2, 
  FileText, 
  FlaskConical, 
  GraduationCap,
  Layers,
  Info,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';
import ConflictingSubgraphNetwork from './ConflictingSubgraphNetwork';
import DemoDataBadge from './DemoDataBadge';
import StatusChip from './StatusChip';

// Labeled fallback mock data in case backend server is unreachable
const FALLBACK_GRAPH_SUMMARY = {
  total_nodes: 18,
  total_edges: 20,
  total_institutions: 3,
  total_faculty: 2,
  total_programmes: 2,
  total_documents: 3,
  total_labs: 2,
  total_buildings: 2,
  total_locations: 2,
  total_issuers: 2
};

const FALLBACK_ANOMALIES = [
  {
    check_id: 'DUAL_EMPLOYMENT_FACULTY',
    conflict_type: 'DUAL_EMPLOYMENT_GHOST_FACULTY',
    title: 'Indicator for Review: Concurrent Full-Time Appointment (Dr. R. K. Sharma)',
    severity: 'CRITICAL',
    indicator_type: 'INDICATOR_FOR_REVIEW',
    explanation: 'Indicator for review: Faculty member Dr. R. K. Sharma (Masked PAN Match AB****89C + Identical DOB 1975-08-12) is recorded as a Full-Time regular employee across multiple distinct institutions: Apex Institute of Technology & Science and Royal College of Engineering with overlapping tenure.',
    recommended_action: 'Indicator for review: Issue formal regulatory inquiry to both institutions requesting Form 16 statements, monthly salary disbursement logs, and physical biometric attendance.',
    conflicting_subgraph: {
      nodes: [
        { id: 'FAC_101', type: 'FACULTY', label: 'Dr. R. K. Sharma', pan_masked: 'AB****89C', aadhaar_masked: 'XXXX-XXXX-9021', designation: 'Professor & Head' },
        { id: 'INST_001', type: 'INSTITUTION', label: 'Apex Institute of Technology & Science', city: 'Bengaluru', aicte_id: '1-109283711' },
        { id: 'INST_002', type: 'INSTITUTION', label: 'Royal College of Engineering', city: 'Mysuru', aicte_id: '1-209384722' }
      ],
      edges: [
        { source: 'INST_001', target: 'FAC_101', relation: 'employs', employment_type: 'Full-Time', role: 'Professor' },
        { source: 'INST_002', target: 'FAC_101', relation: 'employs', employment_type: 'Full-Time', role: 'Professor' }
      ]
    }
  },
  {
    check_id: 'BUILT_UP_AREA_DENSITY_DEFICIT',
    conflict_type: 'AREA_DENSITY_DEFICIT',
    title: 'Indicator for Review: Built-Up Area Density Deficit (Apex Institute of Technology)',
    severity: 'CRITICAL',
    indicator_type: 'INDICATOR_FOR_REVIEW',
    explanation: 'Indicator for review: Total claimed instructional and administrative built-up area of 8,500 m² is insufficient for approved intake of 480 students across 4 concurrent batches (1,920 total enrolment), yielding 4.43 m²/student against the statutory minimum of 7.00 m²/student.',
    recommended_action: 'Indicator for review: Schedule spot verification by regional inspection committee to verify actual carpet area of instructional spaces and physical laboratory allocations.',
    conflicting_subgraph: {
      nodes: [
        { id: 'INST_001', type: 'INSTITUTION', label: 'Apex Institute of Technology', total_built_up_area_sqm: 8500, approved_intake: 480 },
        { id: 'BLD_001', type: 'BUILDING', label: 'Main Academic Block A', built_up_area_sqm: 4500 },
        { id: 'BLD_002', type: 'BUILDING', label: 'Workshop & Laboratory Block B', built_up_area_sqm: 4000 }
      ],
      edges: [
        { source: 'INST_001', target: 'BLD_001', relation: 'holds' },
        { source: 'INST_001', target: 'BLD_002', relation: 'holds' }
      ]
    }
  },
  {
    check_id: 'SHARED_DOCUMENT_REFERENCE_COLLISION',
    conflict_type: 'SHARED_DOCUMENT_REFERENCE',
    title: 'Indicator for Review: Cross-Institutional Reference Number Reuse (FIR/KA/99102)',
    severity: 'CRITICAL',
    indicator_type: 'INDICATOR_FOR_REVIEW',
    explanation: 'Indicator for review: Fire Safety NOC document reference number FIR/KA/99102 is claimed concurrently in regulatory filings by both Apex Institute of Technology and Royal College of Engineering.',
    recommended_action: 'Indicator for review: Query issuing Fire and Emergency Services Directorate database to authenticate original recipient institution of certificate FIR/KA/99102.',
    conflicting_subgraph: {
      nodes: [
        { id: 'DOC_102', type: 'DOCUMENT', label: 'Fire Safety NOC (FIR/KA/99102)', doc_number: 'FIR/KA/99102' },
        { id: 'INST_001', type: 'INSTITUTION', label: 'Apex Institute of Technology', city: 'Bengaluru' },
        { id: 'INST_002', type: 'INSTITUTION', label: 'Royal College of Engineering', city: 'Mysuru' },
        { id: 'ISS_001', type: 'ISSUER', label: 'Karnataka Fire & Emergency Services' }
      ],
      edges: [
        { source: 'INST_001', target: 'DOC_102', relation: 'holds' },
        { source: 'INST_002', target: 'DOC_102', relation: 'holds' },
        { source: 'DOC_102', target: 'ISS_001', relation: 'issued_by' }
      ]
    }
  }
];

export default function ImpossibilityGraph() {
  const [graphData, setGraphData] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDemoData, setIsDemoData] = useState(false);
  const [filterType, setFilterType] = useState('ALL');
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [activeTopologyTab, setActiveTopologyTab] = useState('SUBGRAPH'); // 'SUBGRAPH' | 'MACRO'
  const [showJsonMap, setShowJsonMap] = useState({});

  const fetchGraphAndAnomalies = async () => {
    setLoading(true);
    try {
      const [gData, aData] = await Promise.all([
        api.getKnowledgeGraph(),
        api.getImpossibilities()
      ]);

      if (gData && Array.isArray(aData)) {
        setGraphData(gData);
        setAnomalies(aData);
        setIsDemoData(false);
        if (aData.length > 0) {
          setSelectedAnomaly(aData[0]);
        }
      } else {
        throw new Error('Invalid graph data format received from API');
      }
    } catch (err) {
      console.warn('API fetch for graph/impossibilities failed, using labeled demo fallback:', err);
      setGraphData({ summary: FALLBACK_GRAPH_SUMMARY });
      setAnomalies(FALLBACK_ANOMALIES);
      setSelectedAnomaly(FALLBACK_ANOMALIES[0]);
      setIsDemoData(true);
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
    const t = (type || '').toUpperCase();
    switch (t) {
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
              {isDemoData && <DemoDataBadge message="Demo data (live graph fallback)" />}
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-text tracking-tight">
              Institution Twin: Multi-College Regulatory Radar
            </h1>
            <p className="text-xs text-muted mt-1 max-w-2xl">
              Constructs an inter-institutional digital twin knowledge graph of Institutions, Faculty, Programmes, Documents, Labs, Buildings, Locations, and Issuers to detect mathematically and physically impossible claims across regional colleges.
            </p>
          </div>
          <button
            onClick={fetchGraphAndAnomalies}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-surface border border-border hover:bg-surface-2 text-xs font-semibold text-text transition-colors shadow-xs shrink-0 disabled:opacity-60"
            type="button"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-run Conflict Queries</span>
          </button>
        </div>

        {/* Graph Metrics */}
        {graphData && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-border">
            <div className="bg-surface-2 rounded-xl p-3 border border-border shadow-xs">
              <div className="text-[11px] text-muted uppercase font-medium">Institutions</div>
              <div className="text-xl font-bold text-sky-700">{graphData.summary?.total_institutions || 0}</div>
            </div>
            <div className="bg-surface-2 rounded-xl p-3 border border-border shadow-xs">
              <div className="text-[11px] text-muted uppercase font-medium">Faculty Nodes</div>
              <div className="text-xl font-bold text-indigo-700">{graphData.summary?.total_faculty || 0}</div>
            </div>
            <div className="bg-surface-2 rounded-xl p-3 border border-border shadow-xs">
              <div className="text-[11px] text-muted uppercase font-medium">Documents & Labs</div>
              <div className="text-xl font-bold text-emerald-700">
                {(graphData.summary?.total_documents || 0) + (graphData.summary?.total_labs || 0)}
              </div>
            </div>
            <div className="bg-surface-2 rounded-xl p-3 border border-border shadow-xs">
              <div className="text-[11px] text-muted uppercase font-medium">Review Indicators</div>
              <div className="text-xl font-bold text-rose-600">{anomalies.length} Flagged</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-none">
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
                : 'bg-surface border-border text-muted hover:text-text hover:bg-surface-2'
            }`}
            type="button"
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Grid: Graph Visualizer & Anomaly Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Interactive Topology View */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          {/* Tab Switcher for Topology View */}
          <div className="flex items-center justify-between bg-surface border border-border rounded-xl p-1.5 shadow-2xs">
            <div className="flex space-x-1">
              <button
                onClick={() => setActiveTopologyTab('SUBGRAPH')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  activeTopologyTab === 'SUBGRAPH'
                    ? 'bg-rose-50 text-rose-800 border border-rose-200 shadow-2xs'
                    : 'text-muted hover:text-text hover:bg-surface-2'
                }`}
                type="button"
              >
                <Network className="w-3.5 h-3.5 text-rose-600" />
                <span>Conflicting Subgraph Topology</span>
              </button>

              <button
                onClick={() => setActiveTopologyTab('MACRO')}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  activeTopologyTab === 'MACRO'
                    ? 'bg-sky-50 text-sky-800 border border-sky-200 shadow-2xs'
                    : 'text-muted hover:text-text hover:bg-surface-2'
                }`}
                type="button"
              >
                <Layers className="w-3.5 h-3.5 text-sky-600" />
                <span>Macro Institutional Twin</span>
              </button>
            </div>

            {selectedAnomaly && (
              <span className="text-[11px] text-slate-500 font-mono hidden sm:inline px-2">
                Focused: <span className="text-slate-800 font-semibold">{selectedAnomaly.check_id || 'FINDING'}</span>
              </span>
            )}
          </div>

          {/* Interactive Topology Container */}
          {activeTopologyTab === 'SUBGRAPH' ? (
            <ConflictingSubgraphNetwork
              subgraph={selectedAnomaly?.conflicting_subgraph}
              activeFindingTitle={selectedAnomaly?.title}
            />
          ) : (
            <div className="bg-surface border border-border rounded-xl p-5 shadow-xs flex flex-col space-y-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-sky-600" />
                  <h3 className="text-sm font-semibold text-text">
                    Macro Multi-College Digital Twin Topology
                  </h3>
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
              <div className="relative bg-surface-2 border border-border rounded-xl p-4 min-h-[380px] flex items-center justify-center overflow-hidden">
                <svg className="w-full h-full max-h-[360px]" viewBox="0 0 600 360">
                  {/* Conflict Connection Lines */}
                  <line x1="160" y1="100" x2="300" y2="180" stroke="#be123c" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
                  <line x1="440" y1="100" x2="300" y2="180" stroke="#be123c" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
                  
                  <line x1="160" y1="100" x2="160" y2="280" stroke="#8A94A0" strokeWidth="1.5" />
                  <line x1="440" y1="100" x2="440" y2="280" stroke="#8A94A0" strokeWidth="1.5" />

                  {/* Edge Labels */}
                  <rect x="195" y="128" width="95" height="18" rx="4" fill="#FFFFFF" stroke="#D5D9DE" />
                  <text x="242" y="141" fill="#0F172A" fontSize="8" textAnchor="middle" fontWeight="bold">employs (Full-Time)</text>

                  <rect x="325" y="128" width="95" height="18" rx="4" fill="#FFFFFF" stroke="#D5D9DE" />
                  <text x="372" y="141" fill="#0F172A" fontSize="8" textAnchor="middle" fontWeight="bold">employs (Full-Time)</text>

                  {/* Node 1: Apex Institute */}
                  <g transform="translate(160, 100)" className="cursor-pointer">
                    <circle r="36" fill="#E0F2FE" stroke="#0284C7" strokeWidth="1.5" />
                    <Building2 x="-12" y="-20" className="w-6 h-6 text-[#075985]" />
                    <text y="8" fill="#075985" fontSize="9" fontWeight="bold" textAnchor="middle">Apex Tech</text>
                    <text y="20" fill="#64748B" fontSize="8" textAnchor="middle">Bengaluru</text>
                  </g>

                  {/* Node 2: Royal College */}
                  <g transform="translate(440, 100)" className="cursor-pointer">
                    <circle r="36" fill="#E0F2FE" stroke="#0284C7" strokeWidth="1.5" />
                    <Building2 x="-12" y="-20" className="w-6 h-6 text-[#075985]" />
                    <text y="8" fill="#075985" fontSize="9" fontWeight="bold" textAnchor="middle">Royal College</text>
                    <text y="20" fill="#64748B" fontSize="8" textAnchor="middle">Mysuru</text>
                  </g>

                  {/* Center Conflict Node: Faculty */}
                  <g transform="translate(300, 180)" className="cursor-pointer">
                    <circle r="32" fill="#FFE4E6" stroke="#E11D48" strokeWidth="2" className="animate-pulse" />
                    <Users x="-10" y="-16" className="w-5 h-5 text-[#9F1239]" />
                    <text y="6" fill="#9F1239" fontSize="8" fontWeight="bold" textAnchor="middle">Dr. R. K. Sharma</text>
                    <text y="16" fill="#64748B" fontSize="7" textAnchor="middle">AB****89C</text>
                  </g>

                  {/* Document Node */}
                  <g transform="translate(160, 280)" className="cursor-pointer">
                    <rect x="-35" y="-18" width="70" height="36" rx="6" fill="#FEF3C7" stroke="#D97706" strokeWidth="1" />
                    <text y="-2" fill="#92400E" fontSize="8" fontWeight="bold" textAnchor="middle">Fire Safety NOC</text>
                    <text y="10" fill="#92400E" fontSize="7" textAnchor="middle">FIR/KA/99102</text>
                  </g>

                  {/* Lab Node */}
                  <g transform="translate(440, 280)" className="cursor-pointer">
                    <rect x="-35" y="-18" width="70" height="36" rx="6" fill="#DCFCE7" stroke="#16A34A" strokeWidth="1" />
                    <text y="-2" fill="#166534" fontSize="8" fontWeight="bold" textAnchor="middle">Mech Workshop</text>
                    <text y="10" fill="#166534" fontSize="7" textAnchor="middle">Lathe, Milling, UTM</text>
                  </g>
                </svg>

                <div className="absolute bottom-3 left-3 bg-white/95 border border-slate-200 rounded-lg px-2.5 py-1 text-[10px] text-slate-500 shadow-xs">
                  Global Topological Projection • NetworkX MultiDiGraph (8 Node Types • 5 Edge Types)
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
                <span className="font-semibold text-slate-800">Macro Twin Overview: </span>
                Multi-college knowledge graph connects statutory entities across all affiliated institutions to identify inter-institutional collisions that are mathematically or legally irreconcilable.
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Review Indicator Dossiers */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text">
              Indicators for Review ({filteredAnomalies.length})
            </h3>
            <span className="text-xs text-rose-700 font-mono font-medium">Statutory review flags</span>
          </div>

          {loading ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 space-y-3">
              <RefreshCw className="w-6 h-6 animate-spin text-rose-600 mx-auto" />
              <p className="text-xs font-medium">Analyzing inter-institutional knowledge graph...</p>
            </div>
          ) : filteredAnomalies.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <h4 className="text-sm font-semibold text-slate-800">No Indicators in this Category</h4>
              <p className="text-xs text-slate-500">
                No active mathematical or statutory conflicts detected for the selected filter.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
              {filteredAnomalies.map((anomaly, idx) => {
                const isSelected = selectedAnomaly === anomaly;
                return (
                  <div 
                    key={idx}
                    onClick={() => {
                      setSelectedAnomaly(anomaly);
                      setActiveTopologyTab('SUBGRAPH');
                    }}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected 
                        ? 'bg-rose-50/90 border-rose-300 ring-2 ring-rose-200/50 shadow-xs' 
                        : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                        <span className="text-xs font-bold text-slate-900 leading-tight">
                          {anomaly.title}
                        </span>
                      </div>
                      <StatusChip status="Mismatch Detected" size="sm" />
                    </div>

                    {/* AI Review Banner strictly stating "Indicator for review" */}
                    <div className="mb-2 inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100/80 text-rose-800 border border-rose-200">
                      <ShieldAlert className="w-3 h-3 text-rose-600" />
                      <span>Indicator for review</span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed mb-3">
                      {anomaly.explanation}
                    </p>

                    {/* Conflicting Subgraph Entities Preview */}
                    {anomaly.conflicting_subgraph && (
                      <div className="mb-3 bg-white p-2.5 rounded-lg border border-slate-200/90 space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                          <span className="font-semibold text-slate-700">Conflicting Subgraph Entities:</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleJson(idx);
                            }}
                            className="flex items-center space-x-1 text-sky-700 hover:text-sky-900 font-semibold"
                            type="button"
                          >
                            <Code2 className="w-3 h-3" />
                            <span>{showJsonMap[idx] ? 'Hide JSON' : 'View Subgraph JSON'}</span>
                          </button>
                        </div>

                        <div className="flex flex-wrap gap-1">
                          {anomaly.conflicting_subgraph.nodes?.map((node, nIdx) => (
                            <span 
                              key={nIdx} 
                              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-700"
                            >
                              {getNodeIcon(node.type)}
                              <span className="font-medium">{node.label || node.name || node.id}</span>
                              <span className="text-[9px] text-slate-400">({node.type})</span>
                            </span>
                          ))}
                        </div>

                        {showJsonMap[idx] && (
                          <pre className="mt-2 p-2 rounded bg-slate-900 text-slate-100 font-mono text-[10px] overflow-x-auto max-h-40">
                            {JSON.stringify(anomaly.conflicting_subgraph, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}

                    {/* Officer Action recommendation */}
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-700 mb-2">
                      <strong className="text-rose-700">Recommended Officer Action:</strong> {anomaly.recommended_action}
                    </div>

                    {/* Focus In Graph Button */}
                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAnomaly(anomaly);
                          setActiveTopologyTab('SUBGRAPH');
                        }}
                        className={`inline-flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg border transition-colors ${
                          isSelected 
                            ? 'bg-rose-600 text-white border-rose-600 shadow-2xs' 
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                        type="button"
                      >
                        <Network className="w-3.5 h-3.5" />
                        <span>{isSelected ? 'Viewing in Network' : 'Focus Subgraph Topology'}</span>
                      </button>

                      <span className="text-[10px] text-slate-400 font-mono">
                        {anomaly.conflicting_subgraph?.nodes?.length || 0} nodes involved
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
