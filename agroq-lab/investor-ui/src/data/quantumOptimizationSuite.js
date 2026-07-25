import {
  exactSolveQubo,
  fitQuadraticEnergy,
  qaoaP1Qubo,
  seededRandom,
  sha256,
  simulatedAnnealingQubo,
} from "./quantumSuiteCore.js";

export const irrigationResearchSource = {
  id: "QRS-016",
  sequence: ["Q3"],
  title: "A Physics-Grounded QUBO Encoding of Irrigation Scheduling for QAOA",
  authors: ["Alisher Ortikov", "Alisher Ilhamov"],
  year: 2026,
  venue: "arXiv",
  publicationStatus: "Recent preprint",
  identifier: "arXiv:2607.13374",
  url: "https://arxiv.org/abs/2607.13374",
  mechanism:
    "Root-zone soil-moisture memory, weather inputs, field adjacency, water budgets, and irrigation-window constraints encoded into a QUBO.",
  agroqFeature:
    "Q3 multi-period irrigation reproduction using a small synthetic benchmark and matched classical-versus-simulator comparison.",
  reproductionTarget:
    "Reproduce the formulation pattern on a transparent three-zone, two-period synthetic instance before using field data.",
  evidenceStatus: "Emerging reproduction source",
  limitations:
    "This is a recent preprint. AgroQ uses a simplified synthetic reproduction and does not claim validation, deployment readiness, or quantum advantage.",
  acknowledgment:
    "AgroQ credits Ortikov and Ilhamov for the physics-grounded irrigation-QUBO formulation pattern.",
  endorsementBoundary:
    "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
  tags: ["irrigation", "QUBO", "QAOA", "soil moisture"],
};

const irrigationConfig = {
  zones: [
    { id: "Z1", name: "North Control", initial: 0.52, target: 0.61 },
    { id: "Z2", name: "Compost Trial", initial: 0.47, target: 0.64 },
    { id: "Z3", name: "Cover Crop", initial: 0.55, target: 0.63 },
  ],
  periods: [
    { id: "P1", evapotranspiration: 0.08, rainfall: 0.01 },
    { id: "P2", evapotranspiration: 0.09, rainfall: 0.0 },
  ],
  irrigationGain: 0.13,
  waterBudget: 3,
  waterCost: 0.05,
  adjacencyPenalty: 0.12,
  budgetPenalty: 3.5,
  adjacency: [
    ["Z1", "Z2"],
    ["Z2", "Z3"],
  ],
};

function irrigationVariableNames(config = irrigationConfig) {
  return config.zones.flatMap((zone) =>
    config.periods.map((period) => `${zone.id}_${period.id}`),
  );
}

function irrigationDecode(bits, config = irrigationConfig) {
  const schedule = [];
  let index = 0;
  let waterUsed = 0;
  let stress = 0;
  const finalMoisture = {};

  for (const zone of config.zones) {
    let moisture = zone.initial;
    for (const period of config.periods) {
      const irrigate = bits[index] === 1;
      schedule.push({
        variable: `${zone.id}_${period.id}`,
        zone: zone.name,
        period: period.id,
        irrigate,
      });
      waterUsed += irrigate ? 1 : 0;
      moisture +=
        period.rainfall -
        period.evapotranspiration +
        (irrigate ? config.irrigationGain : 0);
      stress += (zone.target - moisture) ** 2;
      index += 1;
    }
    finalMoisture[zone.id] = moisture;
  }

  let adjacencyOverlaps = 0;
  for (const [left, right] of config.adjacency) {
    const leftIndex = config.zones.findIndex((zone) => zone.id === left);
    const rightIndex = config.zones.findIndex((zone) => zone.id === right);
    config.periods.forEach((_, periodIndex) => {
      const leftBit = bits[leftIndex * config.periods.length + periodIndex];
      const rightBit = bits[rightIndex * config.periods.length + periodIndex];
      adjacencyOverlaps += leftBit * rightBit;
    });
  }

  const feasible = waterUsed <= config.waterBudget;
  const objective =
    stress +
    config.waterCost * waterUsed +
    config.adjacencyPenalty * adjacencyOverlaps +
    config.budgetPenalty * (waterUsed - config.waterBudget) ** 2;

  return {
    feasible,
    schedule,
    waterUsed,
    stress,
    adjacencyOverlaps,
    finalMoisture,
    objective,
  };
}

export function buildIrrigationQubo(config = irrigationConfig) {
  const variableNames = irrigationVariableNames(config);
  const objective = (bits) => irrigationDecode(bits, config).objective;
  const qubo = fitQuadraticEnergy(variableNames, objective);
  return { ...qubo, config };
}

function summarizeOptimization(exact, annealing, qaoa) {
  const exactObjective = exact.best?.objective ?? exact.best?.energy ?? 0;
  const comparison = (record) => {
    const value = record.best?.objective ?? record.best?.energy ?? null;
    return {
      objective: value,
      absoluteGap:
        value === null ? null : Number((value - exactObjective).toFixed(8)),
      exactMatch:
        value !== null && Math.abs(value - exactObjective) < 1e-8,
    };
  };
  return {
    exact: comparison(exact),
    simulatedAnnealing: comparison(annealing),
    qaoa: comparison(qaoa),
  };
}

export async function runQ3Irrigation(options = {}) {
  const seed = Number(options.seed) || 301;
  const budget = Number(options.sampleBudget) || 2048;
  const gridSize = Number(options.gridSize) || 11;
  const qubo = buildIrrigationQubo();
  const decode = (bits) => irrigationDecode(bits, qubo.config);
  const exact = exactSolveQubo(qubo, decode);
  const annealing = simulatedAnnealingQubo(qubo, decode, {
    seed,
    steps: budget,
  });
  const qaoa = qaoaP1Qubo(qubo, decode, {
    seed,
    shots: budget,
    gridSize,
  });
  const datasetHash = await sha256({
    zones: qubo.config.zones,
    periods: qubo.config.periods,
    constraints: {
      waterBudget: qubo.config.waterBudget,
      adjacency: qubo.config.adjacency,
    },
  });
  const formulationHash = await sha256({
    variableNames: qubo.variableNames,
    matrix: qubo.matrix,
    constant: qubo.constant,
  });

  return {
    sequence: "Q3",
    experimentId: `AGQ-Q3-${Date.now()}`,
    title: "Irrigation-scheduling reproduction",
    sourceIds: ["QRS-001", "QRS-002", "QRS-003", "QRS-016"],
    datasetHash,
    formulationHash,
    qubo,
    solvers: { exact, simulatedAnnealing: annealing, qaoa },
    comparison: summarizeOptimization(exact, annealing, qaoa),
    controls: {
      syntheticData: true,
      recentPreprintSource: true,
      classicalBaselineRequired: true,
      matchedBudget: true,
      hardwareUsed: false,
      advantageClaim: false,
      operationalDependency: false,
      humanReviewRequired: true,
    },
    disclosure:
      "This is a simplified synthetic reproduction inspired by a recent irrigation-QUBO preprint, not a reproduction of its full field dataset or hardware experiments.",
  };
}

const graphConfig = {
  nodes: [
    { id: "A", name: "North Control", value: 0.82 },
    { id: "B", name: "Compost Trial", value: 0.93 },
    { id: "C", name: "Cover Crop", value: 0.76 },
    { id: "D", name: "Beneficial Zone", value: 0.88 },
    { id: "E", name: "Calibration Zone", value: 0.71 },
    { id: "F", name: "Untreated Control", value: 0.65 },
  ],
  edges: [
    ["A", "B", 1.0],
    ["A", "C", 0.8],
    ["B", "C", 0.7],
    ["B", "D", 1.1],
    ["C", "E", 0.9],
    ["D", "E", 0.75],
    ["D", "F", 0.8],
    ["E", "F", 1.0],
  ],
  sensorBudget: 2,
  sensorBudgetPenalty: 4,
  redundancyPenalty: 0.28,
};

function nodeIndex(id, config = graphConfig) {
  return config.nodes.findIndex((node) => node.id === id);
}

function maxCutDecode(bits, config = graphConfig) {
  let cutWeight = 0;
  for (const [left, right, weight] of config.edges) {
    if (bits[nodeIndex(left, config)] !== bits[nodeIndex(right, config)]) {
      cutWeight += weight;
    }
  }
  return {
    feasible: true,
    cutWeight,
    partition0: config.nodes
      .filter((_, index) => bits[index] === 0)
      .map((node) => node.id),
    partition1: config.nodes
      .filter((_, index) => bits[index] === 1)
      .map((node) => node.id),
    objective: -cutWeight,
  };
}

function sensorDecode(bits, config = graphConfig) {
  const selected = config.nodes.filter((_, index) => bits[index] === 1);
  const selectedSet = new Set(selected.map((node) => node.id));
  const covered = new Set(selected.map((node) => node.id));

  for (const [left, right] of config.edges) {
    if (selectedSet.has(left)) covered.add(right);
    if (selectedSet.has(right)) covered.add(left);
  }

  const coverageValue = config.nodes
    .filter((node) => covered.has(node.id))
    .reduce((sum, node) => sum + node.value, 0);
  const influenceValue = selected.reduce((sum, node) => {
    const neighborValue = config.edges.reduce((edgeSum, [left, right]) => {
      if (left === node.id) {
        return edgeSum + config.nodes[nodeIndex(right, config)].value * 0.5;
      }
      if (right === node.id) {
        return edgeSum + config.nodes[nodeIndex(left, config)].value * 0.5;
      }
      return edgeSum;
    }, 0);
    return sum + node.value + neighborValue;
  }, 0);
  let redundancy = 0;
  for (const [left, right] of config.edges) {
    if (selectedSet.has(left) && selectedSet.has(right)) redundancy += 1;
  }
  const count = selected.length;
  const budgetViolation = Math.max(0, count - config.sensorBudget);
  const objective =
    -influenceValue +
    config.redundancyPenalty * redundancy +
    config.sensorBudgetPenalty * (count - config.sensorBudget) ** 2;

  return {
    feasible: count <= config.sensorBudget,
    selected: selected.map((node) => node.id),
    covered: [...covered],
    coverageValue,
    influenceValue,
    redundancy,
    sensorCount: count,
    objective,
  };
}

function buildGraphQubos(config = graphConfig) {
  const variableNames = config.nodes.map((node) => `node_${node.id}`);
  return {
    maxCut: {
      ...fitQuadraticEnergy(variableNames, (bits) =>
        maxCutDecode(bits, config).objective,
      ),
      config,
    },
    sensorPlacement: {
      ...fitQuadraticEnergy(variableNames, (bits) =>
        sensorDecode(bits, config).objective,
      ),
      config,
    },
  };
}

function solveGraphProblem(qubo, decode, options) {
  const exact = exactSolveQubo(qubo, decode);
  const annealing = simulatedAnnealingQubo(qubo, decode, {
    seed: options.seed,
    steps: options.sampleBudget,
  });
  const qaoa = qaoaP1Qubo(qubo, decode, {
    seed: options.seed,
    shots: options.sampleBudget,
    gridSize: options.gridSize,
  });
  return {
    exact,
    simulatedAnnealing: annealing,
    qaoa,
    comparison: summarizeOptimization(exact, annealing, qaoa),
  };
}

export async function runQ4Graph(options = {}) {
  const normalized = {
    seed: Number(options.seed) || 301,
    sampleBudget: Number(options.sampleBudget) || 2048,
    gridSize: Number(options.gridSize) || 11,
  };
  const qubos = buildGraphQubos();
  const maxCut = solveGraphProblem(
    qubos.maxCut,
    (bits) => maxCutDecode(bits),
    normalized,
  );
  const sensorPlacement = solveGraphProblem(
    qubos.sensorPlacement,
    (bits) => sensorDecode(bits),
    normalized,
  );
  const datasetHash = await sha256(graphConfig);
  const formulationHash = await sha256({
    maxCut: qubos.maxCut.matrix,
    sensorPlacement: qubos.sensorPlacement.matrix,
  });

  return {
    sequence: "Q4",
    experimentId: `AGQ-Q4-${Date.now()}`,
    title: "Graph partition and sensor-placement QAOA",
    sourceIds: ["QRS-001", "QRS-002", "QRS-004", "QRS-012", "QRS-013"],
    datasetHash,
    formulationHash,
    graph: graphConfig,
    maxCut: { qubo: qubos.maxCut, ...maxCut },
    sensorPlacement: { qubo: qubos.sensorPlacement, ...sensorPlacement },
    controls: {
      syntheticGraph: true,
      exactReferenceRequired: true,
      classicalBaselineRequired: true,
      hardwareUsed: false,
      advantageClaim: false,
      humanReviewRequired: true,
    },
  };
}

export function buildOptimizationExperimentRecord(result) {
  const qaoa =
    result.sequence === "Q3"
      ? result.solvers.qaoa
      : result.sensorPlacement.qaoa;
  const exact =
    result.sequence === "Q3"
      ? result.solvers.exact
      : result.sensorPlacement.exact;
  const formulation =
    result.sequence === "Q3"
      ? result.qubo
      : result.sensorPlacement.qubo;

  return {
    schemaId: "AGROQ-QER-1.0",
    experimentId: result.experimentId,
    sequence: result.sequence,
    title: result.title,
    sourceIds: result.sourceIds,
    researchOwner: "AgroQ Research Team",
    codeCommit: "browser-suite-q3-q10",
    problemFamily:
      result.sequence === "Q3"
        ? "Multi-period irrigation scheduling"
        : "Graph partitioning and sensor placement",
    status: "Simulation complete",
    runType: "quantum-simulator",
    algorithm:
      "Exact enumeration + seeded simulated annealing + QAOA p=1 ideal statevector",
    seed: qaoa.seed,
    runBudget: {
      objectiveEvaluations: qaoa.shots,
      wallClockSeconds: null,
      shots: qaoa.shots,
      matchedAcrossSolvers: true,
      qaoaParameterEvaluations: qaoa.parameterEvaluations,
    },
    dataset: {
      id: `${result.sequence}-SYNTHETIC-001`,
      hash: result.datasetHash,
      version: "1.0.0",
      frozen: true,
      records:
        result.sequence === "Q3"
          ? result.qubo.config.zones.length * result.qubo.config.periods.length
          : result.graph.nodes.length,
    },
    formulation: {
      type: "QUBO",
      hash: result.formulationHash,
      variables: formulation.variableNames.length,
      constraints: result.sequence === "Q3" ? 2 : 2,
      objective: result.title,
    },
    classicalBaseline: {
      required: true,
      algorithm: exact.algorithm,
      objective: exact.best?.energy ?? null,
      feasible: exact.best?.feasible ?? false,
      runtimeSeconds: null,
      budget: "Exact reference",
    },
    execution: {
      backend: qaoa.circuit?.backend || "Browser ideal statevector",
      provider: "AgroQ local prototype",
      shots: qaoa.shots || 0,
      circuitDepth: qaoa.circuit?.estimatedDepth ?? null,
      twoQubitGates: qaoa.circuit?.estimatedTwoQubitGates ?? null,
      qubits: qaoa.circuit?.qubits ?? null,
      noiseModel: qaoa.circuit?.noiseModel || "None",
      optimizer: `${qaoa.gridSize}x${qaoa.gridSize} parameter grid`,
    },
    metrics: {
      objective: qaoa.best?.energy ?? null,
      feasible: qaoa.best?.feasible ?? false,
      constraintViolations: qaoa.best?.feasible ? 0 : 1,
      approximationGap:
        qaoa.best && exact.best
          ? qaoa.best.energy - exact.best.energy
          : null,
      runtimeSeconds: null,
      confidenceInterval: null,
    },
    claimControls: {
      simulatorOnly: true,
      hardwareUsed: false,
      advantageClaim: false,
      operationalDependency: false,
      matchedBudget: true,
      classicalBaselineRequired: true,
      syntheticData: true,
    },
    humanReview: {
      required: true,
      status: "Pending",
      reviewer: "",
      notes: "Review formulation, feasibility, and evidence boundaries.",
    },
    artifacts: [`${result.sequence.toLowerCase()}-results.json`],
    notes:
      "Synthetic research reproduction. No hardware or quantum-advantage claim.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}
