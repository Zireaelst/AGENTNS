import { useEffect, useState } from 'react';

const nodes = [
  { id: 'scout', label: 'SCOUT', x: 100, y: 80, color: '#34d399', desc: 'Detect' },
  { id: 'strategy', label: 'STRATEGY', x: 250, y: 40, color: '#818cf8', desc: 'Analyze' },
  { id: 'executor', label: 'EXECUTOR', x: 400, y: 80, color: '#fb923c', desc: 'Execute' },
  { id: 'ens', label: 'ENS', x: 175, y: 170, color: '#5b9aff', desc: 'Discover' },
  { id: 'axl', label: 'AXL', x: 325, y: 170, color: '#f472b6', desc: 'Relay' },
];

const edges = [
  { from: 'scout', to: 'strategy', delay: 0 },
  { from: 'strategy', to: 'executor', delay: 1 },
  { from: 'scout', to: 'ens', delay: 2 },
  { from: 'strategy', to: 'axl', delay: 0.5 },
  { from: 'executor', to: 'axl', delay: 1.5 },
  { from: 'ens', to: 'axl', delay: 2.5 },
];

export default function NetworkGraph() {
  const [activeEdge, setActiveEdge] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveEdge(prev => (prev + 1) % edges.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const getNode = (id) => nodes.find(n => n.id === id);

  return (
    <svg
      viewBox="0 0 500 220"
      className="w-full h-full"
      style={{ filter: 'drop-shadow(0 0 20px rgba(99, 102, 241, 0.1))' }}
    >
      {/* Grid pattern */}
      <defs>
        <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">
          <path d="M 25 0 L 0 0 0 25" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="500" height="220" fill="url(#grid)" />

      {/* Edges */}
      {edges.map((edge, i) => {
        const from = getNode(edge.from);
        const to = getNode(edge.to);
        const isActive = i === activeEdge;
        return (
          <g key={`edge-${i}`}>
            <line
              x1={from.x} y1={from.y}
              x2={to.x} y2={to.y}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1"
            />
            <line
              x1={from.x} y1={from.y}
              x2={to.x} y2={to.y}
              stroke={isActive ? from.color : 'rgba(255,255,255,0.06)'}
              strokeWidth={isActive ? '2' : '1'}
              strokeDasharray="6 4"
              style={{
                animation: isActive ? 'flowLine 1.5s linear infinite' : 'none',
                filter: isActive ? `drop-shadow(0 0 6px ${from.color})` : 'none',
                transition: 'stroke 0.5s ease',
              }}
            />
          </g>
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <g key={node.id}>
          <circle
            cx={node.x} cy={node.y} r="22"
            fill="none" stroke={node.color} strokeWidth="0.5" opacity="0.15"
          />
          <circle
            cx={node.x} cy={node.y} r="15"
            fill={`${node.color}10`} stroke={node.color} strokeWidth="1" opacity="0.7"
          />
          <circle
            cx={node.x} cy={node.y} r="4"
            fill={node.color}
            style={{ filter: `drop-shadow(0 0 4px ${node.color})` }}
          >
            <animate attributeName="r" values="3.5;5;3.5" dur="3s" repeatCount="indefinite" />
          </circle>
          <text
            x={node.x} y={node.y - 26}
            textAnchor="middle" fill={node.color}
            fontSize="9" fontFamily="'Geist Pixel', monospace" fontWeight="400"
            opacity="0.9"
          >
            {node.label}
          </text>
          <text
            x={node.x} y={node.y + 30}
            textAnchor="middle" fill="rgba(255,255,255,0.3)"
            fontSize="9" fontFamily="'Inter', sans-serif" fontWeight="400"
          >
            {node.desc}
          </text>
        </g>
      ))}
    </svg>
  );
}
