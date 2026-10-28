import React, { useState, useEffect } from 'react';
import { 
  Sun, 
  Satellite, 
  Compass, 
  Building2, 
  AlertTriangle, 
  RefreshCw, 
  Info, 
  ShieldCheck 
} from 'lucide-react';
import DemoDataBadge from './DemoDataBadge';
import { api } from '../services/api';

const SUN_SHADOW_PRESETS = [
  {
    id: 'outdoor_sunlit_quad',
    name: 'Outdoor Sunlit Quadrangle (Consistent)',
    scenario: 'Outdoor Campus',
    latitude: 18.5295,
    longitude: 73.8565,
    timestamp: '2026-05-15T11:30:00Z',
    camera_heading: 21.0,
    photo_category: 'campus_exterior',
    is_indoor: false,
    file_path: 'generated_data/forensic_samples/gt_clean_authentic_scan.jpg',
    desc: 'Outdoor campus quadrangle with clear solar shadow projection coherent with azimuth.'
  },
  {
    id: 'indoor_computer_lab',
    name: 'Computer Lab / Electronics (Indoor)',
    scenario: 'Indoor Laboratory',
    latitude: 18.5295,
    longitude: 73.8565,
    timestamp: '2026-05-15T14:30:00Z',
    camera_heading: null,
    photo_category: 'computer_lab',
    is_indoor: true,
    file_path: 'generated_data/forensic_samples/gt_clean_authentic_affidavit.pdf',
    desc: 'Indoor laboratory with fluorescent lighting; solar shadow plausibility automatically skipped.'
  },
  {
    id: 'suspect_shadow_direction',
    name: 'Suspicious Shadow Discrepancy',
    scenario: 'Outdoor Inconsistent',
    latitude: 28.5448,
    longitude: 77.1556,
    timestamp: '2026-06-21T09:00:00Z',
    camera_heading: 180.0,
    photo_category: 'campus_facade',
    is_indoor: false,
    file_path: 'generated_data/forensic_samples/gt_ela_tampered.jpg',
    desc: 'Shadow angle deviates by 78° from expected astronomical sun azimuth for claimed time.'
  }
];

const BUILT_UP_PRESETS = [
  {
    id: 'coep_pune',
    name: 'College of Engineering Pune (COEP)',
    institution_id: 'INST_001',
    latitude: 18.5295,
    longitude: 73.8565,
    claimed_built_up_area: 8500.0,
    radius_meters: 350.0,
    tolerance_pct: 25.0,
    desc: 'Historic engineering campus with 5 detected Open Buildings / OSM building polygons.'
  },
  {
    id: 'vjti_mumbai',
    name: 'VJTI Matunga Campus (Mumbai)',
    institution_id: 'INST_002',
    latitude: 19.0222,
    longitude: 72.8558,
    claimed_built_up_area: 6200.0,
    radius_meters: 350.0,
    tolerance_pct: 25.0,
    desc: 'Dense urban engineering campus with multiple instructional wings and quadrangle.'
  },
  {
    id: 'bms_bangalore',
    name: 'BMS College of Engineering (Bengaluru)',
    institution_id: 'INST_003',
    latitude: 12.9416,
    longitude: 77.5655,
    claimed_built_up_area: 5800.0,
    radius_meters: 350.0,
    tolerance_pct: 25.0,
    desc: 'Multi-block technical institution with academic, research, and sports complexes.'
  },
  {
    id: 'rural_deficit_test',
    name: 'Rural Technical Site (Deficit Sample)',
    institution_id: 'TEST_DEFICIT',
    latitude: 26.8466,
    longitude: 80.9462,
    claimed_built_up_area: 12000.0,
    radius_meters: 350.0,
    tolerance_pct: 25.0,
    desc: 'Substantial discrepancy between declared 12,000 m² and minimal satellite footprint.'
  }
];

export default function ProofOfRealityView() {
  // Sun-Shadow state
  const [selectedSunPreset, setSelectedSunPreset] = useState(SUN_SHADOW_PRESETS[0]);
  const [sunShadowResult, setSunShadowResult] = useState(null);
  const [sunShadowLoading, setSunShadowLoading] = useState(false);
  const [sunShadowDemo, setSunShadowDemo] = useState(false);

  // Satellite Built-Up Area state
  const [selectedBuiltUpPreset, setSelectedBuiltUpPreset] = useState(BUILT_UP_PRESETS[0]);
  const [builtUpResult, setBuiltUpResult] = useState(null);
  const [builtUpLoading, setBuiltUpLoading] = useState(false);
  const [builtUpDemo, setBuiltUpDemo] = useState(false);

  // Custom coordinate inputs
  const [customLat, setCustomLat] = useState(BUILT_UP_PRESETS[0].latitude);
  const [customLon, setCustomLon] = useState(BUILT_UP_PRESETS[0].longitude);
  const [customClaimedArea, setCustomClaimedArea] = useState(BUILT_UP_PRESETS[0].claimed_built_up_area);
  const [customTolerance, setCustomTolerance] = useState(25);

  // Evaluate Sun-Shadow
  const runSunShadowCheck = async (preset = selectedSunPreset) => {
    setSunShadowLoading(true);
    try {
      const formData = new FormData();
      formData.append('file_path', preset.file_path);
      formData.append('latitude', preset.latitude.toString());
      formData.append('longitude', preset.longitude.toString());
      formData.append('timestamp', preset.timestamp);
      if (preset.camera_heading !== null) formData.append('camera_heading', preset.camera_heading.toString());
      formData.append('photo_category', preset.photo_category);
      if (preset.is_indoor !== null) formData.append('is_indoor', preset.is_indoor ? 'true' : 'false');

      const res = await api.checkSunShadowPlausibility(formData);
      setSunShadowResult(res);
      setSunShadowDemo(false);
    } catch (err) {
      console.warn('Sun-Shadow API fallback:', err);
      // Fallback
      if (preset.is_indoor) {
        setSunShadowResult({
          status: 'SKIPPED_INDOOR',
          plausibility_score: 1.0,
          claimed_gps: { latitude: preset.latitude, longitude: preset.longitude },
          claimed_timestamp: preset.timestamp,
          scene_classification: {
            is_indoor: true,
            scene_type: 'indoor_enclosed',
            reason: 'Indoor environment detected (fluorescent illumination spectrum). Sun-shadow verification skipped.'
          },
          advisory_indicator: 'SKIPPED: Indoor photo, solar check not applicable.',
          human_readable_summary: 'Indicator for review: Indoor photo detected. Astronomical sun-shadow verification is advisory and is automatically skipped for interior classrooms, workshops, and computer laboratories.',
          caveat: 'Advisory Indicator: Sun-shadow and satellite checks are advisory and are skipped for indoor photos.'
        });
      } else {
        setSunShadowResult({
          status: preset.id === 'suspect_shadow_direction' ? 'FLAGGED_DISCREPANCY' : 'PLAUSIBLE',
          plausibility_score: preset.id === 'suspect_shadow_direction' ? 0.22 : 0.88,
          angular_discrepancy_deg: preset.id === 'suspect_shadow_direction' ? 78.4 : 6.2,
          claimed_gps: { latitude: preset.latitude, longitude: preset.longitude },
          claimed_timestamp: preset.timestamp,
          sun_position: {
            azimuth_deg: 285.4,
            elevation_deg: 21.9,
            expected_shadow_azimuth_deg: 105.4
          },
          scene_classification: {
            is_indoor: false,
            scene_type: 'outdoor_sunlit',
            reason: 'Outdoor natural direct solar illumination detected.'
          },
          estimated_shadow: {
            dominant_image_angle_deg: 84.4,
            directional_coherence: 0.23
          },
          advisory_indicator: preset.id === 'suspect_shadow_direction'
            ? 'Indicator for review: Significant shadow angle discrepancy relative to claimed solar position.'
            : 'PLAUSIBLE: Shadows physically coherent with solar position.',
          human_readable_summary: preset.id === 'suspect_shadow_direction'
            ? 'Indicator for review: Claimed time/GPS indicates sun at azimuth 285.4°, but physical shadows align with 183.8° (discrepancy: 78.4°). Committee inquiry recommended.'
            : 'Physical shadow patterns in the infrastructure photograph align with pvlib astronomical solar position for the declared GPS coordinates.',
          caveat: 'Advisory Indicator: Sun-shadow and satellite checks are advisory and are skipped for indoor photos.'
        });
      }
      setSunShadowDemo(true);
    } finally {
      setSunShadowLoading(false);
    }
  };

  // Evaluate Built-Up Area
  const runBuiltUpCheck = async (lat = customLat, lon = customLon, claimed = customClaimedArea, tol = customTolerance) => {
    setBuiltUpLoading(true);
    try {
      const formData = new FormData();
      formData.append('latitude', lat.toString());
      formData.append('longitude', lon.toString());
      formData.append('claimed_built_up_area', claimed.toString());
      formData.append('radius_meters', '350.0');
      formData.append('tolerance_pct', tol.toString());

      const res = await api.checkBuiltUpPlausibility(formData);
      setBuiltUpResult(res);
      setBuiltUpDemo(false);
    } catch (err) {
      console.warn('Built-up area API fallback:', err);
      // Fallback
      const measured = lat === 18.5295 ? 5980.0 : (lat === 26.8466 ? 320.0 : 5400.0);
      const diff = measured - claimed;
      const diffPct = (diff / claimed) * 100;
      const lower = claimed * (1 - tol / 100);
      const isDeficit = measured < lower;

      setBuiltUpResult({
        status: isDeficit ? 'FOOTPRINT_SIGNIFICANTLY_BELOW_CLAIM' : 'WITHIN_TOLERANCE',
        is_within_tolerance: !isDeficit,
        review_recommended: isDeficit,
        advisory_flag: isDeficit ? 'FOOTPRINT_DEFICIT_FLAGGED_FOR_REVIEW' : 'VERIFIED_WITHIN_BAND',
        advisory_summary: isDeficit
          ? `Indicator for review: Measured building footprint of ${measured.toLocaleString()} m² is below the lower tolerance threshold (${lower.toLocaleString()} m²) of claimed built-up area (${claimed.toLocaleString()} m²). Discrepancy: ${diff.toLocaleString()} m² (${diffPct.toFixed(1)}%). Scrutiny committee to cross-examine approved master building plan and sanctioned floor count.`
          : `Measured building footprint of ${measured.toLocaleString()} m² matches declared area within ±${tol}% tolerance band.`,
        numbers_used: {
          claimed_built_up_area_sqm: claimed,
          measured_footprint_sqm: measured,
          discrepancy_sqm: diff,
          discrepancy_pct: diffPct,
          tolerance_lower_bound_sqm: lower,
          tolerance_upper_bound_sqm: claimed * (1 + tol / 100),
          tolerance_percentage: tol,
          building_count: measured > 5000 ? 5 : 1,
          search_radius_meters: 350.0,
          estimated_gross_built_up_sqm: measured * 2.5
        },
        buildings: [
          { id: 'BLD_01', name: 'Main Administrative Block', footprint_area_sqm: measured * 0.4, levels: 2 },
          { id: 'BLD_02', name: 'Instructional Engineering Complex', footprint_area_sqm: measured * 0.35, levels: 3 },
          { id: 'BLD_03', name: 'Department Labs & IT Block', footprint_area_sqm: measured * 0.25, levels: 4 }
        ],
        regulatory_caveat: 'Advisory Indicator: Sun-shadow and satellite checks are advisory and are skipped for indoor photos. Satellite datasets may lag recent construction or omit courtyard clearances.'
      });
      setBuiltUpDemo(true);
    } finally {
      setBuiltUpLoading(false);
    }
  };

  useEffect(() => {
    runSunShadowCheck(selectedSunPreset);
  }, [selectedSunPreset]);

  useEffect(() => {
    setCustomLat(selectedBuiltUpPreset.latitude);
    setCustomLon(selectedBuiltUpPreset.longitude);
    setCustomClaimedArea(selectedBuiltUpPreset.claimed_built_up_area);
    setCustomTolerance(selectedBuiltUpPreset.tolerance_pct);
    runBuiltUpCheck(
      selectedBuiltUpPreset.latitude,
      selectedBuiltUpPreset.longitude,
      selectedBuiltUpPreset.claimed_built_up_area,
      selectedBuiltUpPreset.tolerance_pct
    );
  }, [selectedBuiltUpPreset]);

  return (
    <div className="space-y-6">
      {/* 1. Top Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">Proof-of-Reality Verification</h2>
                {(sunShadowDemo || builtUpDemo) && <DemoDataBadge reason="Fallback Mock Data" />}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Physical ground-truth triangulation combining astronomical solar shadow plausibility and satellite building footprints.
              </p>
            </div>
          </div>
        </div>

        {/* Global Mandatory Statutory Caveat */}
        <div className="text-right">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-xl text-xs font-semibold bg-indigo-50 border border-indigo-200 text-indigo-800">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
            <span>Advisory Triangulation Engine</span>
          </span>
        </div>
      </div>

      {/* Mandatory Statutory Advisory Banner */}
      <div className="bg-amber-50/80 border border-amber-200/90 rounded-2xl p-4 flex items-start space-x-3 text-xs text-amber-950">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <strong>Mandatory Statutory Protocol:</strong> All solar and satellite checks are advisory indicators for committee inquiry. 
          <em> Sun-shadow and satellite checks are advisory and are skipped for indoor photos.</em> Autonomous rejections are strictly prohibited.
        </div>
      </div>

      {/* 2. SECTION A: Sun-Shadow Astronomical Plausibility Checker */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-amber-50 border border-amber-200 rounded-xl text-amber-600">
              <Sun className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Sun-Shadow Astronomical Plausibility</h3>
              <p className="text-xs text-slate-500">Cross-verifies outdoor photo shadow vectors against NOAA solar azimuth algorithms (pvlib).</p>
            </div>
          </div>

          <button
            onClick={() => runSunShadowCheck(selectedSunPreset)}
            disabled={sunShadowLoading}
            className="p-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl transition-colors cursor-pointer self-start sm:self-auto"
            title="Re-run sun shadow test"
          >
            <RefreshCw className={`w-4 h-4 ${sunShadowLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Preset Selector */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">Preset Scenarios</span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {SUN_SHADOW_PRESETS.map((p) => {
              const isSelected = selectedSunPreset.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setSelectedSunPreset(p)}
                  className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-amber-50/50 border-amber-500 ring-2 ring-amber-500/20 shadow-xs'
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900">{p.name}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                      p.is_indoor ? 'bg-indigo-50 text-indigo-700' : 'bg-amber-50 text-amber-800'
                    }`}>
                      {p.scenario}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 line-clamp-1">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Results Card */}
        {sunShadowLoading ? (
          <div className="p-8 text-center text-slate-400 space-y-2 border border-dashed border-slate-200 rounded-xl">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-amber-500" />
            <p className="text-xs font-semibold text-slate-600">Calculating solar position via NOAA pvlib & shadow gradients...</p>
          </div>
        ) : sunShadowResult && (
          <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/60">
              <div className="flex items-center space-x-2">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase border ${
                  sunShadowResult.status === 'SKIPPED_INDOOR'
                    ? 'bg-indigo-50 text-indigo-800 border-indigo-200'
                    : sunShadowResult.status === 'PLAUSIBLE'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}>
                  Status: {sunShadowResult.status}
                </span>

                <span className="text-xs text-slate-500 font-mono">
                  Plausibility Score: <strong>{(sunShadowResult.plausibility_score * 100).toFixed(0)}%</strong>
                </span>
              </div>

              <div className="text-[11px] font-mono text-slate-500 flex items-center space-x-3">
                <span>GPS: {sunShadowResult.claimed_gps?.latitude?.toFixed(4)}, {sunShadowResult.claimed_gps?.longitude?.toFixed(4)}</span>
                <span>•</span>
                <span>Time: {sunShadowResult.claimed_timestamp ? new Date(sunShadowResult.claimed_timestamp).toLocaleTimeString() : 'N/A'}</span>
              </div>
            </div>

            {/* Plain-Language Reason Card */}
            <div className={`p-3.5 rounded-xl border text-xs leading-relaxed font-medium ${
              sunShadowResult.status === 'FLAGGED_DISCREPANCY'
                ? 'bg-amber-50 border-amber-300 text-amber-950'
                : 'bg-white border-slate-200 text-slate-800'
            }`}>
              <div className="font-bold text-slate-900 mb-1 flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Advisory Finding Breakdown</span>
              </div>
              <p>{sunShadowResult.human_readable_summary}</p>
            </div>

            {/* Solar Metric Badges Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Scene Classification</div>
                <div className="text-sm font-bold text-slate-900 mt-1 capitalize">
                  {sunShadowResult.scene_classification?.scene_type?.replace(/_/g, ' ') || 'Outdoor'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {sunShadowResult.scene_classification?.is_indoor ? 'Indoor: Skipped' : 'Outdoor Sunlit'}
                </div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Astronomical Sun Azimuth</div>
                <div className="text-sm font-bold text-amber-600 font-mono mt-1">
                  {sunShadowResult.sun_position?.azimuth_deg ? `${sunShadowResult.sun_position.azimuth_deg.toFixed(1)}°` : 'N/A (Indoor)'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Expected shadow: {sunShadowResult.sun_position?.expected_shadow_azimuth_deg ? `${sunShadowResult.sun_position.expected_shadow_azimuth_deg.toFixed(1)}°` : 'N/A'}</div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Observed Shadow Direction</div>
                <div className="text-sm font-bold text-slate-800 font-mono mt-1">
                  {sunShadowResult.estimated_shadow?.dominant_image_angle_deg ? `${sunShadowResult.estimated_shadow.dominant_image_angle_deg.toFixed(1)}°` : 'N/A (Indoor)'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Coherence: {sunShadowResult.estimated_shadow?.directional_coherence || 'N/A'}</div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Angular Discrepancy</div>
                <div className={`text-sm font-bold font-mono mt-1 ${
                  (sunShadowResult.angular_discrepancy_deg || 0) > 45 ? 'text-rose-600' : 'text-emerald-600'
                }`}>
                  {sunShadowResult.angular_discrepancy_deg !== undefined ? `${sunShadowResult.angular_discrepancy_deg.toFixed(1)}°` : '0.0°'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Tolerance band: ±45°</div>
              </div>
            </div>

            {/* Caveat line */}
            <div className="text-[11px] text-slate-500 italic flex items-center space-x-1.5 pt-1">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>Caveat: Sun-shadow and satellite checks are advisory and are skipped for indoor photos.</span>
            </div>
          </div>
        )}
      </div>

      {/* 3. SECTION B: Satellite & Open Buildings Built-Up Area Footprint Checker */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-indigo-50 border border-indigo-200 rounded-xl text-indigo-600">
              <Satellite className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Satellite & OSM Built-Up Area Triangulation</h3>
              <p className="text-xs text-slate-500">Cross-checks self-declared campus built-up area against Open Buildings v3 & OSM polygon geometry.</p>
            </div>
          </div>

          <button
            onClick={() => runBuiltUpCheck(customLat, customLon, customClaimedArea, customTolerance)}
            disabled={builtUpLoading}
            className="p-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl transition-colors cursor-pointer self-start sm:self-auto"
            title="Re-run geospatial query"
          >
            <RefreshCw className={`w-4 h-4 ${builtUpLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Institution Presets */}
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">Campus Benchmark Presets</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {BUILT_UP_PRESETS.map((p) => {
              const isSelected = selectedBuiltUpPreset.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setSelectedBuiltUpPreset(p)}
                  className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-50/50 border-indigo-500 ring-2 ring-indigo-500/20 shadow-xs'
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                  }`}
                >
                  <div className="text-xs font-bold text-slate-900 mb-0.5 line-clamp-1">{p.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono mb-1">Claim: {p.claimed_built_up_area.toLocaleString()} m²</div>
                  <p className="text-[11px] text-slate-500 line-clamp-1">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Interactive Query Parameter Controls */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Centroid Latitude</label>
            <input
              type="number"
              step="0.0001"
              value={customLat}
              onChange={(e) => setCustomLat(parseFloat(e.target.value) || 0)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-mono text-slate-800"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Centroid Longitude</label>
            <input
              type="number"
              step="0.0001"
              value={customLon}
              onChange={(e) => setCustomLon(parseFloat(e.target.value) || 0)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-mono text-slate-800"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Claimed Area (m²)</label>
            <input
              type="number"
              step="100"
              value={customClaimedArea}
              onChange={(e) => setCustomClaimedArea(parseFloat(e.target.value) || 0)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-mono text-slate-800"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Tolerance Band (±%)</label>
            <div className="flex items-center space-x-2">
              <input
                type="number"
                min="5"
                max="50"
                value={customTolerance}
                onChange={(e) => setCustomTolerance(parseInt(e.target.value) || 25)}
                className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 font-mono text-slate-800"
              />
              <button
                onClick={() => runBuiltUpCheck(customLat, customLon, customClaimedArea, customTolerance)}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold transition-all shadow-2xs"
              >
                Run
              </button>
            </div>
          </div>
        </div>

        {/* Results Card */}
        {builtUpLoading ? (
          <div className="p-8 text-center text-slate-400 space-y-2 border border-dashed border-slate-200 rounded-xl">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-500" />
            <p className="text-xs font-semibold text-slate-600">Querying Open Buildings spatial index within 350m radius...</p>
          </div>
        ) : builtUpResult && (
          <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/60">
              <div className="flex items-center space-x-2">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase border ${
                  builtUpResult.is_within_tolerance
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}>
                  Status: {builtUpResult.status?.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-slate-600">
                  {builtUpResult.is_within_tolerance ? 'Consistent with Satellite Registry' : 'Indicator for review'}
                </span>
              </div>

              <div className="text-[11px] font-mono text-slate-500">
                Polygons: <strong>{builtUpResult.numbers_used?.building_count || 0} structures</strong> in 350m radius
              </div>
            </div>

            {/* Plain-Language Reason / Advisory Recommendation */}
            <div className={`p-3.5 rounded-xl border text-xs leading-relaxed font-medium ${
              builtUpResult.review_recommended
                ? 'bg-amber-50 border-amber-300 text-amber-950'
                : 'bg-white border-slate-200 text-slate-800'
            }`}>
              <div className="font-bold text-slate-900 mb-1 flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Statutory Advisory Finding</span>
              </div>
              <p>{builtUpResult.advisory_summary}</p>
            </div>

            {/* Numbers Breakdown Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Claimed Built-Up Area</div>
                <div className="text-sm font-bold text-slate-900 font-mono mt-1">
                  {builtUpResult.numbers_used?.claimed_built_up_area_sqm?.toLocaleString()} m²
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Institutional Self-Declaration</div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Satellite Ground Footprint</div>
                <div className="text-sm font-bold text-indigo-600 font-mono mt-1">
                  {builtUpResult.numbers_used?.measured_footprint_sqm?.toLocaleString()} m²
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Sum of Open Buildings Polygons</div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Discrepancy (Δ)</div>
                <div className={`text-sm font-bold font-mono mt-1 ${
                  (builtUpResult.numbers_used?.discrepancy_sqm || 0) < 0 ? 'text-amber-700' : 'text-emerald-700'
                }`}>
                  {builtUpResult.numbers_used?.discrepancy_sqm?.toLocaleString()} m² ({builtUpResult.numbers_used?.discrepancy_pct?.toFixed(1)}%)
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Band: ±{customTolerance}%</div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-slate-200">
                <div className="text-[10px] text-slate-400 font-bold uppercase">Tolerance Interval</div>
                <div className="text-sm font-bold text-slate-800 font-mono mt-1">
                  {builtUpResult.numbers_used?.tolerance_lower_bound_sqm?.toLocaleString()} - {builtUpResult.numbers_used?.tolerance_upper_bound_sqm?.toLocaleString()} m²
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Valid Statutory Range</div>
              </div>
            </div>

            {/* Detected Buildings Table */}
            {builtUpResult.buildings && builtUpResult.buildings.length > 0 && (
              <div className="mt-3 bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="p-3 bg-slate-50/70 border-b border-slate-200 text-xs font-bold text-slate-800 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5">
                    <Building2 className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Detected Building Structures ({builtUpResult.buildings.length})</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">Source: Open Buildings v3 / OSM</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/50 text-[10px] font-bold text-slate-500 uppercase border-b border-slate-200">
                      <tr>
                        <th className="py-2 px-3">Structure ID & Name</th>
                        <th className="py-2 px-3">Type</th>
                        <th className="py-2 px-3">Footprint (m²)</th>
                        <th className="py-2 px-3">Levels</th>
                        <th className="py-2 px-3">Est. Built-Up (m²)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {builtUpResult.buildings.map((b, idx) => (
                        <tr key={b.id || idx} className="hover:bg-slate-50/60">
                          <td className="py-2 px-3">
                            <div className="font-bold text-slate-900">{b.name || b.id}</div>
                            <div className="text-[10px] font-mono text-slate-400">{b.id}</div>
                          </td>
                          <td className="py-2 px-3 capitalize text-slate-600">{b.building_type || 'Instructional'}</td>
                          <td className="py-2 px-3 font-mono font-bold text-slate-900">{b.footprint_area_sqm?.toLocaleString()}</td>
                          <td className="py-2 px-3 font-mono">{b.levels || 2}</td>
                          <td className="py-2 px-3 font-mono font-bold text-indigo-700">{b.estimated_built_up_sqm?.toLocaleString() || (b.footprint_area_sqm * (b.levels || 2)).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Caveat line */}
            <div className="text-[11px] text-slate-500 italic flex items-center space-x-1.5 pt-1">
              <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>Caveat: Sun-shadow and satellite checks are advisory and are skipped for indoor photos.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
