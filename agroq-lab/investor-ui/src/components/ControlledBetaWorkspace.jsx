import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileArchive,
  FlaskConical,
  LoaderCircle,
  RefreshCw,
  Rocket,
  Save,
  ShieldCheck,
  Users,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  controlledBetaSummary,
  createControlledBetaClaim,
  createControlledBetaInterview,
  createControlledBetaYcUpdate,
  createPilotDiscoveryRecord,
  createStagingCandidate,
  decideStagingCandidate,
  downloadControlledBetaEvidence,
  getStagingCandidate,
  recordStagingAcceptanceCheck,
  syncControlledBetaContacts,
  updateControlledBetaEvidence,
  updateStagingDeployment,
} from "../data/quantumApi";

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function statusTone(status) {
  if (["passed", "verified", "accepted", "approved", "completed"].includes(status)) {
    return "green";
  }
  if (["failed", "rejected", "declined", "blocked"].includes(status)) {
    return "red";
  }
  if (["pending", "captured", "verifying", "deployed", "reviewing"].includes(status)) {
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

const EMPTY_CANDIDATE = {
  commit_sha: "",
  release_tag: "",
  backend_url: "",
  frontend_url: "",
  service_id: "",
  notes: "",
};

const EMPTY_INTERVIEW = {
  contact_id: "",
  interview_type: "discovery",
  scheduled_at: "",
  completed_at: "",
  goals: "",
  pains: "",
  current_workflow: "",
  success_criteria: "",
  risk_notes: "",
  decision: "pending",
};

const EMPTY_PILOT = {
  contact_id: "",
  site_type: "",
  location_region: "",
  manual_workflow: "",
  available_infrastructure: "",
  data_sources: "",
  constraints: "",
  proposed_scope: "",
  exclusion_scope: "",
};

const EMPTY_CLAIM = {
  claim_text: "",
  claim_type: "product",
  evidence_level: "prototype",
  status: "draft",
  evidence_reference: "",
  limitations: "",
};

const EMPTY_YC = {
  headline: "",
  summary: "",
  metrics: "",
  limitations: "",
};

export default function ControlledBetaWorkspace() {
  const [summary, setSummary] = useState(null);
  const [candidateId, setCandidateId] = useState("");
  const [detail, setDetail] = useState(null);
  const [candidateForm, setCandidateForm] = useState(EMPTY_CANDIDATE);
  const [deploymentStatus, setDeploymentStatus] = useState("draft");
  const [interviewForm, setInterviewForm] = useState(EMPTY_INTERVIEW);
  const [pilotForm, setPilotForm] = useState(EMPTY_PILOT);
  const [claimForm, setClaimForm] = useState(EMPTY_CLAIM);
  const [ycForm, setYcForm] = useState(EMPTY_YC);
  const [decisionReason, setDecisionReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = await controlledBetaSummary();
      setSummary(payload);
      if (!candidateId && payload.candidates?.length) {
        setCandidateId(payload.candidates[0].candidate_id);
      }
    } catch (caught) {
      setError(caught.message || "Controlled-beta operations are unavailable.");
    } finally {
      setBusy(false);
    }
  };

  const loadCandidate = async (id = candidateId) => {
    if (!id) {
      setDetail(null);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const payload = await getStagingCandidate(id);
      setDetail(payload);
      setDeploymentStatus(payload.candidate.status);
    } catch (caught) {
      setError(caught.message || "Staging candidate could not be loaded.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (candidateId) loadCandidate(candidateId);
  }, [candidateId]);

  const perform = async (operation, success) => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      await operation();
      setMessage(success);
      await refresh();
      if (candidateId) await loadCandidate(candidateId);
    } catch (caught) {
      setError(caught.message || "Controlled-beta operation failed.");
    } finally {
      setBusy(false);
    }
  };

  const candidate = detail?.candidate;
  const blockers = detail?.acceptance_blockers;

  const checkCounts = useMemo(() => {
    const result = { passed: 0, pending: 0, failed: 0 };
    for (const check of candidate?.checks || []) {
      if (check.status === "passed" || check.status === "not_applicable") {
        result.passed += 1;
      } else if (check.status === "failed" || check.status === "blocked") {
        result.failed += 1;
      } else {
        result.pending += 1;
      }
    }
    return result;
  }, [candidate]);

  const createCandidate = async () => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const payload = await createStagingCandidate(candidateForm);
      setCandidateId(payload.candidate.candidate_id);
      setCandidateForm(EMPTY_CANDIDATE);
      setMessage(`${payload.candidate.candidate_id} created.`);
      await refresh();
      await loadCandidate(payload.candidate.candidate_id);
    } catch (caught) {
      setError(caught.message || "Staging candidate creation failed.");
    } finally {
      setBusy(false);
    }
  };

  const saveDeployment = () =>
    perform(
      () =>
        updateStagingDeployment(candidateId, {
          status: deploymentStatus,
          backend_url: candidate?.backend_url,
          frontend_url: candidate?.frontend_url,
          service_id: candidate?.service_id,
          notes: candidate?.notes,
        }),
      "Staging deployment metadata updated.",
    );

  const saveCheck = (check, status) =>
    perform(
      () =>
        recordStagingAcceptanceCheck(candidateId, {
          check_code: check.check_code,
          status,
          evidence_reference: check.evidence_reference,
          evidence_sha256: check.evidence_sha256,
          notes: check.notes,
        }),
      `${check.check_code} recorded as ${status}.`,
    );

  const saveEvidence = (item, status) =>
    perform(
      () =>
        updateControlledBetaEvidence(candidateId, {
          evidence_code: item.evidence_code,
          status,
          file_reference: item.file_reference,
          sha256: item.sha256,
          notes: item.notes,
        }),
      `${item.evidence_code} recorded as ${status}.`,
    );

  const syncContacts = () =>
    perform(
      () => syncControlledBetaContacts(),
      "Access requests and beta reservations synchronized.",
    );

  const submitInterview = () =>
    perform(
      () => createControlledBetaInterview(interviewForm),
      "User interview record created.",
    ).then(() => setInterviewForm(EMPTY_INTERVIEW));

  const submitPilot = () =>
    perform(
      () => createPilotDiscoveryRecord(pilotForm),
      "Pilot discovery worksheet created.",
    ).then(() => setPilotForm(EMPTY_PILOT));

  const submitClaim = () =>
    perform(
      () => createControlledBetaClaim(claimForm),
      "Claims-register entry created.",
    ).then(() => setClaimForm(EMPTY_CLAIM));

  const submitYcUpdate = () => {
    let metrics = {};
    try {
      metrics = ycForm.metrics.trim() ? JSON.parse(ycForm.metrics) : {};
    } catch {
      setError("YC metrics must be valid JSON.");
      return;
    }
    perform(
      () =>
        createControlledBetaYcUpdate(candidateId, {
          ...ycForm,
          metrics,
        }),
      "YC update snapshot created.",
    ).then(() => setYcForm(EMPTY_YC));
  };

  const exportEvidence = async () => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const payload = await downloadControlledBetaEvidence(candidateId);
      downloadBlob(payload.blob, payload.filename);
      setMessage(
        `${payload.exportId || "Evidence export"} generated with SHA-256 ${
          payload.sha256 || "recorded"
        }.`,
      );
      await loadCandidate(candidateId);
    } catch (caught) {
      setError(caught.message || "Controlled-beta evidence export failed.");
    } finally {
      setBusy(false);
    }
  };

  const decide = (decision) =>
    perform(
      () =>
        decideStagingCandidate(candidateId, {
          decision,
          reason: decisionReason,
        }),
      `Staging candidate ${decision}.`,
    );

  return (
    <div className="q17-stack">
      <section className="panel q17-hero">
        <Rocket size={34} />
        <div>
          <span className="eyebrow">Q17–Q19 · Controlled beta</span>
          <h2>Staging Acceptance and User Validation Center</h2>
          <p>
            Record staging deployment evidence, restart and redeployment
            persistence, access workflows, beta contacts, user interviews,
            pilot discovery, claims boundaries, demo evidence, and YC updates.
          </p>
        </div>
        <Badge tone={candidate?.status === "accepted" ? "green" : "amber"}>
          {candidate?.status || "No candidate"}
        </Badge>
      </section>

      <section className="q17-metrics">
        <article className="panel">
          <span>Checks passed</span>
          <strong>{checkCounts.passed}</strong>
        </article>
        <article className="panel">
          <span>Checks pending</span>
          <strong>{checkCounts.pending}</strong>
        </article>
        <article className="panel">
          <span>Checks failed</span>
          <strong>{checkCounts.failed}</strong>
        </article>
        <article className="panel">
          <span>Beta contacts</span>
          <strong>{summary?.contacts?.length ?? 0}</strong>
        </article>
      </section>

      <section className="panel q17-toolbar">
        <div>
          <ShieldCheck size={18} />
          <span>
            Controlled beta does not authorize production promotion, physical
            field integration, automatic equipment control, or advanced claims.
          </span>
        </div>
        <button
          className="button button-secondary"
          type="button"
          onClick={refresh}
          disabled={busy}
        >
          {busy ? (
            <LoaderCircle className="q17-spin" size={17} />
          ) : (
            <RefreshCw size={17} />
          )}
          Refresh
        </button>
      </section>

      {message && (
        <section className="panel q17-message q17-message-ok">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}
      {error && (
        <section className="panel q17-message q17-message-error">
          <XCircle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="q17-grid">
        <article className="panel q17-card">
          <h3>Create staging candidate</h3>
          {Object.entries(candidateForm).map(([key, value]) => (
            <label key={key}>
              {key.replaceAll("_", " ")}
              <input
                value={value}
                onChange={(event) =>
                  setCandidateForm((current) => ({
                    ...current,
                    [key]: event.target.value,
                  }))
                }
              />
            </label>
          ))}
          <button
            className="button button-primary"
            type="button"
            onClick={createCandidate}
            disabled={
              busy ||
              !candidateForm.commit_sha.trim() ||
              !candidateForm.release_tag.trim()
            }
          >
            Create candidate
          </button>
        </article>

        <article className="panel q17-card">
          <h3>Select candidate</h3>
          <select
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
          >
            <option value="">Choose candidate</option>
            {(summary?.candidates || []).map((item) => (
              <option key={item.candidate_id} value={item.candidate_id}>
                {item.status} · {item.release_tag}
              </option>
            ))}
          </select>
          {candidate && (
            <div className="q17-candidate-summary">
              <strong>{candidate.candidate_id}</strong>
              <span>{candidate.commit_sha}</span>
              <span>{candidate.release_tag}</span>
              <span>{candidate.service_id || "No service ID"}</span>
            </div>
          )}
          <label>
            Deployment status
            <select
              value={deploymentStatus}
              onChange={(event) => setDeploymentStatus(event.target.value)}
            >
              <option value="draft">draft</option>
              <option value="deployed">deployed</option>
              <option value="verifying">verifying</option>
            </select>
          </label>
          <button
            className="button button-secondary"
            type="button"
            onClick={saveDeployment}
            disabled={busy || !candidateId}
          >
            <Save size={17} />
            Save deployment metadata
          </button>
        </article>
      </section>

      {candidate && (
        <>
          <section className="panel q17-section">
            <div className="q17-section-heading">
              <ClipboardCheck size={23} />
              <div>
                <span className="eyebrow">Q17 staging acceptance</span>
                <h3>Required checks</h3>
              </div>
            </div>
            <div className="q17-check-list">
              {(candidate.checks || []).map((check) => (
                <article key={check.check_id}>
                  <div>
                    <strong>{check.check_code.replaceAll("_", " ")}</strong>
                    <p>{check.notes}</p>
                  </div>
                  <Badge tone={statusTone(check.status)}>
                    {check.status}
                  </Badge>
                  <select
                    value={check.status}
                    onChange={(event) => saveCheck(check, event.target.value)}
                    disabled={busy}
                  >
                    <option value="pending">pending</option>
                    <option value="passed">passed</option>
                    <option value="failed">failed</option>
                    <option value="blocked">blocked</option>
                    <option value="not_applicable">not applicable</option>
                  </select>
                </article>
              ))}
            </div>
          </section>

          <section className="panel q17-section">
            <div className="q17-section-heading">
              <FileArchive size={23} />
              <div>
                <span className="eyebrow">Gate 2 demo evidence</span>
                <h3>Evidence checklist</h3>
              </div>
            </div>
            <div className="q17-evidence-grid">
              {(candidate.demo_evidence || []).map((item) => (
                <article key={item.item_id}>
                  <strong>{item.title}</strong>
                  <input
                    placeholder="File or evidence reference"
                    defaultValue={item.file_reference || ""}
                    onBlur={(event) => {
                      item.file_reference = event.target.value;
                    }}
                  />
                  <input
                    placeholder="SHA-256"
                    defaultValue={item.sha256 || ""}
                    onBlur={(event) => {
                      item.sha256 = event.target.value;
                    }}
                  />
                  <select
                    value={item.status}
                    onChange={(event) => saveEvidence(item, event.target.value)}
                    disabled={busy}
                  >
                    <option value="missing">missing</option>
                    <option value="captured">captured</option>
                    <option value="verified">verified</option>
                    <option value="rejected">rejected</option>
                  </select>
                </article>
              ))}
            </div>
          </section>

          <section className="q17-grid">
            <article className="panel q17-card">
              <div className="q17-section-heading">
                <Users size={23} />
                <div>
                  <span className="eyebrow">Q18 contact ledger</span>
                  <h3>Beta contacts</h3>
                </div>
              </div>
              <button
                className="button button-primary"
                type="button"
                onClick={syncContacts}
                disabled={busy}
              >
                Sync access requests and reservations
              </button>
              <div className="q17-contact-list">
                {(summary?.contacts || []).slice(0, 20).map((contact) => (
                  <article key={contact.contact_id}>
                    <strong>{contact.full_name}</strong>
                    <span>{contact.email}</span>
                    <Badge tone={statusTone(contact.status)}>
                      {contact.status}
                    </Badge>
                  </article>
                ))}
              </div>
            </article>

            <article className="panel q17-card">
              <h3>User interview record</h3>
              <select
                value={interviewForm.contact_id}
                onChange={(event) =>
                  setInterviewForm((current) => ({
                    ...current,
                    contact_id: event.target.value,
                  }))
                }
              >
                <option value="">Choose contact</option>
                {(summary?.contacts || []).map((contact) => (
                  <option key={contact.contact_id} value={contact.contact_id}>
                    {contact.full_name} · {contact.email}
                  </option>
                ))}
              </select>
              {[
                "goals",
                "pains",
                "current_workflow",
                "success_criteria",
                "risk_notes",
              ].map((key) => (
                <label key={key}>
                  {key.replaceAll("_", " ")}
                  <textarea
                    value={interviewForm[key]}
                    onChange={(event) =>
                      setInterviewForm((current) => ({
                        ...current,
                        [key]: event.target.value,
                      }))
                    }
                  />
                </label>
              ))}
              <select
                value={interviewForm.decision}
                onChange={(event) =>
                  setInterviewForm((current) => ({
                    ...current,
                    decision: event.target.value,
                  }))
                }
              >
                <option value="pending">pending</option>
                <option value="continue">continue</option>
                <option value="pilot_candidate">pilot candidate</option>
                <option value="not_a_fit">not a fit</option>
                <option value="follow_up">follow up</option>
              </select>
              <button
                className="button button-secondary"
                type="button"
                onClick={submitInterview}
                disabled={busy || !interviewForm.contact_id}
              >
                Save interview
              </button>
            </article>
          </section>

          <section className="q17-grid">
            <article className="panel q17-card">
              <h3>Pilot discovery worksheet</h3>
              <select
                value={pilotForm.contact_id}
                onChange={(event) =>
                  setPilotForm((current) => ({
                    ...current,
                    contact_id: event.target.value,
                  }))
                }
              >
                <option value="">Choose contact</option>
                {(summary?.contacts || []).map((contact) => (
                  <option key={contact.contact_id} value={contact.contact_id}>
                    {contact.full_name}
                  </option>
                ))}
              </select>
              {Object.entries(pilotForm)
                .filter(([key]) => key !== "contact_id")
                .map(([key, value]) => (
                  <label key={key}>
                    {key.replaceAll("_", " ")}
                    <textarea
                      value={value}
                      onChange={(event) =>
                        setPilotForm((current) => ({
                          ...current,
                          [key]: event.target.value,
                        }))
                      }
                    />
                  </label>
                ))}
              <button
                className="button button-secondary"
                type="button"
                onClick={submitPilot}
                disabled={
                  busy ||
                  !pilotForm.contact_id ||
                  !pilotForm.manual_workflow.trim() ||
                  !pilotForm.proposed_scope.trim() ||
                  !pilotForm.exclusion_scope.trim()
                }
              >
                Save pilot worksheet
              </button>
            </article>

            <article className="panel q17-card">
              <h3>Claims register</h3>
              <label>
                Claim
                <textarea
                  value={claimForm.claim_text}
                  onChange={(event) =>
                    setClaimForm((current) => ({
                      ...current,
                      claim_text: event.target.value,
                    }))
                  }
                />
              </label>
              <select
                value={claimForm.claim_type}
                onChange={(event) =>
                  setClaimForm((current) => ({
                    ...current,
                    claim_type: event.target.value,
                  }))
                }
              >
                {[
                  "product",
                  "research",
                  "quantum",
                  "agricultural",
                  "security",
                  "operational",
                ].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              <select
                value={claimForm.evidence_level}
                onChange={(event) =>
                  setClaimForm((current) => ({
                    ...current,
                    evidence_level: event.target.value,
                  }))
                }
              >
                {[
                  "idea",
                  "prototype",
                  "simulation",
                  "controlled_beta",
                  "field_verified",
                  "publication",
                ].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              <label>
                Limitations
                <textarea
                  value={claimForm.limitations}
                  onChange={(event) =>
                    setClaimForm((current) => ({
                      ...current,
                      limitations: event.target.value,
                    }))
                  }
                />
              </label>
              <button
                className="button button-secondary"
                type="button"
                onClick={submitClaim}
                disabled={
                  busy ||
                  !claimForm.claim_text.trim() ||
                  !claimForm.limitations.trim()
                }
              >
                Add claim
              </button>
              <div className="q17-claim-list">
                {(summary?.claims || []).slice(0, 15).map((claim) => (
                  <article key={claim.claim_id}>
                    <strong>{claim.claim_text}</strong>
                    <span>
                      {claim.claim_type} · {claim.evidence_level}
                    </span>
                    <Badge tone={statusTone(claim.status)}>
                      {claim.status}
                    </Badge>
                  </article>
                ))}
              </div>
            </article>
          </section>

          <section className="q17-grid">
            <article className="panel q17-card">
              <h3>YC update snapshot</h3>
              {["headline", "summary", "metrics", "limitations"].map((key) => (
                <label key={key}>
                  {key}
                  <textarea
                    value={ycForm[key]}
                    placeholder={
                      key === "metrics" ? '{"tests_passed": 0}' : undefined
                    }
                    onChange={(event) =>
                      setYcForm((current) => ({
                        ...current,
                        [key]: event.target.value,
                      }))
                    }
                  />
                </label>
              ))}
              <button
                className="button button-secondary"
                type="button"
                onClick={submitYcUpdate}
                disabled={
                  busy ||
                  !ycForm.headline.trim() ||
                  !ycForm.summary.trim() ||
                  !ycForm.limitations.trim()
                }
              >
                Save YC update
              </button>
            </article>

            <article className="panel q17-card">
              <h3>Acceptance and export</h3>
              <div className="q17-blockers">
                <strong>
                  {blockers?.blocked ? "Acceptance blocked" : "Acceptance ready"}
                </strong>
                <span>
                  Checks: {blockers?.check_blockers?.length ?? 0} blockers
                </span>
                <span>
                  Evidence: {blockers?.evidence_blockers?.length ?? 0} blockers
                </span>
                <span>
                  Scientific gates:{" "}
                  {blockers?.failed_validations?.length ?? 0} failures
                </span>
                <span>
                  Backup: {blockers?.backup_blocker || "verified"}
                </span>
              </div>
              <label>
                Decision reason
                <textarea
                  value={decisionReason}
                  onChange={(event) => setDecisionReason(event.target.value)}
                />
              </label>
              <div className="q17-actions">
                <button
                  className="button button-primary"
                  type="button"
                  onClick={() => decide("accepted")}
                  disabled={busy || !decisionReason.trim() || blockers?.blocked}
                >
                  <CheckCircle2 size={17} />
                  Accept staging
                </button>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => decide("rejected")}
                  disabled={busy || !decisionReason.trim()}
                >
                  <AlertTriangle size={17} />
                  Reject staging
                </button>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={exportEvidence}
                  disabled={busy}
                >
                  <Download size={17} />
                  Export evidence ZIP
                </button>
              </div>
            </article>
          </section>
        </>
      )}
    </div>
  );
}
