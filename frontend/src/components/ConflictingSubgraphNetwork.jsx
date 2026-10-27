import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Network as NetworkIcon, AlertTriangle, ShieldAlert, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

/**
 * Conflicting Subgraph Network Component using vis-network:
 * Renders cross-institutional relationship conflicts (e.g. Ghost Faculty dual employment,
 * shared document numbers, or land parcel overlaps) with interactive force-directed physics.
 */
export default function ConflictingSubgraphNetwork({ subgraph }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !subgraph) return;

    // Convert nodes to vis.js format with vibrant, professional styles
    const nodes = new DataSet(
      (subgraph.nodes || []).map((node) => {
        let bgColor = '#0284c7';
        let borderColor = '#0369a1';
        let fontColor = '#ffffff';

        if (node.group === 'faculty') {
          bgColor = '#e11d48';
          borderColor = '#be123c';
        } else if (node.group === 'document') {
          bgColor = '#d97706';
          borderColor = '#b45309';
        }

        return {
          id: node.id,
          label: node.label,
          color: {
            background: node.color || bgColor,
            border: borderColor,
            highlight: { background: '#f43f5e', border: '#be123c' },
          },
          shape: node.shape || (node.group === 'faculty' ? 'dot' : 'box'),
          size: node.size || 24,
          font: { color: fontColor, size: 11, face: 'Inter, sans-serif', bold: true },
          margin: 10,
          borderWidth: 2,
          shadow: { enabled: true, color: 'rgba(0,0,0,0.1)', size: 4, x: 2, y: 2 },
        };
      })
    );

    // Convert edges to vis.js format
    const edges = new DataSet(
      (subgraph.edges || []).map((edge, idx) => ({
        id: `e-${idx}`,
        from: edge.from,
        to: edge.to,
        label: edge.label,
        font: { size: 9, color: '#334155', background: '#ffffff', strokeWidth: 0 },
        color: { color: edge.color || '#e11d48', highlight: '#f43f5e' },
        dashes: edge.dashes || false,
        width: edge.width || 2,
        arrows: { to: { enabled: true, scaleFactor: 0.8 } },
        smooth: { type: 'curvedCW', roundness: 0.2 },
      }))
    );

    const options = {
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -50,
          centralGravity: 0.01,
          springLength: 130,
          springConstant: 0.08,
          damping: 0.4,
        },
        stabilization: { iterations: 120 },
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
        dragNodes: true,
      },
      nodes: {
        scaling: { min: 14, max: 32 },
      },
    };

    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    return () => {
      if (network) network.destroy();
    };
  }, [subgraph]);

  const handleZoomIn = () => {
    if (!networkRef.current) return;
    const scale = networkRef.current.getScale();
    networkRef.current.moveTo({ scale: scale * 1.25 });
  };

  const handleZoomOut = () => {
    if (!networkRef.current) return;
    const scale = networkRef.current.getScale();
    networkRef.current.moveTo({ scale: scale * 0.8 });
  };

  const handleFit = () => {
    if (!networkRef.current) return;
    networkRef.current.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
  };
  if (!subgraph) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500">
        <NetworkIcon className="w-10 h-10 mx-auto text-slate-400 mb-2" />
        <p className="text-sm font-medium">No conflicting subgraph topology available for this finding.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
      {/* Subgraph Header */}
      <div className="p-3.5 bg-white border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
            <NetworkIcon className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900">
              Conflicting Subgraph Topology
            </h4>
            <p className="text-[10px] text-slate-500">
              vis-network Force-Directed Multi-Institutional Map
            </p>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs"
            title="Fit Graph"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mandatory Statutory Advisory Banner */}
      <div className="bg-rose-50/80 px-4 py-2 border-b border-rose-200 text-[11px] text-rose-900 flex items-center space-x-2">
        <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
        <span className="font-bold">
          Indicator for review: Conflicting multi-college relationship pattern detected.
        </span>
      </div>

      {/* Vis Network Canvas Mount */}
      <div 
        ref={containerRef} 
        className="flex-1 w-full min-h-[420px] bg-slate-900/5 cursor-grab active:cursor-grabbing"
      />

      {/* Legend & Details Footer */}
      <div className="p-3 bg-white border-t border-slate-200 text-xs space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-600 inline-block" />
              <span className="text-slate-700 font-medium">Institution</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block" />
              <span className="text-slate-700 font-medium">Faculty Member</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
              <span className="text-slate-700 font-medium">Statutory Roster</span>
            </span>
          </div>
          <span className="text-[10px] text-slate-400">Interactive: Pan & Drag Nodes</span>
        </div>

        {subgraph.summary && (
          <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-200">
            <strong>Conflict Summary:</strong> {subgraph.summary}
          </p>
        )}
      </div>
    </div>
  );
}
