import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { 
  Network as NetworkIcon, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Layers, 
  Sparkles,
  Info,
  Maximize2
} from 'lucide-react';

/**
 * Force-Directed Cluster Graph Component:
 * - Institutions are NODES
 * - Shared photos are EDGES
 * Renders interactive network with vis-network, supporting click-to-inspect,
 * physics simulation, and smooth edge selection.
 */
export default function PhotoClusterGraph({ 
  graphData, 
  selectedPairId, 
  onSelectPair,
  highlightedNodeId = null 
}) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Convert nodes to vis.js format
    const nodes = new DataSet(
      (graphData.nodes || []).map((node) => {
        const isHighlighted = highlightedNodeId && node.id === highlightedNodeId;
        return {
          id: node.id,
          label: node.label,
          title: node.title,
          color: {
            background: isHighlighted ? '#f43f5e' : (node.color?.background || '#0284c7'),
            border: isHighlighted ? '#be123c' : (node.color?.border || '#0369a1'),
            highlight: {
              background: '#0ea5e9',
              border: '#0284c7',
            },
          },
          shape: node.shape || 'box',
          size: node.size || 26,
          font: {
            color: '#ffffff',
            size: 11,
            face: 'Inter, sans-serif',
            bold: true,
          },
          margin: 12,
          borderWidth: isHighlighted ? 3 : 2,
          shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.12)',
            size: 6,
            x: 2,
            y: 3,
          },
        };
      })
    );

    // Convert edges to vis.js format
    const edges = new DataSet(
      (graphData.edges || []).map((edge) => {
        const isSelected = edge.pairId === selectedPairId;
        return {
          id: edge.id,
          from: edge.from,
          to: edge.to,
          label: edge.label,
          pairId: edge.pairId,
          color: {
            color: isSelected ? '#f43f5e' : (edge.color?.color || '#e11d48'),
            highlight: '#f43f5e',
          },
          width: isSelected ? (edge.width || 3) + 2 : (edge.width || 2.5),
          dashes: edge.dashes || false,
          font: {
            size: 9.5,
            color: '#0f172a',
            background: isSelected ? '#ffe4e6' : '#ffffff',
            strokeWidth: 0,
            bold: true,
          },
          arrows: {
            to: { enabled: true, scaleFactor: 0.7 },
            from: { enabled: true, scaleFactor: 0.7 },
          },
          smooth: { type: 'curvedCW', roundness: 0.15 },
        };
      })
    );

    const options = {
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -70,
          centralGravity: 0.008,
          springLength: 170,
          springConstant: 0.06,
          damping: 0.45,
        },
        stabilization: { iterations: 140 },
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        tooltipDelay: 150,
      },
      nodes: {
        scaling: { min: 16, max: 36 },
      },
    };

    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    // Handle Edge or Node selection
    network.on('click', (params) => {
      if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edgeObj = graphData.edges.find((e) => e.id === edgeId);
        if (edgeObj && edgeObj.pairId && onSelectPair) {
          onSelectPair(edgeObj.pairId);
          return;
        }
      }

      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const connectedEdge = graphData.edges.find((e) => e.from === nodeId || e.to === nodeId);
        if (connectedEdge && connectedEdge.pairId && onSelectPair) {
          onSelectPair(connectedEdge.pairId);
        }
      }
    });

    return () => {
      if (network) network.destroy();
    };
  }, [graphData, selectedPairId, highlightedNodeId]);

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
    networkRef.current.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Graph Toolbar Header */}
      <div className="px-4 py-3 bg-slate-900 text-slate-100 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-400/30">
            <NetworkIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-100 flex items-center space-x-2">
              <span>National Photo Cluster Topology</span>
              <span className="text-[10px] bg-slate-800 text-amber-300 px-2 py-0.5 rounded border border-slate-700 font-mono">
                Nodes = Institutions • Edges = Reused Photos
              </span>
            </h3>
            <p className="text-[10px] text-slate-400">
              Interactive force-directed cluster graph. Click any edge or institution to inspect comparison.
            </p>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 bg-slate-800 rounded-lg p-1 border border-slate-700">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Fit Graph to Viewport"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Graph Canvas Mount */}
      <div 
        ref={containerRef} 
        id="photo-cluster-graph-canvas"
        className="flex-1 w-full min-h-[500px] bg-slate-50 cursor-grab active:cursor-grabbing relative"
      />

      {/* Interactive Legend & Stats Footer */}
      <div className="px-4 py-3 bg-white border-t border-slate-200 text-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="text-slate-400 uppercase font-bold text-[10px]">Legend:</span>
          
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-600 inline-block" />
            <span className="text-slate-700 font-medium">Applicant Institution</span>
          </span>

          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-600 inline-block" />
            <span className="text-slate-700 font-medium">Re-use Counterpart</span>
          </span>

          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-purple-600 inline-block" />
            <span className="text-slate-700 font-medium">Cluster B Colleges</span>
          </span>

          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-600 inline-block" />
            <span className="text-slate-700 font-medium">Clean / Verified</span>
          </span>
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <span>Edge = Shared Infrastructure Photo</span>
        </div>
      </div>
    </div>
  );
}
