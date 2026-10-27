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
  const [, setThemeVersion] = React.useState(0);

  React.useEffect(() => {
    const handleThemeChange = () => setThemeVersion(v => v + 1);
    window.addEventListener('themechange', handleThemeChange);

    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.attributeName === 'data-theme') {
          setThemeVersion(v => v + 1);
        }
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    return () => {
      window.removeEventListener('themechange', handleThemeChange);
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (!containerRef.current || !subgraph) return;

    const computed = typeof window !== 'undefined' ? getComputedStyle(document.documentElement) : null;
    const graphNode = computed?.getPropertyValue('--graph-node').trim() || '#6FA8DC';
    const graphNodeStroke = computed?.getPropertyValue('--graph-node-stroke').trim() || '#3D6FA3';
    const graphRisk = computed?.getPropertyValue('--graph-risk').trim() || '#E58A82';
    const graphEdge = computed?.getPropertyValue('--graph-edge').trim() || '#8A94A0';
    const graphLabel = computed?.getPropertyValue('--graph-label').trim() || '#000000';
    const surface = computed?.getPropertyValue('--surface').trim() || '#FFFFFF';
    const border = computed?.getPropertyValue('--border').trim() || '#D5D9DE';
    const warningBg = computed?.getPropertyValue('--warning-bg').trim() || '#FFF1CC';

    // Convert nodes to vis.js format with vibrant, professional styles
    const nodes = new DataSet(
      (subgraph.nodes || []).map((node) => {
        let bgColor = graphNode;
        let borderColor = graphNodeStroke;
        let fontColor = graphLabel;

        if (node.group === 'faculty') {
          bgColor = graphRisk;
          borderColor = '#be123c';
        } else if (node.group === 'document') {
          bgColor = warningBg;
          borderColor = border;
        }

        return {
          id: node.id,
          label: node.label,
          color: {
            background: node.color || bgColor,
            border: borderColor,
            highlight: { background: graphRisk, border: '#be123c' },
          },
          shape: node.shape || (node.group === 'faculty' ? 'dot' : 'box'),
          size: node.size || 24,
          font: { color: fontColor, size: 11, face: 'Arial, sans-serif', bold: true },
          margin: 10,
          borderWidth: 1,
          shadow: { enabled: true, color: 'rgba(0,0,0,0.08)', size: 4, x: 1, y: 2 },
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
        font: { size: 9, color: graphLabel, background: surface, strokeWidth: 0 },
        color: { color: edge.color || graphEdge, highlight: graphRisk },
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

  return (
    <div className="flex flex-col h-full bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
      {/* Subgraph Header */}
      <div className="p-3.5 bg-[#F4F6F8] border-b border-[#D5D9DE] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-[#E8F1FB] text-[#000000] flex items-center justify-center border border-[#BBD4F0]">
            <NetworkIcon className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-[#000000]">
              Conflicting Subgraph Topology
            </h4>
            <p className="text-[10px] text-[#333333]">
              vis-network Force-Directed Multi-Institutional Map
            </p>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 bg-white rounded-[8px] p-1 border border-[#BFC5CC]">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded-[8px] text-[#000000] hover:bg-[#F1F3F5] transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded-[8px] text-[#000000] hover:bg-[#F1F3F5] transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded-[8px] text-[#000000] hover:bg-[#F1F3F5] transition-colors"
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
        className="flex-1 w-full min-h-[420px] bg-white cursor-grab active:cursor-grabbing"
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
