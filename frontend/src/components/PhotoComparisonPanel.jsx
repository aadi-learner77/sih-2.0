import React, { useState } from 'react';
import { 
  ScanEye, 
  Layers, 
  ExternalLink, 
  AlertTriangle, 
  ShieldAlert, 
  Sliders, 
  Split, 
  Eye, 
  CheckCircle2, 
  FileText, 
  Hash, 
  Building2, 
  Clock, 
  ChevronRight,
  Maximize2
} from 'lucide-react';

/**
 * Side Panel with Side-by-Side Photo Comparison:
 * - Side-by-side photo views (original vs near-duplicate)
 * - Difference overlay / ELA heatmap toggle
 * - Interactive wipe slider comparison
 * - Similarity scores breakdown (Hamming distance, OpenCLIP cosine, Visual %)
 * - Action buttons to open affected institutional applications
 */
export default function PhotoComparisonPanel({ 
  pairData, 
  onOpenApplication,
  onOpenEvidenceLens 
}) {
  const [viewMode, setViewMode] = useState('side_by_side'); // 'side_by_side' | 'difference_overlay' | 'wipe_slider'
  const [wipePosition, setWipePosition] = useState(50); // percentage 0-100 for slider
  const [overlayOpacity, setOverlayOpacity] = useState(65);
  const [toastMsg, setToastMsg] = useState('');

  if (!pairData) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500">
        <ScanEye className="w-10 h-10 mx-auto text-slate-400 mb-2 animate-pulse" />
        <p className="text-sm font-semibold text-slate-700">Select a Photo Reuse Link</p>
        <p className="text-xs text-slate-500 mt-1">
          Click any edge or connected college node in the cluster graph to inspect forensic comparison.
        </p>
      </div>
    );
  }

  const { original_photo, duplicate_photo } = pairData;

  const handleOpenApp = (appNo, instName) => {
    setToastMsg(`Opening application dossier for ${instName} (${appNo})...`);
    setTimeout(() => setToastMsg(''), 3500);
    if (onOpenApplication) {
      onOpenApplication({ application_no: appNo, institution_name: instName });
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
      {/* Side Panel Header */}
      <div className="p-4 bg-slate-900 text-slate-100 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center space-x-2 text-[10px] text-amber-400 uppercase font-mono font-bold tracking-wider mb-0.5">
            <span>Photo Reuse Inspection</span>
            <span>•</span>
            <span>{pairData.id}</span>
          </div>
          <h2 className="text-sm font-bold text-white truncate" title={pairData.title}>
            {pairData.title}
          </h2>
          <div className="text-[11px] text-slate-400 truncate">
            {pairData.category}
          </div>
        </div>

        {/* Severity Badge */}
        <div className="shrink-0 text-right">
          <span className={`text-[11px] font-black px-2.5 py-1 rounded-md border ${
            pairData.similarity_score >= 95
              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
              : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
          }`}>
            {pairData.similarity_score}% Match
          </span>
          <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
            d={pairData.hamming_distance} / 64
          </div>
        </div>
      </div>

      {/* Mandatory Statutory Advisory Banner */}
      <div className="bg-rose-50 px-4 py-2.5 border-b border-rose-200 text-rose-900 text-xs flex items-center space-x-2">
        <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
        <span className="font-bold text-[11px] leading-tight">
          {pairData.ai_wording}
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        
        {/* View Mode Switcher Toolbar */}
        <div className="flex items-center justify-between bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-xs">
          <span className="text-[11px] font-bold text-slate-600 px-2">Comparison View:</span>
          <div className="flex space-x-1">
            <button
              id="view-mode-side-by-side"
              onClick={() => setViewMode('side_by_side')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center space-x-1 ${
                viewMode === 'side_by_side'
                  ? 'bg-white text-slate-900 shadow-2xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Split className="w-3 h-3" />
              <span>Side-by-Side</span>
            </button>

            <button
              id="view-mode-difference-overlay"
              onClick={() => setViewMode('difference_overlay')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center space-x-1 ${
                viewMode === 'difference_overlay'
                  ? 'bg-white text-slate-900 shadow-2xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers className="w-3 h-3 text-rose-600" />
              <span>Difference Overlay</span>
            </button>

            <button
              id="view-mode-wipe-slider"
              onClick={() => setViewMode('wipe_slider')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center space-x-1 ${
                viewMode === 'wipe_slider'
                  ? 'bg-white text-slate-900 shadow-2xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sliders className="w-3 h-3 text-sky-600" />
              <span>Wipe Slider</span>
            </button>
          </div>
        </div>

        {/* 1. SIDE-BY-SIDE VIEW */}
        {viewMode === 'side_by_side' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              
              {/* Original Photo Card */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl overflow-hidden shadow-2xs flex flex-col">
                <div className="bg-slate-200/80 px-3 py-1.5 text-[10px] font-bold text-slate-700 uppercase flex items-center justify-between border-b border-slate-200">
                  <span className="flex items-center space-x-1">
                    <span className="w-2 h-2 rounded-full bg-slate-500" />
                    <span>Original Submission</span>
                  </span>
                  <span className="font-mono text-slate-500">{original_photo.academic_year}</span>
                </div>

                <div className="relative aspect-[4/3] bg-slate-900 overflow-hidden group">
                  <img 
                    src={original_photo.image_url} 
                    alt={original_photo.facility_name} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[9px] font-mono px-2 py-0.5 rounded backdrop-blur-xs">
                    {original_photo.file_name}
                  </div>
                </div>

                <div className="p-3 text-xs space-y-1.5 flex-1 bg-white">
                  <div className="font-bold text-slate-900 text-xs">
                    {original_photo.institution_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {original_photo.city}
                  </div>
                  <div className="text-[11px] text-slate-700 bg-slate-50 p-1.5 rounded border border-slate-100 font-medium">
                    {original_photo.facility_name}
                  </div>
                  <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span>App: {original_photo.application_no}</span>
                    <span>Date: {original_photo.submission_date}</span>
                  </div>
                </div>
              </div>

              {/* Near-Duplicate Photo Card */}
              <div className="bg-slate-50 border-2 border-rose-300 rounded-xl overflow-hidden shadow-2xs flex flex-col">
                <div className="bg-rose-100/80 px-3 py-1.5 text-[10px] font-bold text-rose-800 uppercase flex items-center justify-between border-b border-rose-200">
                  <span className="flex items-center space-x-1">
                    <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse" />
                    <span>Current Near-Duplicate</span>
                  </span>
                  <span className="font-mono text-rose-700">{duplicate_photo.academic_year}</span>
                </div>

                <div className="relative aspect-[4/3] bg-slate-900 overflow-hidden group">
                  <img 
                    src={duplicate_photo.image_url} 
                    alt={duplicate_photo.facility_name} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-2 right-2 bg-rose-600 text-white text-[9px] font-bold px-2 py-0.5 rounded shadow-sm">
                    {pairData.similarity_score}% RE-USE
                  </div>
                  <div className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[9px] font-mono px-2 py-0.5 rounded backdrop-blur-xs">
                    {duplicate_photo.file_name}
                  </div>
                </div>

                <div className="p-3 text-xs space-y-1.5 flex-1 bg-white">
                  <div className="font-bold text-slate-900 text-xs">
                    {duplicate_photo.institution_name}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {duplicate_photo.city}
                  </div>
                  <div className="text-[11px] text-rose-900 bg-rose-50/60 p-1.5 rounded border border-rose-100 font-medium">
                    {duplicate_photo.facility_name}
                  </div>
                  <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span>App: {duplicate_photo.application_no}</span>
                    <span>Date: {duplicate_photo.submission_date}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* 2. DIFFERENCE OVERLAY / ELA HEATMAP VIEW */}
        {viewMode === 'difference_overlay' && (
          <div className="space-y-3">
            <div className="bg-slate-900 rounded-xl p-3 text-slate-200 text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-amber-400 flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Pixel Difference & Forensic ELA Divergence Heatmap</span>
                </span>
                <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                  Opacity: {overlayOpacity}%
                </span>
              </div>

              {/* Overlay Canvas Viewport */}
              <div className="relative aspect-[4/3] rounded-lg overflow-hidden border border-slate-700 bg-black">
                {/* Base Image (Original) */}
                <img 
                  src={original_photo.image_url} 
                  alt="Original" 
                  className="absolute inset-0 w-full h-full object-cover"
                />

                {/* Overlaid Near Duplicate Image with dynamic difference filter */}
                <img 
                  src={duplicate_photo.image_url} 
                  alt="Duplicate" 
                  className="absolute inset-0 w-full h-full object-cover mix-blend-difference"
                  style={{ opacity: overlayOpacity / 100 }}
                />

                {/* Simulated ELA Artifact Highlights (Highlighted Bounding Boxes) */}
                <div 
                  className="absolute border-2 border-rose-500 bg-rose-500/20 rounded shadow-[0_0_12px_rgba(244,63,94,0.8)] animate-pulse"
                  style={{ top: '15%', left: '10%', width: '35%', height: '25%' }}
                >
                  <span className="absolute -top-5 left-0 bg-rose-600 text-white text-[8px] font-mono px-1.5 py-0.2 rounded">
                    CROPPED REGION (ΔE = 14.2)
                  </span>
                </div>

                <div 
                  className="absolute border-2 border-amber-400 bg-amber-400/20 rounded shadow-[0_0_12px_rgba(251,191,36,0.8)]"
                  style={{ top: '35%', right: '12%', width: '22%', height: '45%' }}
                >
                  <span className="absolute -top-5 left-0 bg-amber-600 text-white text-[8px] font-mono px-1.5 py-0.2 rounded">
                    SERVER RACK MATCH (pHash Dist = 0)
                  </span>
                </div>

                <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[9px] font-mono px-2 py-1 rounded backdrop-blur-xs">
                  Difference Blend Mode • Inverted Pixel Channel
                </div>
              </div>

              {/* Opacity Slider */}
              <div className="mt-3 flex items-center space-x-3 text-[11px]">
                <span className="text-slate-400">Blend Slider:</span>
                <input 
                  type="range" 
                  min="10" 
                  max="100" 
                  value={overlayOpacity}
                  onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                  className="flex-1 accent-amber-500 cursor-pointer"
                />
                <span className="font-mono text-slate-300 w-10 text-right">{overlayOpacity}%</span>
              </div>
            </div>

            <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-900">
              <strong>Forensic Analysis:</strong> Red/amber glowing bands highlight pixel difference coordinates. Zero-divergence regions in background confirm identical physical room and furniture geometry.
            </div>
          </div>
        )}

        {/* 3. WIPE SLIDER COMPARISON VIEW */}
        {viewMode === 'wipe_slider' && (
          <div className="space-y-3">
            <div className="bg-slate-900 rounded-xl p-3 text-slate-200 text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sky-400 flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Interactive Split Wipe Slider (Original ⟷ Reused)</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Drag slider to wipe
                </span>
              </div>

              {/* Wipe Viewport */}
              <div className="relative aspect-[4/3] rounded-lg overflow-hidden border border-slate-700 select-none cursor-ew-resize">
                {/* Background: Duplicate Image (Right Side) */}
                <img 
                  src={duplicate_photo.image_url} 
                  alt="Duplicate Photo" 
                  className="absolute inset-0 w-full h-full object-cover"
                />

                {/* Foreground: Original Image (Left Side) clipped by wipePosition */}
                <div 
                  className="absolute inset-0 overflow-hidden"
                  style={{ width: `${wipePosition}%` }}
                >
                  <img 
                    src={original_photo.image_url} 
                    alt="Original Photo" 
                    className="absolute inset-0 w-full h-full object-cover max-w-none"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <div className="absolute top-2 left-2 bg-slate-900/80 text-white text-[9px] font-bold px-2 py-0.5 rounded">
                    Original (Royal College)
                  </div>
                </div>

                {/* Vertical Divider Line */}
                <div 
                  className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] z-20 pointer-events-none"
                  style={{ left: `${wipePosition}%` }}
                >
                  <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-white text-slate-900 flex items-center justify-center shadow-md text-[10px] font-black font-sans">
                    ⇄
                  </div>
                </div>

                <div className="absolute top-2 right-2 bg-rose-600/90 text-white text-[9px] font-bold px-2 py-0.5 rounded z-10">
                  Reused (Apex Tech)
                </div>
              </div>

              {/* Slider Control */}
              <div className="mt-3 flex items-center space-x-3 text-[11px]">
                <span className="text-slate-400">Position:</span>
                <input 
                  type="range" 
                  min="5" 
                  max="95" 
                  value={wipePosition}
                  onChange={(e) => setWipePosition(Number(e.target.value))}
                  className="flex-1 accent-sky-500 cursor-pointer"
                />
                <span className="font-mono text-slate-300 w-10 text-right">{wipePosition}%</span>
              </div>
            </div>
          </div>
        )}

        {/* SIMILARITY SCORES BREAKDOWN CARD */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900">Perceptual & Semantic Similarity Metrics</span>
            <span className="text-[10px] font-bold text-rose-800 bg-rose-100 px-2 py-0.5 rounded border border-rose-300">
              {pairData.match_type}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            {/* Visual Similarity */}
            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase font-medium">Visual Similarity</div>
              <div className="text-base font-black text-rose-600">{pairData.similarity_score}%</div>
              <div className="text-[9px] text-slate-400 font-mono">Inverted Hamming</div>
            </div>

            {/* Hamming Distance */}
            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase font-medium">Hamming Distance</div>
              <div className="text-base font-black text-slate-900">{pairData.hamming_distance} / 64</div>
              <div className="text-[9px] text-emerald-600 font-mono">pHash Bit Delta</div>
            </div>

            {/* OpenCLIP Cosine */}
            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <div className="text-[10px] text-slate-500 uppercase font-medium">OpenCLIP Cosine</div>
              <div className="text-base font-black text-indigo-700">{pairData.clip_cosine}</div>
              <div className="text-[9px] text-slate-400 font-mono">ViT-B-32 Vector</div>
            </div>
          </div>

          <div className="text-[11px] text-slate-700 leading-snug bg-white p-2.5 rounded-lg border border-slate-200">
            <strong>Forensics Difference Summary:</strong> {pairData.difference_summary}
          </div>
        </div>

        {/* ACTION BUTTONS TO OPEN AFFECTED APPLICATIONS */}
        <div className="space-y-2 pt-2 border-t border-slate-200">
          <div className="text-xs font-bold text-slate-800">Open Affected Applications:</div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {/* Open Original App */}
            <button
              onClick={() => handleOpenApp(original_photo.application_no, original_photo.institution_name)}
              id="open-app-original-btn"
              className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-medium transition-all text-left flex items-center justify-between group shadow-2xs"
            >
              <div className="min-w-0 pr-1">
                <div className="text-[10px] text-slate-500 font-mono">Origin Application</div>
                <div className="font-bold truncate text-slate-900">{original_photo.institution_name}</div>
                <div className="text-[10px] text-sky-700 font-mono">{original_photo.application_no}</div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600 shrink-0" />
            </button>

            {/* Open Duplicate App */}
            <button
              onClick={() => handleOpenApp(duplicate_photo.application_no, duplicate_photo.institution_name)}
              id="open-app-duplicate-btn"
              className="p-2.5 rounded-xl border border-rose-300 bg-rose-50/50 hover:bg-rose-50 text-slate-800 text-xs font-medium transition-all text-left flex items-center justify-between group shadow-2xs"
            >
              <div className="min-w-0 pr-1">
                <div className="text-[10px] text-rose-600 font-mono font-bold">Current Flagged Dossier</div>
                <div className="font-bold truncate text-slate-900">{duplicate_photo.institution_name}</div>
                <div className="text-[10px] text-rose-700 font-mono">{duplicate_photo.application_no}</div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-rose-500 group-hover:text-rose-700 shrink-0" />
            </button>
          </div>

          {/* Jump to Evidence Lens */}
          <button
            onClick={() => onOpenEvidenceLens && onOpenEvidenceLens(pairData)}
            id="jump-to-evidence-lens-btn"
            className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2 cursor-pointer"
          >
            <FileText className="w-4 h-4 text-sky-400" />
            <span>Open Finding in Evidence Lens Regulatory Strip</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Dynamic Toast Feedback Banner */}
        {toastMsg && (
          <div className="bg-emerald-50 border border-emerald-300 text-emerald-950 px-3 py-2 rounded-xl text-xs flex items-center space-x-2 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

      </div>
    </div>
  );
}
