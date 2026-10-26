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
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function ImpossibilityGraph() {
  const [graphData, setGraphData] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('ALL');
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);

  const fetchGraphAndAnomalies = async () => {
    setLoading(true);
    try {
      const [gData, aData] = await Promise.all([
        api.getKnowledgeGraph(),
        api.getImpossibilities()
      ]);
      setGraphData(gData);
      setAnomalies(aData);
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

  const filteredAnomalies = filterType === 'ALL' 
    ? anomalies 
    : anomalies.filter(a => a.conflict_type === filterType);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-rose-50 via-white to-slate-50 border border-rose-200/70 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-700 uppercase tracking-widest mb-1">
              <span>NetworkX Graph Analytics</span>
              <span>•</span>
              <span>Cross-Institution Integrity</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Impossibility Engine: Multi-College Conflict Radar
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Constructs an inter-institutional knowledge graph of colleges, faculty, and land parcels to detect mathematically and physically impossible claims across regional institutions.
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
              <div className="text-[11px] text-slate-500 uppercase font-medium">Mapped Colleges</div>
              <div className="text-xl font-bold text-sky-700">{graphData.summary.total_institutions}</div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Faculty Nodes</div>
              <div className="text-xl font-bold text-indigo-700">{graphData.summary.total_faculty}</div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Land Parcels</div>
              <div className="text-xl font-bold text-purple-700">{graphData.summary.total_parcels}</div>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs">
              <div className="text-[11px] text-slate-500 uppercase font-medium">Impossibility Flags</div>
              <div className="text-xl font-bold text-rose-600">{anomalies.length} Critical</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-1">
        {[
          { id: 'ALL', label: 'All Impossibilities' },
          { id: 'DUAL_EMPLOYMENT_GHOST_FACULTY', label: 'Ghost Faculty (Dual Full-Time)' },
          { id: 'SHARED_LAND_PARCEL_COLLISION', label: 'Land Parcel Collisions' },
          { id: 'PHYSICAL_DENSITY_IMPOSSIBILITY', label: 'Physical Density Violations' }
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
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Network className="w-4 h-4 text-sky-600" />
              <h3 className="text-sm font-semibold text-slate-900">Cross-Institutional Relational Map</h3>
            </div>
            <div className="flex items-center space-x-3 text-[11px]">
              <span className="flex items-center space-x-1.5 text-sky-700">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-600 inline-block" />
                <span>Colleges</span>
              </span>
              <span className="flex items-center space-x-1.5 text-rose-700">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block" />
                <span>Ghost Faculty</span>
              </span>
              <span className="flex items-center space-x-1.5 text-purple-700">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-600 inline-block" />
                <span>Land Deed</span>
              </span>
            </div>
          </div>

          {/* Interactive SVG Graph Rendering */}
          <div className="relative bg-slate-50 border border-slate-200/80 rounded-xl p-4 h-96 flex items-center justify-center overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 600 360">
              {/* Conflict Connection Lines (Dual Employment) */}
              <line x1="160" y1="100" x2="300" y2="180" stroke="#e11d48" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
              <line x1="440" y1="100" x2="300" y2="180" stroke="#e11d48" strokeWidth="2.5" strokeDasharray="5,5" className="animate-pulse" />
              
              {/* Conflict Connection Lines (Land Sharing) */}
              <line x1="160" y1="100" x2="220" y2="280" stroke="#9333ea" strokeWidth="2" strokeDasharray="4,4" />
              <line x1="160" y1="280" x2="220" y2="280" stroke="#9333ea" strokeWidth="2" strokeDasharray="4,4" />

              {/* Edge Label: Dual Full Time */}
              <rect x="200" y="130" width="85" height="18" rx="4" fill="#ffffff" stroke="#cbd5e1" />
              <text x="242" y="143" fill="#334155" fontSize="8" textAnchor="middle" fontWeight="bold">Full-Time (CSE)</text>

              <rect x="330" y="130" width="85" height="18" rx="4" fill="#ffffff" stroke="#cbd5e1" />
              <text x="372" y="143" fill="#334155" fontSize="8" textAnchor="middle" fontWeight="bold">Full-Time (CSE)</text>

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

              {/* Node 3: National Academy */}
              <g transform="translate(160, 280)" className="cursor-pointer">
                <circle r="32" fill="#ffffff" stroke="#0284c7" strokeWidth="2" />
                <Building2 x="-10" y="-18" className="w-5 h-5 text-sky-600" />
                <text y="8" fill="#0f172a" fontSize="8" fontWeight="bold" textAnchor="middle">National Acad.</text>
              </g>

              {/* Center Conflict Node: Dr. R. K. Sharma (Ghost Faculty) */}
              <g transform="translate(300, 180)" className="cursor-pointer">
                <circle r="32" fill="#ffe4e6" stroke="#e11d48" strokeWidth="3" className="animate-pulse" />
                <Users x="-10" y="-16" className="w-5 h-5 text-rose-700" />
                <text y="6" fill="#881337" fontSize="8" fontWeight="bold" textAnchor="middle">Dr. R. K. Sharma</text>
                <text y="16" fill="#be123c" fontSize="7" textAnchor="middle">AB****89C</text>
              </g>

              {/* Land Conflict Node: Survey 42/1 */}
              <g transform="translate(220, 280)" className="cursor-pointer">
                <rect x="-28" y="-20" width="56" height="40" rx="8" fill="#f3e8ff" stroke="#9333ea" strokeWidth="2" />
                <text y="-4" fill="#581c87" fontSize="8" fontWeight="bold" textAnchor="middle">Sy. 42/1</text>
                <text y="8" fill="#7e22ce" fontSize="7" textAnchor="middle">5.5 Acres</text>
              </g>
            </svg>

            <div className="absolute bottom-3 left-3 bg-white/95 border border-slate-200 rounded-lg px-2.5 py-1 text-[10px] text-slate-500 shadow-xs">
              Interactive topological projection • NetworkX MultiDiGraph
            </div>
          </div>
        </div>

        {/* Right Column: Anomaly Dossiers */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Detected Impossibilities ({filteredAnomalies.length})</h3>
            <span className="text-xs text-rose-700 font-mono font-medium">Statutory review flags</span>
          </div>

          <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
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
                    {anomaly.severity}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  {anomaly.explanation}
                </p>

                {/* Evidence Chain Pill */}
                {anomaly.pan_masked && (
                  <div className="flex items-center space-x-3 text-[11px] text-slate-600 font-mono mb-3 bg-slate-50 p-2 rounded-lg border border-slate-200">
                    <span>PAN: <strong className="text-slate-800">{anomaly.pan_masked}</strong></span>
                    <span>•</span>
                    <span>Aadhaar: <strong className="text-slate-800">{anomaly.aadhaar_masked}</strong></span>
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
