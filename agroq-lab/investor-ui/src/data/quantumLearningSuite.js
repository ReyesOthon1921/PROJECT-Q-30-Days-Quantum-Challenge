import {
  classificationMetrics,
  kernelRidgeClassifier,
  normalRandom,
  predictLinear,
  regressionMetrics,
  ridgeRegression,
  seededRandom,
  sha256,
} from "./quantumSuiteCore.js";

function createStressDataset(seed = 301) {
  const random = seededRandom(seed);
  const rows = [];

  for (let index = 0; index < 48; index += 1) {
    const moisture = 0.25 + random() * 0.55;
    const temperature = 18 + random() * 18;
    const ec = 0.15 + random() * 1.1;
    const canopy = 0.35 + random() * 0.6;
    const hiddenScore =
      2.4 * (0.5 - moisture) +
      0.08 * (temperature - 28) +
      0.7 * (ec - 0.65) +
      1.2 * (0.65 - canopy) +
      normalRandom(random) * 0.12;
    rows.push({
      id: `STRESS-${String(index + 1).padStart(3, "0")}`,
      features: [moisture, temperature / 40, ec / 1.5, canopy],
      raw: { moisture, temperature, ec, canopy },
      label: hiddenScore > 0.35 ? 1 : 0,
    });
  }

  return rows;
}

function rbfKernel(left, right, gamma = 2.2) {
  const squaredDistance = left.reduce(
    (sum, value, index) => sum + (value - right[index]) ** 2,
    0,
  );
  return Math.exp(-gamma * squaredDistance);
}

function complexFeatureMap(features) {
  const [moisture, temperature, ec, canopy] = features;
  const a = (Math.PI / 2) * moisture;
  const b = (Math.PI / 2) * canopy;
  const c = Math.PI * temperature;
  const d = Math.PI * ec;
  const phases = [0, c, d, c + d + Math.PI * moisture * ec];
  const amplitudes = [
    Math.cos(a) * Math.cos(b),
    Math.cos(a) * Math.sin(b),
    Math.sin(a) * Math.cos(b),
    Math.sin(a) * Math.sin(b),
  ];

  return amplitudes.map((magnitude, index) => ({
    real: magnitude * Math.cos(phases[index]),
    imaginary: magnitude * Math.sin(phases[index]),
  }));
}

function quantumKernel(left, right) {
  const a = complexFeatureMap(left);
  const b = complexFeatureMap(right);
  let real = 0;
  let imaginary = 0;

  for (let index = 0; index < a.length; index += 1) {
    real +=
      a[index].real * b[index].real +
      a[index].imaginary * b[index].imaginary;
    imaginary +=
      a[index].real * b[index].imaginary -
      a[index].imaginary * b[index].real;
  }
  return real ** 2 + imaginary ** 2;
}

export async function runQ5QuantumKernel(options = {}) {
  const seed = Number(options.seed) || 301;
  const dataset = createStressDataset(seed);
  const train = dataset.filter((_, index) => index % 4 !== 0);
  const test = dataset.filter((_, index) => index % 4 === 0);
  const trainX = train.map((row) => row.features);
  const trainY = train.map((row) => row.label);
  const testX = test.map((row) => row.features);
  const testY = test.map((row) => row.label);

  const classical = kernelRidgeClassifier(
    trainX,
    trainY,
    testX,
    rbfKernel,
    0.15,
  );
  const quantum = kernelRidgeClassifier(
    trainX,
    trainY,
    testX,
    quantumKernel,
    0.15,
  );
  const datasetHash = await sha256(dataset);

  return {
    sequence: "Q5",
    experimentId: `AGQ-Q5-${Date.now()}`,
    title: "Quantum-kernel stress classifier",
    sourceIds: ["QRS-005", "QRS-014"],
    datasetHash,
    dataset: {
      records: dataset.length,
      train: train.length,
      test: test.length,
      features: ["soil moisture", "temperature", "EC", "canopy proxy"],
      synthetic: true,
    },
    classical: {
      method: "RBF kernel ridge classifier",
      metrics: classificationMetrics(testY, classical.predictions),
      scores: classical.scores,
      predictions: classical.predictions,
    },
    quantum: {
      method: "Two-qubit pure-state fidelity kernel",
      qubits: 2,
      metrics: classificationMetrics(testY, quantum.predictions),
      scores: quantum.scores,
      predictions: quantum.predictions,
      simulator: "Analytic statevector feature map",
    },
    testRows: test.map((row, index) => ({
      id: row.id,
      actual: row.label,
      classical: classical.predictions[index],
      quantum: quantum.predictions[index],
      ...row.raw,
    })),
    controls: {
      identicalSplit: true,
      identicalRegularization: true,
      syntheticData: true,
      hardwareUsed: false,
      advantageClaim: false,
      humanReviewRequired: true,
    },
  };
}

function createTimeSeries(seed = 301, length = 150) {
  const random = seededRandom(seed);
  const rows = [];
  let moisture = 0.62;

  for (let time = 0; time < length; time += 1) {
    const temperature =
      27 + 6 * Math.sin((2 * Math.PI * time) / 24) + normalRandom(random) * 0.8;
    const rain = random() < 0.08 ? 0.05 + random() * 0.1 : 0;
    const irrigation = time % 31 === 0 ? 0.09 : 0;
    const evapotranspiration = 0.012 + Math.max(0, temperature - 24) * 0.0012;
    moisture =
      0.9 * moisture +
      rain +
      irrigation -
      evapotranspiration +
      normalRandom(random) * 0.005;
    moisture = Math.max(0.18, Math.min(0.82, moisture));
    rows.push({ time, moisture, temperature: temperature / 40, rain, irrigation });
  }
  return rows;
}

function createSupervisedSeries(rows) {
  const features = [];
  const targets = [];
  for (let index = 2; index < rows.length - 1; index += 1) {
    features.push([
      1,
      rows[index].moisture,
      rows[index - 1].moisture,
      rows[index].temperature,
      rows[index].rain,
      rows[index].irrigation,
    ]);
    targets.push(rows[index + 1].moisture);
  }
  return { features, targets };
}

function classicalReservoirFeatures(inputs, seed = 301, nodes = 8) {
  const random = seededRandom(seed);
  const state = Array(nodes).fill(0);
  const inputWeights = Array.from({ length: nodes }, () =>
    Array.from({ length: inputs[0].length }, () => (random() - 0.5) * 1.4),
  );
  const recurrent = Array.from({ length: nodes }, () =>
    Array.from({ length: nodes }, () => (random() - 0.5) * 0.45),
  );
  const output = [];

  inputs.forEach((input) => {
    const next = state.map((_, node) => {
      const driven = input.reduce(
        (sum, value, index) => sum + value * inputWeights[node][index],
        0,
      );
      const memory = state.reduce(
        (sum, value, index) => sum + value * recurrent[node][index],
        0,
      );
      return Math.tanh(driven + memory);
    });
    state.splice(0, state.length, ...next);
    output.push([1, ...state]);
  });
  return output;
}

function applyRy(state, qubit, angle) {
  const cosine = Math.cos(angle / 2);
  const sine = Math.sin(angle / 2);
  const mask = 1 << qubit;
  for (let basis = 0; basis < state.length; basis += 1) {
    if (basis & mask) continue;
    const paired = basis | mask;
    const a = state[basis];
    const b = state[paired];
    state[basis] = {
      real: cosine * a.real - sine * b.real,
      imaginary: cosine * a.imaginary - sine * b.imaginary,
    };
    state[paired] = {
      real: sine * a.real + cosine * b.real,
      imaginary: sine * a.imaginary + cosine * b.imaginary,
    };
  }
}

function applyRz(state, qubit, angle) {
  const mask = 1 << qubit;
  state.forEach((amplitude, basis) => {
    const phase = (basis & mask ? 1 : -1) * angle / 2;
    const cosine = Math.cos(phase);
    const sine = Math.sin(phase);
    state[basis] = {
      real: amplitude.real * cosine - amplitude.imaginary * sine,
      imaginary: amplitude.real * sine + amplitude.imaginary * cosine,
    };
  });
}

function applyCnot(state, control, target) {
  const controlMask = 1 << control;
  const targetMask = 1 << target;
  for (let basis = 0; basis < state.length; basis += 1) {
    if (!(basis & controlMask) || basis & targetMask) continue;
    const paired = basis | targetMask;
    [state[basis], state[paired]] = [state[paired], state[basis]];
  }
}

function zExpectation(state, qubit) {
  const mask = 1 << qubit;
  return state.reduce((sum, amplitude, basis) => {
    const probability = amplitude.real ** 2 + amplitude.imaginary ** 2;
    return sum + (basis & mask ? -probability : probability);
  }, 0);
}

function zzExpectation(state) {
  return state.reduce((sum, amplitude, basis) => {
    const probability = amplitude.real ** 2 + amplitude.imaginary ** 2;
    const z0 = basis & 1 ? -1 : 1;
    const z1 = basis & 2 ? -1 : 1;
    return sum + z0 * z1 * probability;
  }, 0);
}

function quantumReservoirFeatures(inputs) {
  const state = [
    { real: 1, imaginary: 0 },
    { real: 0, imaginary: 0 },
    { real: 0, imaginary: 0 },
    { real: 0, imaginary: 0 },
  ];
  return inputs.map((input, time) => {
    const moisture = input[1];
    const temperature = input[3];
    const rain = input[4];
    applyRy(state, 0, 0.45 + 1.8 * moisture);
    applyRy(state, 1, 0.2 + 1.4 * temperature + 3 * rain);
    applyCnot(state, 0, 1);
    applyRz(state, 0, 0.17 + time * 0.013);
    applyRz(state, 1, 0.31);
    return [1, zExpectation(state, 0), zExpectation(state, 1), zzExpectation(state)];
  });
}

export async function runQ6QuantumReservoir(options = {}) {
  const seed = Number(options.seed) || 301;
  const rows = createTimeSeries(seed);
  const supervised = createSupervisedSeries(rows);
  const split = Math.floor(supervised.features.length * 0.72);
  const trainInputs = supervised.features.slice(0, split);
  const testInputs = supervised.features.slice(split);
  const trainTargets = supervised.targets.slice(0, split);
  const testTargets = supervised.targets.slice(split);

  const linearWeights = ridgeRegression(trainInputs, trainTargets, 0.01);
  const linearPredictions = predictLinear(testInputs, linearWeights);
  const persistencePredictions = testInputs.map((row) => row[1]);

  const classicalAll = classicalReservoirFeatures(supervised.features, seed, 8);
  const classicalTrain = classicalAll.slice(0, split);
  const classicalTest = classicalAll.slice(split);
  const classicalWeights = ridgeRegression(classicalTrain, trainTargets, 0.02);
  const classicalPredictions = predictLinear(classicalTest, classicalWeights);

  const quantumAll = quantumReservoirFeatures(supervised.features);
  const quantumTrain = quantumAll.slice(0, split);
  const quantumTest = quantumAll.slice(split);
  const quantumWeights = ridgeRegression(quantumTrain, trainTargets, 0.02);
  const quantumPredictions = predictLinear(quantumTest, quantumWeights);

  return {
    sequence: "Q6",
    experimentId: `AGQ-Q6-${Date.now()}`,
    title: "Quantum reservoir time-series experiment",
    sourceIds: ["QRS-006", "QRS-014"],
    datasetHash: await sha256(rows),
    dataset: {
      records: rows.length,
      train: trainInputs.length,
      test: testInputs.length,
      synthetic: true,
    },
    methods: {
      persistence: {
        metrics: regressionMetrics(testTargets, persistencePredictions),
      },
      linear: {
        metrics: regressionMetrics(testTargets, linearPredictions),
      },
      classicalReservoir: {
        nodes: 8,
        metrics: regressionMetrics(testTargets, classicalPredictions),
      },
      quantumReservoir: {
        qubits: 2,
        observables: ["Z0", "Z1", "Z0Z1"],
        metrics: regressionMetrics(testTargets, quantumPredictions),
      },
    },
    preview: testTargets.slice(0, 20).map((actual, index) => ({
      actual,
      persistence: persistencePredictions[index],
      linear: linearPredictions[index],
      classicalReservoir: classicalPredictions[index],
      quantumReservoir: quantumPredictions[index],
    })),
    controls: {
      frozenChronologicalSplit: true,
      identicalTargets: true,
      simulatorOnly: true,
      advantageClaim: false,
      humanReviewRequired: true,
    },
  };
}

function binomialSample(trials, probability, random) {
  let successes = 0;
  for (let trial = 0; trial < trials; trial += 1) {
    if (random() < probability) successes += 1;
  }
  return successes;
}

function maximumLikelihoodAmplitudeEstimate(
  trueProbability,
  shotsPerCircuit,
  seed,
) {
  const random = seededRandom(seed);
  const powers = [0, 1, 2, 4];
  const observations = powers.map((power) => {
    const theta = Math.asin(Math.sqrt(trueProbability));
    const probability = Math.sin((2 * power + 1) * theta) ** 2;
    return {
      power,
      successes: binomialSample(shotsPerCircuit, probability, random),
      shots: shotsPerCircuit,
      probability,
    };
  });

  let best = null;
  const gridPoints = 4001;
  for (let index = 1; index < gridPoints - 1; index += 1) {
    const theta = (Math.PI / 2) * (index / (gridPoints - 1));
    let logLikelihood = 0;
    for (const observation of observations) {
      const probability = Math.max(
        1e-12,
        Math.min(
          1 - 1e-12,
          Math.sin((2 * observation.power + 1) * theta) ** 2,
        ),
      );
      logLikelihood +=
        observation.successes * Math.log(probability) +
        (observation.shots - observation.successes) *
          Math.log(1 - probability);
    }
    if (!best || logLikelihood > best.logLikelihood) {
      best = { theta, logLikelihood };
    }
  }

  return {
    estimate: Math.sin(best.theta) ** 2,
    observations,
    oracleApplications: observations.reduce(
      (sum, observation) =>
        sum + observation.shots * (2 * observation.power + 1),
      0,
    ),
  };
}

export async function runQ7AmplitudeEstimation(options = {}) {
  const seed = Number(options.seed) || 301;
  const trueProbability = Number(options.trueProbability) || 0.18;
  const shotsPerCircuit = Number(options.shotsPerCircuit) || 128;
  const random = seededRandom(seed);
  const monteCarloShots = shotsPerCircuit * 4;
  const monteCarloSuccesses = binomialSample(
    monteCarloShots,
    trueProbability,
    random,
  );
  const monteCarloEstimate = monteCarloSuccesses / monteCarloShots;
  const mlae = maximumLikelihoodAmplitudeEstimate(
    trueProbability,
    shotsPerCircuit,
    seed + 17,
  );

  return {
    sequence: "Q7",
    experimentId: `AGQ-Q7-${Date.now()}`,
    title: "Amplitude-estimation uncertainty experiment",
    sourceIds: ["QRS-007"],
    datasetHash: await sha256({
      trueProbability,
      seed,
      shotsPerCircuit,
    }),
    event:
      "Synthetic probability that soil moisture falls below the research threshold.",
    trueProbability,
    monteCarlo: {
      shots: monteCarloShots,
      estimate: monteCarloEstimate,
      absoluteError: Math.abs(monteCarloEstimate - trueProbability),
      queryCount: monteCarloShots,
    },
    maximumLikelihoodAmplitudeEstimation: {
      ...mlae,
      shotsPerCircuit,
      absoluteError: Math.abs(mlae.estimate - trueProbability),
      simulator: "Likelihood model over Grover powers",
    },
    controls: {
      knownSyntheticProbability: true,
      statePreparationCostExcluded: true,
      oracleConstructionCostExcluded: true,
      hardwareUsed: false,
      speedupClaim: false,
      humanReviewRequired: true,
    },
  };
}

export function buildLearningExperimentRecord(result) {
  const metricSource =
    result.sequence === "Q5"
      ? result.quantum.metrics
      : result.sequence === "Q6"
        ? result.methods.quantumReservoir.metrics
        : {
            objective:
              result.maximumLikelihoodAmplitudeEstimation.absoluteError,
          };

  return {
    schemaId: "AGROQ-QER-1.0",
    experimentId: result.experimentId,
    sequence: result.sequence,
    title: result.title,
    sourceIds: result.sourceIds,
    researchOwner: "AgroQ Research Team",
    codeCommit: "browser-suite-q3-q10",
    problemFamily:
      result.sequence === "Q5"
        ? "Supervised classification"
        : result.sequence === "Q6"
          ? "Temporal forecasting"
          : "Threshold probability estimation",
    status: "Simulation complete",
    runType: "quantum-simulator",
    algorithm:
      result.sequence === "Q5"
        ? "Classical RBF kernel and two-qubit fidelity kernel"
        : result.sequence === "Q6"
          ? "Persistence, linear, classical reservoir, and two-qubit reservoir"
          : "Monte Carlo and maximum-likelihood amplitude estimation",
    seed: 301,
    runBudget: {
      objectiveEvaluations: null,
      wallClockSeconds: null,
      shots:
        result.sequence === "Q7"
          ? result.maximumLikelihoodAmplitudeEstimation.observations.reduce(
              (sum, item) => sum + item.shots,
              0,
            )
          : 0,
      matchedAcrossSolvers: result.sequence !== "Q6",
    },
    dataset: {
      id: `${result.sequence}-SYNTHETIC-001`,
      hash: result.datasetHash,
      version: "1.0.0",
      frozen: true,
      records: result.dataset?.records || 1,
    },
    formulation: {
      type:
        result.sequence === "Q5"
          ? "Kernel classification"
          : result.sequence === "Q6"
            ? "Reservoir readout regression"
            : "Likelihood-based amplitude estimation",
      hash: result.datasetHash,
      variables: null,
      constraints: 0,
      objective: result.title,
    },
    classicalBaseline: {
      required: true,
      algorithm:
        result.sequence === "Q5"
          ? "RBF kernel ridge classifier"
          : result.sequence === "Q6"
            ? "Persistence and classical reservoir"
            : "Ordinary Monte Carlo",
      objective:
        result.sequence === "Q5"
          ? result.classical.metrics.accuracy
          : result.sequence === "Q6"
            ? result.methods.classicalReservoir.metrics.rmse
            : result.monteCarlo.absoluteError,
      feasible: true,
      runtimeSeconds: null,
      budget: "Declared in result artifact",
    },
    execution: {
      backend: "Browser analytic simulator",
      provider: "AgroQ local prototype",
      shots: result.sequence === "Q7" ? 512 : 0,
      circuitDepth: null,
      twoQubitGates: null,
      qubits:
        result.sequence === "Q5"
          ? result.quantum.qubits
          : result.sequence === "Q6"
            ? result.methods.quantumReservoir.qubits
            : null,
      noiseModel: "Synthetic sampling only",
      optimizer: "Deterministic local computation",
    },
    metrics: {
      objective:
        metricSource.accuracy ??
        metricSource.rmse ??
        metricSource.objective ??
        null,
      feasible: true,
      constraintViolations: 0,
      approximationGap: null,
      runtimeSeconds: null,
      confidenceInterval: null,
    },
    claimControls: {
      simulatorOnly: true,
      hardwareUsed: false,
      advantageClaim: false,
      operationalDependency: false,
      matchedBudget: result.sequence !== "Q6",
      classicalBaselineRequired: true,
      syntheticData: true,
    },
    humanReview: {
      required: true,
      status: "Pending",
      reviewer: "",
      notes: "Review data split, metrics, resource boundaries, and claims.",
    },
    artifacts: [`${result.sequence.toLowerCase()}-results.json`],
    notes: "Synthetic simulator research record.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}
