import {
  Archive,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileArchive,
  History,
  LoaderCircle,
  RefreshCw,
  Save,
  ShieldCheck,
  UserCheck,
  Workflow,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  assignQuantumResearchOperation,
  createQuantumResearchOperation,
  downloadQuantumEvidenceBundle,
  ensureQuantumRunOperation,
  getQuantumResearchOperation,
  listQuantumResearchOperations,
  transitionQuantumResearchOperation,
  updateQuantumReleaseChecklist,
} from "../data/quantumApi";

const MANUAL_CHECKS = [
  ["limitations_disclosed", "Limitations disclosed"],
  ["evidence_reviewed", "Evidence package reviewed"],
  ["rollback_plan_documented", "Rollback plan documented"],
  ["release_notes_complete", "Release notes complete"],
];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function stateTone(state) {
  if (["Approved for research", "Released", "Completed"].includes(state)) {
    return "green";
  }
  if (["Rejected", "Failed"].includes(state)) return "red";
  if (["Under review", "Ready to run", "Running"].includes(state)) {
    return "amber";
  }
  return "slate";
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function QuantumResearchOpsWorkspace() {
  const [summary, setSummary] = useState(null);
  const [operationId, setOperationId] = useState("");
  const [detail, setDetail] = useState(null);
  const [experimentId, setExperimentId] = useState("");
  const [runId, setRunId] = useState("");
  const [targetState, setTargetState] = useState("");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [limitations, setLimitations] = useState("");
  const [researcherId, setResearcherId] = useState("");
  const [reviewerId, setReviewerId] = useState("");
  const [manual, setManual] = useState(
    Object.fromEntries(MANUAL_CHECKS.map(([key]) => [key, false])),
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = await listQuantumResearchOperations();
      setSummary(payload);
      if (!operationId && payload.operations?.length) {
        setOperationId(payload.operations[0].operation_id);
      }
      if (!experimentId && payload.experiments?.length) {
        setExperimentId(payload.experiments[0].experiment_id);
      }
      if (!runId && payload.runs?.length) {
        setRunId(payload.runs[0].run_id);
      }
    } catch (caught) {
      setError(caught.message || "Q15 research operations are unavailable.");
    } finally {
      setBusy(false);
    }
  };

  const loadDetail = async (id = operationId) => {
    if (!id) {
      setDetail(null);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const payload = await getQuantumResearchOperation(id);
      setDetail(payload);
      const operation = payload.operation;
      setNotes(operation.research_notes || "");
      setLimitations(operation.limitations || "");
      setResearcherId(operation.researcher_id || "");
      setReviewerId(operation.reviewer_id || "");
      setManual({
        ...Object.fromEntries(MANUAL_CHECKS.map(([key]) => [key, false])),
        ...(payload.release_checklist?.manual || {}),
      });
      setTargetState(payload.allowed_transitions?.[0] || "");
    } catch (caught) {
      setError(caught.message || "Research operation could not be loaded.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (operationId) loadDetail(operationId);
  }, [operationId]);

  const selectedOperation = detail?.operation;
  const checklist = detail?.release_checklist;

  const metrics = useMemo(
    () => [
      ["Draft", summary?.counts?.Draft ?? 0],
      ["Under review", summary?.counts?.["Under review"] ?? 0],
      ["Approved", summary?.counts?.["Approved for research"] ?? 0],
      ["Released", summary?.counts?.Released ?? 0],
    ],
    [summary],
  );

  const perform = async (operation, successMessage) => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      await operation();
      setMessage(successMessage);
      await refresh();
      if (operationId) await loadDetail(operationId);
    } catch (caught) {
      setError(caught.message || "Q15 operation failed.");
    } finally {
      setBusy(false);
    }
  };

  const createDraft = () =>
    perform(
      () =>
        createQuantumResearchOperation({
          experiment_id: experimentId,
          research_notes: notes,
          limitations,
        }),
      "Draft research operation created.",
    );

  const ensureRun = async () => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const payload = await ensureQuantumRunOperation(runId);
      setOperationId(payload.operation.operation_id);
      setMessage(`${payload.operation.operation_id} connected to ${runId}.`);
      await refresh();
      await loadDetail(payload.operation.operation_id);
    } catch (caught) {
      setError(caught.message || "Persistent run could not be connected.");
    } finally {
      setBusy(false);
    }
  };

  const transition = () =>
    perform(
      () =>
        transitionQuantumResearchOperation(operationId, {
          to_state: targetState,
          reason,
          research_notes: notes,
          limitations,
        }),
      `Lifecycle transition to ${targetState} recorded.`,
    );

  const saveAssignments = () =>
    perform(
      () =>
        assignQuantumResearchOperation(operationId, {
          researcher_id: researcherId,
          reviewer_id: reviewerId || null,
        }),
      "Named researcher and reviewer assignments updated.",
    );

  const saveChecklist = () =>
    perform(
      () => updateQuantumReleaseChecklist(operationId, manual),
      "Release checklist certification recorded.",
    );

  const exportEvidence = async () => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const bundle = await downloadQuantumEvidenceBundle(operationId);
      downloadBlob(bundle.blob, bundle.filename);
      setMessage(
        `${bundle.bundleId || "Evidence bundle"} generated with SHA-256 ${bundle.sha256 || "recorded"}.`,
      );
      await refresh();
      await loadDetail(operationId);
    } catch (caught) {
      setError(caught.message || "Evidence package generation failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="q15-stack">
      <section className="panel q15-hero">
        <Workflow size={34} />
        <div>
          <span className="eyebrow">Q15 · Research operations</span>
          <h2>Controlled Quantum Research Lifecycle</h2>
          <p>
            Track named ownership, immutable lifecycle decisions, independent
            review, superseded work, evidence-package generation, release
            readiness, and manual approval without rewriting raw evidence.
          </p>
        </div>
        <Badge tone="green">Audit controlled</Badge>
      </section>

      <section className="q15-metrics">
        {metrics.map(([label, value]) => (
          <article className="panel" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className="panel q15-toolbar">
        <div>
          <ShieldCheck size={18} />
          <span>
            Researchers prepare and submit work. A different administrator must
            approve or reject it. Release requires a complete evidence bundle
            and checklist.
          </span>
        </div>
        <button
          className="button button-secondary"
          type="button"
          onClick={refresh}
          disabled={busy}
        >
          {busy ? (
            <LoaderCircle className="q15-spin" size={17} />
          ) : (
            <RefreshCw size={17} />
          )}
          Refresh Q15
        </button>
      </section>

      {message && (
        <section className="panel q15-message q15-message-ok">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}
      {error && (
        <section className="panel q15-message q15-message-error">
          <XCircle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="q15-grid">
        <article className="panel q15-card">
          <div className="q15-heading">
            <Workflow size={22} />
            <div>
              <span className="eyebrow">Create or connect</span>
              <h3>Research operation</h3>
            </div>
          </div>

          <label>
            Experiment for new draft
            <select
              value={experimentId}
              onChange={(event) => setExperimentId(event.target.value)}
            >
              <option value="">Choose experiment</option>
              {(summary?.experiments || []).map((experiment) => (
                <option
                  key={experiment.experiment_id}
                  value={experiment.experiment_id}
                >
                  {experiment.sequence} · {experiment.title}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button button-secondary"
            type="button"
            onClick={createDraft}
            disabled={busy || !experimentId}
          >
            Create draft
          </button>

          <label>
            Existing persistent run
            <select
              value={runId}
              onChange={(event) => setRunId(event.target.value)}
            >
              <option value="">Choose run</option>
              {(summary?.runs || []).map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {run.sequence} · {run.run_id} · {run.status}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button button-primary"
            type="button"
            onClick={ensureRun}
            disabled={busy || !runId}
          >
            Connect persistent run
          </button>
        </article>

        <article className="panel q15-card">
          <div className="q15-heading">
            <Archive size={22} />
            <div>
              <span className="eyebrow">Operation registry</span>
              <h3>Select lifecycle record</h3>
            </div>
          </div>
          <select
            value={operationId}
            onChange={(event) => setOperationId(event.target.value)}
          >
            <option value="">Choose operation</option>
            {(summary?.operations || []).map((operation) => (
              <option
                key={operation.operation_id}
                value={operation.operation_id}
              >
                {operation.lifecycle_state} · {operation.operation_id}
              </option>
            ))}
          </select>
          {selectedOperation && (
            <div className="q15-selected">
              <div>
                <strong>{selectedOperation.operation_id}</strong>
                <Badge tone={stateTone(selectedOperation.lifecycle_state)}>
                  {selectedOperation.lifecycle_state}
                </Badge>
              </div>
              <span>
                Researcher:{" "}
                {selectedOperation.researcher_name ||
                  selectedOperation.researcher_id}
              </span>
              <span>
                Reviewer:{" "}
                {selectedOperation.reviewer_name ||
                  selectedOperation.reviewer_id ||
                  "Not assigned"}
              </span>
              <span>
                Run: {selectedOperation.run_id || "Not attached"}
              </span>
              {selectedOperation.run?.error_message && (
                <span className="q15-run-error">
                  Failure diagnostic: {selectedOperation.run.error_message}
                </span>
              )}
            </div>
          )}
        </article>
      </section>

      {selectedOperation && (
        <>
          <section className="q15-grid">
            <article className="panel q15-card">
              <div className="q15-heading">
                <UserCheck size={22} />
                <div>
                  <span className="eyebrow">Named accountability</span>
                  <h3>Researcher and reviewer</h3>
                </div>
              </div>
              <label>
                Researcher user ID
                <input
                  value={researcherId}
                  onChange={(event) => setResearcherId(event.target.value)}
                />
              </label>
              <label>
                Reviewer user ID
                <input
                  value={reviewerId}
                  onChange={(event) => setReviewerId(event.target.value)}
                  placeholder="Administrator different from researcher"
                />
              </label>
              <button
                className="button button-secondary"
                type="button"
                onClick={saveAssignments}
                disabled={busy}
              >
                <Save size={17} />
                Save assignments
              </button>
            </article>

            <article className="panel q15-card">
              <div className="q15-heading">
                <History size={22} />
                <div>
                  <span className="eyebrow">State transition</span>
                  <h3>Record lifecycle decision</h3>
                </div>
              </div>
              <label>
                Next allowed state
                <select
                  value={targetState}
                  onChange={(event) => setTargetState(event.target.value)}
                >
                  {(detail?.allowed_transitions || []).map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Decision reason
                <textarea
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="Why this transition is justified"
                />
              </label>
              <button
                className="button button-primary"
                type="button"
                onClick={transition}
                disabled={busy || !targetState || !reason.trim()}
              >
                Record transition
              </button>
            </article>
          </section>

          <section className="panel q15-notes">
            <div className="q15-heading">
              <ClipboardCheck size={22} />
              <div>
                <span className="eyebrow">Research interpretation</span>
                <h3>Notes and limitations</h3>
              </div>
            </div>
            <div className="q15-grid">
              <label>
                Research notes
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="What was tested, compared, and observed"
                />
              </label>
              <label>
                Known limitations
                <textarea
                  value={limitations}
                  onChange={(event) => setLimitations(event.target.value)}
                  placeholder="Simulation, data, hardware, and claim limitations"
                />
              </label>
            </div>
          </section>

          <section className="q15-grid">
            <article className="panel q15-card">
              <div className="q15-heading">
                <FileArchive size={22} />
                <div>
                  <span className="eyebrow">Evidence package</span>
                  <h3>Immutable research export</h3>
                </div>
              </div>
              <p>
                Export experiment, frozen-data manifest, lineage records,
                configuration, solver results, validation history, review
                history, claim controls, environment, artifacts, and checksums.
              </p>
              <button
                className="button button-primary"
                type="button"
                onClick={exportEvidence}
                disabled={busy || !selectedOperation.run_id}
              >
                <Download size={17} />
                Generate evidence ZIP
              </button>
              <small>
                Bundles recorded:{" "}
                {selectedOperation.evidence_bundles?.length || 0}
              </small>
            </article>

            <article className="panel q15-card">
              <div className="q15-heading">
                <ClipboardCheck size={22} />
                <div>
                  <span className="eyebrow">Release controls</span>
                  <h3>Manual checklist</h3>
                </div>
              </div>
              <div className="q15-checklist">
                {MANUAL_CHECKS.map(([key, label]) => (
                  <label key={key}>
                    <input
                      type="checkbox"
                      checked={Boolean(manual[key])}
                      onChange={(event) =>
                        setManual((current) => ({
                          ...current,
                          [key]: event.target.checked,
                        }))
                      }
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
              <button
                className="button button-secondary"
                type="button"
                onClick={saveChecklist}
                disabled={busy}
              >
                Certify checklist
              </button>
              <Badge tone={checklist?.complete ? "green" : "amber"}>
                {checklist?.complete
                  ? "Release ready"
                  : "Release blocked"}
              </Badge>
            </article>
          </section>

          <section className="panel q15-history">
            <div className="q15-heading">
              <History size={22} />
              <div>
                <span className="eyebrow">Immutable history</span>
                <h3>Lifecycle decisions</h3>
              </div>
            </div>
            {(selectedOperation.history || []).length === 0 ? (
              <p>No lifecycle events recorded.</p>
            ) : (
              <div className="q15-history-list">
                {selectedOperation.history.map((event) => (
                  <article key={event.event_id}>
                    <div>
                      <strong>
                        {event.from_state || "Created"} → {event.to_state}
                      </strong>
                      <span>{event.reason}</span>
                    </div>
                    <small>
                      {event.actor_name || event.actor_id} · {event.created_at}
                    </small>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
