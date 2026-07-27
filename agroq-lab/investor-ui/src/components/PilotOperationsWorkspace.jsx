import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Download,
  LoaderCircle,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  activatePilotEnrollment,
  createPilotEnrollment,
  decidePilotExit,
  downloadPilotEvidence,
  getPilotEnrollment,
  pilotOperationsSummary,
  recordPilotAcknowledgment,
  recordPilotMetric,
  submitPilotFeedback,
  submitPilotIncident,
  updatePilotOnboarding,
} from "../data/quantumApi";

const EMPTY_ENROLLMENT = {
  pilot_id: "",
  candidate_id: "",
  participant_user_id: "",
  support_owner_id: "",
  cohort_name: "",
  scope: "",
  exclusion_scope: "",
};

const EMPTY_FEEDBACK = {
  category: "workflow",
  rating: "4",
  description: "",
  context: "",
  evidence_reference: "",
};

const EMPTY_INCIDENT = {
  severity: "low",
  category: "workflow",
  title: "",
  description: "",
  impact: "",
  immediate_manual_action: "",
  evidence_reference: "",
};

const EMPTY_METRIC = {
  metric_code: "",
  metric_name: "",
  baseline_value: "",
  target_value: "",
  observed_value: "",
  unit: "",
  direction: "informational",
  evidence_reference: "",
  evidence_sha256: "",
  limitations: "",
};

const ACKNOWLEDGMENTS = [
  "data_handling",
  "human_control",
  "research_limitations",
];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function tone(status) {
  if (["active", "completed", "resolved", "closed"].includes(status)) return "green";
  if (["paused", "blocked", "high", "critical", "withdrawn"].includes(status)) {
    return "red";
  }
  if (["onboarding", "open", "triaged", "contained"].includes(status)) {
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

function FormFields({ value, setValue, fields }) {
  return fields.map((field) => (
    <label key={field.name}>
      {field.label || field.name.replaceAll("_", " ")}
      {field.options ? (
        <select
          value={value[field.name]}
          onChange={(event) =>
            setValue((current) => ({
              ...current,
              [field.name]: event.target.value,
            }))
          }
        >
          {field.options.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      ) : field.multiline ? (
        <textarea
          value={value[field.name]}
          onChange={(event) =>
            setValue((current) => ({
              ...current,
              [field.name]: event.target.value,
            }))
          }
        />
      ) : (
        <input
          value={value[field.name]}
          onChange={(event) =>
            setValue((current) => ({
              ...current,
              [field.name]: event.target.value,
            }))
          }
        />
      )}
    </label>
  ));
}

export default function PilotOperationsWorkspace() {
  const [summary, setSummary] = useState(null);
  const [enrollmentId, setEnrollmentId] = useState("");
  const [detail, setDetail] = useState(null);
  const [enrollmentForm, setEnrollmentForm] = useState(EMPTY_ENROLLMENT);
  const [feedbackForm, setFeedbackForm] = useState(EMPTY_FEEDBACK);
  const [incidentForm, setIncidentForm] = useState(EMPTY_INCIDENT);
  const [metricForm, setMetricForm] = useState(EMPTY_METRIC);
  const [evidenceRefs, setEvidenceRefs] = useState({});
  const [activationReason, setActivationReason] = useState("");
  const [decision, setDecision] = useState("continue");
  const [decisionReason, setDecisionReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = await pilotOperationsSummary();
      setSummary(payload);
      if (!enrollmentId && payload.enrollments?.length) {
        setEnrollmentId(payload.enrollments[0].enrollment_id);
      }
    } catch (caught) {
      setError(caught.message || "Pilot operations are unavailable.");
    } finally {
      setBusy(false);
    }
  };

  const loadDetail = async (id = enrollmentId) => {
    if (!id) {
      setDetail(null);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const payload = await getPilotEnrollment(id);
      setDetail(payload.enrollment);
    } catch (caught) {
      setError(caught.message || "Pilot enrollment could not be loaded.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (enrollmentId) loadDetail(enrollmentId);
  }, [enrollmentId]);

  const perform = async (operation, success, after) => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const result = await operation();
      setMessage(success);
      if (after) after(result);
      await refresh();
      const target = result?.enrollment?.enrollment_id || enrollmentId;
      if (target) {
        setEnrollmentId(target);
        await loadDetail(target);
      }
    } catch (caught) {
      setError(caught.message || "Pilot operation failed.");
    } finally {
      setBusy(false);
    }
  };

  const exportEvidence = async () => {
    if (!enrollmentId) return;
    await perform(async () => {
      const result = await downloadPilotEvidence(enrollmentId);
      downloadBlob(result.blob, result.filename);
      return result;
    }, "Pilot evidence bundle downloaded.");
  };

  const metrics = summary?.enrollment_counts || {};
  const severeIncidents =
    (summary?.incident_counts?.high || 0) +
    (summary?.incident_counts?.critical || 0);

  return (
    <div className="q20-stack">
      <section className="panel q20-hero">
        <ShieldCheck size={34} />
        <div>
          <span className="eyebrow">Q20–Q22 · Controlled pilot operations</span>
          <h2>Activate carefully, learn immutably, decide with evidence</h2>
          <p>
            Human-gated onboarding, participant feedback, incident stops,
            evidence-backed metrics, and a separate release-review recommendation.
          </p>
        </div>
        <Badge tone="amber">No automatic promotion</Badge>
      </section>

      <section className="q20-metrics">
        <article className="panel"><Users size={19} /><span>Enrollments</span><strong>{summary?.enrollments?.length || 0}</strong></article>
        <article className="panel"><PlayCircle size={19} /><span>Active</span><strong>{metrics.active || 0}</strong></article>
        <article className="panel"><PauseCircle size={19} /><span>Paused</span><strong>{metrics.paused || 0}</strong></article>
        <article className="panel"><AlertTriangle size={19} /><span>Severe incidents</span><strong>{severeIncidents}</strong></article>
      </section>

      <section className="panel q20-toolbar">
        <div>
          <strong>Enrollment workspace</strong>
          <span>{summary?.schema_version || "Checking backend…"}</span>
        </div>
        <select
          value={enrollmentId}
          onChange={(event) => setEnrollmentId(event.target.value)}
        >
          <option value="">Select enrollment</option>
          {(summary?.enrollments || []).map((item) => (
            <option key={item.enrollment_id} value={item.enrollment_id}>
              {item.cohort_name} · {item.status}
            </option>
          ))}
        </select>
        <button className="button button-secondary" onClick={refresh} disabled={busy}>
          <RefreshCw className={busy ? "q20-spin" : ""} size={17} /> Refresh
        </button>
      </section>

      {message && <div className="panel q20-message q20-ok"><CheckCircle2 size={18} />{message}</div>}
      {error && <div className="panel q20-message q20-error"><AlertTriangle size={18} />{error}</div>}

      <section className="q20-grid">
        <article className="panel q20-card">
          <span className="eyebrow">Q20 enrollment</span>
          <h3>Create controlled enrollment</h3>
          <FormFields
            value={enrollmentForm}
            setValue={setEnrollmentForm}
            fields={[
              { name: "pilot_id" },
              { name: "candidate_id" },
              { name: "participant_user_id" },
              { name: "support_owner_id" },
              { name: "cohort_name" },
              { name: "scope", multiline: true },
              { name: "exclusion_scope", multiline: true },
            ]}
          />
          <button
            className="button button-primary"
            disabled={busy}
            onClick={() =>
              perform(
                () => createPilotEnrollment(enrollmentForm),
                "Controlled-pilot enrollment created.",
                (payload) => {
                  setEnrollmentForm(EMPTY_ENROLLMENT);
                  setEnrollmentId(payload.enrollment.enrollment_id);
                },
              )
            }
          >
            <Users size={17} /> Create enrollment
          </button>
        </article>

        <article className="panel q20-card">
          <span className="eyebrow">Q20 human activation</span>
          <h3>{detail?.cohort_name || "Select an enrollment"}</h3>
          {detail && (
            <>
              <div className="q20-status-line">
                <Badge tone={tone(detail.status)}>{detail.status}</Badge>
                <span>{detail.enrollment_id}</span>
              </div>
              <textarea
                value={activationReason}
                onChange={(event) => setActivationReason(event.target.value)}
                placeholder="Administrator activation or reactivation reason"
              />
              <button
                className="button button-primary"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => activatePilotEnrollment(enrollmentId, activationReason),
                    "Pilot activation decision recorded.",
                    () => setActivationReason(""),
                  )
                }
              >
                <PlayCircle size={17} /> Activate with human approval
              </button>
              <div className="q20-blockers">
                <strong>Activation blockers</strong>
                {(detail.activation_blockers || []).length ? (
                  detail.activation_blockers.map((item) => <span key={item}>{item}</span>)
                ) : (
                  <span>No activation blockers recorded.</span>
                )}
              </div>
            </>
          )}
        </article>
      </section>

      {detail && (
        <>
          <section className="panel q20-section">
            <div className="q20-section-heading">
              <ClipboardCheck size={21} />
              <div><span className="eyebrow">Q20 onboarding</span><h3>Evidence and acknowledgments</h3></div>
            </div>
            <div className="q20-checks">
              {detail.onboarding_checks.map((check) => (
                <article key={check.check_id}>
                  <div>
                    <strong>{check.title}</strong>
                    <Badge tone={tone(check.status)}>{check.status}</Badge>
                  </div>
                  <input
                    value={evidenceRefs[check.check_code] || ""}
                    onChange={(event) =>
                      setEvidenceRefs((current) => ({
                        ...current,
                        [check.check_code]: event.target.value,
                      }))
                    }
                    placeholder="Evidence reference"
                  />
                  <button
                    className="button button-secondary"
                    disabled={busy}
                    onClick={() =>
                      perform(
                        () =>
                          updatePilotOnboarding(enrollmentId, {
                            check_code: check.check_code,
                            status: "completed",
                            evidence_reference: evidenceRefs[check.check_code] || "",
                            notes: "Human-verified onboarding evidence.",
                          }),
                        `${check.check_code} recorded.`,
                      )
                    }
                  >
                    Complete
                  </button>
                </article>
              ))}
            </div>
            <div className="q20-ack-grid">
              {ACKNOWLEDGMENTS.map((acknowledgmentType) => {
                const existing = detail.acknowledgments.some(
                  (item) => item.acknowledgment_type === acknowledgmentType,
                );
                return (
                  <article key={acknowledgmentType}>
                    <strong>{acknowledgmentType.replaceAll("_", " ")}</strong>
                    <Badge tone={existing ? "green" : "amber"}>
                      {existing ? "recorded" : "required"}
                    </Badge>
                    <input
                      value={evidenceRefs[`ack-${acknowledgmentType}`] || ""}
                      onChange={(event) =>
                        setEvidenceRefs((current) => ({
                          ...current,
                          [`ack-${acknowledgmentType}`]: event.target.value,
                        }))
                      }
                      placeholder="Acknowledgment evidence"
                    />
                    <button
                      className="button button-secondary"
                      disabled={busy || existing}
                      onClick={() =>
                        perform(
                          () =>
                            recordPilotAcknowledgment(enrollmentId, {
                              acknowledgment_type: acknowledgmentType,
                              version: "pilot-v1",
                              accepted: true,
                              evidence_reference:
                                evidenceRefs[`ack-${acknowledgmentType}`] || "",
                            }),
                          `${acknowledgmentType} acknowledgment preserved.`,
                        )
                      }
                    >
                      Record acknowledgment
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="q20-grid">
            <article className="panel q20-card">
              <span className="eyebrow">Q21 participant learning</span>
              <h3>Submit immutable feedback</h3>
              <FormFields
                value={feedbackForm}
                setValue={setFeedbackForm}
                fields={[
                  { name: "category", options: ["usability", "workflow", "data_quality", "research", "support", "other"] },
                  { name: "rating" },
                  { name: "description", multiline: true },
                  { name: "context", multiline: true },
                  { name: "evidence_reference" },
                ]}
              />
              <button
                className="button button-primary"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => submitPilotFeedback(enrollmentId, feedbackForm),
                    "Immutable feedback submitted.",
                    () => setFeedbackForm(EMPTY_FEEDBACK),
                  )
                }
              >
                Save feedback
              </button>
            </article>

            <article className="panel q20-card q20-incident-card">
              <span className="eyebrow">Q21 safety stop</span>
              <h3>Report incident</h3>
              <FormFields
                value={incidentForm}
                setValue={setIncidentForm}
                fields={[
                  { name: "severity", options: ["low", "medium", "high", "critical"] },
                  { name: "category", options: ["access", "privacy", "data_integrity", "availability", "workflow", "field_safety", "other"] },
                  { name: "title" },
                  { name: "description", multiline: true },
                  { name: "impact", multiline: true },
                  { name: "immediate_manual_action", multiline: true },
                  { name: "evidence_reference" },
                ]}
              />
              <button
                className="button button-secondary"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => submitPilotIncident(enrollmentId, incidentForm),
                    "Incident preserved; serious incidents pause the pilot.",
                    () => setIncidentForm(EMPTY_INCIDENT),
                  )
                }
              >
                <AlertTriangle size={17} /> Preserve incident
              </button>
            </article>
          </section>

          <section className="q20-grid">
            <article className="panel q20-card">
              <span className="eyebrow">Q22 evidence metric</span>
              <h3>Record immutable observation</h3>
              <FormFields
                value={metricForm}
                setValue={setMetricForm}
                fields={[
                  { name: "metric_code" },
                  { name: "metric_name" },
                  { name: "baseline_value" },
                  { name: "target_value" },
                  { name: "observed_value" },
                  { name: "unit" },
                  { name: "direction", options: ["higher", "lower", "range", "informational"] },
                  { name: "evidence_reference" },
                  { name: "evidence_sha256" },
                  { name: "limitations", multiline: true },
                ]}
              />
              <button
                className="button button-primary"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => recordPilotMetric(enrollmentId, metricForm),
                    "Evidence-backed metric recorded.",
                    () => setMetricForm(EMPTY_METRIC),
                  )
                }
              >
                Save metric
              </button>
            </article>

            <article className="panel q20-card">
              <span className="eyebrow">Q22 human exit gate</span>
              <h3>Record pilot decision</h3>
              <select value={decision} onChange={(event) => setDecision(event.target.value)}>
                {["continue", "extend", "pause", "complete", "stop", "recommend_release_review"].map((item) => (
                  <option key={item}>{item}</option>
                ))}
              </select>
              <textarea
                value={decisionReason}
                onChange={(event) => setDecisionReason(event.target.value)}
                placeholder="Human decision reason"
              />
              <button
                className="button button-primary"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => decidePilotExit(enrollmentId, { decision, reason: decisionReason }),
                    "Pilot decision preserved. Production was not promoted.",
                    () => setDecisionReason(""),
                  )
                }
              >
                <ShieldCheck size={17} /> Record decision
              </button>
              <div className="q20-blockers">
                <strong>Release-review blockers</strong>
                {(detail.release_review_blockers || []).length ? (
                  detail.release_review_blockers.map((item) => <span key={item}>{item}</span>)
                ) : (
                  <span>No release-review blockers recorded.</span>
                )}
              </div>
              <button className="button button-secondary" onClick={exportEvidence} disabled={busy}>
                <Download size={17} /> Download evidence ZIP
              </button>
            </article>
          </section>

          <section className="panel q20-section">
            <div className="q20-section-heading">
              {busy ? <LoaderCircle className="q20-spin" size={21} /> : <AlertTriangle size={21} />}
              <div><span className="eyebrow">Q21 live register</span><h3>Feedback and incident state</h3></div>
            </div>
            <div className="q20-record-grid">
              {(detail.feedback || []).map((item) => (
                <article key={item.feedback_id}>
                  <Badge tone={tone(item.status)}>{item.status}</Badge>
                  <strong>{item.category}</strong>
                  <p>{item.description}</p>
                </article>
              ))}
              {(detail.incidents || []).map((item) => (
                <article key={item.incident_id}>
                  <Badge tone={tone(item.severity)}>{item.severity}</Badge>
                  <strong>{item.title}</strong>
                  <p>{item.status} · {item.immediate_manual_action}</p>
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
