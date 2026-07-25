import {
  CheckCircle2,
  Database,
  Download,
  FlaskConical,
  Link2,
  LoaderCircle,
  Play,
  RefreshCw,
  Save,
  Server,
  ShieldCheck,
  Table2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  attachQuantumDataset,
  freezeQuantumDataset,
  listPersistentQuantumExperiments,
  listQuantumDatasets,
  quantumBackendHealth,
  reviewPersistentQuantumRun,
  runPersistentQuantumExperiment,
} from "../data/quantumApi";

const DATASET_TABLES = [
  ["plots", "Plots"],
  ["observations", "Observations"],
  ["samples", "Samples"],
  ["treatments", "Treatments"],
  ["treatment_assignments", "Treatment assignments"],
  ["manual_tasks", "Manual tasks"],
  ["gateway_devices", "Gateway devices"],
  ["device_health_events", "Device-health events"],
  ["experiments", "Field experiments"],
  ["evidence_attachments", "Evidence attachments"],
];

const SEQUENCES = ["Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return String(value);
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

export default function QuantumBackendWorkspace() {
  const [health, setHealth] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selectedTables, setSelectedTables] = useState([
    "plots",
    "observations",
  ]);
  const [datasetName, setDatasetName] = useState(
    "AgroQ Quantum Research Snapshot",
  );
  const [permitted, setPermitted] = useState([...SEQUENCES]);
  const [selectedExperiment, setSelectedExperiment] = useState("");
  const [selectedDataset, setSelectedDataset] = useState("");
  const [runBudget, setRunBudget] = useState(2048);
  const [seed, setSeed] = useState(301);
  const [gridSize, setGridSize] = useState(11);
  const [latestRun, setLatestRun] = useState(null);
  const [reviewNotes, setReviewNotes] = useState(
    "Reviewed formulation, frozen data lineage, solver comparison, and claim controls.",
  );
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const authenticated = Boolean(health);

  const refresh = async () => {
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const [healthPayload, datasetPayload, experimentPayload] =
        await Promise.all([
          quantumBackendHealth(),
          listQuantumDatasets(),
          listPersistentQuantumExperiments(),
        ]);
      setHealth(healthPayload);
      setDatasets(datasetPayload.datasets || []);
      setExperiments(experimentPayload.experiments || []);
      if (!selectedDataset && datasetPayload.datasets?.length) {
        setSelectedDataset(datasetPayload.datasets[0].dataset_id);
      }
      if (
        !selectedExperiment &&
        experimentPayload.experiments?.length
      ) {
        setSelectedExperiment(
          experimentPayload.experiments[0].experiment_id,
        );
      }
    } catch (caught) {
      setHealth(null);
      setDatasets([]);
      setExperiments([]);
      if (caught.status === 401) {
        setError(
          "Sign in to AgroQ to use persistent quantum storage, data freezing, server runs, and reviews.",
        );
      } else if (caught.status === 403) {
        setError(
          "This account can view the public simulator, but persistent research operations require additional permissions.",
        );
      } else {
        setError(caught.message || "Quantum backend is unavailable.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const toggleTable = (table) => {
    setSelectedTables((current) =>
      current.includes(table)
        ? current.filter((item) => item !== table)
        : [...current, table],
    );
  };

  const toggleSequence = (sequence) => {
    setPermitted((current) =>
      current.includes(sequence)
        ? current.filter((item) => item !== sequence)
        : [...current, sequence],
    );
  };

  const freezeDataset = async () => {
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const payload = await freezeQuantumDataset({
        name: datasetName,
        source_tables: selectedTables,
        permitted_families: permitted,
      });
      setDatasets((current) => [payload.dataset, ...current]);
      setMessage(
        `${payload.dataset.dataset_id} frozen with ${payload.dataset.record_count} lineage records.`,
      );
    } catch (caught) {
      setError(caught.message || "Dataset freeze failed.");
    } finally {
      setLoading(false);
    }
  };

  const attachDataset = async () => {
    if (!selectedExperiment || !selectedDataset) {
      setError("Choose both a persistent experiment and a frozen dataset.");
      return;
    }
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const payload = await attachQuantumDataset(
        selectedExperiment,
        selectedDataset,
      );
      setExperiments((current) =>
        current.map((item) =>
          item.experiment_id === payload.experiment.experiment_id
            ? payload.experiment
            : item,
        ),
      );
      setMessage(
        `${selectedDataset} attached to ${selectedExperiment}.`,
      );
    } catch (caught) {
      setError(caught.message || "Dataset attachment failed.");
    } finally {
      setLoading(false);
    }
  };

  const runExperiment = async () => {
    if (!selectedExperiment) {
      setError("Choose a persistent experiment first.");
      return;
    }
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const payload = await runPersistentQuantumExperiment(
        selectedExperiment,
        {
          seed,
          run_budget: runBudget,
          grid_size: gridSize,
        },
      );
      setLatestRun(payload.run);
      setMessage(
        `${payload.run.run_id} completed and stored with ${payload.run.artifacts.length} evidence artifacts.`,
      );
      await refresh();
    } catch (caught) {
      setError(caught.message || "Server-side quantum run failed.");
    } finally {
      setLoading(false);
    }
  };

  const reviewRun = async (decision) => {
    if (!latestRun) return;
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const payload = await reviewPersistentQuantumRun(
        latestRun.run_id,
        decision,
        reviewNotes,
      );
      setMessage(
        `${payload.review.review_id} recorded: ${payload.review.decision}.`,
      );
      const updated = {
        ...latestRun,
        reviews: [payload.review, ...(latestRun.reviews || [])],
      };
      setLatestRun(updated);
    } catch (caught) {
      setError(caught.message || "Run review failed.");
    } finally {
      setLoading(false);
    }
  };

  const selectedExperimentRecord = useMemo(
    () =>
      experiments.find(
        (item) => item.experiment_id === selectedExperiment,
      ),
    [experiments, selectedExperiment],
  );

  return (
    <div className="q-backend-stack">
      <section className="panel q-backend-hero">
        <div className="q-backend-hero-icon">
          <Server size={32} />
        </div>
        <div>
          <span className="eyebrow">Q11–Q13 combined</span>
          <h2>Persistent Quantum Research Backend</h2>
          <p>
            Move experiment records out of browser-only storage, freeze
            traceable AgroQ datasets, execute reproducible Python server runs,
            preserve artifacts and claim controls, and require human review.
          </p>
        </div>
        <Badge tone={authenticated ? "green" : "amber"}>
          {authenticated ? "Backend connected" : "Sign-in required"}
        </Badge>
      </section>

      <section className="q-backend-metrics">
        <article className="panel">
          <Database size={20} />
          <span>Frozen datasets</span>
          <strong>{health?.counts?.datasets ?? 0}</strong>
        </article>
        <article className="panel">
          <FlaskConical size={20} />
          <span>Persistent experiments</span>
          <strong>{health?.counts?.experiments ?? 0}</strong>
        </article>
        <article className="panel">
          <Play size={20} />
          <span>Server runs</span>
          <strong>{health?.counts?.runs ?? 0}</strong>
        </article>
        <article className="panel">
          <Link2 size={20} />
          <span>Research sources</span>
          <strong>{health?.counts?.sources ?? 0}</strong>
        </article>
      </section>

      <section className="panel q-backend-toolbar">
        <div>
          <ShieldCheck size={18} />
          <span>
            Persistent writes require an administrator or researcher session.
            Viewer access remains read-only.
          </span>
        </div>
        <button
          className="button button-secondary"
          type="button"
          onClick={refresh}
          disabled={loading}
        >
          {loading ? (
            <LoaderCircle className="q-backend-spin" size={17} />
          ) : (
            <RefreshCw size={17} />
          )}
          Refresh backend
        </button>
        {!authenticated && (
          <a className="button button-primary" href="/login">
            Sign in
          </a>
        )}
      </section>

      {message && (
        <section className="panel q-backend-message q-backend-message-ok">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}

      {error && (
        <section className="panel q-backend-message q-backend-message-error">
          <XCircle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="q-backend-two-column">
        <article className="panel q-backend-card">
          <div className="q-backend-card-heading">
            <div>
              <span className="eyebrow">Q13 · Data lineage</span>
              <h2>Freeze AgroQ dataset</h2>
            </div>
            <Table2 size={22} />
          </div>

          <label>
            Snapshot name
            <input
              value={datasetName}
              onChange={(event) => setDatasetName(event.target.value)}
            />
          </label>

          <div className="q-backend-field-group">
            <span>Source tables</span>
            <div className="q-backend-check-grid">
              {DATASET_TABLES.map(([table, label]) => (
                <label key={table}>
                  <input
                    type="checkbox"
                    checked={selectedTables.includes(table)}
                    onChange={() => toggleTable(table)}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="q-backend-field-group">
            <span>Permitted experiment families</span>
            <div className="q-backend-sequence-grid">
              {SEQUENCES.map((sequence) => (
                <button
                  key={sequence}
                  className={
                    permitted.includes(sequence)
                      ? "q-backend-sequence-on"
                      : ""
                  }
                  type="button"
                  onClick={() => toggleSequence(sequence)}
                >
                  {sequence}
                </button>
              ))}
            </div>
          </div>

          <button
            className="button button-primary full-width"
            type="button"
            onClick={freezeDataset}
            disabled={
              loading ||
              !authenticated ||
              !datasetName.trim() ||
              selectedTables.length === 0 ||
              permitted.length === 0
            }
          >
            <Save size={17} />
            Freeze dataset and lineage
          </button>
        </article>

        <article className="panel q-backend-card">
          <div className="q-backend-card-heading">
            <div>
              <span className="eyebrow">Q12 · Server runner</span>
              <h2>Execute persistent experiment</h2>
            </div>
            <Server size={22} />
          </div>

          <label>
            Registered experiment
            <select
              value={selectedExperiment}
              onChange={(event) =>
                setSelectedExperiment(event.target.value)
              }
            >
              <option value="">Choose an experiment</option>
              {experiments.map((item) => (
                <option
                  key={item.experiment_id}
                  value={item.experiment_id}
                >
                  {item.sequence} · {item.title}
                </option>
              ))}
            </select>
          </label>

          <label>
            Frozen dataset
            <select
              value={selectedDataset}
              onChange={(event) =>
                setSelectedDataset(event.target.value)
              }
            >
              <option value="">Choose a frozen dataset</option>
              {datasets.map((dataset) => (
                <option
                  key={dataset.dataset_id}
                  value={dataset.dataset_id}
                >
                  {dataset.name} · {dataset.record_count} records
                </option>
              ))}
            </select>
          </label>

          <button
            className="button button-secondary full-width"
            type="button"
            onClick={attachDataset}
            disabled={
              loading ||
              !authenticated ||
              !selectedExperiment ||
              !selectedDataset
            }
          >
            <Link2 size={17} />
            Attach frozen dataset
          </button>

          {selectedExperimentRecord && (
            <div className="q-backend-selected-experiment">
              <Badge tone="green">
                {selectedExperimentRecord.sequence}
              </Badge>
              <strong>{selectedExperimentRecord.problem_family}</strong>
              <small>
                Dataset:{" "}
                {selectedExperimentRecord.dataset_id ||
                  "synthetic fallback"}
              </small>
            </div>
          )}

          <label>
            Seed
            <input
              type="number"
              value={seed}
              onChange={(event) => setSeed(Number(event.target.value))}
            />
          </label>

          <label>
            Matched stochastic budget
            <strong>{runBudget}</strong>
            <input
              type="range"
              min="512"
              max="8192"
              step="512"
              value={runBudget}
              onChange={(event) =>
                setRunBudget(Number(event.target.value))
              }
            />
          </label>

          <label>
            QAOA parameter grid
            <strong>
              {gridSize} × {gridSize}
            </strong>
            <input
              type="range"
              min="5"
              max="21"
              step="2"
              value={gridSize}
              onChange={(event) =>
                setGridSize(Number(event.target.value))
              }
            />
          </label>

          <button
            className="button button-primary full-width"
            type="button"
            onClick={runExperiment}
            disabled={loading || !authenticated || !selectedExperiment}
          >
            <Play size={17} />
            Run on Flask server
          </button>
        </article>
      </section>

      <section className="panel q-backend-card">
        <div className="q-backend-card-heading">
          <div>
            <span className="eyebrow">Frozen evidence inventory</span>
            <h2>Persistent datasets</h2>
          </div>
          <Database size={22} />
        </div>
        {datasets.length === 0 ? (
          <p className="q-backend-empty-copy">
            No persistent dataset snapshots are available for this session.
          </p>
        ) : (
          <div className="q-backend-dataset-grid">
            {datasets.map((dataset) => (
              <article key={dataset.dataset_id}>
                <div>
                  <Badge
                    tone={
                      dataset.review_status === "approved"
                        ? "green"
                        : "amber"
                    }
                  >
                    {dataset.review_status}
                  </Badge>
                  <span>{dataset.dataset_id}</span>
                </div>
                <h3>{dataset.name}</h3>
                <p>
                  {dataset.record_count} records from{" "}
                  {dataset.source_tables.join(", ")}
                </p>
                <code>{dataset.sha256}</code>
                <small>{formatDate(dataset.created_at)}</small>
              </article>
            ))}
          </div>
        )}
      </section>

      {latestRun && (
        <section className="panel q-backend-card">
          <div className="q-backend-card-heading">
            <div>
              <span className="eyebrow">Persistent run evidence</span>
              <h2>{latestRun.run_id}</h2>
            </div>
            <Badge tone="green">{latestRun.status}</Badge>
          </div>

          <div className="q-backend-run-grid">
            <div>
              <span>Result hash</span>
              <code>{latestRun.result_sha256}</code>
            </div>
            <div>
              <span>Runtime</span>
              <strong>
                {Number(latestRun.runtime_seconds || 0).toFixed(4)} s
              </strong>
            </div>
            <div>
              <span>Solver records</span>
              <strong>{latestRun.solver_results?.length || 0}</strong>
            </div>
            <div>
              <span>Artifacts</span>
              <strong>{latestRun.artifacts?.length || 0}</strong>
            </div>
          </div>

          <div className="q-backend-artifact-list">
            {(latestRun.artifacts || []).map((artifact) => (
              <a
                key={artifact.artifact_id}
                href={`/api/quantum/artifacts/${encodeURIComponent(
                  artifact.artifact_id,
                )}`}
              >
                <Download size={15} />
                <span>{artifact.filename}</span>
                <small>{artifact.sha256}</small>
              </a>
            ))}
          </div>

          <label>
            Review notes
            <textarea
              rows="3"
              value={reviewNotes}
              onChange={(event) =>
                setReviewNotes(event.target.value)
              }
            />
          </label>

          <div className="q-backend-review-actions">
            <button
              className="button button-primary"
              type="button"
              onClick={() =>
                reviewRun("approved_for_research")
              }
              disabled={loading || !reviewNotes.trim()}
            >
              <CheckCircle2 size={17} />
              Approve for research
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => reviewRun("needs_revision")}
              disabled={loading || !reviewNotes.trim()}
            >
              Needs revision
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => reviewRun("rejected")}
              disabled={loading || !reviewNotes.trim()}
            >
              Reject
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() =>
                downloadJson(
                  `${latestRun.run_id.toLowerCase()}-registry.json`,
                  latestRun,
                )
              }
            >
              <Download size={17} />
              Export registry record
            </button>
          </div>
        </section>
      )}

      <section className="panel q-backend-boundary">
        <ShieldCheck size={22} />
        <div>
          <h3>Persistent research boundary</h3>
          <p>
            Q11–Q13 adds durable storage, lineage, server execution, evidence
            artifacts, and review controls. It does not authorize autonomous
            field control, quantum-hardware claims, quantum-advantage claims,
            chemistry-grade interpretation, or production cryptographic
            migration.
          </p>
        </div>
      </section>
    </div>
  );
}
