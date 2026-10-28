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
    if (!containerRef.current || !graphData) return;

    const computed = typeof window !== 'undefined' ? getComputedStyle(document.documentElement) : null;
    const graphNode = computed?.getPropertyValue('--graph-node').trim() || '#6FA8DC';
    const graphNodeStroke = computed?.getPropertyValue('--graph-node-stroke').trim() || '#3D6FA3';
    const graphRisk = computed?.getPropertyValue('--graph-risk').trim() || '#E58A82';
    const graphEdge = computed?.getPropertyValue('--graph-edge').trim() || '#8A94A0';
    const graphLabel = computed?.getPropertyValue('--graph-label').trim() || '#000000';
    const surface = computed?.getPropertyValue('--surface').trim() || '#FFFFFF';
    const warningBg = computed?.getPropertyValue('--warning-bg').trim() || '#FFF1CC';

    // Convert nodes to vis.js format
    const nodes = new DataSet(
      (graphData.nodes || []).map((node) => {
        const isHighlighted = highlightedNodeId && node.id === highlightedNodeId;
        return {
          id: node.id,
          label: node.label,
          title: node.title,
          color: {
            background: isHighlighted ? graphRisk : graphNode,
            border: isHighlighted ? '#be123c' : graphNodeStroke,
            highlight: {
              background: graphRisk,
              border: '#be123c',
            },
          },
          shape: node.shape || 'box',
          size: node.size ? Math.max(node.size, 28) : 32,
          font: {
            color: graphLabel,
            size: 13,
            face: 'Inter, system-ui, sans-serif',
            bold: true,
          },
          margin: 14,
          borderWidth: 2,
          shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.1)',
            size: 5,
            x: 1,
            y: 2,
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
            color: isSelected ? graphRisk : graphEdge,
            highlight: graphRisk,
          },
          width: isSelected ? 4 : 2.5,
          dashes: edge.dashes || false,
          font: {
            size: 11,
            color: graphLabel,
            background: isSelected ? warningBg : surface,
            strokeWidth: 0,
            bold: true,
            face: 'Inter, system-ui, sans-serif',
          },
          arrows: {
            to: { enabled: true, scaleFactor: 0.8 },
            from: { enabled: true, scaleFactor: 0.8 },
          },
          smooth: { type: 'curvedCW', roundness: 0.15 },
        };
      })
    );

    const options = {
      autoResize: true,
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -130,
          centralGravity: 0.006,
          springLength: 210,
          springConstant: 0.05,
          damping: 0.5,
        },
        stabilization: {
          enabled: true,
          iterations: 150,
          updateInterval: 25,
        },
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        tooltipDelay: 150,
      },
      nodes: {
        scaling: { min: 20, max: 40 },
      },
    };

    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    // Automatically zoom to fit once layout settles
    network.once('stabilizationIterationsDone', () => {
      network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    });
    network.once('stabilized', () => {
      network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    });

    const initTimer = setTimeout(() => {
      if (networkRef.current) {
        networkRef.current.fit();
      }
    }, 350);

    const resizeObserver = new ResizeObserver(() => {
      if (networkRef.current) {
        networkRef.current.fit();
      }
    });
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

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
      clearTimeout(initTimer);
      resizeObserver.disconnect();
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
      <div className="px-4 py-3 bg-[#F4F6F8] text-[#000000] border-b border-[#D5D9DE] flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#E8F1FB] text-[#000000] flex items-center justify-center border border-[#BBD4F0]">
            <NetworkIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#000000] flex items-center space-x-2">
              <span>National Photo Cluster Topology</span>
              <span className="text-[10px] bg-[#E8F1FB] text-[#000000] px-2 py-0.5 rounded border border-[#BBD4F0]">
                Nodes = Institutions • Edges = Reused Photos
              </span>
            </h3>
            <p className="text-[10px] text-[#333333]">
              Interactive force-directed cluster graph. Click any edge or institution to inspect comparison.
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
        className="w-full h-[540px] min-h-[520px] bg-white cursor-grab active:cursor-grabbing relative"
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
