export const quantumResearchSources = [
  {
    id: "QRS-001",
    sequence: ["Q0", "Q2", "Q3", "Q4"],
    title: "Quantum Bridge Analytics I: A Tutorial on Formulating and Using QUBO Models",
    authors: ["Fred Glover", "Gary Kochenberger", "Yu Du"],
    year: 2019,
    venue: "4OR",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1007/s10288-019-00424-y",
    url: "https://doi.org/10.1007/s10288-019-00424-y",
    mechanism: "Quadratic unconstrained binary optimization, penalty construction, and binary model reformulation.",
    agroqFeature: "Common QUBO contract for soil sampling, irrigation, graph partitioning, sensor placement, and scheduling.",
    reproductionTarget: "Translate a frozen AgroQ decision problem into a documented QUBO and verify it with exact enumeration on small instances.",
    evidenceStatus: "Foundation",
    limitations: "QUBO compatibility does not establish that a quantum solver will outperform a classical solver.",
    acknowledgment: "AgroQ credits Glover, Kochenberger, and Du for the QUBO formulation framework used by the research lane.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["QUBO", "optimization", "classical baseline"],
  },
  {
    id: "QRS-002",
    sequence: ["Q0", "Q2", "Q3", "Q4"],
    title: "A Quantum Approximate Optimization Algorithm",
    authors: ["Edward Farhi", "Jeffrey Goldstone", "Sam Gutmann"],
    year: 2014,
    venue: "arXiv",
    publicationStatus: "Preprint / foundational algorithm",
    identifier: "arXiv:1411.4028",
    url: "https://arxiv.org/abs/1411.4028",
    mechanism: "Alternating cost and mixer Hamiltonians with classically optimized circuit parameters.",
    agroqFeature: "QAOA simulator experiments for frozen QUBO benchmarks.",
    reproductionTarget: "Reproduce small MaxCut or QUBO examples and compare with exact and classical heuristic baselines.",
    evidenceStatus: "Foundation",
    limitations: "Near-term simulator or hardware results do not by themselves demonstrate practical quantum advantage.",
    acknowledgment: "AgroQ credits Farhi, Goldstone, and Gutmann for the foundational QAOA method.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["QAOA", "variational", "optimization"],
  },
  {
    id: "QRS-003",
    sequence: ["Q2", "Q3", "Q4"],
    title: "Warm-starting quantum optimization",
    authors: ["Daniel J. Egger", "Jakub Mareček", "Stefan Woerner"],
    year: 2021,
    venue: "Quantum",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.22331/q-2021-06-17-479",
    url: "https://doi.org/10.22331/q-2021-06-17-479",
    mechanism: "Use a classical relaxation or incumbent solution to initialize a variational quantum optimization process.",
    agroqFeature: "Warm-start QAOA using the required AgroQ classical baseline.",
    reproductionTarget: "Compare standard and warm-start QAOA on the same frozen sample-selection and sensor-placement instances.",
    evidenceStatus: "Reproduction candidate",
    limitations: "Benefits depend on formulation, relaxation quality, circuit design, optimization method, and noise.",
    acknowledgment: "AgroQ credits Egger, Mareček, and Woerner for the warm-start quantum optimization method.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["warm start", "QAOA", "hybrid"],
  },
  {
    id: "QRS-004",
    sequence: ["Q2", "Q3", "Q4"],
    title: "Adaptive quantum approximate optimization algorithm for solving combinatorial problems on a quantum computer",
    authors: ["Linghua Zhu", "Ho Lun Tang", "George S. Barron", "F. A. Calderon-Vargas", "Nicholas J. Mayhall", "Edwin Barnes", "Sophia E. Economou"],
    year: 2022,
    venue: "Physical Review Research",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1103/PhysRevResearch.4.033029",
    url: "https://doi.org/10.1103/PhysRevResearch.4.033029",
    mechanism: "Build a problem-adapted variational ansatz iteratively from an operator pool.",
    agroqFeature: "Later ADAPT-QAOA comparison for small AgroQ optimization benchmarks.",
    reproductionTarget: "Reproduce a small graph benchmark before applying the method to AgroQ decision graphs.",
    evidenceStatus: "Later experiment",
    limitations: "Adaptive circuit construction can add measurement and optimization overhead.",
    acknowledgment: "AgroQ credits Zhu and collaborators for the ADAPT-QAOA framework.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["ADAPT-QAOA", "ansatz", "optimization"],
  },
  {
    id: "QRS-005",
    sequence: ["Q5"],
    title: "Supervised learning with quantum-enhanced feature spaces",
    authors: ["Vojtěch Havlíček", "Antonio D. Córcoles", "Kristan Temme", "Aram W. Harrow", "Abhinav Kandala", "Jerry M. Chow", "Jay M. Gambetta"],
    year: 2019,
    venue: "Nature",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1038/s41586-019-0980-2",
    url: "https://doi.org/10.1038/s41586-019-0980-2",
    mechanism: "Quantum feature maps, quantum kernel estimation, and variational classification.",
    agroqFeature: "Quantum-kernel stress and sensor-state classifier benchmarked against classical SVM and tree models.",
    reproductionTarget: "Use identical train/test splits, seeds, scaling, and metrics for classical and simulated quantum kernels.",
    evidenceStatus: "Reproduction candidate",
    limitations: "Quantum kernels can concentrate or fail to provide useful separation; classical baselines remain mandatory.",
    acknowledgment: "AgroQ credits Havlíček and collaborators for the quantum feature-space and kernel methods.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["quantum kernel", "classification", "QML"],
  },
  {
    id: "QRS-006",
    sequence: ["Q6"],
    title: "Harnessing Disordered-Ensemble Quantum Dynamics for Machine Learning",
    authors: ["Keisuke Fujii", "Kohei Nakajima"],
    year: 2017,
    venue: "Physical Review Applied",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1103/PhysRevApplied.8.024030",
    url: "https://doi.org/10.1103/PhysRevApplied.8.024030",
    mechanism: "Quantum reservoir computing for temporal processing using fixed quantum dynamics and trained classical readout.",
    agroqFeature: "Time-series benchmark for moisture, temperature, EC, rainfall, and plant-health signals.",
    reproductionTarget: "Compare persistence, linear, classical reservoir, and simulated quantum reservoir models under frozen data splits.",
    evidenceStatus: "Reproduction candidate",
    limitations: "Performance depends on encoding, reservoir dynamics, readout, noise, and fair hyperparameter budgets.",
    acknowledgment: "AgroQ credits Fujii and Nakajima for the quantum reservoir computing framework.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["quantum reservoir", "time series", "forecasting"],
  },
  {
    id: "QRS-007",
    sequence: ["Q7"],
    title: "Quantum Amplitude Amplification and Estimation",
    authors: ["Gilles Brassard", "Peter Høyer", "Michele Mosca", "Alain Tapp"],
    year: 2000,
    venue: "arXiv / AMS proceedings",
    publicationStatus: "Foundational paper",
    identifier: "arXiv:quant-ph/0005055",
    url: "https://arxiv.org/abs/quant-ph/0005055",
    mechanism: "Estimate amplitudes or event probabilities through amplitude amplification and phase-estimation ideas.",
    agroqFeature: "Uncertainty and threshold-probability experiment compared with ordinary Monte Carlo.",
    reproductionTarget: "Estimate a synthetic low-moisture or sensor-failure probability using exact probability, Monte Carlo, and simulated amplitude estimation.",
    evidenceStatus: "Reproduction candidate",
    limitations: "State preparation, oracle design, circuit depth, and noise can dominate practical cost.",
    acknowledgment: "AgroQ credits Brassard, Høyer, Mosca, and Tapp for amplitude amplification and estimation.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["amplitude estimation", "probability", "uncertainty"],
  },
  {
    id: "QRS-008",
    sequence: ["Q8"],
    title: "Action potentials induce biomagnetic fields in carnivorous Venus flytrap plants",
    authors: ["Anne Fabricant", "Wenjing I. H. Iwata", "Paulo Schwindt", "Eric A. S. Laub"],
    year: 2021,
    venue: "Scientific Reports",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1038/s41598-021-81114-w",
    url: "https://doi.org/10.1038/s41598-021-81114-w",
    mechanism: "Optically pumped magnetometry used to observe magnetic fields associated with plant electrical activity.",
    agroqFeature: "Quantum-sensing signal simulator, calibration records, and signal-to-noise experiments.",
    reproductionTarget: "Reproduce signal-processing and detection logic with published-scale synthetic traces before considering hardware.",
    evidenceStatus: "Simulation candidate",
    limitations: "The published experiment used sensitive instrumentation and controlled conditions; AgroQ has no active biomagnetic sensor.",
    acknowledgment: "AgroQ credits Fabricant and collaborators for the plant biomagnetism experiment.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["quantum sensing", "plant signals", "magnetometry"],
  },
  {
    id: "QRS-009",
    sequence: ["Q8"],
    title: "A CMOS-integrated quantum sensor based on nitrogen-vacancy centres",
    authors: ["Donggyu Kim", "Mohamed Ibrahim", "Christopher Foy", "Matthew Trusheim", "Ruonan Han", "Dirk Englund"],
    year: 2019,
    venue: "Nature Electronics",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1038/s41928-019-0275-5",
    url: "https://doi.org/10.1038/s41928-019-0275-5",
    mechanism: "Integrated nitrogen-vacancy-center magnetometry and thermometry with optical and microwave control.",
    agroqFeature: "NV-center ODMR simulator, calibration workflow, and future hardware adapter specification.",
    reproductionTarget: "Simulate ODMR spectra and estimate field or temperature shifts under controlled synthetic noise.",
    evidenceStatus: "Simulation candidate",
    limitations: "AgroQ is not fabricating or operating an NV sensor in the current phase.",
    acknowledgment: "AgroQ credits Kim and collaborators for the integrated NV quantum-sensor system.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["NV center", "magnetometry", "thermometry"],
  },
  {
    id: "QRS-010",
    sequence: ["Q9"],
    title: "A variational eigenvalue solver on a photonic quantum processor",
    authors: ["Alberto Peruzzo", "Jarrod McClean", "Peter Shadbolt", "Man-Hong Yung", "Xiao-Qi Zhou", "Peter J. Love", "Alán Aspuru-Guzik", "Jeremy L. O'Brien"],
    year: 2014,
    venue: "Nature Communications",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1038/ncomms5213",
    url: "https://doi.org/10.1038/ncomms5213",
    mechanism: "Hybrid variational estimation of quantum-system energies.",
    agroqFeature: "Small-molecule VQE and resource-estimation education workspace.",
    reproductionTarget: "Begin with simulator-only H2 or another small published benchmark and compare against exact reference energy.",
    evidenceStatus: "Reproduction candidate",
    limitations: "Small molecular demonstrations do not imply near-term practical simulation of complex soil chemistry.",
    acknowledgment: "AgroQ credits Peruzzo and collaborators for the VQE framework.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["VQE", "quantum chemistry", "hybrid"],
  },
  {
    id: "QRS-011",
    sequence: ["Q9"],
    title: "Elucidating reaction mechanisms on quantum computers",
    authors: ["Markus Reiher", "Nathan Wiebe", "Krysta M. Svore", "Dave Wecker", "Matthias Troyer"],
    year: 2017,
    venue: "Proceedings of the National Academy of Sciences",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1073/pnas.1619152114",
    url: "https://doi.org/10.1073/pnas.1619152114",
    mechanism: "Fault-tolerant resource analysis for chemically relevant quantum simulation, including FeMoco.",
    agroqFeature: "Long-term nitrogen-fixation literature and resource-estimation registry.",
    reproductionTarget: "Reproduce only resource-accounting concepts after small-molecule simulator validation.",
    evidenceStatus: "Long-term research",
    limitations: "The required fault-tolerant resources are beyond the current AgroQ prototype.",
    acknowledgment: "AgroQ credits Reiher, Wiebe, Svore, Wecker, and Troyer for the quantum chemistry resource analysis.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["FeMoco", "resource estimation", "nitrogen fixation"],
  },
  {
    id: "QRS-012",
    sequence: ["Q4"],
    title: "Grover Adaptive Search for Constrained Polynomial Binary Optimization",
    authors: ["Austin Gilliam", "Stefan Woerner", "Constantin Gonciulea"],
    year: 2021,
    venue: "Quantum",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.22331/q-2021-04-08-428",
    url: "https://doi.org/10.22331/q-2021-04-08-428",
    mechanism: "Adaptive threshold search using Grover-style amplification for binary optimization.",
    agroqFeature: "Later constrained optimization comparison for small registered problems.",
    reproductionTarget: "Reproduce a small constrained binary example and record oracle, ancilla, and depth costs.",
    evidenceStatus: "Later experiment",
    limitations: "Oracle arithmetic and ancillary-qubit requirements can make implementations expensive.",
    acknowledgment: "AgroQ credits Gilliam, Woerner, and Gonciulea for Grover Adaptive Search.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["Grover Adaptive Search", "constraints", "optimization"],
  },
  {
    id: "QRS-013",
    sequence: ["Q4"],
    title: "Quantum Graph Neural Networks",
    authors: ["Guillaume Verdon", "Trevor McCourt", "Enxhell Luzhnica", "Vikash Singh", "Stefan Leichenauer", "Jack Hidary"],
    year: 2019,
    venue: "arXiv",
    publicationStatus: "Preprint",
    identifier: "arXiv:1909.12264",
    url: "https://arxiv.org/abs/1909.12264",
    mechanism: "Parameterized quantum models designed for graph-structured information.",
    agroqFeature: "Future graph-learning experiment after classical graph and kernel baselines.",
    reproductionTarget: "Reproduce a small graph classification or graph-state benchmark before using AgroQ graph data.",
    evidenceStatus: "Later research",
    limitations: "The original framework is not direct evidence of benefit on agricultural graph data.",
    acknowledgment: "AgroQ credits Verdon and collaborators for the quantum graph neural-network framework.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["quantum graphs", "QGNN", "graph learning"],
  },
  {
    id: "QRS-014",
    sequence: ["Q5", "Q6"],
    title: "Barren plateaus in quantum neural network training landscapes",
    authors: ["Jarrod R. McClean", "Sergio Boixo", "Vadim N. Smelyanskiy", "Ryan Babbush", "Hartmut Neven"],
    year: 2018,
    venue: "Nature Communications",
    publicationStatus: "Peer reviewed",
    identifier: "doi:10.1038/s41467-018-07090-4",
    url: "https://doi.org/10.1038/s41467-018-07090-4",
    mechanism: "Analysis of exponentially vanishing gradients in broad classes of parameterized quantum circuits.",
    agroqFeature: "Circuit-complexity and trainability controls for QML experiments.",
    reproductionTarget: "Measure gradient magnitude versus qubit count and circuit depth on small simulated ansätze.",
    evidenceStatus: "Risk-control source",
    limitations: "The result motivates careful circuit design but does not determine every model's trainability.",
    acknowledgment: "AgroQ credits McClean and collaborators for the barren-plateau analysis.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["barren plateau", "trainability", "QML"],
  },
  {
    id: "QRS-015",
    sequence: ["Q10"],
    title: "Post-Quantum Cryptography Standards: FIPS 203, FIPS 204, and FIPS 205",
    authors: ["National Institute of Standards and Technology"],
    year: 2024,
    venue: "NIST Computer Security Resource Center",
    publicationStatus: "Final standards",
    identifier: "FIPS 203 / FIPS 204 / FIPS 205",
    url: "https://csrc.nist.gov/projects/post-quantum-cryptography",
    mechanism: "Standardized key encapsulation and digital-signature algorithms designed for post-quantum security.",
    agroqFeature: "Crypto-agility, signed experiment exports, gateway identity, and migration registry.",
    reproductionTarget: "Create standards metadata and interoperability tests without replacing production cryptography prematurely.",
    evidenceStatus: "Standards foundation",
    limitations: "Deployment requires approved libraries, key management, interoperability testing, and an organization-wide migration plan.",
    acknowledgment: "AgroQ credits NIST and the contributing cryptographic research community for the post-quantum standards process.",
    endorsementBoundary: "Citation does not imply endorsement, partnership, or affiliation with AgroQ.",
    tags: ["post-quantum", "ML-KEM", "ML-DSA", "SLH-DSA"],
  },
];

export const quantumExperimentSchema = {
  schemaId: "AGROQ-QER-1.0",
  description:
    "Auditable registry for classical, quantum-inspired, simulator, and hardware research runs.",
  required: [
    "experimentId",
    "sequence",
    "title",
    "sourceIds",
    "problemFamily",
    "status",
    "runType",
    "dataset",
    "formulation",
    "classicalBaseline",
    "execution",
    "metrics",
    "claimControls",
    "humanReview",
    "createdAt",
    "updatedAt",
  ],
  groups: [
    {
      name: "Identity and attribution",
      fields: [
        "experimentId",
        "sequence",
        "title",
        "sourceIds",
        "researchOwner",
        "codeCommit",
      ],
    },
    {
      name: "Frozen problem",
      fields: [
        "problemFamily",
        "dataset.id",
        "dataset.hash",
        "dataset.version",
        "formulation.type",
        "formulation.hash",
        "formulation.variables",
        "formulation.constraints",
      ],
    },
    {
      name: "Matched execution",
      fields: [
        "runType",
        "algorithm",
        "seed",
        "runBudget",
        "classicalBaseline.algorithm",
        "classicalBaseline.objective",
        "execution.backend",
        "execution.shots",
        "execution.circuitDepth",
        "execution.twoQubitGates",
        "execution.noiseModel",
      ],
    },
    {
      name: "Outcomes",
      fields: [
        "metrics.objective",
        "metrics.feasible",
        "metrics.constraintViolations",
        "metrics.approximationGap",
        "metrics.runtimeSeconds",
        "metrics.confidenceInterval",
      ],
    },
    {
      name: "Claim controls",
      fields: [
        "claimControls.simulatorOnly",
        "claimControls.hardwareUsed",
        "claimControls.advantageClaim",
        "claimControls.operationalDependency",
        "claimControls.matchedBudget",
        "claimControls.classicalBaselineRequired",
        "claimControls.syntheticData",
      ],
    },
    {
      name: "Human review",
      fields: [
        "humanReview.required",
        "humanReview.status",
        "humanReview.reviewer",
        "humanReview.notes",
      ],
    },
  ],
};

export const experimentTemplates = [
  {
    sequence: "Q2",
    title: "Frozen soil-sampling QUBO benchmark",
    sourceIds: ["QRS-001", "QRS-002", "QRS-003"],
    problemFamily: "Constrained sample selection",
    algorithm: "Exact + simulated annealing + QAOA simulator",
  },
  {
    sequence: "Q3",
    title: "Irrigation-scheduling reproduction",
    sourceIds: ["QRS-001", "QRS-002", "QRS-003"],
    problemFamily: "Multi-period irrigation scheduling",
    algorithm: "Classical baseline + QAOA simulator",
  },
  {
    sequence: "Q4",
    title: "Graph partition and sensor-placement QAOA",
    sourceIds: ["QRS-001", "QRS-002", "QRS-004", "QRS-012", "QRS-013"],
    problemFamily: "Graph partitioning and facility placement",
    algorithm: "Exact + greedy + QAOA variants",
  },
  {
    sequence: "Q5",
    title: "Quantum-kernel stress classifier",
    sourceIds: ["QRS-005", "QRS-014"],
    problemFamily: "Supervised classification",
    algorithm: "Classical SVM + fidelity quantum kernel",
  },
  {
    sequence: "Q6",
    title: "Quantum reservoir time-series experiment",
    sourceIds: ["QRS-006", "QRS-014"],
    problemFamily: "Temporal forecasting",
    algorithm: "Classical reservoir + simulated quantum reservoir",
  },
  {
    sequence: "Q7",
    title: "Amplitude-estimation uncertainty experiment",
    sourceIds: ["QRS-007"],
    problemFamily: "Threshold probability estimation",
    algorithm: "Monte Carlo + amplitude-estimation simulator",
  },
  {
    sequence: "Q8",
    title: "Quantum sensing simulation workspace",
    sourceIds: ["QRS-008", "QRS-009"],
    problemFamily: "Quantum-sensor signal simulation",
    algorithm: "Signal generation + calibration + detection",
  },
  {
    sequence: "Q9",
    title: "Quantum chemistry and resource-estimation workspace",
    sourceIds: ["QRS-010", "QRS-011"],
    problemFamily: "Molecular energy and resource estimation",
    algorithm: "Exact reference + VQE simulator",
  },
  {
    sequence: "Q10",
    title: "Post-quantum security registry",
    sourceIds: ["QRS-015"],
    problemFamily: "Cryptographic migration and interoperability",
    algorithm: "Standards registry + approved-library tests",
  },
];

const emptyDataset = {
  id: "DATASET-PENDING",
  hash: "sha256:pending",
  version: "0.0.0",
  frozen: false,
  records: 0,
};

const emptyFormulation = {
  type: "Pending",
  hash: "sha256:pending",
  variables: 0,
  constraints: 0,
  objective: "Not yet frozen",
};

const emptyBaseline = {
  required: true,
  algorithm: "Pending",
  objective: null,
  feasible: null,
  runtimeSeconds: null,
  budget: "Matched budget pending",
};

const emptyExecution = {
  backend: "Not run",
  provider: "Local simulator",
  shots: 0,
  circuitDepth: null,
  twoQubitGates: null,
  qubits: null,
  noiseModel: "None",
  optimizer: "Pending",
};

const emptyMetrics = {
  objective: null,
  feasible: null,
  constraintViolations: null,
  approximationGap: null,
  runtimeSeconds: null,
  confidenceInterval: null,
};

const defaultClaimControls = {
  simulatorOnly: true,
  hardwareUsed: false,
  advantageClaim: false,
  operationalDependency: false,
  matchedBudget: true,
  classicalBaselineRequired: true,
  syntheticData: true,
};

const defaultHumanReview = {
  required: true,
  status: "Pending",
  reviewer: "",
  notes: "No operational decision may be made from this registry record alone.",
};

export function createExperimentFromTemplate(template, index = 1) {
  const now = new Date().toISOString();
  return {
    schemaId: quantumExperimentSchema.schemaId,
    experimentId: `AGQ-${template.sequence}-${String(index).padStart(3, "0")}`,
    sequence: template.sequence,
    title: template.title,
    sourceIds: [...template.sourceIds],
    researchOwner: "AgroQ Research Team",
    codeCommit: "pending",
    problemFamily: template.problemFamily,
    status: "Planned",
    runType: "quantum-simulator",
    algorithm: template.algorithm,
    seed: 301,
    runBudget: {
      objectiveEvaluations: 0,
      wallClockSeconds: null,
      shots: 0,
      matchedAcrossSolvers: true,
    },
    dataset: { ...emptyDataset },
    formulation: { ...emptyFormulation },
    classicalBaseline: { ...emptyBaseline },
    execution: { ...emptyExecution },
    metrics: { ...emptyMetrics },
    claimControls: { ...defaultClaimControls },
    humanReview: { ...defaultHumanReview },
    artifacts: [],
    notes: "Registry record created before experiment implementation.",
    createdAt: now,
    updatedAt: now,
  };
}

export function createFrozenSoilSamplingExperiment(frozenProblem, index = 1) {
  const record = createExperimentFromTemplate(experimentTemplates[0], index);
  const candidateCount = frozenProblem?.candidates?.length || 0;
  const selectedCount = frozenProblem?.classicalSelection?.length || 0;

  return {
    ...record,
    experimentId: `AGQ-Q2-SOIL-${String(index).padStart(3, "0")}`,
    title: "Frozen soil-sampling QUBO benchmark",
    status: "Registered",
    dataset: {
      id: frozenProblem?.id || "SOIL-SAMPLING-FROZEN",
      hash: "sha256:generated-on-export",
      version: "1.0.0",
      frozen: true,
      records: candidateCount,
    },
    formulation: {
      type: "QUBO-ready constrained binary selection",
      hash: "sha256:generated-on-export",
      variables: candidateCount,
      constraints: 2,
      objective: frozenProblem?.objective || "Maximize information under sampling budget.",
    },
    classicalBaseline: {
      required: true,
      algorithm: "Transparent ranked selection",
      objective: frozenProblem?.classicalScore ?? null,
      feasible: true,
      runtimeSeconds: null,
      budget: frozenProblem?.budget ?? "Unknown",
    },
    runBudget: {
      objectiveEvaluations: 0,
      wallClockSeconds: null,
      shots: 0,
      matchedAcrossSolvers: true,
      sampleBudget: frozenProblem?.budget ?? null,
    },
    notes: `Imported ${candidateCount} candidates and ${selectedCount} classical selections from the frozen Soil Biology problem.`,
    updatedAt: new Date().toISOString(),
  };
}

export function validateExperimentRecord(record) {
  const errors = [];
  const warnings = [];

  for (const field of quantumExperimentSchema.required) {
    if (record[field] === undefined || record[field] === null || record[field] === "") {
      errors.push(`Missing required field: ${field}`);
    }
  }

  if (!Array.isArray(record.sourceIds) || record.sourceIds.length === 0) {
    errors.push("At least one research source is required.");
  }

  if (!record.classicalBaseline?.required) {
    errors.push("A classical baseline is required by AgroQ policy.");
  }

  if (!record.claimControls?.matchedBudget) {
    warnings.push("Matched-budget comparison is not confirmed.");
  }

  if (record.runType === "quantum-hardware" && !record.claimControls?.hardwareUsed) {
    errors.push("Hardware run type requires hardwareUsed=true.");
  }

  if (record.claimControls?.advantageClaim) {
    warnings.push("Any advantage claim requires independent statistical and resource review.");
  }

  if (record.claimControls?.operationalDependency) {
    errors.push("No operational service may depend exclusively on quantum execution.");
  }

  if (!record.humanReview?.required) {
    errors.push("Human review cannot be disabled.");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    completeness: Math.max(0, 100 - errors.length * 15 - warnings.length * 5),
  };
}

export function stableSerialize(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableSerialize).join(",")}]`;
  }

  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
      .join(",")}}`;
  }

  return JSON.stringify(value);
}

export async function sha256Object(value) {
  const encoded = new TextEncoder().encode(stableSerialize(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", encoded);
  return `sha256:${Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")}`;
}

export function buildRegistryExport(experiments) {
  return {
    registry: "AgroQ Quantum Research and Experiment Registry",
    schemaId: quantumExperimentSchema.schemaId,
    generatedAt: new Date().toISOString(),
    sourceCount: quantumResearchSources.length,
    experimentCount: experiments.length,
    boundaries: {
      separateRunTypes: true,
      classicalBaselineRequired: true,
      matchedBudgetRequired: true,
      humanReviewRequired: true,
      quantumHardwareRequiredForHardwareClaim: true,
      operationalDependencyOnQuantum: false,
      endorsementImpliedByCitation: false,
    },
    sources: quantumResearchSources,
    experiments,
  };
}
