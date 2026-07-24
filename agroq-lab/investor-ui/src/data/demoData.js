export const scenarios = {
  baseline: {
    label: "Baseline Operations",
    description: "Stable manual and virtual-sensor conditions across the digital acre.",
    moistureShift: 0,
    temperatureShift: 0,
    healthShift: 0,
  },
  drought: {
    label: "Drought Stress",
    description: "Declining soil moisture increases inspection and sampling priority.",
    moistureShift: -9,
    temperatureShift: 4,
    healthShift: -7,
  },
  drift: {
    label: "Sensor Drift",
    description: "One virtual node diverges from manual reference measurements.",
    moistureShift: -2,
    temperatureShift: 1,
    healthShift: -4,
  },
  pest: {
    label: "Pest Pressure",
    description: "Synthetic scouting indicators trigger crop-health inspections.",
    moistureShift: -1,
    temperatureShift: 2,
    healthShift: -15,
  },
  outage: {
    label: "Offline Gateway",
    description: "The local gateway remains operational while cloud connectivity is unavailable.",
    moistureShift: 0,
    temperatureShift: 0,
    healthShift: -2,
  },
};

export const zones = [
  {
    id: "north-control",
    name: "North Control",
    type: "Control",
    position: [-3.5, 0.16, -2.45],
    size: [3.5, 0.2, 2.35],
    color: "#4f9d69",
    moisture: 25,
    health: 94,
    experiment: "Baseline comparison",
  },
  {
    id: "compost-treatment",
    name: "Compost Treatment",
    type: "Treatment",
    position: [0.25, 0.16, -2.45],
    size: [3.5, 0.2, 2.35],
    color: "#7eaa4f",
    moisture: 20,
    health: 83,
    experiment: "Compost amendment study",
  },
  {
    id: "beneficial-zone",
    name: "Beneficial Organism Zone",
    type: "Treatment",
    position: [-3.5, 0.16, 0.35],
    size: [3.5, 0.2, 2.35],
    color: "#48a87a",
    moisture: 28,
    health: 96,
    experiment: "Habitat-support trial",
  },
  {
    id: "calibration-zone",
    name: "Calibration Zone",
    type: "Calibration",
    position: [0.25, 0.16, 0.35],
    size: [3.5, 0.2, 2.35],
    color: "#4d8fa7",
    moisture: 22,
    health: 88,
    experiment: "Virtual-node calibration",
  },
];

export const experiments = [
  {
    id: "AGQ-EXP-001",
    name: "Compost amendment comparison",
    stage: "Active",
    progress: 68,
    samples: 18,
    plots: 2,
  },
  {
    id: "AGQ-EXP-002",
    name: "Beneficial-organism habitat trial",
    stage: "Sampling",
    progress: 44,
    samples: 11,
    plots: 2,
  },
  {
    id: "AGQ-EXP-003",
    name: "Virtual sensor calibration",
    stage: "Simulation",
    progress: 82,
    samples: 30,
    plots: 1,
  },
];

export const recommendations = [
  {
    id: "AGQ-REC-001",
    priority: "High",
    title: "Inspect compost-treatment moisture",
    rationale:
      "The synthetic trend is below the demonstration threshold. Manual verification is required before any action.",
    status: "Pending approval",
  },
  {
    id: "AGQ-REC-002",
    priority: "Medium",
    title: "Review calibration-node drift",
    rationale:
      "The digital-twin node is diverging from the manual reference series.",
    status: "Pending review",
  },
  {
    id: "AGQ-REC-003",
    priority: "Normal",
    title: "Continue beneficial-organism observations",
    rationale:
      "The demonstration health index remains stable across the current sampling window.",
    status: "Approved for observation",
  },
];

export const tasks = [
  {
    title: "Inspect prototype enclosure",
    owner: "Field operations",
    status: "Open",
    priority: "High",
  },
  {
    title: "Record North Control observation",
    owner: "Research team",
    status: "In progress",
    priority: "Normal",
  },
  {
    title: "Review calibration comparison",
    owner: "Research lead",
    status: "Pending review",
    priority: "Medium",
  },
];

export const activity = [
  "Manual observation recorded in North Control",
  "Synthetic gateway heartbeat received",
  "Calibration-drift recommendation generated",
  "Experiment checkpoint reviewed",
  "Offline queue synchronized with local gateway",
];

export function createScenarioView(key) {
  const scenario = scenarios[key] ?? scenarios.baseline;
  return zones.map((zone, index) => {
    const driftPenalty = key === "drift" && index === 3 ? -13 : 0;
    const pestPenalty = key === "pest" && index === 2 ? -11 : 0;
    return {
      ...zone,
      moisture: Math.max(
        4,
        zone.moisture + scenario.moistureShift + (index === 1 ? -2 : 0),
      ),
      health: Math.max(
        30,
        zone.health + scenario.healthShift + driftPenalty + pestPenalty,
      ),
      temperature: 24 + scenario.temperatureShift + index,
      status:
        zone.health + scenario.healthShift + driftPenalty + pestPenalty < 75
          ? "Attention"
          : index === 3 && key === "drift"
            ? "Drift detected"
            : "Stable",
    };
  });
}

export const architectureLayers = [
  "Manual operations",
  "Synthetic sensor adapters",
  "Local edge gateway",
  "Digital twin",
  "AI and forecasting",
  "Graph intelligence",
  "Classical optimization",
  "Quantum research lane",
  "Human approval",
];

export const phaseRoadmap = [
  {
    phase: "Phase 3",
    title: "Digital Twin & Sensor Simulation",
    status: "Prototype",
    detail: "3D acre, virtual nodes, raw-payload previews, manual comparison.",
  },
  {
    phase: "Phase 4",
    title: "Baseline Intelligence",
    status: "Prototype",
    detail: "Rules, anomaly flags, forecast previews, recommendation traceability.",
  },
  {
    phase: "Phase 5",
    title: "Graph & Experiment Intelligence",
    status: "Prototype",
    detail: "Spatial graph, Laplacian score, active sampling, experiment ranking.",
  },
  {
    phase: "Phase 6",
    title: "Quantum Research Lane",
    status: "Prototype",
    detail: "QUBO workspace, matched classical baseline, simulator-only run registry.",
  },
];
