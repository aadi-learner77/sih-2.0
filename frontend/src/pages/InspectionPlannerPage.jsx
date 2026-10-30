import React, { useState, useEffect } from 'react';
import { 
  Compass, 
  MapPin, 
  Building2, 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Calendar, 
  Users, 
  Clock, 
  FileText, 
  Route, 
  ChevronRight, 
  ChevronDown, 
  RefreshCw, 
  Filter, 
  SlidersHorizontal,
  Navigation,
  Check
} from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';
import { api } from '../services/api';

const MOCK_PLANNER_DATA = {
  total_flagged_institutions: 6,
  total_states: 2,
  total_clusters: 3,
  state_clusters: [
    {
      state: 'Karnataka',
      total_institutions: 5,
      districts_count: 2,
      districts: [
        {
          district: 'Bengaluru',
          institution_count: 4,
          highest_priority: 100.0,
          institutions: [
            {
              sequence_in_district: 1,
              institution_id: 1,
              aicte_id: '1-109283711',
              name: 'Apex Institute of Technology & Science',
              state: 'Karnataka',
              district: 'Bengaluru',
              city: 'Bengaluru',
              category: 'Engineering & Technology',
              approved_intake: 300,
              application_no: 'APP-2025-09812',
              status: 'INSPECTION_RECOMMENDED',
              readiness_score: 54.0,
              priority_score: 100.0,
              risk_tier: 'CRITICAL_URGENCY',
              critical_findings_count: 2,
              flagged_issues: [
                'Concurrent full-time tenure (Dr. R. K. Sharma)',
                'Building plan footprint deficit (-22%)',
                'Scrutiny Officer Inspection Mandate'
              ],
              recommended_inspection_type: 'SURPRISE_PHYSICAL_INSPECTION',
              geo_coordinates: { lat: 13.08, lng: 77.58 },
              address: 'Campus Sector 4, Outer Ring Road, Bengaluru'
            },
            {
              sequence_in_district: 2,
              institution_id: 2,
              aicte_id: '1-17d56e87',
              name: 'Incomplete Tech Institute 17d56e87',
              state: 'Karnataka',
              district: 'Bengaluru',
              city: 'Bengaluru',
              category: 'Engineering & Technology',
              approved_intake: 240,
              application_no: 'APP-2025-0002',
              status: 'UNDER_SCRUTINY',
              readiness_score: 48.0,
              priority_score: 100.0,
              risk_tier: 'CRITICAL_URGENCY',
              critical_findings_count: 3,
              flagged_issues: [
                'Expired Fire Safety NOC',
                'Missing Land Conversion Certificate',
                'Sub-Threshold Faculty Cadre Ratio'
              ],
              recommended_inspection_type: 'SURPRISE_PHYSICAL_INSPECTION',
              geo_coordinates: { lat: 12.98, lng: 77.52 },
              address: 'Industrial Area Phase 2, Peenya, Bengaluru'
            },
            {
              sequence_in_district: 3,
              institution_id: 3,
              aicte_id: '1-3a7cc8c5',
              name: 'Silicon Valley College of Polytechnic',
              state: 'Karnataka',
              district: 'Bengaluru',
              city: 'Bengaluru',
              category: 'Applied Arts & Crafts',
              approved_intake: 180,
              application_no: 'APP-2025-0003',
              status: 'SUBMITTED',
              readiness_score: 68.5,
              priority_score: 45.0,
              risk_tier: 'MODERATE_REVIEW',
              critical_findings_count: 0,
              flagged_issues: [
                'Pending University Affiliation Order',
                'Computer Center Carpet Area Minor Shortfall'
              ],
              recommended_inspection_type: 'HYBRID_360_AUDIT',
              geo_coordinates: { lat: 12.93, lng: 77.62 },
              address: 'Koramangala 4th Block, Bengaluru'
            },
            {
              sequence_in_district: 4,
              institution_id: 4,
              aicte_id: '1-84b52ebc',
              name: 'Bengaluru Rural Engineering Academy',
              state: 'Karnataka',
              district: 'Bengaluru',
              city: 'Bengaluru',
              category: 'Engineering & Technology',
              approved_intake: 360,
              application_no: 'APP-2025-0004',
              status: 'SUBMITTED',
              readiness_score: 72.0,
              priority_score: 35.0,
              risk_tier: 'MODERATE_REVIEW',
              critical_findings_count: 0,
              flagged_issues: ['Periodic Random Sample Inspection'],
              recommended_inspection_type: 'VIRTUAL_INFRASTRUCTURE_VERIFICATION',
              geo_coordinates: { lat: 13.15, lng: 77.60 },
              address: 'Yelahanka Satellite Town, Bengaluru'
            }
          ]
        },
        {
          district: 'Mysuru',
          institution_count: 1,
          highest_priority: 58.3,
          institutions: [
            {
              sequence_in_district: 1,
              institution_id: 5,
              aicte_id: '1-309485733',
              name: 'Royal College of Engineering',
              state: 'Karnataka',
              district: 'Mysuru',
              city: 'Mysuru',
              category: 'Engineering & Technology',
              approved_intake: 300,
              application_no: 'APP-2025-0005',
              status: 'INSPECTION_RECOMMENDED',
              readiness_score: 62.0,
              priority_score: 58.3,
              risk_tier: 'HIGH_PRIORITY',
              critical_findings_count: 1,
              flagged_issues: [
                'Cadre Exclusivity Conflict (Cross-Employment)',
                'Fire Safety Certificate Lapsed'
              ],
              recommended_inspection_type: 'SURPRISE_PHYSICAL_INSPECTION',
              geo_coordinates: { lat: 12.30, lng: 76.65 },
              address: 'Hunsur Main Road, Mysuru'
            }
          ]
        }
      ]
    },
    {
      state: 'Delhi',
      total_institutions: 1,
      districts_count: 1,
      districts: [
        {
          district: 'New Delhi',
          institution_count: 1,
          highest_priority: 100.0,
          institutions: [
            {
              sequence_in_district: 1,
              institution_id: 6,
              aicte_id: '1-99882211',
              name: 'Pramaan Verification Testing Institute',
              state: 'Delhi',
              district: 'New Delhi',
              city: 'New Delhi',
              category: 'Engineering & Technology',
              approved_intake: 420,
              application_no: 'APP-2025-0006',
              status: 'UNDER_SCRUTINY',
              readiness_score: 42.0,
              priority_score: 100.0,
              risk_tier: 'CRITICAL_URGENCY',
              critical_findings_count: 2,
              flagged_issues: [
                'Unrectified Non-Judicial Stamp Paper Discrepancy Indicator',
                'Architectural Built-Up Deficit'
              ],
              recommended_inspection_type: 'SURPRISE_PHYSICAL_INSPECTION',
              geo_coordinates: { lat: 28.61, lng: 77.20 },
              address: 'Barakhamba Road, Connaught Place, New Delhi'
            }
          ]
        }
      ]
    }
  ]
};

export default function InspectionPlannerPage() {
  const [plannerData, setPlannerData] = useState(MOCK_PLANNER_DATA);
  const [isDemoData, setIsDemoData] = useState(true);
  const [loading, setLoading] = useState(false);
  const [selectedState, setSelectedState] = useState('ALL');
  const [minPriority, setMinPriority] = useState(0);
  const [expandedDistricts, setExpandedDistricts] = useState({});
  const [scheduledOrders, setScheduledOrders] = useState({});

  const loadPlanner = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedState !== 'ALL') params.state = selectedState;
      if (minPriority > 0) params.min_priority = minPriority;
      
      const res = await api.getInspectionPlanner(params);
      if (res && res.state_clusters && res.state_clusters.length > 0) {
        setPlannerData(res);
        setIsDemoData(false);
      } else {
        setPlannerData(MOCK_PLANNER_DATA);
        setIsDemoData(true);
      }
    } catch (err) {
      console.warn('Backend inspection planner offline, using mock data:', err.message);
      setPlannerData(MOCK_PLANNER_DATA);
      setIsDemoData(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlanner();
  }, [selectedState, minPriority]);

  const toggleDistrict = (key) => {
    setExpandedDistricts(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleScheduleOrder = (instId) => {
    setScheduledOrders(prev => ({
      ...prev,
      [instId]: true
    }));
  };

  const statesList = ['ALL', 'Karnataka', 'Delhi', 'Maharashtra', 'Telangana'];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* 1. Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sky-400 text-xs font-bold uppercase tracking-wider">
              <Compass className="w-4 h-4" />
              <span>AICTE Scrutiny & Vigilance Bureau</span>
              {isDemoData && <DemoDataBadge reason="Fallback Mock Data" />}
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Surprise Inspection Planner
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Geographical clustering of flagged institutions by State and District.
              Automated sequencing orders inspection itineraries to minimize officer travel time while prioritizing high-urgency regulatory discrepancies.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={loadPlanner}
              disabled={loading}
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-white font-bold text-xs flex items-center space-x-2 transition-all cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Clusters</span>
            </button>
          </div>
        </div>

        {/* Decorative Grid Accent */}
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-sky-500/10 to-transparent pointer-events-none" />
      </div>

      {/* 2. Key Metrics Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Flagged Institutions</span>
            <Building2 className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {plannerData.total_flagged_institutions || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Across {plannerData.total_states || 0} States</div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>District Clusters</span>
            <MapPin className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            {plannerData.total_clusters || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Optimal Itinerary Routes</div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Critical Urgency</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-black text-rose-600 mt-2">
            3
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Mandatory Physical Audits</div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>AI Sequencing Engine</span>
            <Route className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 mt-2">
            Active
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Prioritized by Risk & Proximity</div>
        </div>
      </div>

      {/* 3. Filter Controls Deck */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-sky-600" />
            <span>State Cluster:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {statesList.map(st => (
              <button
                key={st}
                onClick={() => setSelectedState(st)}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  selectedState === st
                    ? 'bg-slate-900 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <span className="font-bold text-slate-600">Min Risk Priority:</span>
          <select
            value={minPriority}
            onChange={(e) => setMinPriority(Number(e.target.value))}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-bold text-slate-800"
          >
            <option value="0">All Priorities</option>
            <option value="40">Moderate+ (≥ 40)</option>
            <option value="60">High Priority (≥ 60)</option>
            <option value="80">Critical Only (≥ 80)</option>
          </select>
        </div>
      </div>

      {/* 4. State & District Clusters Accordions */}
      <div className="space-y-6">
        {(plannerData.state_clusters || []).map((stateCluster, stIdx) => (
          <div key={stateCluster.state || stIdx} className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-sky-50 text-sky-700 border border-sky-200 flex items-center justify-center font-black text-sm">
                  {stateCluster.state.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <h2 className="text-lg font-black text-slate-900">{stateCluster.state} Region</h2>
                  <p className="text-xs text-slate-500">
                    {stateCluster.total_institutions} Flagged Institutions across {stateCluster.districts_count} District Clusters
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono font-bold bg-slate-100 text-slate-700 px-3 py-1 rounded-full border border-slate-200">
                {stateCluster.total_institutions} Inspections Pending
              </span>
            </div>

            {/* Districts in State */}
            <div className="space-y-4">
              {(stateCluster.districts || []).map((dist, dIdx) => {
                const distKey = `${stateCluster.state}-${dist.district}`;
                const isExpanded = expandedDistricts[distKey] !== false; // expanded by default

                return (
                  <div key={dist.district || dIdx} className="border border-slate-200 rounded-2xl overflow-hidden shadow-2xs">
                    {/* District Header Bar */}
                    <div 
                      onClick={() => toggleDistrict(distKey)}
                      className="bg-slate-50/80 hover:bg-slate-100/80 p-4 flex items-center justify-between cursor-pointer transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <MapPin className="w-4 h-4 text-sky-600" />
                        <span className="font-bold text-sm text-slate-900">{dist.district} Cluster</span>
                        <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200">
                          {dist.institution_count} Stops in Route
                        </span>
                      </div>

                      <div className="flex items-center space-x-3 text-xs text-slate-500">
                        <span>Highest Urgency: <strong>{dist.highest_priority}/100</strong></span>
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </div>
                    </div>

                    {/* Institutions Itinerary Sequence */}
                    {isExpanded && (
                      <div className="p-4 bg-white divide-y divide-slate-100">
                        {(dist.institutions || []).map((inst) => {
                          const isCritical = inst.risk_tier === 'CRITICAL_URGENCY';
                          const isHigh = inst.risk_tier === 'HIGH_PRIORITY';
                          const isOrdered = scheduledOrders[inst.institution_id];

                          return (
                            <div key={inst.institution_id} className="py-4 first:pt-1 last:pb-1 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                              {/* Left: Sequence badge & details */}
                              <div className="flex items-start space-x-3.5">
                                <div className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center font-black text-xs shadow-2xs border ${
                                  inst.sequence_in_district === 1 
                                    ? 'bg-rose-600 text-white border-rose-700 ring-2 ring-rose-500/20' 
                                    : 'bg-slate-900 text-white border-slate-800'
                                }`}>
                                  #{inst.sequence_in_district}
                                </div>

                                <div className="space-y-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <h3 className="font-bold text-sm text-slate-900">{inst.name}</h3>
                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                                      AICTE: {inst.aicte_id}
                                    </span>
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                                      isCritical ? 'bg-rose-50 text-rose-800 border-rose-300' :
                                      isHigh ? 'bg-amber-50 text-amber-800 border-amber-300' :
                                      'bg-slate-100 text-slate-800 border-slate-300'
                                    }`}>
                                      {inst.risk_tier}
                                    </span>
                                  </div>

                                  <div className="text-xs text-slate-500 flex flex-wrap items-center gap-2">
                                    <span>{inst.category}</span>
                                    <span>•</span>
                                    <span>Intake: {inst.approved_intake}</span>
                                    <span>•</span>
                                    <span className="font-mono text-sky-700">{inst.application_no}</span>
                                    <span>•</span>
                                    <span className="text-slate-400">{inst.address}</span>
                                  </div>

                                  {/* Flagged issues */}
                                  <div className="pt-1 flex flex-wrap gap-1.5">
                                    {(inst.flagged_issues || []).map((iss, iIdx) => (
                                      <span key={iIdx} className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200 flex items-center space-x-1">
                                        <AlertTriangle className="w-3 h-3 text-rose-600 shrink-0" />
                                        <span>{iss}</span>
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              {/* Right: Scores & Actions */}
                              <div className="flex flex-wrap items-center gap-4 lg:self-center shrink-0">
                                <div className="text-right">
                                  <div className="text-xs font-bold text-slate-700">Urgency Score</div>
                                  <div className={`text-base font-black ${
                                    inst.priority_score >= 80 ? 'text-rose-600' :
                                    inst.priority_score >= 50 ? 'text-amber-600' : 'text-slate-700'
                                  }`}>
                                    {inst.priority_score}/100
                                  </div>
                                </div>

                                <div className="text-right border-l border-slate-200 pl-3">
                                  <div className="text-[10px] font-bold text-slate-500 uppercase">Recommended Mode</div>
                                  <div className="text-xs font-bold text-slate-800 font-mono">
                                    {inst.recommended_inspection_type.replace(/_/g, ' ')}
                                  </div>
                                </div>

                                <button
                                  id={`btn-schedule-inspection-${inst.institution_id}`}
                                  onClick={() => handleScheduleOrder(inst.institution_id)}
                                  disabled={isOrdered}
                                  className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-2xs flex items-center space-x-1.5 cursor-pointer ${
                                    isOrdered 
                                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 cursor-default'
                                      : 'bg-slate-900 hover:bg-slate-800 text-white'
                                  }`}
                                >
                                  {isOrdered ? (
                                    <>
                                      <Check className="w-3.5 h-3.5 text-emerald-700" />
                                      <span>Order Dispatched</span>
                                    </>
                                  ) : (
                                    <>
                                      <Navigation className="w-3.5 h-3.5" />
                                      <span>Dispatch Squad Order</span>
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
