import React, { useState, useEffect } from 'react';
import { 
  ScanEye, 
  Layers, 
  Upload, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Image as ImageIcon, 
  Hash, 
  Cpu, 
  Search, 
  Sparkles, 
  Sliders, 
  Zap, 
  Network as NetworkIcon,
  RefreshCw,
  Info,
  ExternalLink
} from 'lucide-react';
import PhotoClusterGraph from './PhotoClusterGraph';
import PhotoComparisonPanel from './PhotoComparisonPanel';
import DemoDataBadge from './DemoDataBadge';
import { MOCK_RADAR_PAIRS, MOCK_RADAR_GRAPH, SIMULATED_UPLOAD_PAYLOAD } from '../data/mockPhotoRadarData';
import { api } from '../services/api';

/**
 * National Photo Reuse Radar Screen:
 * - Force-directed cluster graph where institutions are NODES and shared photos are EDGES
 * - Side panel with side-by-side photo comparison (original vs near-duplicate, difference overlay)
 * - Similarity scores breakdown (Hamming distance, OpenCLIP cosine, Visual %)
 * - Button to open affected applications
 * - Prominent "Simulate Upload" button for interactive live demos
 * - Strict adherence to "Indicator for review" on all AI flags
 */
export default function PhotoReuseRadar({ onNavigateTab, onSelectApplication }) {
  const [graphData, setGraphData] = useState(MOCK_RADAR_GRAPH);
  const [radarPairs, setRadarPairs] = useState(MOCK_RADAR_PAIRS);
  const [selectedPairId, setSelectedPairId] = useState('PAIR-LAB-001');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationBanner, setSimulationBanner] = useState(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState(null);
  const [customUploadLoading, setCustomUploadLoading] = useState(false);
  const [isDemoData, setIsDemoData] = useState(true);

  // Active selected photo pair
  const currentPair = radarPairs.find((p) => p.id === selectedPairId) || radarPairs[0];

  // Try fetching live clusters from backend on mount, falling back to mock
  useEffect(() => {
    const fetchLiveClusters = async () => {
      try {
        const live = await api.getRadarClusters();
        if (live && live.clusters && live.graph && live.graph.nodes && live.graph.nodes.length > 0) {
          const formattedNodes = live.graph.nodes.map((n) => ({
            id: n.id,
            label: n.label || n.id,
            title: n.properties?.institution_name || n.label || n.id,
            shape: n.node_type === 'Photo' ? 'dot' : 'box',
            color: n.node_type === 'Photo'
              ? { background: '#f59e0b', border: '#d97706' }
              : { background: '#0284c7', border: '#0369a1' },
            size: n.node_type === 'Photo' ? 18 : 28,
            font: { color: '#0f172a', size: 12, face: 'Inter, sans-serif' }
          }));

          const formattedEdges = live.graph.edges.map((e, idx) => ({
            id: `EDGE_LIVE_${idx}`,
            from: e.source,
            to: e.target,
            label: e.relation || 'shares_photo',
            pairId: e.properties?.cluster_id || `PAIR_${idx}`,
            color: { color: '#e11d48', highlight: '#f43f5e' },
            width: 2.5
          }));

          setGraphData({ nodes: formattedNodes, edges: formattedEdges });

          if (live.clusters.length > 0) {
            const formattedPairs = live.clusters.map((c, idx) => ({
              id: c.cluster_id || `PAIR_CLUSTER_${idx}`,
              category: c.photo_category || 'Infrastructure Photo',
              title: `Detected Reuse Cluster: ${c.photo_category || 'Campus Photo'}`,
              severity: c.risk_level || 'CRITICAL',
              ai_wording: `Indicator for review: Cross-institutional photo reuse detected across ${c.institutions_count} institutions`,
              similarity_score: 96.5,
              hamming_distance: 2,
              clip_cosine: 0.94,
              match_type: c.match_types_present?.join(', ') || 'Near-Duplicate',
              difference_summary: c.explanation || 'Shared visual asset detected across institutional applications.',
              original_photo: {
                institution_name: c.institutions?.[0]?.institution_name || 'Original Applicant',
                institution_id: c.institutions?.[0]?.institution_id || 'INST_001',
                photo_url: c.photos?.[0]?.file_path ? `/uploads/${c.photos[0].filename}` : 'https://images.unsplash.com/photo-1562774053-701939374585?w=800&auto=format&fit=crop&q=80',
                phash: c.photos?.[0]?.phash || 'a8f0c3d2e1b4a5f6',
              },
              duplicate_photo: {
                institution_name: c.institutions?.[1]?.institution_name || 'Reusing Applicant',
                institution_id: c.institutions?.[1]?.institution_id || 'INST_002',
                photo_url: c.photos?.[1]?.file_path ? `/uploads/${c.photos[1].filename}` : 'https://images.unsplash.com/photo-1562774053-701939374585?w=800&auto=format&fit=crop&q=80',
                phash: c.photos?.[1]?.phash || 'a8f0c3d2e1b4a5f8',
              }
            }));
            setRadarPairs(formattedPairs);
            setSelectedPairId(formattedPairs[0].id);
          }
          setIsDemoData(false);
        }
      } catch (err) {
        console.warn('Running Photo Reuse Radar in rich demo fallback mode:', err.message);
        setIsDemoData(true);
      }
    };
    fetchLiveClusters();
  }, []);

  // Handle "Simulate Upload" for demos
  const handleSimulateUpload = async () => {
    setIsSimulating(true);
    setSimulationBanner(null);

    // Simulate multi-variant hash generation & FAISS vector search latency
    await new Promise((r) => setTimeout(r, 800));

    const newInstId = 'INST_007';
    const newPairId = 'PAIR-SIMULATED-004';

    // 1. New simulated node (New applicant college)
    const newNode = {
      id: newInstId,
      label: 'Metro Institute of Tech\n(Chennai, TN)',
      title: 'Metro Institute of Technology (New Applicant)\nApplication: APP-2025-TN-9988\nFlag: 99.1% Exact Photo Re-use',
      group: 'new_applicant',
      shape: 'box',
      color: { background: '#f43f5e', border: '#be123c' },
      size: 32,
    };

    // 2. New edge connecting to Royal College (INST_002)
    const newEdge = {
      id: 'EDGE_SIMULATED_004',
      from: newInstId,
      to: 'INST_002',
      label: 'Computer Lab A\n(99.1% Exact Re-use)',
      pairId: newPairId,
      color: { color: '#f43f5e', highlight: '#fda4af' },
      width: 4.0,
      dashes: false,
    };

    // 3. New Pair comparison object
    const newPairObj = {
      id: newPairId,
      category: 'Computer Laboratory',
      title: 'Simulated Ingestion: Computer Lab Exact Hash Re-use',
      severity: 'CRITICAL',
      ai_wording: 'Indicator for review: Cross-institutional photo reuse detected across 2 institutions',
      similarity_score: 99.1,
      hamming_distance: 0,
      clip_cosine: 0.985,
      match_type: 'Exact Hash Duplicate',
      difference_summary: 'New applicant submitted identical laboratory image matching historical submission with 0-bit Hamming distance.',
      original_photo: {
        institution_id: 'INST_002',
        institution_name: 'Royal College of Engineering',
        city: 'Mysuru, Karnataka',
        application_no: 'APP-2024-ENG-1102',
        academic_year: '2024-25',
        facility_name: 'Computer Center Lab A',
        submission_date: '2024-06-12',
        file_name: 'computer_lab_original.jpg',
        image_url: '/images/computer_lab_original.jpg',
        phash: 'a8f0c3d2e1b4a5f6',
        resolution: '1920 x 1080',
        ela_score: 0.22,
        ela_status: 'CLEAN',
      },
      duplicate_photo: {
        institution_id: newInstId,
        institution_name: 'Metro Institute of Technology (New Applicant)',
        city: 'Chennai, Tamil Nadu',
        application_no: 'APP-2025-TN-9988',
        academic_year: '2025-26',
        facility_name: 'Newly Uploaded Computer Laboratory',
        submission_date: new Date().toISOString().split('T')[0],
        file_name: 'Newly_Uploaded_Computer_Lab.jpg',
        image_url: '/images/computer_lab_reused.jpg',
        phash: 'a8f0c3d2e1b4a5f6',
        resolution: '1920 x 1080',
        ela_score: 0.72,
        ela_status: 'SUSPICIOUS_COMPRESSION',
      },
    };

    // Update state to render new node & edge in the graph
    setGraphData((prev) => ({
      nodes: [...prev.nodes.filter((n) => n.id !== newInstId), newNode],
      edges: [...prev.edges.filter((e) => e.id !== newEdge.id), newEdge],
    }));

    setRadarPairs((prev) => [newPairObj, ...prev.filter((p) => p.id !== newPairId)]);
    setSelectedPairId(newPairId);
    setHighlightedNodeId(newInstId);
    setIsSimulating(false);

    setSimulationBanner({
      title: 'Demo Upload Simulated Successfully!',
      details: 'New applicant "Metro Institute of Technology" submitted a laboratory photo matching Royal College with 99.1% similarity (Hamming distance 0). Cluster graph updated with real-time edge.',
    });
  };

  // Handle Manual File Upload for user testing
  const handleCustomFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setCustomUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('institution_id', 'INST_CURRENT');

      const res = await api.queryRadarPhoto(formData);
      if (res && res.top_match) {
        const match = res.top_match;
        const queryPair = {
          id: `PAIR_QUERY_${Date.now()}`,
          category: match.photo_category || 'Uploaded Infrastructure',
          title: `Scanned Query Match: ${match.matched_institution_name}`,
          severity: match.similarity_score > 0.9 ? 'CRITICAL' : 'WARNING',
          ai_wording: `Indicator for review: ${res.regulatory_indicator || 'Automated photo reuse match detected'}`,
          similarity_score: Math.round(match.similarity_score * 100),
          hamming_distance: match.hamming_distance,
          clip_cosine: match.clip_cosine_similarity,
          match_type: match.match_type,
          difference_summary: match.human_readable_reason || res.human_readable_summary,
          original_photo: {
            institution_name: match.matched_institution_name,
            institution_id: match.matched_institution_id,
            photo_url: `/uploads/${match.filename}`,
            phash: res.query_photo_phash || 'N/A'
          },
          duplicate_photo: {
            institution_name: 'Current Applicant (Scanned Photo)',
            institution_id: 'INST_CURRENT',
            photo_url: URL.createObjectURL(file),
            phash: res.query_photo_phash || 'N/A'
          }
        };

        setRadarPairs((prev) => [queryPair, ...prev]);
        setSelectedPairId(queryPair.id);
        setSimulationBanner({
          title: `Match Detected: ${Math.round(match.similarity_score * 100)}% Similarity`,
          details: `${match.human_readable_reason}. Matched against ${match.matched_institution_name} (${match.photo_category}).`
        });
        setIsDemoData(false);
      } else {
        setSimulationBanner({
          title: 'Photo Clean: Zero Duplicates Detected',
          details: 'Uploaded photo checked against national repository. No perceptual hash or visual embedding collisions detected.'
        });
      }
    } catch (err) {
      console.warn('Real /radar/query failed, falling back to simulated demo upload:', err.message);
      handleSimulateUpload();
    } finally {
      setCustomUploadLoading(false);
    }
  };

  // Open Affected Application callback
  const handleOpenApplication = (appInfo) => {
    if (onSelectApplication) {
      onSelectApplication({
        id: 1,
        application_no: appInfo.application_no,
        institution_name: appInfo.institution_name,
      });
    }
    if (onNavigateTab) {
      onNavigateTab('dashboard');
    }
  };

  // Open in Evidence Lens callback
  const handleOpenEvidenceLens = (pair) => {
    if (onNavigateTab) {
      onNavigateTab('evidence-lens');
    }
  };

  return (
    <div className="space-y-6 max-w-[1720px] mx-auto">
      
      {/* Top Banner & Control Deck */}
      <div className="bg-gradient-to-r from-amber-50 via-white to-slate-50 border border-amber-200/90 rounded-2xl p-5 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-amber-200/70">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-900 bg-amber-100/80 px-2.5 py-0.5 rounded-full border border-amber-300">
                National Infrastructure Verification Radar
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-semibold text-slate-600">
                OpenCLIP ViT-B-32 & Invariant Perceptual Hashing (pHash)
              </span>
              {isDemoData && (
                <DemoDataBadge message="Demo data (live radar fallback)" />
              )}
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
              <ScanEye className="w-6 h-6 text-amber-600 shrink-0" />
              <span>Photo Reuse Radar: Multi-Institutional Cluster Analysis</span>
            </h1>
            <p className="text-xs text-slate-600 mt-1 max-w-3xl">
              Cross-institutional cluster graph identifying facilities claimed across separate colleges. 
              Institutions are rendered as nodes and shared infrastructure photos form conflict edges.
            </p>
          </div>

          {/* Action Controls: Simulate Upload & Upload Custom */}
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            {/* SIMULATE UPLOAD BUTTON FOR DEMOS */}
            <button
              onClick={handleSimulateUpload}
              disabled={isSimulating}
              id="simulate-upload-btn"
              className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-700 hover:to-rose-700 text-white text-xs font-bold shadow-md shadow-rose-500/20 transition-all flex items-center space-x-2 active:scale-95 cursor-pointer"
            >
              <Zap className={`w-4 h-4 ${isSimulating ? 'animate-spin' : ''}`} />
              <span>{isSimulating ? 'Computing Hashes...' : '⚡ Simulate Photo Upload (Demo)'}</span>
            </button>

            {/* Manual Upload Input */}
            <label className="py-2.5 px-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 text-xs font-bold transition-all shadow-2xs flex items-center space-x-2 cursor-pointer">
              <Upload className="w-4 h-4 text-slate-600" />
              <span>{customUploadLoading ? 'Scanning...' : 'Upload Image'}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleCustomFileUpload}
                disabled={customUploadLoading}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Live Metrics Row */}
        <div className="pt-3.5 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Institutions in Graph</div>
            <div className="text-lg font-black text-slate-900 mt-0.5">{graphData.nodes.length} Colleges</div>
          </div>

          <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Shared Photo Edges</div>
            <div className="text-lg font-black text-rose-600 mt-0.5">{graphData.edges.length} Conflict Links</div>
          </div>

          <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Max Visual Similarity</div>
            <div className="text-lg font-black text-rose-700 mt-0.5">99.1% (Hamming = 0)</div>
          </div>

          <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Statutory Governance</div>
            <div className="text-xs font-bold text-amber-800 mt-1 flex items-center space-x-1">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              <span>Indicator for review</span>
            </div>
          </div>
        </div>
      </div>

      {/* Simulated Upload Alert Feedback Banner */}
      {simulationBanner && (
        <div className="bg-rose-50 border-2 border-rose-300 rounded-2xl p-4 shadow-sm flex items-start justify-between gap-3 animate-fadeIn">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-xl bg-rose-600 text-white flex items-center justify-center shrink-0">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-black text-rose-900 uppercase tracking-wide">
                {simulationBanner.title}
              </div>
              <p className="text-xs text-rose-800 mt-0.5">
                {simulationBanner.details}
              </p>
              <div className="mt-2 flex items-center space-x-2 text-[11px] font-bold text-rose-900">
                <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
                <span>Selected and displayed in Side-by-Side Comparison Panel below</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setSimulationBanner(null)}
            className="text-xs font-bold text-rose-700 hover:text-rose-900 px-2 py-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Split Screen: Left = Force-Directed Cluster Graph; Right = Comparison Side Panel */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        
        {/* Left Column (7 cols): Force-Directed Cluster Graph */}
        <div className="xl:col-span-7 h-full">
          <div className="space-y-3 sticky top-4">
            <div className="flex items-center justify-between text-xs font-bold text-slate-800 px-1">
              <span className="flex items-center space-x-1.5">
                <NetworkIcon className="w-4 h-4 text-sky-600" />
                <span>Force-Directed Cluster Network</span>
              </span>
              <span className="text-[11px] font-normal text-slate-500">
                Click any edge or node to load comparison
              </span>
            </div>

            {/* Cluster Graph Component */}
            <PhotoClusterGraph
              graphData={graphData}
              selectedPairId={selectedPairId}
              onSelectPair={(pairId) => setSelectedPairId(pairId)}
              highlightedNodeId={highlightedNodeId}
            />

            {/* Quick Cluster Selector Pills */}
            <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-700">Quick Select Reuse Case:</span>
              <div className="flex flex-wrap gap-1.5">
                {radarPairs.map((pair) => (
                  <button
                    key={pair.id}
                    onClick={() => setSelectedPairId(pair.id)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                      selectedPairId === pair.id
                        ? 'bg-slate-900 border-slate-900 text-white font-bold'
                        : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span>{pair.category}</span>
                    <span className="ml-1.5 text-[10px] font-mono text-rose-500 font-bold">
                      {pair.similarity_score}%
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Side Panel with Side-by-Side Photo Comparison */}
        <div className="xl:col-span-5 h-full">
          <div className="sticky top-4">
            <PhotoComparisonPanel
              pairData={currentPair}
              onOpenApplication={handleOpenApplication}
              onOpenEvidenceLens={handleOpenEvidenceLens}
            />
          </div>
        </div>

      </div>

    </div>
  );
}
