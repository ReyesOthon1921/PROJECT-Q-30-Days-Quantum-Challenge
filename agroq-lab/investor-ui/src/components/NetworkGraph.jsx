const nodes = [
  { id: "NC", x: 80, y: 55, label: "North Control" },
  { id: "CT", x: 210, y: 65, label: "Compost" },
  { id: "BZ", x: 90, y: 170, label: "Beneficial Zone" },
  { id: "CZ", x: 220, y: 175, label: "Calibration" },
  { id: "GW", x: 340, y: 115, label: "Gateway" },
];

const edges = [
  ["NC", "CT"],
  ["NC", "BZ"],
  ["CT", "CZ"],
  ["BZ", "CZ"],
  ["CT", "GW"],
  ["CZ", "GW"],
];

export default function NetworkGraph({ activeZone }) {
  const byId = Object.fromEntries(nodes.map((node) => [node.id, node]));
  return (
    <svg className="network-graph" viewBox="0 0 420 230" role="img">
      {edges.map(([from, to]) => (
        <line
          key={`${from}-${to}`}
          x1={byId[from].x}
          y1={byId[from].y}
          x2={byId[to].x}
          y2={byId[to].y}
          stroke="#355948"
          strokeWidth="3"
        />
      ))}
      {nodes.map((node) => {
        const highlighted =
          activeZone &&
          node.label.toLowerCase().includes(activeZone.name.split(" ")[0].toLowerCase());
        return (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={highlighted ? 20 : 16}
              fill={highlighted ? "#63f3a3" : "#173e2b"}
              stroke={highlighted ? "#d9ffea" : "#5f8f75"}
              strokeWidth="3"
            />
            <text
              x={node.x}
              y={node.y + 35}
              textAnchor="middle"
              className="graph-label"
            >
              {node.id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
