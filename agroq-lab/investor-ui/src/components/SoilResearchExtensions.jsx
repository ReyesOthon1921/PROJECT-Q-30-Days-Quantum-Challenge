import {
  Activity,
  Atom,
  BarChart3,
  Beaker,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Cpu,
  Database,
  ExternalLink,
  FlaskConical,
  Gauge,
  GitBranch,
  Grid3X3,
  Layers3,
  Leaf,
  MapPin,
  Microscope,
  Network,
  RadioTower,
  Scale,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Sprout,
  TestTube2,
  Waves,
} from "lucide-react";
import { useMemo, useState } from "react";

const sourceRegistry = [
  {
    id: "SRC-001",
    author: "Dr. Elaine R. Ingham and collaborators",
    paper: "Soil Food Web publications and Soil Biology Primer",
    doi: "Publication collection",
    mechanism: "Soil organisms, decomposition, nutrient cycling, and plant–microbe interactions",
    feature: "Soil Food Web overview and biological observations",
    status: "Research foundation",
    limitations:
      "Methods and claims must be checked against individual publications and validated protocols.",
    url: "https://soilfoodweb.com/publications/",
  },
  {
    id: "SRC-002",
    author: "USDA Natural Resources Conservation Service",
    paper: "Soil Health Assessment",
    doi: "Official guidance",
    mechanism: "Physical, chemical, and biological soil-health indicators",
    feature: "Indicator framework and evidence boundaries",
    status: "Operational reference",
    limitations:
      "Indicators must be interpreted for soil type, climate, management, and sampling method.",
    url: "https://www.nrcs.usda.gov/conservation-basics/soil/soil-health/soil-health-assessment",
  },
  {
    id: "SRC-003",
    author: "S. S. Andrews, D. L. Karlen, and C. A. Cambardella",
    paper: "The Soil Management Assessment Framework",
    doi: "10.2136/sssaj2004.1945",
    mechanism: "Indicator selection, scoring curves, and integrated soil-quality assessment",
    feature: "Multi-domain soil indicator cards",
    status: "Peer reviewed",
    limitations:
      "AgroQ does not reproduce SMAF scoring without validated scoring curves and local calibration.",
    url: "https://doi.org/10.2136/sssaj2004.1945",
  },
  {
    id: "SRC-004",
    author: "Jo Handelsman",
    paper: "Metagenomics: Application of Genomics to Uncultured Microorganisms",
    doi: "10.1128/MMBR.68.4.669-685.2004",
    mechanism: "Culture-independent analysis of microbial communities",
    feature: "Future metagenomics research lane",
    status: "Later research",
    limitations:
      "Requires validated sampling, extraction, sequencing, bioinformatics, and contamination controls.",
    url: "https://doi.org/10.1128/MMBR.68.4.669-685.2004",
  },
  {
    id: "SRC-005",
    author: "USDA Agricultural Research Service",
    paper: "VNIR, electrical conductivity, and penetration-resistance sensor fusion",
    doi: "USDA ARS publication record",
    mechanism: "Combining complementary sensors to estimate soil indicators",
    feature: "Sensor-fusion records and calibration tracking",
    status: "Pilot reference",
    limitations:
      "Models require ground-truth laboratory data and site-specific calibration.",
    url: "https://www.ars.usda.gov/research/publications/publication/?seqNo115=329618",
  },
  {
    id: "SRC-006",
    author: "David J. C. MacKay",
    paper: "Information-Based Objective Functions for Active Data Selection",
    doi: "10.1162/neco.1992.4.4.590",
    mechanism: "Selecting measurements that maximize expected information gain",
    feature: "Classical active-sampling optimizer",
    status: "Method foundation",
    limitations:
      "The current score is a transparent demonstration, not a validated Bayesian field model.",
    url: "https://doi.org/10.1162/neco.1992.4.4.590",
  },
  {
    id: "SRC-007",
    author: "Fred Glover, Gary Kochenberger, and Yu Du",
    paper: "A Tutorial on Formulating and Using QUBO Models",
    doi: "10.1007/s10288-019-00424-y",
    mechanism: "Binary optimization and penalty-based QUBO formulation",
    feature: "Frozen soil-sampling problem sent to Quantum Lab",
    status: "Optimization foundation",
    limitations:
      "A QUBO formulation does not establish quantum advantage and must retain a classical baseline.",
    url: "https://doi.org/10.1007/s10288-019-00424-y",
  },
  {
    id: "SRC-008",
    author: "Edward Farhi, Jeffrey Goldstone, and Sam Gutmann",
    paper: "A Quantum Approximate Optimization Algorithm",
    doi: "arXiv:1411.4028",
    mechanism: "Approximate optimization using parameterized quantum circuits",
    feature: "Quantum-simulator comparison lane",
    status: "Quantum foundation",
    limitations:
      "Simulator results are research demonstrations; no hardware or advantage claim is made.",
    url: "https://arxiv.org/abs/1411.4028",
  },
  {
    id: "SRC-009",
    author: "Hirokazu Toju and collaborators",
    paper: "Core microbiomes for sustainable agroecosystems",
    doi: "10.1038/s41477-018-0139-4",
    mechanism: "Microbiome functions and possible agroecosystem applications",
    feature: "Future microbial-ecology and microbial-engineering lane",
    status: "Later research",
    limitations:
      "No automated microbial intervention is authorized; field safety and validation are required.",
    url: "https://doi.org/10.1038/s41477-018-0139-4",
  },
];

const physicalIndicators = [
  ["Aggregate stability", "82%", "Wet-sieving or slake-test protocol", "Stable"],
  ["Infiltration rate", "31 mm/hr", "Double-ring field estimate", "Review"],
  ["Bulk density", "1.24 g/cm³", "Core method at 0–15 cm", "Stable"],
  ["Penetration resistance", "1.48 MPa", "Cone index, moisture corrected", "Review"],
  ["Water-holding capacity", "24%", "Lab reference required", "Pilot"],
  ["Surface cover", "76%", "Manual transect estimate", "Stable"],
];

const chemicalIndicators = [
  ["pH", "6.6", "1:1 soil-water method", "Stable"],
  ["Electrical conductivity", "0.42 dS/m", "Calibrated EC probe", "Stable"],
  ["Organic matter", "3.8%", "Laboratory reference", "Review"],
  ["Nitrate-N", "18 mg/kg", "Laboratory extract", "Review"],
  ["Extractable phosphorus", "22 mg/kg", "Method-specific", "Stable"],
  ["Extractable potassium", "184 mg/kg", "Method-specific", "Stable"],
];

const sensorFusionRecords = [
  {
    id: "FUS-001",
    zone: "North Control",
    inputs: ["Moisture", "Temperature", "EC", "Penetration"],
    calibration: "CAL-2026-07-A",
    quality: 92,
    lastSync: "2 minutes ago",
    state: "Ground-truthed",
  },
  {
    id: "FUS-002",
    zone: "Compost Trial",
    inputs: ["VNIR", "EC", "Moisture", "Weather"],
    calibration: "CAL-2026-07-B",
    quality: 84,
    lastSync: "6 minutes ago",
    state: "Pilot",
  },
  {
    id: "FUS-003",
    zone: "Beneficial Zone",
    inputs: ["Moisture", "Temperature", "Canopy proxy"],
    calibration: "CAL-2026-06-C",
    quality: 76,
    lastSync: "14 minutes ago",
    state: "Needs check",
  },
];

const graphNodes = [
  { id: "sample-control", label: "SFW-001", type: "sample", x: 82, y: 94 },
  { id: "sample-compost", label: "SFW-004", type: "sample", x: 265, y: 78 },
  { id: "north", label: "North Control", type: "plot", x: 95, y: 222 },
  { id: "compost", label: "Compost Trial", type: "plot", x: 280, y: 220 },
  { id: "protocol", label: "SFW-MICRO-1.1", type: "protocol", x: 455, y: 82 },
  { id: "sensor", label: "Fusion FUS-002", type: "sensor", x: 465, y: 225 },
  { id: "experiment", label: "Compost vs Control", type: "experiment", x: 645, y: 150 },
];

const graphEdges = [
  ["sample-control", "north"],
  ["sample-compost", "compost"],
  ["sample-control", "protocol"],
  ["sample-compost", "protocol"],
  ["compost", "sensor"],
  ["north", "experiment"],
  ["compost", "experiment"],
  ["sensor", "experiment"],
];

const candidateSamples = [
  {
    id: "C-01",
    zone: "Compost Trial",
    uncertainty: 0.91,
    diversity: 0.74,
    urgency: 0.88,
    cost: 2,
    distance: 1.2,
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
    reason: "Sensor drift needs ground-truth sample",
  },
  {
    id: "C-03",
    zone: "North Control",
    uncertainty: 0.61,
    diversity: 0.79,
    urgency: 0.58,
    cost: 1,
    distance: 0.8,
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
    reason: "Baseline comparison",
  },
];

const futureCapabilities = [
  {
    title: "Metagenomics",
    icon: Database,
    stage: "Later research",
    tone: "amber",
    mechanism: "DNA-based characterization of microbial-community composition and function.",
    boundary:
      "No sequencing data are active. Requires contamination controls, validated pipelines, privacy review, and qualified interpretation.",
  },
  {
    title: "VNIR / MIR spectroscopy",
    icon: Gauge,
    stage: "Pilot candidate",
    tone: "amber",
    mechanism: "Rapid spectral estimates calibrated against laboratory soil measurements.",
    boundary:
      "Spectral predictions cannot replace reference laboratory tests without local calibration and error reporting.",
  },
  {
    title: "Microbial engineering",
    icon: Microscope,
    stage: "Research only",
    tone: "red",
    mechanism: "Study of microbial consortia and plant–microbe functions.",
    boundary:
      "No automated release, inoculation, or biological intervention is authorized by the platform.",
  },
  {
    title: "Automated field predictions",
    icon: Sparkles,
    stage: "Not authorized",
    tone: "red",
    mechanism: "Models could estimate risk, response, or sampling priority.",
    boundary:
      "Predictions remain advisory, confidence-labeled, and subject to human and agronomic review.",
  },
];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function SectionHeader({ eyebrow, title, copy, icon: Icon }) {
  return (
    <div className="research-extension-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{copy}</p>
      </div>
      <div className="research-extension-icon">
        <Icon size={25} />
      </div>
    </div>
  );
}

function IndicatorWorkspace({ type }) {
  const isPhysical = type === "Soil Structure & Water";
  const indicators = isPhysical ? physicalIndicators : chemicalIndicators;
  const Icon = isPhysical ? Waves : Beaker;

  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow={isPhysical ? "Physical indicators" : "Chemical indicators"}
          title={type}
          copy={
            isPhysical
              ? "Track structure, water movement, compaction, and habitat conditions alongside biological evidence."
              : "Track chemistry beside biology and physical structure without treating one layer as the whole soil system."
          }
          icon={Icon}
        />
      </section>

      <section className="indicator-workspace-grid">
        {indicators.map(([name, value, method, status]) => (
          <article className="panel indicator-workspace-card" key={name}>
            <div>
              <span>{name}</span>
              <strong>{value}</strong>
            </div>
            <p>{method}</p>
            <Badge tone={status === "Stable" ? "green" : "amber"}>{status}</Badge>
          </article>
        ))}
      </section>

      <section className="two-column">
        <article className="panel research-extension-card">
          <h3>Interpretation boundary</h3>
          <p>
            Values are synthetic prototype records. Valid decisions require consistent
            depth, method, calibration, soil type, weather context, and comparison with
            prior measurements or reference plots.
          </p>
        </article>
        <article className="panel research-extension-card">
          <h3>Cross-domain connection</h3>
          <div className="mechanism-chain">
            {[
              isPhysical ? "Structure" : "Chemistry",
              "Microbial habitat",
              "Root function",
              "Plant response",
              "Human review",
            ].map((step, index) => (
              <div key={step}>
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

function SourceRegistry() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All statuses");

  const filtered = useMemo(
    () =>
      sourceRegistry.filter((source) => {
        const text = `${source.author} ${source.paper} ${source.mechanism} ${source.feature}`.toLowerCase();
        return (
          text.includes(query.toLowerCase()) &&
          (status === "All statuses" || source.status === status)
        );
      }),
    [query, status],
  );

  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Traceable evidence"
          title="Research Source Registry"
          copy="Connect every author, paper, DOI, mechanism, application feature, evidence status, and limitation."
          icon={BookOpen}
        />
      </section>

      <section className="panel source-registry-controls">
        <label>
          Search sources
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Author, paper, mechanism, or feature"
          />
        </label>
        <label>
          Evidence status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option>All statuses</option>
            {[...new Set(sourceRegistry.map((source) => source.status))].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <div className="source-registry-count">
          <BookOpen size={18} />
          <strong>{filtered.length}</strong>
          <span>registered sources</span>
        </div>
      </section>

      <section className="panel source-registry-panel">
        <div className="source-registry-scroll">
          <table className="source-registry-table">
            <thead>
              <tr>
                <th>Author / organization</th>
                <th>Paper or guidance</th>
                <th>DOI / identifier</th>
                <th>Mechanism</th>
                <th>AgroQ feature</th>
                <th>Status</th>
                <th>Limitations</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((source) => (
                <tr key={source.id}>
                  <td>
                    <strong>{source.author}</strong>
                    <small>{source.id}</small>
                  </td>
                  <td>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.paper}
                      <ExternalLink size={13} />
                    </a>
                  </td>
                  <td>{source.doi}</td>
                  <td>{source.mechanism}</td>
                  <td>{source.feature}</td>
                  <td>
                    <Badge
                      tone={
                        source.status.includes("Later") ||
                        source.status.includes("Pilot")
                          ? "amber"
                          : "green"
                      }
                    >
                      {source.status}
                    </Badge>
                  </td>
                  <td>{source.limitations}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function normalizeSamples(observations) {
  const fallbackGps = [
    "39.14021, -121.59142",
    "39.14036, -121.59101",
    "39.13994, -121.59072",
    "39.13971, -121.59131",
    "39.14008, -121.59038",
  ];

  return observations.map((sample, index) => ({
    ...sample,
    protocol: sample.protocol || (sample.method === "Root staining" ? "ROOT-COL-1.0" : "SFW-MICRO-1.1"),
    calibrationId: sample.calibrationId || `CAL-MICRO-${String(index + 1).padStart(2, "0")}`,
    depthCm: sample.depthCm || (index % 2 ? 15 : 10),
    gps: sample.gps || fallbackGps[index % fallbackGps.length],
    confidence: sample.confidence || [88, 82, 74, 91, 79][index % 5],
    analyst: sample.analyst || "Research operator",
    reviewStatus: sample.reviewStatus || (index === 2 ? "Needs review" : "Reviewed"),
  }));
}

function SampleProvenance({ observations }) {
  const samples = normalizeSamples(observations);

  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Chain of custody"
          title="Sample Provenance & Quality Control"
          copy="Every result stays connected to its protocol, calibration, depth, GPS location, analyst, confidence, and review state."
          icon={ShieldCheck}
        />
      </section>

      <section className="metrics-grid">
        <article className="panel provenance-metric">
          <MapPin size={20} />
          <span>GPS-linked samples</span>
          <strong>{samples.length}</strong>
        </article>
        <article className="panel provenance-metric">
          <FlaskConical size={20} />
          <span>Protocol versions</span>
          <strong>{new Set(samples.map((sample) => sample.protocol)).size}</strong>
        </article>
        <article className="panel provenance-metric">
          <Gauge size={20} />
          <span>Average confidence</span>
          <strong>
            {Math.round(
              samples.reduce((sum, sample) => sum + sample.confidence, 0) /
                samples.length,
            )}
            %
          </strong>
        </article>
        <article className="panel provenance-metric">
          <CheckCircle2 size={20} />
          <span>Reviewed records</span>
          <strong>
            {samples.filter((sample) => sample.reviewStatus === "Reviewed").length}
          </strong>
        </article>
      </section>

      <section className="panel provenance-table-panel">
        <div className="source-registry-scroll">
          <table className="source-registry-table">
            <thead>
              <tr>
                <th>Sample</th>
                <th>Zone</th>
                <th>Protocol</th>
                <th>Calibration</th>
                <th>Depth</th>
                <th>GPS</th>
                <th>Analyst</th>
                <th>Confidence</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody>
              {samples.map((sample) => (
                <tr key={sample.id}>
                  <td>
                    <strong>{sample.id}</strong>
                    <small>{sample.date}</small>
                  </td>
                  <td>{sample.zone}</td>
                  <td>{sample.protocol}</td>
                  <td>{sample.calibrationId}</td>
                  <td>{sample.depthCm} cm</td>
                  <td>{sample.gps}</td>
                  <td>{sample.analyst}</td>
                  <td>{sample.confidence}%</td>
                  <td>
                    <Badge tone={sample.reviewStatus === "Reviewed" ? "green" : "amber"}>
                      {sample.reviewStatus}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function SensorFusion() {
  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Sensor fusion"
          title="Calibration-Aware Sensor Records"
          copy="Combine complementary measurements while preserving the raw inputs, calibration identity, quality score, and ground-truth state."
          icon={RadioTower}
        />
      </section>

      <section className="sensor-fusion-grid">
        {sensorFusionRecords.map((record) => (
          <article className="panel sensor-fusion-card" key={record.id}>
            <div className="sensor-fusion-title">
              <div>
                <span>{record.id}</span>
                <h3>{record.zone}</h3>
              </div>
              <Badge
                tone={
                  record.state === "Ground-truthed"
                    ? "green"
                    : record.state === "Pilot"
                      ? "amber"
                      : "red"
                }
              >
                {record.state}
              </Badge>
            </div>
            <div className="sensor-chip-list">
              {record.inputs.map((input) => (
                <span key={input}>{input}</span>
              ))}
            </div>
            <div className="fusion-quality">
              <span>Quality score</span>
              <strong>{record.quality}%</strong>
              <div>
                <i style={{ width: `${record.quality}%` }} />
              </div>
            </div>
            <div className="sensor-fusion-meta">
              <span>
                Calibration
                <strong>{record.calibration}</strong>
              </span>
              <span>
                Last sync
                <strong>{record.lastSync}</strong>
              </span>
            </div>
          </article>
        ))}
      </section>

      <section className="panel sensor-fusion-boundary">
        <ShieldCheck size={22} />
        <div>
          <h3>Ground truth remains required</h3>
          <p>
            Sensor fusion can improve coverage and prioritization, but estimates must be
            calibrated and checked against laboratory or standardized field measurements.
          </p>
        </div>
      </section>
    </div>
  );
}

function SampleGraph({ observations }) {
  const normalized = normalizeSamples(observations);
  const nodeMap = Object.fromEntries(graphNodes.map((node) => [node.id, node]));

  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Knowledge graph"
          title="Sample-to-Decision Graph"
          copy="Connect samples, plots, protocols, sensors, treatments, and experiments so every recommendation can be traced backward."
          icon={Network}
        />
      </section>

      <section className="two-column sample-graph-layout">
        <article className="panel sample-graph-panel">
          <svg viewBox="0 0 730 310" role="img" aria-label="Soil research knowledge graph">
            {graphEdges.map(([from, to]) => {
              const a = nodeMap[from];
              const b = nodeMap[to];
              return (
                <line
                  key={`${from}-${to}`}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  className="sample-graph-edge"
                />
              );
            })}
            {graphNodes.map((node) => (
              <g
                className={`sample-graph-node sample-graph-${node.type}`}
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
              >
                <circle r="25" />
                <text y="44" textAnchor="middle">
                  {node.label}
                </text>
              </g>
            ))}
          </svg>
          <div className="sample-graph-legend">
            {[
              ["sample", "Sample"],
              ["plot", "Plot"],
              ["protocol", "Protocol"],
              ["sensor", "Sensor fusion"],
              ["experiment", "Experiment"],
            ].map(([type, label]) => (
              <span key={type}>
                <i className={`sample-graph-${type}`} />
                {label}
              </span>
            ))}
          </div>
        </article>

        <article className="panel research-extension-card">
          <h3>Graph-linked evidence</h3>
          <div className="graph-evidence-list">
            <div>
              <span>Observation nodes</span>
              <strong>{normalized.length}</strong>
            </div>
            <div>
              <span>Protocol relationships</span>
              <strong>{normalized.length}</strong>
            </div>
            <div>
              <span>Sensor-fusion links</span>
              <strong>{sensorFusionRecords.length}</strong>
            </div>
            <div>
              <span>Human review gate</span>
              <strong>Required</strong>
            </div>
          </div>
          <p>
            The current graph is a deterministic prototype. Future analytics can compute
            similarity, spatial clusters, anomaly scores, and missing-evidence warnings.
          </p>
        </article>
      </section>
    </div>
  );
}

function ActiveSamplingOptimizer({ onFreezeProblem, onOpenQuantum }) {
  const [budget, setBudget] = useState(5);
  const [uncertaintyWeight, setUncertaintyWeight] = useState(45);
  const [diversityWeight, setDiversityWeight] = useState(25);
  const [urgencyWeight, setUrgencyWeight] = useState(30);
  const [frozen, setFrozen] = useState(null);

  const ranked = useMemo(() => {
    const rawWeights = uncertaintyWeight + diversityWeight + urgencyWeight || 1;
    return candidateSamples
      .map((candidate) => {
        const information =
          (candidate.uncertainty * uncertaintyWeight +
            candidate.diversity * diversityWeight +
            candidate.urgency * urgencyWeight) /
          rawWeights;
        const travelPenalty = candidate.distance * 0.025;
        const value = information - travelPenalty;
        return { ...candidate, value: Number(value.toFixed(3)) };
      })
      .sort((a, b) => b.value - a.value);
  }, [diversityWeight, uncertaintyWeight, urgencyWeight]);

  const selected = useMemo(() => {
    let remaining = budget;
    const picks = [];
    for (const candidate of ranked) {
      if (candidate.cost <= remaining) {
        picks.push(candidate);
        remaining -= candidate.cost;
      }
    }
    return { picks, remaining };
  }, [budget, ranked]);

  const freezeProblem = () => {
    const problem = {
      id: `SOIL-SAMPLING-${new Date().toISOString().slice(0, 10)}`,
      createdAt: new Date().toISOString(),
      objective:
        "Maximize uncertainty reduction, diversity, and urgency under sample-budget and travel penalties.",
      budget,
      weights: {
        uncertainty: uncertaintyWeight,
        diversity: diversityWeight,
        urgency: urgencyWeight,
      },
      candidates: ranked,
      classicalSelection: selected.picks.map((candidate) => candidate.id),
      classicalScore: Number(
        selected.picks.reduce((sum, candidate) => sum + candidate.value, 0).toFixed(3),
      ),
      controls: {
        datasetFrozen: true,
        classicalBaselineRequired: true,
        simulatorOnly: true,
        advantageClaim: false,
        humanReviewRequired: true,
      },
    };

    window.localStorage.setItem(
      "agroq-frozen-soil-sampling-problem",
      JSON.stringify(problem),
    );
    onFreezeProblem?.(problem);
    setFrozen(problem);
  };

  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Classical optimization"
          title="Active-Sampling Optimizer"
          copy="Prioritize the next soil samples using a transparent, matched-budget classical baseline before sending the frozen problem to the Quantum Lab."
          icon={SlidersHorizontal}
        />
      </section>

      <section className="two-column optimizer-layout">
        <article className="panel optimizer-controls">
          <h3>Objective and constraints</h3>
          <label>
            Sampling budget: <strong>{budget} units</strong>
            <input
              type="range"
              min="2"
              max="9"
              value={budget}
              onChange={(event) => setBudget(Number(event.target.value))}
            />
          </label>
          {[
            ["Uncertainty", uncertaintyWeight, setUncertaintyWeight],
            ["Diversity", diversityWeight, setDiversityWeight],
            ["Urgency", urgencyWeight, setUrgencyWeight],
          ].map(([label, value, setter]) => (
            <label key={label}>
              {label}: <strong>{value}%</strong>
              <input
                type="range"
                min="0"
                max="100"
                value={value}
                onChange={(event) => setter(Number(event.target.value))}
              />
            </label>
          ))}
          <div className="optimizer-constraints">
            <div>
              <Scale size={17} />
              <span>Limited sample budget</span>
            </div>
            <div>
              <MapPin size={17} />
              <span>Travel penalty included</span>
            </div>
            <div>
              <ShieldCheck size={17} />
              <span>Human approval required</span>
            </div>
          </div>
        </article>

        <article className="panel optimizer-result">
          <div className="optimizer-result-heading">
            <div>
              <span>Classical baseline</span>
              <h3>Recommended sample set</h3>
            </div>
            <Badge tone="green">{selected.picks.length} selected</Badge>
          </div>
          <div className="optimizer-selection-list">
            {selected.picks.map((candidate, index) => (
              <div key={candidate.id}>
                <span>{index + 1}</span>
                <div>
                  <strong>{candidate.zone}</strong>
                  <small>{candidate.reason}</small>
                </div>
                <b>{candidate.value}</b>
              </div>
            ))}
          </div>
          <div className="optimizer-summary">
            <span>
              Budget remaining
              <strong>{selected.remaining}</strong>
            </span>
            <span>
              Classical score
              <strong>
                {selected.picks
                  .reduce((sum, candidate) => sum + candidate.value, 0)
                  .toFixed(3)}
              </strong>
            </span>
          </div>
          <button className="button button-primary full-width" type="button" onClick={freezeProblem}>
            <Atom size={18} />
            Freeze problem for Quantum Lab
          </button>
          {frozen && (
            <button
              className="button button-secondary full-width"
              type="button"
              onClick={onOpenQuantum}
            >
              Open Quantum Lab
              <ChevronRight size={17} />
            </button>
          )}
        </article>
      </section>

      <section className="panel optimizer-ranking-panel">
        <div className="optimizer-ranking-heading">
          <h3>Candidate ranking</h3>
          <span>Transparent demonstration score</span>
        </div>
        <div className="optimizer-ranking-grid">
          {ranked.map((candidate, index) => (
            <article key={candidate.id}>
              <span>#{index + 1}</span>
              <div>
                <strong>{candidate.zone}</strong>
                <small>
                  U {candidate.uncertainty} · D {candidate.diversity} · P {candidate.urgency}
                </small>
              </div>
              <b>{candidate.value}</b>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function FutureResearch() {
  return (
    <div className="page-stack research-extension-page">
      <section className="panel research-extension-hero">
        <SectionHeader
          eyebrow="Controlled roadmap"
          title="Future Research & Pilot Capabilities"
          copy="Advanced capabilities remain clearly separated from active operational features."
          icon={Layers3}
        />
      </section>

      <section className="future-capability-grid">
        {futureCapabilities.map(({ title, icon: Icon, stage, tone, mechanism, boundary }) => (
          <article className="panel future-capability-card" key={title}>
            <div className="future-capability-title">
              <div className="future-capability-icon">
                <Icon size={23} />
              </div>
              <Badge tone={tone}>{stage}</Badge>
            </div>
            <h3>{title}</h3>
            <p>{mechanism}</p>
            <div className="future-capability-boundary">
              <ShieldCheck size={17} />
              <span>{boundary}</span>
            </div>
          </article>
        ))}
      </section>

      <section className="panel future-authorization-strip">
        <ShieldCheck size={23} />
        <div>
          <h3>Authorization boundary</h3>
          <p>
            Research labels describe possible future investigation. They do not represent
            deployed biological interventions, validated diagnostics, autonomous actuation,
            or guaranteed field outcomes.
          </p>
        </div>
      </section>
    </div>
  );
}

export default function SoilResearchExtensions({
  activeTab,
  observations,
  onFreezeProblem,
  onOpenQuantum,
  onBack,
}) {
  let content;

  if (activeTab === "Soil Structure & Water" || activeTab === "Soil Chemistry") {
    content = <IndicatorWorkspace type={activeTab} />;
  } else if (activeTab === "Research Source Registry") {
    content = <SourceRegistry />;
  } else if (activeTab === "Sample Provenance") {
    content = <SampleProvenance observations={observations} />;
  } else if (activeTab === "Sensor Fusion") {
    content = <SensorFusion />;
  } else if (activeTab === "Sample Graph") {
    content = <SampleGraph observations={observations} />;
  } else if (activeTab === "Sampling Optimizer") {
    content = (
      <ActiveSamplingOptimizer
        onFreezeProblem={onFreezeProblem}
        onOpenQuantum={onOpenQuantum}
      />
    );
  } else {
    content = <FutureResearch />;
  }

  return (
    <div className="page-stack">
      <button className="text-button research-back-button" type="button" onClick={onBack}>
        ← Return to Soil Food Web overview
      </button>
      {content}
    </div>
  );
}
