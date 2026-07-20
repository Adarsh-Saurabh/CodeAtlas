import React, { useMemo, memo } from 'react';
import ReactFlow, { Background, Controls, MarkerType, Handle, Position } from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';

const nodeWidth = 300;
const nodeHeight = 120;

const getLayoutedElements = (nodes, edges) => {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', marginx: 60, marginy: 60, ranksep: 120, nodesep: 50 });

  nodes.forEach((node) => {
    const isExpanded = node.data.isActive && node.data.internal_steps?.length > 0;
    const h = isExpanded ? 120 + node.data.internal_steps.length * 36 : nodeHeight;
    g.setNode(node.id, { width: nodeWidth, height: h });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  nodes.forEach((node) => {
    const pos = g.node(node.id);
    node.position = { x: pos.x - nodeWidth / 2, y: pos.y - (pos.height || nodeHeight) / 2 };
  });

  return { nodes, edges };
};

// Custom Node — defined OUTSIDE the component to avoid re-creation
const LayerNode = memo(({ data }) => {
  const isActive = data.isActive;
  const isPast = data.isPast;
  const borderColor = isActive ? (data.color || '#2ed573') : isPast ? 'rgba(46,213,115,0.4)' : 'rgba(255,255,255,0.08)';
  
  return (
    <div
      className="layer-node"
      style={{
        borderColor,
        boxShadow: isActive ? `0 0 24px ${data.color || '#2ed573'}55` : 'none',
        transform: isActive ? 'scale(1.04)' : 'scale(1)',
        opacity: isPast || isActive ? 1 : 0.55,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: borderColor, width: 8, height: 8 }} />
      
      <div className="layer-node-header" style={{ borderBottomColor: borderColor }}>
        <span className="layer-type-badge" style={{ background: data.color || '#747d8c' }}>{data.label}</span>
        <span className="layer-node-title">{data.title}</span>
      </div>
      
      {data.args && <div className="layer-node-args">{data.args}</div>}
      
      {/* Show internal steps when active */}
      {isActive && data.internal_steps && data.internal_steps.length > 0 && (
        <div className="layer-internal-steps">
          {data.internal_steps.map((s, i) => (
            <div key={i} className="internal-step">
              <span className="step-dot" style={{ background: data.color || '#2ed573' }}></span>
              <span className="step-label">{s.step}</span>
            </div>
          ))}
        </div>
      )}
      
      <Handle type="source" position={Position.Right} style={{ background: borderColor, width: 8, height: 8 }} />
    </div>
  );
});

const nodeTypes = { layerNode: LayerNode };

export default function GraphVisualizer({ graphData, activeNodeIndex }) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    if (!graphData || !graphData.nodes) return { nodes: [], edges: [] };

    const rfNodes = graphData.nodes.map((n, idx) => ({
      id: n.id,
      type: 'layerNode',
      data: {
        ...n.data,
        isActive: idx === activeNodeIndex,
        isPast: idx < activeNodeIndex,
      },
      position: { x: 0, y: 0 },
    }));

    const rfEdges = graphData.edges.map((e) => {
      const sourceIdx = graphData.nodes.findIndex(n => n.id === e.source);
      const isTraversed = activeNodeIndex !== null && sourceIdx !== -1 && sourceIdx < activeNodeIndex;
      const isCurrentEdge = activeNodeIndex !== null && sourceIdx !== -1 && sourceIdx === activeNodeIndex - 1;

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: isCurrentEdge,
        style: {
          stroke: isTraversed || isCurrentEdge ? '#2ed573' : '#333',
          strokeWidth: isCurrentEdge ? 4 : isTraversed ? 3 : 2,
          transition: 'stroke 0.4s ease, stroke-width 0.4s ease',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isTraversed || isCurrentEdge ? '#2ed573' : '#555',
          width: 20,
          height: 20,
        },
      };
    });

    return getLayoutedElements(rfNodes, rfEdges);
  }, [graphData, activeNodeIndex]);

  if (!graphData) return null;

  return (
    <ReactFlow
      nodes={layoutedNodes}
      edges={layoutedEdges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.3 }}
      className="dark-flow"
      minZoom={0.2}
      maxZoom={2}
    >
      <Background color="#1e272e" gap={20} size={1} />
      <Controls position="bottom-left" />
    </ReactFlow>
  );
}
