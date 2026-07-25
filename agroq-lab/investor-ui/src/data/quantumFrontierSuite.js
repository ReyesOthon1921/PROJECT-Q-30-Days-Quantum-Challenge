import {
  normalRandom,
  seededRandom,
  sha256,
} from "./quantumSuiteCore.js";

function movingAverage(values, windowSize = 7) {
  return values.map((_, index) => {
    const start = Math.max(0, index - windowSize + 1);
    const slice = values.slice(start, index + 1);
    return slice.reduce((sum, value) => sum + value, 0) / slice.length;
  });
}

function generatePlantMagneticSignal(seed = 301) {
  const random = seededRandom(seed);
  const points = [];
  const eventCenter = 4.8;
  const eventWidth = 0.42;
  const amplitudePt = 0.55;

  for (let index = 0; index < 240; index += 1) {
    const time = index * 0.05;
    const event =
      amplitudePt *
      Math.exp(-((time - eventCenter) ** 2) / (2 * eventWidth ** 2));
    const drift = 0.025 * Math.sin(time * 0.55);
    const noise = normalRandom(random) * 0.09;
    points.push({
      time,
      truth: event + drift,
      measured: event + drift + noise,
    });
  }

  const filtered = movingAverage(
    points.map((point) => point.measured),
    9,
  );
  const baseline = filtered.slice(0, 60);
  const baselineMean =
    baseline.reduce((sum, value) => sum + value, 0) / baseline.length;
  const baselineVariance =
    baseline.reduce(
      (sum, value) => sum + (value - baselineMean) ** 2,
      0,
    ) / baseline.length;
  const baselineStd = Math.sqrt(baselineVariance);
  const peak = Math.max(...filtered);
  const peakIndex = filtered.indexOf(peak);

  return {
    points: points.map((point, index) => ({
      ...point,
      filtered: filtered[index],
    })),
    amplitudePt,
    detectedPeakPt: peak,
    detectedTime: points[peakIndex].time,
    baselineStdPt: baselineStd,
    snr: baselineStd === 0 ? 0 : (peak - baselineMean) / baselineStd,
    detectionThresholdPt: baselineMean + 4 * baselineStd,
  };
}

function lorentzian(x, center, width) {
  return 1 / (1 + ((x - center) / width) ** 2);
}

function generateNvOdMr(seed = 301, fieldMicroTesla = 18, temperatureC = 28) {
  const random = seededRandom(seed);
  const zeroFieldGHz = 2.87;
  const temperatureShiftGHz = -0.000074 * (temperatureC - 25);
  const zeemanGHz = 0.000028 * fieldMicroTesla;
  const centers = [
    zeroFieldGHz + temperatureShiftGHz - zeemanGHz,
    zeroFieldGHz + temperatureShiftGHz + zeemanGHz,
  ];
  const width = 0.00035;
  const points = [];

  for (let index = 0; index <= 400; index += 1) {
    const frequencyGHz = 2.866 + index * 0.00002;
    const contrast =
      1 -
      0.065 * lorentzian(frequencyGHz, centers[0], width) -
      0.065 * lorentzian(frequencyGHz, centers[1], width) +
      normalRandom(random) * 0.0018;
    points.push({ frequencyGHz, contrast });
  }

  const minima = [...points]
    .sort((left, right) => left.contrast - right.contrast)
    .reduce((selected, point) => {
      if (
        selected.every(
          (candidate) =>
            Math.abs(candidate.frequencyGHz - point.frequencyGHz) > 0.00045,
        )
      ) {
        selected.push(point);
      }
      return selected;
    }, [])
    .slice(0, 2)
    .sort((left, right) => left.frequencyGHz - right.frequencyGHz);

  const estimatedCenter =
    minima.reduce((sum, point) => sum + point.frequencyGHz, 0) /
    minima.length;
  const estimatedSplit =
    minima.length === 2
      ? (minima[1].frequencyGHz - minima[0].frequencyGHz) / 2
      : 0;
  const estimatedFieldMicroTesla = estimatedSplit / 0.000028;
  const estimatedTemperatureC =
    25 + (zeroFieldGHz - estimatedCenter) / 0.000074;

  return {
    points,
    truth: { fieldMicroTesla, temperatureC, centers },
    estimate: {
      resonanceCentersGHz: minima.map((point) => point.frequencyGHz),
      fieldMicroTesla: estimatedFieldMicroTesla,
      temperatureC: estimatedTemperatureC,
      fieldAbsoluteError: Math.abs(
        estimatedFieldMicroTesla - fieldMicroTesla,
      ),
      temperatureAbsoluteError: Math.abs(
        estimatedTemperatureC - temperatureC,
      ),
    },
    boundary:
      "Synthetic ODMR spectrum. No NV-diamond device is connected to AgroQ.",
  };
}

export async function runQ8QuantumSensing(options = {}) {
  const seed = Number(options.seed) || 301;
  const plantMagnetism = generatePlantMagneticSignal(seed);
  const nvOdMr = generateNvOdMr(
    seed + 11,
    Number(options.fieldMicroTesla) || 18,
    Number(options.temperatureC) || 28,
  );

  return {
    sequence: "Q8",
    experimentId: `AGQ-Q8-${Date.now()}`,
    title: "Quantum sensing simulation workspace",
    sourceIds: ["QRS-008", "QRS-009"],
    datasetHash: await sha256({ plantMagnetism, nvOdMr }),
    plantMagnetism,
    nvOdMr,
    controls: {
      syntheticSignals: true,
      hardwareConnected: false,
      diagnosticClaim: false,
      automatedActuation: false,
      humanReviewRequired: true,
    },
  };
}

function exactGroundEnergy2x2(a, b, d) {
  const trace = a + d;
  const discriminant = Math.sqrt((a - d) ** 2 + 4 * b ** 2);
  return (trace - discriminant) / 2;
}

function variationalEnergy(theta, hamiltonian) {
  const c = Math.cos(theta / 2);
  const s = Math.sin(theta / 2);
  return (
    hamiltonian.a * c ** 2 +
    2 * hamiltonian.b * c * s +
    hamiltonian.d * s ** 2
  );
}

function runToyVqe(gridPoints = 721) {
  const hamiltonian = {
    label: "H2-inspired reduced two-level educational Hamiltonian",
    a: -1.0,
    b: 0.2,
    d: -0.5,
    units: "arbitrary energy units",
  };
  const exactEnergy = exactGroundEnergy2x2(
    hamiltonian.a,
    hamiltonian.b,
    hamiltonian.d,
  );
  let best = null;
  const curve = [];

  for (let index = 0; index < gridPoints; index += 1) {
    const theta = (2 * Math.PI * index) / (gridPoints - 1);
    const energy = variationalEnergy(theta, hamiltonian);
    curve.push({ theta, energy });
    if (!best || energy < best.energy) best = { theta, energy };
  }

  return {
    hamiltonian,
    exactEnergy,
    variational: best,
    absoluteError: Math.abs(best.energy - exactEnergy),
    curve: curve.filter((_, index) => index % 12 === 0),
    ansatz: "Single-parameter RY state on one logical qubit",
    boundary:
      "Educational two-level VQE benchmark, not a chemistry-grade H2 or FeMoco calculation.",
  };
}

function chemistryResourceTable() {
  return [
    {
      system: "Two-level educational model",
      logicalQubits: 1,
      estimatedPauliTerms: 3,
      stage: "Active simulator",
      evidence: "QRS-010",
    },
    {
      system: "Small molecular active-space example",
      logicalQubits: "4–12",
      estimatedPauliTerms: "tens to hundreds",
      stage: "Later simulator",
      evidence: "QRS-010",
    },
    {
      system: "FeMoco resource-analysis literature",
      logicalQubits: "fault-tolerant scale",
      estimatedPauliTerms: "large active space",
      stage: "Literature registry only",
      evidence: "QRS-011",
    },
  ];
}

export async function runQ9QuantumChemistry() {
  const vqe = runToyVqe();
  const resources = chemistryResourceTable();

  return {
    sequence: "Q9",
    experimentId: `AGQ-Q9-${Date.now()}`,
    title: "Quantum chemistry and resource-estimation workspace",
    sourceIds: ["QRS-010", "QRS-011"],
    datasetHash: await sha256({ vqe, resources }),
    vqe,
    resources,
    controls: {
      educationalToyModel: true,
      chemistryGradeClaim: false,
      feMocoSimulationClaim: false,
      hardwareUsed: false,
      advantageClaim: false,
      humanReviewRequired: true,
    },
  };
}

export const postQuantumStandards = [
  {
    standard: "FIPS 203",
    algorithm: "ML-KEM",
    use: "Key encapsulation",
    status: "Final standard",
    sourceId: "QRS-015",
  },
  {
    standard: "FIPS 204",
    algorithm: "ML-DSA",
    use: "Digital signatures",
    status: "Final standard",
    sourceId: "QRS-015",
  },
  {
    standard: "FIPS 205",
    algorithm: "SLH-DSA",
    use: "Stateless hash-based signatures",
    status: "Final standard",
    sourceId: "QRS-015",
  },
];

export const initialCryptoInventory = [
  {
    id: "PQC-001",
    system: "Edge gateway transport",
    current: "TLS library inventory pending",
    target: "Crypto-agile hybrid transition",
    owner: "Platform engineering",
    stage: "Inventory",
    approvedLibrarySelected: false,
    interoperabilityTested: false,
    rollbackDocumented: false,
  },
  {
    id: "PQC-002",
    system: "Signed experiment exports",
    current: "Application signature policy pending",
    target: "ML-DSA-capable signature profile",
    owner: "Research governance",
    stage: "Planning",
    approvedLibrarySelected: false,
    interoperabilityTested: false,
    rollbackDocumented: true,
  },
  {
    id: "PQC-003",
    system: "Sensor firmware releases",
    current: "Vendor-specific signatures",
    target: "Crypto-agile firmware verification",
    owner: "Device engineering",
    stage: "Research",
    approvedLibrarySelected: false,
    interoperabilityTested: false,
    rollbackDocumented: false,
  },
  {
    id: "PQC-004",
    system: "Long-lived research archives",
    current: "Retention risk review pending",
    target: "Post-quantum migration classification",
    owner: "Data governance",
    stage: "Inventory",
    approvedLibrarySelected: false,
    interoperabilityTested: false,
    rollbackDocumented: true,
  },
];

export function scoreCryptoInventory(inventory) {
  const checks = inventory.flatMap((item) => [
    item.current !== "Unknown",
    Boolean(item.target),
    Boolean(item.owner),
    item.approvedLibrarySelected,
    item.interoperabilityTested,
    item.rollbackDocumented,
  ]);
  const completed = checks.filter(Boolean).length;
  return {
    completed,
    total: checks.length,
    percent: Math.round((completed / checks.length) * 100),
  };
}

export async function runQ10PostQuantumSecurity(
  inventory = initialCryptoInventory,
) {
  const readiness = scoreCryptoInventory(inventory);

  return {
    sequence: "Q10",
    experimentId: `AGQ-Q10-${Date.now()}`,
    title: "Post-quantum security registry",
    sourceIds: ["QRS-015"],
    datasetHash: await sha256({ postQuantumStandards, inventory }),
    standards: postQuantumStandards,
    inventory,
    readiness,
    controls: {
      cryptographicImplementationIncluded: false,
      approvedLibraryRequired: true,
      interoperabilityTestingRequired: true,
      rollbackRequired: true,
      productionMigrationAuthorized: false,
      humanSecurityReviewRequired: true,
    },
    boundary:
      "Registry and migration-planning prototype only. It does not implement or replace production cryptography.",
  };
}

export function buildFrontierExperimentRecord(result) {
  return {
    schemaId: "AGROQ-QER-1.0",
    experimentId: result.experimentId,
    sequence: result.sequence,
    title: result.title,
    sourceIds: result.sourceIds,
    researchOwner: "AgroQ Research Team",
    codeCommit: "browser-suite-q3-q10",
    problemFamily:
      result.sequence === "Q8"
        ? "Quantum-sensor signal simulation"
        : result.sequence === "Q9"
          ? "Molecular energy and resource estimation"
          : "Cryptographic migration and interoperability",
    status:
      result.sequence === "Q10"
        ? "Registry complete"
        : "Simulation complete",
    runType:
      result.sequence === "Q10"
        ? "standards-registry"
        : "quantum-simulator",
    algorithm:
      result.sequence === "Q8"
        ? "Synthetic OPM and NV ODMR signal analysis"
        : result.sequence === "Q9"
          ? "Exact 2x2 diagonalization and one-parameter VQE"
          : "NIST post-quantum standards and migration inventory",
    seed: result.sequence === "Q8" ? 301 : null,
    runBudget: {
      objectiveEvaluations:
        result.sequence === "Q9" ? 721 : null,
      wallClockSeconds: null,
      shots: 0,
      matchedAcrossSolvers: result.sequence === "Q9",
    },
    dataset: {
      id: `${result.sequence}-SYNTHETIC-001`,
      hash: result.datasetHash,
      version: "1.0.0",
      frozen: true,
      records:
        result.sequence === "Q8"
          ? result.plantMagnetism.points.length + result.nvOdMr.points.length
          : result.sequence === "Q9"
            ? result.resources.length
            : result.inventory.length,
    },
    formulation: {
      type:
        result.sequence === "Q8"
          ? "Signal simulation and calibration"
          : result.sequence === "Q9"
            ? "Variational energy minimization"
            : "Security control registry",
      hash: result.datasetHash,
      variables: result.sequence === "Q9" ? 1 : null,
      constraints: 0,
      objective: result.title,
    },
    classicalBaseline: {
      required: result.sequence !== "Q10",
      algorithm:
        result.sequence === "Q8"
          ? "Known synthetic truth"
          : result.sequence === "Q9"
            ? "Exact eigenvalue"
            : "Standards conformance review",
      objective:
        result.sequence === "Q8"
          ? result.nvOdMr.estimate.fieldAbsoluteError
          : result.sequence === "Q9"
            ? result.vqe.exactEnergy
            : result.readiness.percent,
      feasible: true,
      runtimeSeconds: null,
      budget: "Prototype",
    },
    execution: {
      backend: "Browser analytic simulator",
      provider: "AgroQ local prototype",
      shots: 0,
      circuitDepth: result.sequence === "Q9" ? 1 : null,
      twoQubitGates: 0,
      qubits: result.sequence === "Q9" ? 1 : null,
      noiseModel: result.sequence === "Q8" ? "Synthetic Gaussian noise" : "None",
      optimizer:
        result.sequence === "Q9" ? "Deterministic theta grid" : "Not applicable",
    },
    metrics: {
      objective:
        result.sequence === "Q8"
          ? result.plantMagnetism.snr
          : result.sequence === "Q9"
            ? result.vqe.absoluteError
            : result.readiness.percent,
      feasible: true,
      constraintViolations: 0,
      approximationGap:
        result.sequence === "Q9" ? result.vqe.absoluteError : null,
      runtimeSeconds: null,
      confidenceInterval: null,
    },
    claimControls: {
      simulatorOnly: result.sequence !== "Q10",
      hardwareUsed: false,
      advantageClaim: false,
      operationalDependency: false,
      matchedBudget: result.sequence === "Q9",
      classicalBaselineRequired: result.sequence !== "Q10",
      syntheticData: result.sequence !== "Q10",
    },
    humanReview: {
      required: true,
      status: "Pending",
      reviewer: "",
      notes:
        result.sequence === "Q10"
          ? "Security and legal review required before any migration."
          : "Review scientific boundaries and simulator assumptions.",
    },
    artifacts: [`${result.sequence.toLowerCase()}-results.json`],
    notes:
      result.sequence === "Q10"
        ? result.boundary
        : "Synthetic research simulator record.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}
