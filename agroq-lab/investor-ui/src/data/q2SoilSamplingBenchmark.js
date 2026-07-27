import {
  quantumExperimentSchema,
  sha256Object,
} from "./quantumRegistryData.js";

export const Q2_SOURCE_IDS = ["QRS-001", "QRS-002", "QRS-003"];

export const referenceSoilSamplingProblem = {
  id: "SOIL-SAMPLING-REFERENCE-001",
  createdAt: "2026-07-25T00:00:00.000Z",
  objective:
    "Maximize uncertainty reduction, spatial diversity, treatment coverage, and urgency while respecting the sampling budget.",
  budget: 5,
  weights: {
    uncertainty: 45,
    diversity: 25,
    urgency: 30,
  },
  candidates: [
    {
      id: "C-01",
      zone: "Compost Trial",
      uncertainty: 0.91,
      diversity: 0.74,
      urgency: 0.88,
      cost: 2,
      distance: 1.2,
      value: 0.82,
      reason: "Moisture decline and high model uncertainty",
    },
    {
      id: "C-02",
      zone: "Calibration Zone",
      uncertainty: 0.87,
      diversity: 0.82,
      urgency: 0.73,
      cost: 2,
      distance: 2.1,
      value: 0.78,
      reason: "Sensor drift needs a ground-truth sample",
    },
    {
      id: "C-03",
      zone: "North Control",
      uncertainty: 0.61,
      diversity: 0.79,
      urgency: 0.58,
      cost: 1,
      distance: 0.8,
      value: 0.67,
      reason: "Maintain control continuity",
    },
    {
      id: "C-04",
      zone: "Beneficial Zone",
      uncertainty: 0.72,
      diversity: 0.67,
      urgency: 0.64,
      cost: 1,
      distance: 1.6,
      value: 0.66,
      reason: "Treatment-response confirmation",
    },
    {
      id: "C-05",
      zone: "Cover Crop Zone",
      uncertainty: 0.68,
      diversity: 0.86,
      urgency: 0.52,
      cost: 2,
      distance: 2.8,
      value: 0.64,
      reason: "Distinct root-colonization profile",
    },
    {
      id: "C-06",
      zone: "Untreated Control",
      uncertainty: 0.55,
      diversity: 0.71,
      urgency: 0.49,
      cost: 1,
      distance: 1.9,
      value: 0.56,
      reason: "Baseline comparison",
    },
  ],
  controls: {
    datasetFrozen: true,
    classicalBaselineRequired: true,
    simulatorOnly: true,
    advantageClaim: false,
    humanReviewRequired: true,
  },
};

function numberOr(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function normalizeSoilSamplingProblem(problem) {
  const source = problem?.candidates?.length ? problem : referenceSoilSamplingProblem;
  const budget = Math.max(1, Math.round(numberOr(source.budget, 5)));
  const candidates = source.candidates.map((candidate, index) => {
    const uncertainty = numberOr(candidate.uncertainty, 0.5);
    const diversity = numberOr(candidate.diversity, 0.5);
    const urgency = numberOr(candidate.urgency, 0.5);
    const distance = Math.max(0, numberOr(candidate.distance, 0));
    const cost = Math.max(1, Math.round(numberOr(candidate.cost, 1)));
    const weighted =
      uncertainty * 0.45 + diversity * 0.25 + urgency * 0.3 - distance * 0.025;

    return {
      id: candidate.id || `C-${String(index + 1).padStart(2, "0")}`,
      zone: candidate.zone || `Candidate ${index + 1}`,
      uncertainty,
      diversity,
      urgency,
      cost,
      distance,
      value: Number(numberOr(candidate.value, weighted).toFixed(6)),
      reason: candidate.reason || "Registered candidate sample.",
    };
  });

  return {
    id: source.id || "SOIL-SAMPLING-FROZEN",
    createdAt: source.createdAt || new Date().toISOString(),
    objective:
      source.objective ||
      "Maximize information value while respecting the sampling budget.",
    budget,
    weights: source.weights || referenceSoilSamplingProblem.weights,
    candidates,
    controls: {
      datasetFrozen: source.controls?.datasetFrozen !== false,
      classicalBaselineRequired: true,
      simulatorOnly: true,
      advantageClaim: false,
      humanReviewRequired: true,
      ...source.controls,
    },
    sourceMode: problem?.candidates?.length
      ? "Frozen Soil Biology problem"
      : "Reference synthetic benchmark",
  };
}

function slackWeightsForBudget(budget) {
  const count = Math.max(1, Math.ceil(Math.log2(budget + 1)));
  return Array.from({ length: count }, (_, index) => 2 ** index);
}

export function buildSoilSamplingQubo(problemInput, options = {}) {
  const problem = normalizeSoilSamplingProblem(problemInput);
  const totalReward = problem.candidates.reduce(
    (sum, candidate) => sum + Math.max(0, candidate.value),
    0,
  );
  const requestedPenalty = numberOr(options.penalty, 0);
  const penalty = Math.max(requestedPenalty, totalReward + 1);
  const slackWeights = slackWeightsForBudget(problem.budget);
  const variables = [
    ...problem.candidates.map((candidate, index) => ({
      index,
      name: `select_${candidate.id}`,
      kind: "selection",
      coefficient: candidate.cost,
      candidateId: candidate.id,
      label: candidate.zone,
    })),
    ...slackWeights.map((weight, slackIndex) => ({
      index: problem.candidates.length + slackIndex,
      name: `slack_${weight}`,
      kind: "slack",
      coefficient: weight,
      candidateId: null,
      label: `Unused budget ${weight}`,
    })),
  ];

  const size = variables.length;
  const matrix = Array.from({ length: size }, () => Array(size).fill(0));
  const linear = Array(size).fill(0);
  const quadratic = [];
  const constant = penalty * problem.budget ** 2;

  variables.forEach((variable, index) => {
    const coefficient = variable.coefficient;
    const reward =
      variable.kind === "selection"
        ? problem.candidates[index].value
        : 0;
    linear[index] =
      -reward +
      penalty * (coefficient ** 2 - 2 * problem.budget * coefficient);
    matrix[index][index] = linear[index];
  });

  for (let left = 0; left < size; left += 1) {
    for (let right = left + 1; right < size; right += 1) {
      const coefficient =
        2 *
        penalty *
        variables[left].coefficient *
        variables[right].coefficient;
      matrix[left][right] = coefficient;
      quadratic.push({
        left,
        right,
        coefficient,
        leftName: variables[left].name,
        rightName: variables[right].name,
      });
    }
  }

  return {
    problem,
    penalty,
    constant,
    variables,
    selectionCount: problem.candidates.length,
    slackWeights,
    matrix,
    linear,
    quadratic,
    quboTermCount:
      linear.filter((coefficient) => coefficient !== 0).length +
      quadratic.filter((term) => term.coefficient !== 0).length,
  };
}

export function bitsFromState(state, size) {
  return Array.from({ length: size }, (_, index) => (state >> index) & 1);
}

export function stateFromBits(bits) {
  return bits.reduce(
    (state, bit, index) => state | ((bit ? 1 : 0) << index),
    0,
  );
}

export function evaluateQuboBits(bits, qubo) {
  let energy = qubo.constant;
  for (let left = 0; left < bits.length; left += 1) {
    if (!bits[left]) continue;
    energy += qubo.matrix[left][left];
    for (let right = left + 1; right < bits.length; right += 1) {
      if (bits[right]) {
        energy += qubo.matrix[left][right];
      }
    }
  }
  return energy;
}

function encodeSlack(value, weights) {
  let remaining = Math.max(0, Math.round(value));
  const bits = Array(weights.length).fill(0);
  for (let index = weights.length - 1; index >= 0; index -= 1) {
    if (weights[index] <= remaining) {
      bits[index] = 1;
      remaining -= weights[index];
    }
  }
  return bits;
}

export function decodeSolution(bits, qubo) {
  const selectionBits = bits.slice(0, qubo.selectionCount);
  const slackBits = bits.slice(qubo.selectionCount);
  const selected = qubo.problem.candidates.filter(
    (_, index) => selectionBits[index] === 1,
  );
  const usedBudget = selected.reduce(
    (sum, candidate) => sum + candidate.cost,
    0,
  );
  const slackValue = slackBits.reduce(
    (sum, bit, index) => sum + bit * qubo.slackWeights[index],
    0,
  );
  const residual = usedBudget + slackValue - qubo.problem.budget;
  const utility = selected.reduce(
    (sum, candidate) => sum + candidate.value,
    0,
  );
  const energy = evaluateQuboBits(bits, qubo);

  return {
    bits,
    state: stateFromBits(bits),
    selected,
    selectedIds: selected.map((candidate) => candidate.id),
    selectedZones: selected.map((candidate) => candidate.zone),
    usedBudget,
    slackValue,
    residual,
    feasible: usedBudget <= qubo.problem.budget && residual === 0,
    utility: Number(utility.toFixed(6)),
    energy: Number(energy.toFixed(6)),
    constraintViolations:
      (usedBudget > qubo.problem.budget ? 1 : 0) +
      (residual !== 0 ? 1 : 0),
  };
}

export function createFeasibleBits(selectionBits, qubo) {
  const usedBudget = selectionBits.reduce(
    (sum, bit, index) =>
      sum + bit * qubo.problem.candidates[index].cost,
    0,
  );
  const unused = Math.max(0, qubo.problem.budget - usedBudget);
  return [...selectionBits, ...encodeSlack(unused, qubo.slackWeights)];
}

export function exactEnumerateQubo(qubo) {
  const stateCount = 2 ** qubo.variables.length;
  let globalBest = null;
  let feasibleBest = null;

  for (let state = 0; state < stateCount; state += 1) {
    const solution = decodeSolution(
      bitsFromState(state, qubo.variables.length),
      qubo,
    );
    if (!globalBest || solution.energy < globalBest.energy) {
      globalBest = solution;
    }
    if (
      solution.feasible &&
      (!feasibleBest ||
        solution.energy < feasibleBest.energy ||
        (solution.energy === feasibleBest.energy &&
          solution.utility > feasibleBest.utility))
    ) {
      feasibleBest = solution;
    }
  }

  return {
    algorithm: "Exact enumeration",
    stateCount,
    globalBest,
    best: feasibleBest,
    quboGroundStateFeasible:
      Boolean(globalBest?.feasible) &&
      globalBest?.state === feasibleBest?.state,
    objectiveEvaluations: stateCount,
  };
}

export function greedySoilSampling(qubo) {
  const ranked = qubo.problem.candidates
    .map((candidate, index) => ({
      ...candidate,
      index,
      ratio: candidate.value / candidate.cost,
    }))
    .sort(
      (left, right) =>
        right.ratio - left.ratio ||
        right.value - left.value ||
        left.cost - right.cost,
    );

  const selectionBits = Array(qubo.selectionCount).fill(0);
  let remaining = qubo.problem.budget;

  for (const candidate of ranked) {
    if (candidate.cost <= remaining) {
      selectionBits[candidate.index] = 1;
      remaining -= candidate.cost;
    }
  }

  return {
    algorithm: "Greedy value-per-cost",
    best: decodeSolution(createFeasibleBits(selectionBits, qubo), qubo),
    objectiveEvaluations: ranked.length,
    ranking: ranked.map((candidate) => candidate.id),
  };
}

export function createSeededRandom(seedInput = 301) {
  let seed = Math.trunc(numberOr(seedInput, 301)) >>> 0;
  return () => {
    seed += 0x6d2b79f5;
    let value = seed;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export function simulatedAnnealingQubo(qubo, options = {}) {
  const steps = Math.max(64, Math.round(numberOr(options.steps, 2048)));
  const seed = Math.round(numberOr(options.seed, 301));
  const random = createSeededRandom(seed);
  const greedy = greedySoilSampling(qubo);
  let bits = [...greedy.best.bits];
  let current = decodeSolution(bits, qubo);
  let best = current;
  let bestFeasible = current.feasible ? current : null;
  let acceptedMoves = 0;
  const startTemperature = Math.max(
    0.1,
    numberOr(options.startTemperature, qubo.penalty * 2),
  );
  const endTemperature = Math.max(
    0.0001,
    numberOr(options.endTemperature, 0.01),
  );

  for (let step = 0; step < steps; step += 1) {
    const progress = steps === 1 ? 1 : step / (steps - 1);
    const temperature =
      startTemperature *
      (endTemperature / startTemperature) ** progress;
    const nextBits = [...bits];
    const flipIndex = Math.floor(random() * nextBits.length);
    nextBits[flipIndex] = nextBits[flipIndex] ? 0 : 1;
    const next = decodeSolution(nextBits, qubo);
    const delta = next.energy - current.energy;

    if (delta <= 0 || random() < Math.exp(-delta / temperature)) {
      bits = nextBits;
      current = next;
      acceptedMoves += 1;
    }

    if (current.energy < best.energy) {
      best = current;
    }
    if (
      current.feasible &&
      (!bestFeasible ||
        current.energy < bestFeasible.energy ||
        (current.energy === bestFeasible.energy &&
          current.utility > bestFeasible.utility))
    ) {
      bestFeasible = current;
    }
  }

  return {
    algorithm: "Seeded simulated annealing",
    seed,
    steps,
    objectiveEvaluations: steps + 1,
    acceptedMoves,
    acceptanceRate: Number((acceptedMoves / steps).toFixed(6)),
    globalBest: best,
    best: bestFeasible || greedy.best,
  };
}

function applyCostLayer(real, imaginary, normalizedEnergies, gamma) {
  for (let state = 0; state < real.length; state += 1) {
    const phase = -gamma * normalizedEnergies[state];
    const cosine = Math.cos(phase);
    const sine = Math.sin(phase);
    const currentReal = real[state];
    const currentImaginary = imaginary[state];
    real[state] =
      currentReal * cosine - currentImaginary * sine;
    imaginary[state] =
      currentReal * sine + currentImaginary * cosine;
  }
}

function applyMixerLayer(real, imaginary, qubitCount, beta) {
  const cosine = Math.cos(beta);
  const sine = Math.sin(beta);

  for (let qubit = 0; qubit < qubitCount; qubit += 1) {
    const mask = 1 << qubit;
    for (let state = 0; state < real.length; state += 1) {
      if (state & mask) continue;
      const paired = state | mask;
      const leftReal = real[state];
      const leftImaginary = imaginary[state];
      const rightReal = real[paired];
      const rightImaginary = imaginary[paired];

      real[state] = cosine * leftReal + sine * rightImaginary;
      imaginary[state] = cosine * leftImaginary - sine * rightReal;
      real[paired] = cosine * rightReal + sine * leftImaginary;
      imaginary[paired] = cosine * rightImaginary - sine * leftReal;
    }
  }
}

function qaoaStatevector(normalizedEnergies, qubitCount, gamma, beta) {
  const stateCount = normalizedEnergies.length;
  const amplitude = 1 / Math.sqrt(stateCount);
  const real = new Float64Array(stateCount);
  const imaginary = new Float64Array(stateCount);
  real.fill(amplitude);
  applyCostLayer(real, imaginary, normalizedEnergies, gamma);
  applyMixerLayer(real, imaginary, qubitCount, beta);
  return { real, imaginary };
}

function probabilitiesFromStatevector(statevector) {
  const probabilities = new Float64Array(statevector.real.length);
  for (let state = 0; state < probabilities.length; state += 1) {
    probabilities[state] =
      statevector.real[state] ** 2 + statevector.imaginary[state] ** 2;
  }
  return probabilities;
}

function expectationFromProbabilities(probabilities, values) {
  let expectation = 0;
  for (let index = 0; index < probabilities.length; index += 1) {
    expectation += probabilities[index] * values[index];
  }
  return expectation;
}

function cumulativeProbabilities(probabilities) {
  const cumulative = new Float64Array(probabilities.length);
  let sum = 0;
  for (let index = 0; index < probabilities.length; index += 1) {
    sum += probabilities[index];
    cumulative[index] = sum;
  }
  cumulative[cumulative.length - 1] = 1;
  return cumulative;
}

function sampleState(cumulative, random) {
  const target = random();
  let left = 0;
  let right = cumulative.length - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (target <= cumulative[middle]) {
      right = middle;
    } else {
      left = middle + 1;
    }
  }
  return left;
}

export function qaoaP1Statevector(qubo, options = {}) {
  const qubitCount = qubo.variables.length;
  const stateCount = 2 ** qubitCount;

  if (qubitCount > 12) {
    return {
      algorithm: "QAOA p=1 ideal statevector",
      supported: false,
      reason:
        "The browser prototype limits ideal statevector runs to 12 qubits.",
      best: null,
    };
  }

  const rawEnergies = new Float64Array(stateCount);
  let minimumEnergy = Number.POSITIVE_INFINITY;
  let maximumEnergy = Number.NEGATIVE_INFINITY;

  for (let state = 0; state < stateCount; state += 1) {
    const energy = evaluateQuboBits(
      bitsFromState(state, qubitCount),
      qubo,
    );
    rawEnergies[state] = energy;
    minimumEnergy = Math.min(minimumEnergy, energy);
    maximumEnergy = Math.max(maximumEnergy, energy);
  }

  const energyRange = Math.max(1e-12, maximumEnergy - minimumEnergy);
  const normalizedEnergies = Float64Array.from(
    rawEnergies,
    (energy) => (energy - minimumEnergy) / energyRange,
  );
  const gridSize = Math.max(
    5,
    Math.min(31, Math.round(numberOr(options.gridSize, 13))),
  );
  let bestParameters = null;
  let bestStatevector = null;

  for (let gammaIndex = 0; gammaIndex < gridSize; gammaIndex += 1) {
    const gamma = (2 * Math.PI * gammaIndex) / gridSize;
    for (let betaIndex = 0; betaIndex < gridSize; betaIndex += 1) {
      const beta =
        (Math.PI * betaIndex) / (2 * Math.max(1, gridSize - 1));
      const statevector = qaoaStatevector(
        normalizedEnergies,
        qubitCount,
        gamma,
        beta,
      );
      const probabilities = probabilitiesFromStatevector(statevector);
      const normalizedExpectation = expectationFromProbabilities(
        probabilities,
        normalizedEnergies,
      );

      if (
        !bestParameters ||
        normalizedExpectation < bestParameters.normalizedExpectation
      ) {
        bestParameters = {
          gamma,
          beta,
          normalizedExpectation,
        };
        bestStatevector = statevector;
      }
    }
  }

  const probabilities = probabilitiesFromStatevector(bestStatevector);
  const rawExpectation = expectationFromProbabilities(
    probabilities,
    rawEnergies,
  );
  let highestProbabilityFeasible = null;

  for (let state = 0; state < stateCount; state += 1) {
    const solution = decodeSolution(
      bitsFromState(state, qubitCount),
      qubo,
    );
    if (
      solution.feasible &&
      (!highestProbabilityFeasible ||
        probabilities[state] > highestProbabilityFeasible.probability)
    ) {
      highestProbabilityFeasible = {
        ...solution,
        probability: probabilities[state],
      };
    }
  }

  const shots = Math.max(128, Math.round(numberOr(options.shots, 2048)));
  const seed = Math.round(numberOr(options.seed, 301));
  const random = createSeededRandom(seed);
  const cumulative = cumulativeProbabilities(probabilities);
  const counts = new Map();

  for (let shot = 0; shot < shots; shot += 1) {
    const state = sampleState(cumulative, random);
    counts.set(state, (counts.get(state) || 0) + 1);
  }

  const histogram = [...counts.entries()]
    .map(([state, count]) => {
      const solution = decodeSolution(
        bitsFromState(state, qubitCount),
        qubo,
      );
      return {
        state,
        bitstring: bitsFromState(state, qubitCount)
          .slice()
          .reverse()
          .join(""),
        count,
        probability: count / shots,
        feasible: solution.feasible,
        energy: solution.energy,
        utility: solution.utility,
        selectedIds: solution.selectedIds,
      };
    })
    .sort((left, right) => right.count - left.count)
    .slice(0, 12);

  const bestSampledFeasible = [...counts.keys()]
    .map((state) =>
      decodeSolution(bitsFromState(state, qubitCount), qubo),
    )
    .filter((solution) => solution.feasible)
    .sort(
      (left, right) =>
        left.energy - right.energy ||
        right.utility - left.utility,
    )[0];

  const nonzeroQuadratic = qubo.quadratic.filter(
    (term) => term.coefficient !== 0,
  ).length;

  return {
    algorithm: "QAOA p=1 ideal statevector",
    supported: true,
    seed,
    shots,
    gridSize,
    parameterEvaluations: gridSize ** 2,
    gamma: Number(bestParameters.gamma.toFixed(8)),
    beta: Number(bestParameters.beta.toFixed(8)),
    normalizedExpectation: Number(
      bestParameters.normalizedExpectation.toFixed(8),
    ),
    rawExpectation: Number(rawExpectation.toFixed(8)),
    energyNormalization: {
      minimum: Number(minimumEnergy.toFixed(8)),
      maximum: Number(maximumEnergy.toFixed(8)),
      range: Number(energyRange.toFixed(8)),
    },
    best:
      bestSampledFeasible ||
      highestProbabilityFeasible,
    mostProbableFeasible: highestProbabilityFeasible,
    histogram,
    circuit: {
      ansatz: "QAOA p=1",
      qubits: qubitCount,
      estimatedDepth: 3 + nonzeroQuadratic * 2,
      estimatedTwoQubitGates: nonzeroQuadratic * 2,
      measurementShots: shots,
      backend: "Browser ideal statevector",
      noiseModel: "None",
      estimateBoundary:
        "Gate counts are formulation-level estimates before device transpilation.",
    },
  };
}

function solutionComparison(exactUtility, solution) {
  if (!solution) {
    return {
      utilityGap: null,
      relativeUtilityGap: null,
      exactMatch: false,
    };
  }
  const utilityGap = exactUtility - solution.utility;
  return {
    utilityGap: Number(utilityGap.toFixed(8)),
    relativeUtilityGap:
      exactUtility === 0
        ? 0
        : Number((utilityGap / Math.abs(exactUtility)).toFixed(8)),
    exactMatch: Math.abs(utilityGap) < 1e-9,
  };
}

export async function runQ2Benchmark(problemInput, options = {}) {
  const startedAt = performance.now();
  const qubo = buildSoilSamplingQubo(problemInput, options);
  const exact = exactEnumerateQubo(qubo);
  const greedy = greedySoilSampling(qubo);
  const sharedSampleBudget = Math.max(
    128,
    Math.round(numberOr(options.sharedSampleBudget, 2048)),
  );
  const simulatedAnnealing = simulatedAnnealingQubo(qubo, {
    steps: sharedSampleBudget,
    seed: options.seed,
  });
  const qaoa = qaoaP1Statevector(qubo, {
    shots: sharedSampleBudget,
    seed: options.seed,
    gridSize: options.gridSize,
  });
  const datasetHash = await sha256Object({
    id: qubo.problem.id,
    budget: qubo.problem.budget,
    candidates: qubo.problem.candidates,
    weights: qubo.problem.weights,
  });
  const quboHash = await sha256Object({
    variableMap: qubo.variables,
    matrix: qubo.matrix,
    constant: qubo.constant,
    penalty: qubo.penalty,
  });
  const completedAt = performance.now();
  const exactUtility = exact.best?.utility ?? 0;

  return {
    schemaId: "AGROQ-Q2-BENCHMARK-1.0",
    experimentId: `AGQ-Q2-${Date.now()}`,
    generatedAt: new Date().toISOString(),
    sourceIds: Q2_SOURCE_IDS,
    problem: qubo.problem,
    datasetHash,
    quboHash,
    qubo: {
      penalty: qubo.penalty,
      constant: qubo.constant,
      variables: qubo.variables,
      slackWeights: qubo.slackWeights,
      matrix: qubo.matrix,
      linear: qubo.linear,
      quadratic: qubo.quadratic,
      quboTermCount: qubo.quboTermCount,
    },
    solvers: {
      exact: {
        ...exact,
        comparison: solutionComparison(exactUtility, exact.best),
      },
      greedy: {
        ...greedy,
        comparison: solutionComparison(exactUtility, greedy.best),
      },
      simulatedAnnealing: {
        ...simulatedAnnealing,
        comparison: solutionComparison(
          exactUtility,
          simulatedAnnealing.best,
        ),
      },
      qaoa: {
        ...qaoa,
        comparison: solutionComparison(exactUtility, qaoa.best),
      },
    },
    matchedBudgetAudit: {
      sharedSolutionSampleBudget: sharedSampleBudget,
      simulatedAnnealingTransitions: sharedSampleBudget,
      qaoaMeasurementShots: sharedSampleBudget,
      qaoaParameterEvaluations: qaoa.parameterEvaluations || 0,
      exactEnumerationRole:
        "Reference optimum; excluded from matched heuristic budget.",
      greedyRole:
        "Deterministic baseline; excluded from matched stochastic budget.",
      disclosure:
        "QAOA parameter-grid evaluations are reported separately from measurement shots.",
    },
    runtimeMilliseconds: Number((completedAt - startedAt).toFixed(3)),
    controls: {
      syntheticOrFrozenPrototypeData: true,
      exactReferenceRequired: true,
      classicalBaselineRequired: true,
      matchedStochasticBudget: true,
      idealStatevectorOnly: true,
      quantumHardwareUsed: false,
      quantumAdvantageClaim: false,
      operationalDependency: false,
      humanReviewRequired: true,
    },
  };
}

export function buildQ2ExperimentRecord(result, codeCommit = "browser-q2-prototype") {
  const qaoa = result.solvers.qaoa;
  const exact = result.solvers.exact;
  const qaoaBest = qaoa.best;

  return {
    schemaId: quantumExperimentSchema.schemaId,
    experimentId: result.experimentId,
    sequence: "Q2",
    title: "Frozen soil-sampling QUBO benchmark",
    sourceIds: [...result.sourceIds],
    researchOwner: "AgroQ Research Team",
    codeCommit,
    problemFamily: "Constrained sample selection",
    status: "Simulation complete",
    runType: "quantum-simulator",
    algorithm:
      "Exact enumeration + greedy + simulated annealing + QAOA p=1 ideal statevector",
    seed: qaoa.seed,
    runBudget: {
      objectiveEvaluations:
        result.matchedBudgetAudit.simulatedAnnealingTransitions,
      wallClockSeconds: result.runtimeMilliseconds / 1000,
      shots: qaoa.shots,
      matchedAcrossSolvers: true,
      qaoaParameterEvaluations: qaoa.parameterEvaluations,
    },
    dataset: {
      id: result.problem.id,
      hash: result.datasetHash,
      version: "1.0.0",
      frozen: true,
      records: result.problem.candidates.length,
    },
    formulation: {
      type: "QUBO with binary slack encoding",
      hash: result.quboHash,
      variables: result.qubo.variables.length,
      constraints: 1,
      objective: result.problem.objective,
    },
    classicalBaseline: {
      required: true,
      algorithm: exact.algorithm,
      objective: exact.best?.energy ?? null,
      feasible: exact.best?.feasible ?? false,
      runtimeSeconds: null,
      budget: result.problem.budget,
    },
    execution: {
      backend: qaoa.circuit?.backend || "Browser ideal statevector",
      provider: "AgroQ local prototype",
      shots: qaoa.shots || 0,
      circuitDepth: qaoa.circuit?.estimatedDepth ?? null,
      twoQubitGates: qaoa.circuit?.estimatedTwoQubitGates ?? null,
      qubits: qaoa.circuit?.qubits ?? null,
      noiseModel: qaoa.circuit?.noiseModel || "None",
      optimizer: `Deterministic ${qaoa.gridSize}x${qaoa.gridSize} parameter grid`,
    },
    metrics: {
      objective: qaoaBest?.energy ?? null,
      feasible: qaoaBest?.feasible ?? false,
      constraintViolations: qaoaBest?.constraintViolations ?? null,
      approximationGap: qaoa.comparison?.relativeUtilityGap ?? null,
      runtimeSeconds: result.runtimeMilliseconds / 1000,
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
      notes:
        "Review dataset, formulation, solver budget, feasibility, and claim boundary before publication.",
    },
    artifacts: [
      "q2-benchmark.json",
      "q2-solver-results.csv",
      "q2-qubo-matrix.csv",
    ],
    notes:
      "Q2 browser-based ideal-statevector reproduction. No hardware or quantum-advantage claim.",
    createdAt: result.generatedAt,
    updatedAt: new Date().toISOString(),
  };
}

export function q2SolverRows(result) {
  const solverEntries = [
    ["Exact enumeration", result.solvers.exact],
    ["Greedy", result.solvers.greedy],
    ["Simulated annealing", result.solvers.simulatedAnnealing],
    ["QAOA p=1 statevector", result.solvers.qaoa],
  ];

  return solverEntries.map(([solver, record]) => ({
    solver,
    feasible: record.best?.feasible ?? false,
    energy: record.best?.energy ?? "",
    utility: record.best?.utility ?? "",
    usedBudget: record.best?.usedBudget ?? "",
    selectedIds: record.best?.selectedIds?.join("|") || "",
    utilityGap: record.comparison?.utilityGap ?? "",
    relativeUtilityGap: record.comparison?.relativeUtilityGap ?? "",
    exactMatch: record.comparison?.exactMatch ?? false,
    objectiveEvaluations:
      record.objectiveEvaluations ??
      record.parameterEvaluations ??
      "",
    shots: record.shots ?? "",
    seed: record.seed ?? "",
  }));
}

export function rowsToCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    const text = String(value ?? "");
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  return [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => escape(row[header])).join(",")),
  ].join("\n");
}

export function quboMatrixToCsv(result) {
  const names = result.qubo.variables.map((variable) => variable.name);
  return [
    ["variable", ...names].join(","),
    ...result.qubo.matrix.map((row, index) =>
      [names[index], ...row].join(","),
    ),
  ].join("\n");
}
