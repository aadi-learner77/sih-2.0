import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { 
  Network as NetworkIcon, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  X,
  Info
} from 'lucide-react';

/**
 * Conflicting Subgraph Network Component using vis-network:
 * Clean, readable force-directed graph with high contrast labels in both themes.
 */
export default function ConflictingSubgraphNetwork({ 
  subgraph, 
  activeFindingTitle = null 
}) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [, setThemeVersion] = useState(0);
  const [selectedNodeData, setSelectedNodeData] = useState(null);

  useEffect(() => {
    const handleThemeChange = () => setThemeVersion(v => v + 1);
    window.addEventListener('themechange', handleThemeChange);

    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.attributeName === 'data-theme' || m.attributeName === 'class') {
          setThemeVersion(v => v + 1);
        }
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class'] });

    return () => {
      window.removeEventListener('themechange', handleThemeChange);
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    setSelectedNodeData(null);

    if (!containerRef.current || !subgraph || (!subgraph.nodes?.length && !subgraph.edges?.length)) {
      return;
    }

    const isDark = document.documentElement.classList.contains('dark') || 
                   document.documentElement.getAttribute('data-theme') === 'dark';

    // Map each node type with high-contrast text and solid borders
    const nodes = new DataSet(
      (subgraph.nodes || []).map((node) => {
        const rawType = (node.type || node.group || '').toUpperCase();
        let bgColor = isDark ? '#162142' : '#E8EEFF';
        let borderColor = isDark ? '#3B6BFF' : '#1F4BFF';
        let fontColor = isDark ? '#FFFFFF' : '#0F1B33';
        let shape = 'box';
        let size = 26;

        switch (rawType) {
          case 'FACULTY':
            bgColor = isDark ? '#4C0519' : '#FFE4E6';
            borderColor = '#E11D48';
            fontColor = isDark ? '#FFE4E6' : '#9F1239';
            shape = 'dot';
            size = 28;
            break;
          case 'INSTITUTION':
            bgColor = isDark ? '#082F49' : '#E0F2FE';
            borderColor = '#0284C7';
            fontColor = isDark ? '#E0F2FE' : '#075985';
            shape = 'box';
            size = 32;
            break;
          case 'DOCUMENT':
            bgColor = isDark ? '#451A03' : '#FEF3C7';
            borderColor = '#D97706';
            fontColor = isDark ? '#FEF3C7' : '#92400E';
            shape = 'box';
            size = 24;
            break;
          default:
            bgColor = isDark ? '#1E293B' : '#F1F5F9';
            borderColor = isDark ? '#475569' : '#94A3B8';
            fontColor = isDark ? '#F8FAFC' : '#0F172A';
            shape = 'box';
            size = 24;
            break;
        }

        const displayName = node.label || node.name || node.doc_number || node.id || 'Node';

        return {
          id: node.id,
          label: displayName,
          rawNode: node,
          color: {
            background: node.color || bgColor,
            border: borderColor,
            highlight: { 
              background: '#FEE2E2', 
              border: '#DC2626' 
            },
          },
          shape,
          size,
          font: { 
            color: fontColor, 
            size: 13, 
            face: 'Inter, system-ui, sans-serif', 
            bold: true 
          },
          margin: 10,
          borderWidth: 2,
          shadow: { enabled: false },
        };
      })
    );

    const edges = new DataSet(
      (subgraph.edges || []).map((edge, idx) => {
        const fromId = edge.from || edge.source;
        const toId = edge.to || edge.target;
        const labelText = edge.label || edge.relation || edge.conflict_type || '';
        const isConflict = edge.conflict || edge.is_conflict || edge.relation === 'employs';

        return {
          id: edge.id || `edge-${idx}`,
          from: fromId,
          to: toId,
          label: labelText,
          color: isConflict ? '#DC2626' : (isDark ? '#64748B' : '#94A3B8'),
          width: isConflict ? 3 : 1.5,
          dashes: isConflict ? [5, 5] : false,
          arrows: {
            to: { enabled: true, scaleFactor: 0.8 },
          },
          font: {
            size: 11,
            color: isConflict ? (isDark ? '#FCA5A5' : '#B91C1C') : (isDark ? '#CBD5E1' : '#475569'),
            strokeWidth: 2,
            strokeColor: isDark ? '#0E1730' : '#FFFFFF',
            face: 'Inter, system-ui, sans-serif',
          },
          smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.3,
          },
        };
      })
    );

    const options = {
      nodes: {
        borderWidth: 2,
      },
      edges: {
        selectionWidth: 3,
      },
      physics: {
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -70,
          centralGravity: 0.015,
          springLength: 140,
          springConstant: 0.08,
          damping: 0.4,
        },
        stabilization: {
          iterations: 120,
          updateInterval: 25,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        navigationButtons: false,
      },
    };

    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    network.on('click', (params) => {
      if (params.nodes && params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const clickedNode = nodes.get(nodeId);
        if (clickedNode) {
          setSelectedNodeData(clickedNode.rawNode || clickedNode);
        }
      } else {
        setSelectedNodeData(null);
      }
    });

    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, [subgraph]);

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.25 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
    }
  };

  const nodesCount = subgraph?.nodes?.length || 0;
  const edgesCount = subgraph?.edges?.length || 0;

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-xs relative">
      {/* Top Toolbar without duplicated heading */}
      <div className="px-4 py-2.5 border-b border-border bg-surface-2 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs text-text-muted">
          <NetworkIcon className="w-4 h-4 text-primary" />
          <span className="font-semibold text-text">{nodesCount} Nodes, {edgesCount} Edges</span>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 bg-surface rounded-lg p-0.5 border border-border">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            title="Zoom In"
            type="button"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            title="Zoom Out"
            type="button"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
            title="Fit to Screen"
            type="button"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Vis Canvas */}
      <div 
        ref={containerRef} 
        className="w-full h-[460px] bg-bg/40 cursor-grab active:cursor-grabbing" 
      />

      {/* Node Inspector Drawer */}
      {selectedNodeData && (
        <div className="absolute bottom-3 left-3 right-3 bg-surface border border-border rounded-xl p-3 shadow-xl z-20 text-xs text-text animate-fadeIn">
          <div className="flex items-center justify-between pb-1.5 border-b border-border font-bold">
            <span className="flex items-center space-x-1.5">
              <Info className="w-4 h-4 text-primary" />
              <span>{selectedNodeData.label || selectedNodeData.name || selectedNodeData.id}</span>
            </span>
            <button 
              onClick={() => setSelectedNodeData(null)}
              className="text-text-muted hover:text-text cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="pt-2 text-[11px] text-text-muted">
            {selectedNodeData.institution && <div>Institution: <strong className="text-text">{selectedNodeData.institution}</strong></div>}
            {selectedNodeData.role && <div>Designation: <strong className="text-text">{selectedNodeData.role}</strong></div>}
            {selectedNodeData.conflict_details && <div className="text-rose-600 dark:text-rose-400 mt-1">{selectedNodeData.conflict_details}</div>}
          </div>
        </div>
      )}
    </div>
  );
}
