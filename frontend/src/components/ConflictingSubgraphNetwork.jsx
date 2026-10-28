import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { 
  Network as NetworkIcon, 
  ShieldAlert, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  Building2,
  Users,
  FileText,
  FlaskConical,
  GraduationCap,
  MapPin,
  X,
  Info
} from 'lucide-react';

/**
 * Conflicting Subgraph Network Component using vis-network:
 * Renders cross-institutional relationship conflicts (e.g. Ghost Faculty dual employment,
 * shared document numbers, or land parcel overlaps) with interactive force-directed physics.
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
    // Reset selected node when subgraph changes
    setSelectedNodeData(null);

    if (!containerRef.current || !subgraph || (!subgraph.nodes?.length && !subgraph.edges?.length)) {
      return;
    }

    const computed = typeof window !== 'undefined' ? getComputedStyle(document.documentElement) : null;
    const graphNode = computed?.getPropertyValue('--graph-node').trim() || '#E0F2FE';
    const graphNodeStroke = computed?.getPropertyValue('--graph-node-stroke').trim() || '#0284C7';
    const graphRisk = computed?.getPropertyValue('--graph-risk').trim() || '#FFE4E6';
    const graphEdge = computed?.getPropertyValue('--graph-edge').trim() || '#64748B';
    const graphLabel = computed?.getPropertyValue('--graph-label').trim() || '#0F172A';
    const surface = computed?.getPropertyValue('--surface').trim() || '#FFFFFF';

    // Map each node type to specialized visual token
    const nodes = new DataSet(
      (subgraph.nodes || []).map((node) => {
        const rawType = (node.type || node.group || '').toUpperCase();
        let bgColor = graphNode;
        let borderColor = graphNodeStroke;
        let fontColor = graphLabel;
        let shape = 'box';
        let size = 24;

        switch (rawType) {
          case 'FACULTY':
            bgColor = graphRisk;
            borderColor = '#E11D48';
            fontColor = '#9F1239';
            shape = 'dot';
            size = 28;
            break;
          case 'INSTITUTION':
            bgColor = '#E0F2FE';
            borderColor = '#0284C7';
            fontColor = '#075985';
            shape = 'box';
            size = 32;
            break;
          case 'DOCUMENT':
            bgColor = '#FEF3C7';
            borderColor = '#D97706';
            fontColor = '#92400E';
            shape = 'box';
            size = 22;
            break;
          case 'LAB':
            bgColor = '#DCFCE7';
            borderColor = '#16A34A';
            fontColor = '#166534';
            shape = 'ellipse';
            size = 24;
            break;
          case 'PROGRAMME':
            bgColor = '#EDE9FE';
            borderColor = '#7C3AED';
            fontColor = '#5B21B6';
            shape = 'box';
            size = 22;
            break;
          case 'BUILDING':
            bgColor = '#CFFAFE';
            borderColor = '#0891B2';
            fontColor = '#155E75';
            shape = 'box';
            size = 22;
            break;
          case 'LOCATION':
            bgColor = '#F3E8FF';
            borderColor = '#9333EA';
            fontColor = '#6B21A8';
            shape = 'dot';
            size = 20;
            break;
          case 'ISSUER':
            bgColor = '#FFEDD5';
            borderColor = '#EA580C';
            fontColor = '#9A3412';
            shape = 'box';
            size = 22;
            break;
          default:
            bgColor = '#F1F5F9';
            borderColor = '#94A3B8';
            fontColor = '#334155';
            shape = 'ellipse';
            size = 20;
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
            size: 11, 
            face: 'Inter, system-ui, sans-serif', 
            bold: true 
          },
          margin: 9,
          borderWidth: 2,
          shadow: { enabled: true, color: 'rgba(0,0,0,0.06)', size: 4, x: 1, y: 2 },
        };
      })
    );

    // Convert edges to vis.js format (supporting both from/to and source/target)
    const edges = new DataSet(
      (subgraph.edges || []).map((edge, idx) => {
        const fromId = edge.from || edge.source;
        const toId = edge.to || edge.target;
        const labelText = edge.label || edge.relation || edge.conflict_type || '';
        const isConflict = edge.conflict || edge.is_conflict || edge.relation === 'employs';

        return {
          id: `e-${idx}`,
          from: fromId,
          to: toId,
          label: labelText,
          font: { 
            size: 9, 
            color: isConflict ? '#BE123C' : graphLabel, 
            background: surface, 
            strokeWidth: 0,
            bold: isConflict 
          },
          color: { 
            color: isConflict ? '#E11D48' : (edge.color || graphEdge), 
            highlight: '#DC2626' 
          },
          dashes: edge.dashes || (!isConflict && edge.relation !== 'employs'),
          width: isConflict ? 2.5 : (edge.width || 1.8),
          arrows: { to: { enabled: true, scaleFactor: 0.8 } },
          smooth: { type: 'curvedCW', roundness: 0.2 },
        };
      })
    );

    const options = {
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -60,
          centralGravity: 0.015,
          springLength: 140,
          springConstant: 0.07,
          damping: 0.45,
        },
        stabilization: { iterations: 140 },
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        selectConnectedEdges: true,
      },
      nodes: {
        scaling: { min: 14, max: 34 },
      },
    };

    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    // Handle node selection
    network.on('selectNode', (params) => {
      if (params.nodes && params.nodes.length > 0) {
        const clickedId = params.nodes[0];
        const originalNode = (subgraph.nodes || []).find(n => n.id === clickedId);
        setSelectedNodeData(originalNode || { id: clickedId });
      }
    });

    network.on('deselectNode', () => {
      setSelectedNodeData(null);
    });

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

  const getNodeIcon = (type) => {
    const t = (type || '').toUpperCase();
    switch (t) {
      case 'INSTITUTION': return <Building2 className="w-3.5 h-3.5 text-sky-600" />;
      case 'FACULTY': return <Users className="w-3.5 h-3.5 text-rose-600" />;
      case 'DOCUMENT': return <FileText className="w-3.5 h-3.5 text-amber-600" />;
      case 'LAB': return <FlaskConical className="w-3.5 h-3.5 text-emerald-600" />;
      case 'PROGRAMME': return <GraduationCap className="w-3.5 h-3.5 text-indigo-600" />;
      case 'LOCATION': return <MapPin className="w-3.5 h-3.5 text-purple-600" />;
      case 'BUILDING': return <Building2 className="w-3.5 h-3.5 text-cyan-600" />;
      default: return <Info className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  if (!subgraph || (!subgraph.nodes?.length && !subgraph.edges?.length)) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 flex flex-col items-center justify-center min-h-[420px]">
        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
          <NetworkIcon className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-800 mb-1">No Conflicting Subgraph Selected</h4>
        <p className="text-xs text-slate-500 max-w-sm">
          Select an indicator from the review list to load and inspect its force-directed inter-institutional topology map.
        </p>
      </div>
    );
  }

  const nodesCount = subgraph.nodes?.length || 0;
  const edgesCount = subgraph.edges?.length || 0;

  return (
    <div className="flex flex-col h-full bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
      {/* Subgraph Header */}
      <div className="p-3.5 bg-slate-100/80 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-200 shrink-0">
            <NetworkIcon className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h4 className="text-xs font-bold text-slate-900 truncate">
              {activeFindingTitle || 'Conflicting Subgraph Topology'}
            </h4>
            <p className="text-[10px] text-slate-500 flex items-center space-x-2">
              <span>vis-network Force-Directed Engine</span>
              <span>•</span>
              <span className="font-mono text-slate-700 font-semibold">{nodesCount} Nodes, {edgesCount} Edges</span>
            </p>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 bg-white rounded-lg p-1 border border-slate-200 shadow-2xs shrink-0">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Zoom In"
            type="button"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Zoom Out"
            type="button"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Reset Fit"
            type="button"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mandatory Statutory Advisory Banner */}
      <div className="bg-rose-50/80 px-4 py-2 border-b border-rose-200 text-[11px] text-rose-900 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
          <span className="font-semibold">
            Indicator for review: Conflicting multi-college relationship pattern detected.
          </span>
        </div>
        <span className="text-[10px] text-rose-700 font-mono font-medium hidden sm:inline">
          Advisory Finding
        </span>
      </div>

      {/* Vis Network Canvas Mount */}
      <div 
        ref={containerRef} 
        className="flex-1 w-full min-h-[380px] bg-white cursor-grab active:cursor-grabbing relative"
      />

      {/* Interactive Node Inspector Drawer / Card */}
      {selectedNodeData && (
        <div className="p-3 bg-sky-50/80 border-t border-sky-200 text-xs transition-all">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1.5">
              {getNodeIcon(selectedNodeData.type)}
              <span className="font-bold text-slate-900">
                {selectedNodeData.label || selectedNodeData.name || selectedNodeData.id}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-white border border-sky-200 text-sky-800">
                {selectedNodeData.type || 'Entity'}
              </span>
            </div>
            <button
              onClick={() => setSelectedNodeData(null)}
              className="text-slate-400 hover:text-slate-700 p-0.5 rounded"
              title="Close inspector"
              type="button"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
            <div>
              <span className="text-slate-500 block text-[10px]">Entity ID:</span>
              <span className="font-mono text-slate-800 font-semibold">{selectedNodeData.id}</span>
            </div>
            {selectedNodeData.aicte_id && (
              <div>
                <span className="text-slate-500 block text-[10px]">AICTE Permanent ID:</span>
                <span className="font-mono text-slate-800">{selectedNodeData.aicte_id}</span>
              </div>
            )}
            {selectedNodeData.city && (
              <div>
                <span className="text-slate-500 block text-[10px]">Location:</span>
                <span className="text-slate-800">{selectedNodeData.city}, {selectedNodeData.state || ''}</span>
              </div>
            )}
            {selectedNodeData.pan_masked && (
              <div>
                <span className="text-slate-500 block text-[10px]">Masked PAN:</span>
                <span className="font-mono text-slate-800">{selectedNodeData.pan_masked}</span>
              </div>
            )}
            {selectedNodeData.aadhaar_masked && (
              <div>
                <span className="text-slate-500 block text-[10px]">Masked Aadhaar:</span>
                <span className="font-mono text-slate-800">{selectedNodeData.aadhaar_masked}</span>
              </div>
            )}
            {selectedNodeData.designation && (
              <div>
                <span className="text-slate-500 block text-[10px]">Designation:</span>
                <span className="text-slate-800">{selectedNodeData.designation}</span>
              </div>
            )}
            {selectedNodeData.approved_intake && (
              <div>
                <span className="text-slate-500 block text-[10px]">Approved Intake:</span>
                <span className="text-slate-800">{selectedNodeData.approved_intake} students</span>
              </div>
            )}
            {selectedNodeData.total_built_up_area_sqm && (
              <div>
                <span className="text-slate-500 block text-[10px]">Built-Up Area:</span>
                <span className="text-slate-800">{selectedNodeData.total_built_up_area_sqm} m²</span>
              </div>
            )}
            {selectedNodeData.survey_numbers && (
              <div>
                <span className="text-slate-500 block text-[10px]">Land Survey Number:</span>
                <span className="font-mono text-slate-800">{selectedNodeData.survey_numbers}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Legend & Summary Footer */}
      <div className="p-3 bg-white border-t border-slate-200 text-xs space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded bg-sky-100 border border-sky-500 inline-block" />
              <span className="text-slate-700 font-medium">Institution</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-100 border border-rose-500 inline-block" />
              <span className="text-slate-700 font-medium">Faculty</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded bg-amber-100 border border-amber-500 inline-block" />
              <span className="text-slate-700 font-medium">Document</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-100 border border-emerald-500 inline-block" />
              <span className="text-slate-700 font-medium">Lab / Workshop</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded bg-purple-100 border border-purple-500 inline-block" />
              <span className="text-slate-700 font-medium">Location</span>
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium">Pan, zoom & click nodes to inspect</span>
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
