import {
  AlertTriangle,
  Atom,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Database,
  Download,
  ExternalLink,
  FileCode2,
  Filter,
  FlaskConical,
  Gauge,
  GitBranch,
  HardDrive,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  TestTube2,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import Q2SoilSamplingBenchmark from "./Q2SoilSamplingBenchmark";
import QuantumQ3Q10Workspace from "./QuantumQ3Q10Workspace";
import {
  buildRegistryExport,
  createExperimentFromTemplate,
  createFrozenSoilSamplingExperiment,
  experimentTemplates,
  quantumExperimentSchema,
  quantumResearchSources,
  sha256Object,
  validateExperimentRecord,
} from "../data/quantumRegistryData";

const STORAGE_KEY = "agroq-quantum-experiment-registry-v1";

const tabs = [
  "Q0 · Research Sources",
  "Q1 · Experiment Registry",
  "Q2 · Soil QUBO Benchmark",
  "Q3–Q10 · Research Suite",
  "Data Model",
  "Reproducibility Gate",
  "Acknowledgments",
];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function readStoredExperiments() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function toneForStatus(status) {
  if (
    status === "Foundation" ||
    status === "Reproduction candidate" ||
    status === "Standards foundation" ||
    status === "Registered"
  ) {
    return "green";
  }

  if (
    status === "Later experiment" ||
    status === "Later research" ||
    status === "Long-term research" ||
    status === "Simulation candidate" ||
    status === "Risk-control source" ||
    status === "Planned"
  ) {
    return "amber";
  }

  return "slate";
}

function SourceRegistry() {
  const [query, setQuery] = useState("");
  const [sequence, setSequence] = useState("All sequences");
  const [evidence, setEvidence] = useState("All evidence");

  const evidenceOptions = useMemo(
    () => [
      "All evidence",
      ...new Set(quantumResearchSources.map((source) => source.evidenceStatus)),
    ],
    [],
  );

  const sequenceOptions = [
    "All sequences",
    "Q0",
    "Q2",
    "Q3",
    "Q4",
    "Q5",
    "Q6",
    "Q7",
    "Q8",
    "Q9",
    "Q10",
  ];

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return quantumResearchSources.filter((source) => {
      const searchable = [
        source.title,
        source.authors.join(" "),
        source.mechanism,
        source.agroqFeature,
        source.reproductionTarget,
        source.tags.join(" "),
      ]
        .join(" ")
        .toLowerCase();

      return (
        (!normalized || searchable.includes(normalized)) &&
        (sequence === "All sequences" || source.sequence.includes(sequence)) &&
        (evidence === "All evidence" || source.evidenceStatus === evidence)
      );
    });
  }, [evidence, query, sequence]);

  return (
    <div className="quantum-registry-stack">
      <section className="quantum-registry-metrics">
        <article className="panel">
          <BookOpen size={20} />
          <span>Registered sources</span>
          <strong>{quantumResearchSources.length}</strong>
        </article>
        <article className="panel">
          <Users size={20} />
          <span>Named contributors</span>
          <strong>
            {new Set(quantumResearchSources.flatMap((source) => source.authors)).size}
          </strong>
        </article>
        <article className="panel">
          <TestTube2 size={20} />
          <span>Experiment sequences</span>
          <strong>Q2–Q10</strong>
        </article>
        <article className="panel">
          <ShieldCheck size={20} />
          <span>Endorsement boundary</span>
          <strong>Explicit</strong>
        </article>
      </section>

      <section className="panel quantum-source-controls">
        <label>
          Search
          <div>
            <Search size={16} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Author, paper, mechanism, feature, or tag"
            />
          </div>
        </label>
        <label>
          Sequence
          <select value={sequence} onChange={(event) => setSequence(event.target.value)}>
            {sequenceOptions.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
        <label>
          Evidence status
          <select value={evidence} onChange={(event) => setEvidence(event.target.value)}>
            {evidenceOptions.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
        <button
          className="button button-secondary"
          type="button"
          onClick={() =>
            downloadJson("agroq-quantum-research-sources.json", {
              generatedAt: new Date().toISOString(),
              sources: quantumResearchSources,
            })
          }
        >
          <Download size={16} />
          Export Q0
        </button>
      </section>

      <section className="quantum-source-grid">
        {filtered.map((source) => (
          <article className="panel quantum-source-card" key={source.id}>
            <div className="quantum-source-topline">
              <span>{source.id}</span>
              <Badge tone={toneForStatus(source.evidenceStatus)}>
                {source.evidenceStatus}
              </Badge>
            </div>
            <h3>{source.title}</h3>
            <strong className="quantum-source-authors">
              {source.authors.join(", ")}
            </strong>
            <div className="quantum-source-meta">
              <span>{source.year}</span>
              <span>{source.venue}</span>
              <span>{source.publicationStatus}</span>
            </div>
            <div className="quantum-source-section">
              <span>Mechanism</span>
              <p>{source.mechanism}</p>
            </div>
            <div className="quantum-source-section">
              <span>AgroQ feature</span>
              <p>{source.agroqFeature}</p>
            </div>
            <div className="quantum-source-section">
              <span>Reproduction target</span>
              <p>{source.reproductionTarget}</p>
            </div>
            <div className="quantum-source-limit">
              <AlertTriangle size={16} />
              <span>{source.limitations}</span>
            </div>
            <div className="quantum-source-footer">
              <div>
                {source.sequence.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.identifier}
                <ExternalLink size={14} />
              </a>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}

function ExperimentModal({ onClose, onSave, experimentIndex }) {
  const [templateSequence, setTemplateSequence] = useState("Q2");
  const [runType, setRunType] = useState("quantum-simulator");
  const [researchOwner, setResearchOwner] = useState("AgroQ Research Team");
  const [codeCommit, setCodeCommit] = useState("pending");
  const [notes, setNotes] = useState("");

  const selectedTemplate =
    experimentTemplates.find((template) => template.sequence === templateSequence) ||
    experimentTemplates[0];

  const submit = (event) => {
    event.preventDefault();
    const record = createExperimentFromTemplate(selectedTemplate, experimentIndex);
    onSave({
      ...record,
      runType,
      researchOwner: researchOwner.trim(),
      codeCommit: codeCommit.trim(),
      notes: notes.trim() || record.notes,
      updatedAt: new Date().toISOString(),
    });
  };

  return (
    <div className="quantum-modal-backdrop">
      <form className="panel quantum-experiment-modal" onSubmit={submit}>
        <div className="quantum-modal-heading">
          <div>
            <span className="eyebrow">Q1 registry entry</span>
            <h2>Register planned quantum experiment</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose}>
            <X size={19} />
          </button>
        </div>

        <div className="quantum-form-grid">
          <label>
            Coding sequence
            <select
              value={templateSequence}
              onChange={(event) => setTemplateSequence(event.target.value)}
            >
              {experimentTemplates.map((template) => (
                <option key={template.sequence} value={template.sequence}>
                  {template.sequence} · {template.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Run type
            <select value={runType} onChange={(event) => setRunType(event.target.value)}>
              <option value="classical">Classical</option>
              <option value="quantum-inspired">Quantum-inspired</option>
              <option value="quantum-simulator">Quantum simulator</option>
              <option value="quantum-hardware">Quantum hardware</option>
            </select>
          </label>
          <label>
            Research owner
            <input
              required
              value={researchOwner}
              onChange={(event) => setResearchOwner(event.target.value)}
            />
          </label>
          <label>
            Code commit
            <input
              required
              value={codeCommit}
              onChange={(event) => setCodeCommit(event.target.value)}
            />
          </label>
          <label className="quantum-form-wide">
            Notes
            <textarea
              rows="4"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Purpose, assumptions, planned comparison, or constraints."
            />
          </label>
        </div>

        <div className="quantum-modal-actions">
          <button className="button button-secondary" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="button button-primary" type="submit">
            <Plus size={17} />
            Register experiment
          </button>
        </div>
      </form>
    </div>
  );
}

function ExperimentRegistry({ frozenProblem }) {
  const [experiments, setExperiments] = useState(readStoredExperiments);
  const [showModal, setShowModal] = useState(false);
  const [sequence, setSequence] = useState("All sequences");
  const [status, setStatus] = useState("All statuses");
  const [message, setMessage] = useState("");

  const persist = (records) => {
    setExperiments(records);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  };

  const addExperiment = (record) => {
    persist([record, ...experiments]);
    setShowModal(false);
    setMessage(`${record.experimentId} registered.`);
  };

  const importFrozen = async () => {
    if (!frozenProblem) return;

    const record = createFrozenSoilSamplingExperiment(
      frozenProblem,
      experiments.length + 1,
    );
    const datasetHash = await sha256Object({
      id: frozenProblem.id,
      candidates: frozenProblem.candidates,
      budget: frozenProblem.budget,
      weights: frozenProblem.weights,
    });
    const formulationHash = await sha256Object({
      objective: frozenProblem.objective,
      budget: frozenProblem.budget,
      controls: frozenProblem.controls,
      candidates: frozenProblem.candidates?.map((candidate) => ({
        id: candidate.id,
        value: candidate.value,
        cost: candidate.cost,
      })),
    });

    const completed = {
      ...record,
      dataset: { ...record.dataset, hash: datasetHash },
      formulation: { ...record.formulation, hash: formulationHash },
      updatedAt: new Date().toISOString(),
    };

    persist([completed, ...experiments]);
    setMessage(`${completed.experimentId} imported with SHA-256 manifests.`);
  };

  const updateReview = (experimentId, nextStatus) => {
    const records = experiments.map((record) =>
      record.experimentId === experimentId
        ? {
            ...record,
            humanReview: {
              ...record.humanReview,
              status: nextStatus,
              reviewer: nextStatus === "Approved for research" ? "Research lead" : "",
            },
            updatedAt: new Date().toISOString(),
          }
        : record,
    );
    persist(records);
  };

  const filtered = useMemo(
    () =>
      experiments.filter(
        (record) =>
          (sequence === "All sequences" || record.sequence === sequence) &&
          (status === "All statuses" || record.status === status),
      ),
    [experiments, sequence, status],
  );

  const validations = useMemo(
    () =>
      Object.fromEntries(
        experiments.map((record) => [
          record.experimentId,
          validateExperimentRecord(record),
        ]),
      ),
    [experiments],
  );

  const exportRegistry = async () => {
    const payload = buildRegistryExport(experiments);
    const manifestHash = await sha256Object(payload);
    downloadJson("agroq-quantum-registry-q0-q1.json", {
      ...payload,
      manifestHash,
      hashScope:
        "SHA-256 covers the stable serialized export before manifestHash is attached.",
    });
  };

  const registeredSequences = new Set(experiments.map((record) => record.sequence));

  return (
    <div className="quantum-registry-stack">
      <section className="quantum-registry-metrics">
        <article className="panel">
          <FlaskConical size={20} />
          <span>Experiment records</span>
          <strong>{experiments.length}</strong>
        </article>
        <article className="panel">
          <CheckCircle2 size={20} />
          <span>Valid records</span>
          <strong>
            {experiments.filter(
              (record) => validations[record.experimentId]?.valid,
            ).length}
          </strong>
        </article>
        <article className="panel">
          <GitBranch size={20} />
          <span>Sequences registered</span>
          <strong>{registeredSequences.size}/9</strong>
        </article>
        <article className="panel">
          <HardDrive size={20} />
          <span>Storage mode</span>
          <strong>Local prototype</strong>
        </article>
      </section>

      <section className="panel quantum-experiment-toolbar">
        <div>
          <Filter size={17} />
          <select value={sequence} onChange={(event) => setSequence(event.target.value)}>
            <option>All sequences</option>
            {experimentTemplates.map((template) => (
              <option key={template.sequence}>{template.sequence}</option>
            ))}
          </select>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option>All statuses</option>
            <option>Planned</option>
            <option>Registered</option>
            <option>Ready for baseline</option>
            <option>Simulation complete</option>
          </select>
        </div>
        <div>
          {frozenProblem && (
            <button className="button button-secondary" type="button" onClick={importFrozen}>
              <Database size={16} />
              Register frozen soil problem
            </button>
          )}
          <button className="button button-secondary" type="button" onClick={exportRegistry}>
            <Download size={16} />
            Export Q0 + Q1
          </button>
          <button
            className="button button-primary"
            type="button"
            onClick={() => setShowModal(true)}
          >
            <Plus size={16} />
            New registry record
          </button>
        </div>
      </section>

      {message && (
        <section className="panel quantum-registry-message">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}

      {filtered.length === 0 ? (
        <section className="panel quantum-registry-empty">
          <FlaskConical size={30} />
          <h3>No experiment records yet</h3>
          <p>
            Register the frozen Soil Biology problem or create the first planned Q2–Q10
            experiment record.
          </p>
        </section>
      ) : (
        <section className="quantum-experiment-list">
          {filtered.map((record) => {
            const validation = validations[record.experimentId];
            return (
              <article className="panel quantum-experiment-record" key={record.experimentId}>
                <div className="quantum-experiment-heading">
                  <div>
                    <span>
                      {record.sequence} · {record.experimentId}
                    </span>
                    <h3>{record.title}</h3>
                  </div>
                  <div>
                    <Badge tone={toneForStatus(record.status)}>{record.status}</Badge>
                    <Badge tone={validation.valid ? "green" : "red"}>
                      {validation.valid ? "Schema valid" : "Needs correction"}
                    </Badge>
                  </div>
                </div>

                <div className="quantum-experiment-grid">
                  <div>
                    <span>Problem family</span>
                    <strong>{record.problemFamily}</strong>
                  </div>
                  <div>
                    <span>Run type</span>
                    <strong>{record.runType}</strong>
                  </div>
                  <div>
                    <span>Algorithm</span>
                    <strong>{record.algorithm}</strong>
                  </div>
                  <div>
                    <span>Code commit</span>
                    <strong>{record.codeCommit}</strong>
                  </div>
                  <div>
                    <span>Dataset</span>
                    <strong>{record.dataset.id}</strong>
                    <small>{record.dataset.hash}</small>
                  </div>
                  <div>
                    <span>Formulation</span>
                    <strong>{record.formulation.type}</strong>
                    <small>{record.formulation.hash}</small>
                  </div>
                  <div>
                    <span>Classical baseline</span>
                    <strong>{record.classicalBaseline.algorithm}</strong>
                    <small>
                      Objective: {record.classicalBaseline.objective ?? "pending"}
                    </small>
                  </div>
                  <div>
                    <span>Human review</span>
                    <strong>{record.humanReview.status}</strong>
                    <small>{record.humanReview.reviewer || "No reviewer assigned"}</small>
                  </div>
                </div>

                <div className="quantum-claim-controls">
                  {[
                    ["Classical baseline required", record.claimControls.classicalBaselineRequired],
                    ["Matched budget", record.claimControls.matchedBudget],
                    ["Simulator only", record.claimControls.simulatorOnly],
                    ["Hardware used", record.claimControls.hardwareUsed],
                    ["Advantage claimed", record.claimControls.advantageClaim],
                    ["Operational dependency", record.claimControls.operationalDependency],
                    ["Human review required", record.humanReview.required],
                  ].map(([label, enabled]) => (
                    <div key={label}>
                      {enabled ? (
                        <CheckCircle2 size={15} />
                      ) : (
                        <X size={15} />
                      )}
                      <span>{label}</span>
                    </div>
                  ))}
                </div>

                {(validation.errors.length > 0 || validation.warnings.length > 0) && (
                  <div className="quantum-validation-box">
                    {validation.errors.map((error) => (
                      <p key={error}>Error: {error}</p>
                    ))}
                    {validation.warnings.map((warning) => (
                      <p key={warning}>Warning: {warning}</p>
                    ))}
                  </div>
                )}

                <div className="quantum-experiment-footer">
                  <div>
                    {record.sourceIds.map((sourceId) => (
                      <span key={sourceId}>{sourceId}</span>
                    ))}
                  </div>
                  <select
                    value={record.humanReview.status}
                    onChange={(event) =>
                      updateReview(record.experimentId, event.target.value)
                    }
                  >
                    <option>Pending</option>
                    <option>Under review</option>
                    <option>Approved for research</option>
                    <option>Rejected</option>
                  </select>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {showModal && (
        <ExperimentModal
          experimentIndex={experiments.length + 1}
          onClose={() => setShowModal(false)}
          onSave={addExperiment}
        />
      )}
    </div>
  );
}

function DataModel() {
  return (
    <div className="quantum-registry-stack">
      <section className="panel quantum-model-hero">
        <FileCode2 size={30} />
        <div>
          <span className="eyebrow">Q1 data contract</span>
          <h2>{quantumExperimentSchema.schemaId}</h2>
          <p>{quantumExperimentSchema.description}</p>
        </div>
        <Badge tone="green">{quantumExperimentSchema.required.length} required groups</Badge>
      </section>

      <section className="quantum-model-grid">
        {quantumExperimentSchema.groups.map((group, index) => (
          <article className="panel quantum-model-card" key={group.name}>
            <div className="quantum-model-number">{index + 1}</div>
            <h3>{group.name}</h3>
            <div>
              {group.fields.map((field) => (
                <code key={field}>{field}</code>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="panel quantum-model-boundary">
        <ShieldCheck size={22} />
        <div>
          <h3>Immutable evidence principle</h3>
          <p>
            A completed run should create a new registry record or append a reviewed
            result. Raw evidence, frozen hashes, seeds, solver budgets, and source links
            should not be silently overwritten.
          </p>
        </div>
      </section>
    </div>
  );
}

function ReproducibilityGate() {
  const gates = [
    ["Research sources linked", "Every mechanism points to one or more QRS records."],
    ["Dataset frozen", "Dataset ID, version, record count, and SHA-256 manifest recorded."],
    ["Formulation frozen", "Variables, constraints, objective, QUBO or model hash recorded."],
    ["Classical baseline complete", "Exact or recognized classical method executed first."],
    ["Matched budget declared", "Objective evaluations, shots, runtime, and tuning budget recorded."],
    ["Seeds recorded", "Data split, optimizer, simulator, and solver seeds preserved."],
    ["Quantum mode labeled", "Quantum-inspired, simulator, and hardware records remain distinct."],
    ["Circuit resources recorded", "Qubits, depth, two-qubit gates, shots, and noise model stored."],
    ["Feasibility checked", "Constraint violations and objective values reported together."],
    ["No unsupported advantage claim", "Claims require statistical, runtime, and resource review."],
    ["Human review completed", "A named reviewer approves research use before publication."],
    ["Artifacts exportable", "Inputs, configurations, results, plots, and environment metadata linked."],
  ];

  return (
    <div className="quantum-registry-stack">
      <section className="panel quantum-gate-hero">
        <ClipboardCheck size={30} />
        <div>
          <span className="eyebrow">Release control</span>
          <h2>Quantum Experiment Reproducibility Gate</h2>
          <p>
            Q2–Q10 cannot be marked reproducible until every applicable gate is
            documented.
          </p>
        </div>
      </section>

      <section className="quantum-gate-grid">
        {gates.map(([title, copy], index) => (
          <article className="panel" key={title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <CheckCircle2 size={20} />
            <h3>{title}</h3>
            <p>{copy}</p>
          </article>
        ))}
      </section>
    </div>
  );
}

function Acknowledgments() {
  const groups = [
    {
      title: "Optimization and QUBO",
      people:
        "Fred Glover, Gary Kochenberger, Yu Du, Edward Farhi, Jeffrey Goldstone, Sam Gutmann, Daniel J. Egger, Jakub Mareček, Stefan Woerner, Linghua Zhu and collaborators, Austin Gilliam, Constantin Gonciulea, Alisher Ortikov, and Alisher Ilhamov.",
      sources: ["QRS-001", "QRS-002", "QRS-003", "QRS-004", "QRS-012", "QRS-016"],
    },
    {
      title: "Quantum machine learning",
      people:
        "Vojtěch Havlíček and collaborators, Keisuke Fujii, Kohei Nakajima, Jarrod McClean and collaborators, and Guillaume Verdon and collaborators.",
      sources: ["QRS-005", "QRS-006", "QRS-013", "QRS-014"],
    },
    {
      title: "Probability algorithms",
      people: "Gilles Brassard, Peter Høyer, Michele Mosca, and Alain Tapp.",
      sources: ["QRS-007"],
    },
    {
      title: "Quantum sensing",
      people:
        "Anne Fabricant and collaborators; Donggyu Kim, Mohamed Ibrahim, Christopher Foy, Matthew Trusheim, Ruonan Han, Dirk Englund, and collaborators.",
      sources: ["QRS-008", "QRS-009"],
    },
    {
      title: "Quantum chemistry",
      people:
        "Alberto Peruzzo and collaborators; Markus Reiher, Nathan Wiebe, Krysta M. Svore, Dave Wecker, and Matthias Troyer.",
      sources: ["QRS-010", "QRS-011"],
    },
    {
      title: "Post-quantum security",
      people:
        "The National Institute of Standards and Technology and the international cryptographic research community contributing to the post-quantum standards process.",
      sources: ["QRS-015"],
    },
  ];

  return (
    <div className="quantum-registry-stack">
      <section className="panel quantum-ack-hero">
        <Sparkles size={30} />
        <div>
          <span className="eyebrow">Attribution and gratitude</span>
          <h2>Quantum Research Acknowledgments</h2>
          <p>
            AgroQ gives credit for intellectual foundations while clearly stating that
            citation does not imply endorsement, partnership, employment, or affiliation.
          </p>
        </div>
      </section>

      <section className="quantum-ack-grid">
        {groups.map((group) => (
          <article className="panel" key={group.title}>
            <Atom size={22} />
            <h3>{group.title}</h3>
            <p>{group.people}</p>
            <div>
              {group.sources.map((source) => (
                <span key={source}>{source}</span>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="panel quantum-ack-boundary">
        <ShieldCheck size={22} />
        <p>
          AgroQ independently selects its problems, designs its integrations, writes its
          code, and performs its own reproductions. Researchers are credited for the
          specific published mechanisms listed in Q0.
        </p>
      </section>
    </div>
  );
}

export default function QuantumRegistryWorkspace({ frozenProblem }) {
  const [activeTab, setActiveTab] = useState(tabs[0]);

  return (
    <section className="quantum-registry-workspace">
      <div className="quantum-registry-tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? "quantum-registry-tab-active" : ""}
            type="button"
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === tabs[0] && <SourceRegistry />}
      {activeTab === tabs[1] && <ExperimentRegistry frozenProblem={frozenProblem} />}
      {activeTab === tabs[2] && (
        <Q2SoilSamplingBenchmark frozenProblem={frozenProblem} />
      )}
      {activeTab === tabs[3] && <QuantumQ3Q10Workspace />}
      {activeTab === tabs[4] && <DataModel />}
      {activeTab === tabs[5] && <ReproducibilityGate />}
      {activeTab === tabs[6] && <Acknowledgments />}
    </section>
  );
}
