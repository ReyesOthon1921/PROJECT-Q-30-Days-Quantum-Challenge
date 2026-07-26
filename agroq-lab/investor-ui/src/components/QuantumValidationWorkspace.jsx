import {
  AlertTriangle,
  CheckCircle2,
  Database,
  History,
  LoaderCircle,
  RefreshCw,
  Repeat2,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  quantumRunValidationHistory,
  quantumValidationSummary,
  replayPersistentQuantumRun,
  validatePersistentQuantumRun,
  verifyPersistentQuantumDataset,
} from "../data/quantumApi";

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function tone(status) {
  if (status === "passed" || status === "pass") return "green";
  if (status === "warning") return "amber";
  if (status === "failed" || status === "error") return "red";
  return "slate";
}

export default function QuantumValidationWorkspace() {
  const [summary, setSummary] = useState(null);
  const [runId, setRunId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = await quantumValidationSummary();
      setSummary(payload);
      if (!runId && payload.runs?.length) setRunId(payload.runs[0].run_id);
      if (!datasetId && payload.datasets?.length) {
        setDatasetId(payload.datasets[0].dataset_id);
      }
    } catch (caught) {
      setError(caught.message || "Q14 validation service is unavailable.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const selectedRun = useMemo(
    () => summary?.runs?.find((item) => item.run_id === runId),
    [runId, summary],
  );

  const execute = async (operation) => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const payload = await operation();
      setLatest(payload.validation);
      setMessage(
        `${payload.validation.validation_id}: ${payload.validation.status}.`,
      );
      if (runId) {
        const historyPayload = await quantumRunValidationHistory(runId);
        setHistory(historyPayload.events || []);
      }
      await refresh();
    } catch (caught) {
      setError(caught.message || "Q14 operation failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="q14-stack">
      <section className="panel q14-hero">
        <ShieldCheck size={32} />
        <div>
          <span className="eyebrow">Q14 · Scientific validation</span>
          <h2>Quantum Reproducibility Control Center</h2>
          <p>
            Verify frozen data, replay the same seed and configuration, enforce
            classical baselines and matched budgets, and block unsupported claims.
          </p>
        </div>
        <Badge tone="green">Human-controlled</Badge>
      </section>

      <section className="q14-metrics">
        {[
          ["Passed", summary?.counts?.passed ?? 0, CheckCircle2],
          ["Warnings", summary?.counts?.warning ?? 0, AlertTriangle],
          ["Failed", summary?.counts?.failed ?? 0, XCircle],
          ["Runs", summary?.runs?.length ?? 0, History],
        ].map(([label, value, Icon]) => (
          <article className="panel" key={label}>
            <Icon size={20} />
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className="panel q14-toolbar">
        <p>
          Approval stays blocked until every error gate passes. Warnings remain
          visible in the immutable validation history.
        </p>
        <button
          className="button button-secondary"
          type="button"
          onClick={refresh}
          disabled={busy}
        >
          {busy ? <LoaderCircle className="q14-spin" size={17} /> : <RefreshCw size={17} />}
          Refresh
        </button>
      </section>

      {message && <div className="panel q14-message q14-ok">{message}</div>}
      {error && <div className="panel q14-message q14-error">{error}</div>}

      <section className="q14-grid">
        <article className="panel q14-card">
          <Database size={22} />
          <h3>Persistent-data integrity</h3>
          <select value={datasetId} onChange={(event) => setDatasetId(event.target.value)}>
            <option value="">Choose dataset</option>
            {(summary?.datasets || []).map((dataset) => (
              <option key={dataset.dataset_id} value={dataset.dataset_id}>
                {dataset.dataset_id} · {dataset.name}
              </option>
            ))}
          </select>
          <button
            className="button button-primary"
            type="button"
            disabled={busy || !datasetId}
            onClick={() =>
              execute(() => verifyPersistentQuantumDataset(datasetId))
            }
          >
            Verify frozen dataset
          </button>
        </article>

        <article className="panel q14-card">
          <ShieldCheck size={22} />
          <h3>Scientific gates</h3>
          <select
            value={runId}
            onChange={(event) => {
              setRunId(event.target.value);
              setLatest(null);
              setHistory([]);
            }}
          >
            <option value="">Choose run</option>
            {(summary?.runs || []).map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {run.sequence} · {run.run_id}
              </option>
            ))}
          </select>
          {selectedRun && (
            <small>
              {selectedRun.title} · {selectedRun.status}
            </small>
          )}
          <div className="q14-actions">
            <button
              className="button button-primary"
              type="button"
              disabled={busy || !runId}
              onClick={() =>
                execute(() => validatePersistentQuantumRun(runId, false))
              }
            >
              Validate
            </button>
            <button
              className="button button-secondary"
              type="button"
              disabled={busy || !runId}
              onClick={() => execute(() => replayPersistentQuantumRun(runId))}
            >
              <Repeat2 size={16} />
              Replay
            </button>
            <button
              className="button button-secondary"
              type="button"
              disabled={busy || !runId}
              onClick={async () => {
                const payload = await quantumRunValidationHistory(runId);
                setHistory(payload.events || []);
              }}
            >
              <History size={16} />
              History
            </button>
          </div>
        </article>
      </section>

      <section className="panel q14-results">
        <div>
          <h3>{latest?.gate_type || "Latest validation"}</h3>
          {latest && <Badge tone={tone(latest.status)}>{latest.status}</Badge>}
        </div>
        {(latest?.findings || []).map((finding) => (
          <article key={`${finding.code}-${finding.message}`}>
            {finding.status === "pass" ? (
              <CheckCircle2 size={16} />
            ) : finding.status === "warning" ? (
              <AlertTriangle size={16} />
            ) : (
              <XCircle size={16} />
            )}
            <div>
              <strong>{finding.code}</strong>
              <p>{finding.message}</p>
            </div>
            <Badge tone={tone(finding.status)}>{finding.status}</Badge>
          </article>
        ))}
      </section>

      <section className="panel q14-history">
        <h3>Validation history</h3>
        {history.length === 0 ? (
          <p>No run history loaded.</p>
        ) : (
          history.map((event) => (
            <article key={event.validation_id}>
              <strong>{event.gate_type}</strong>
              <span>{event.validation_id}</span>
              <Badge tone={tone(event.status)}>{event.status}</Badge>
              <small>{event.created_at}</small>
            </article>
          ))
        )}
      </section>
    </div>
  );
}
