import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Database,
  Dna,
  Download,
  ExternalLink,
  FlaskConical,
  LockKeyhole,
  Search,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";

const API_BASE = (import.meta.env.VITE_AGROQ_API_BASE || "").replace(/\/$/, "");

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed with HTTP ${response.status}`);
  }
  return data;
}

function ExperimentCard({ experiment, csrfToken, isAdmin, reload }) {
  const [rationale, setRationale] = useState("");
  const [working, setWorking] = useState(false);

  const decide = async (decision) => {
    setWorking(true);
    try {
      await api(`/api/bio/experiments/${experiment.experiment_id}/approval`, {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken },
        body: JSON.stringify({
          decision,
          rationale: rationale || `${decision} through the administrator demonstration gate.`,
        }),
      });
      setRationale("");
      await reload();
    } finally {
      setWorking(false);
    }
  };

  return (
    <article className="experiment-record">
      <div className="experiment-record__top">
        <div>
          <span className="data-badge">{experiment.evidence_mode}</span>
          <span className="data-badge">{experiment.approval_state}</span>
        </div>
        <span>{experiment.experiment_id}</span>
      </div>
      <h3>{experiment.title}</h3>
      <p>{experiment.objective}</p>
      <dl className="experiment-metrics">
        <div><dt>Organism</dt><dd>{experiment.organism}</dd></div>
        <div><dt>Primary outcome</dt><dd>{experiment.primary_outcome}</dd></div>
        <div><dt>Sequence records</dt><dd>{experiment.sequence_count}</dd></div>
        <div><dt>Status</dt><dd>{experiment.status}</dd></div>
      </dl>
      <details>
        <summary>Protocol and limitations</summary>
        <p><strong>Hypothesis:</strong> {experiment.hypothesis}</p>
        <p><strong>Outcomes:</strong> {experiment.secondary_outcomes.join(", ")}</p>
        <p><strong>Limitations:</strong> {experiment.limitations}</p>
      </details>
      {isAdmin && (
        <div className="approval-controls">
          <input
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            placeholder="Administrator rationale"
          />
          <button disabled={working} onClick={() => decide("approved")}>Approve demo</button>
          <button className="secondary" disabled={working} onClick={() => decide("rejected")}>Reject</button>
        </div>
      )}
    </article>
  );
}

export default function AdminLabPage() {
  const [sessionData, setSessionData] = useState(null);
  const [overview, setOverview] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [sequences, setSequences] = useState([]);
  const [database, setDatabase] = useState("nuccore");
  const [query, setQuery] = useState("Lactuca sativa pigmentation");
  const [selectedExperiment, setSelectedExperiment] = useState("AGQ-GENO-003");
  const [results, setResults] = useState([]);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const currentSession = await api("/api/bio/session");
      setSessionData(currentSession);
      const [experimentData, sequenceData] = await Promise.all([
        api("/api/bio/experiments"),
        api("/api/bio/sequences"),
      ]);
      setExperiments(experimentData.experiments || []);
      setSequences(sequenceData.sequences || []);
      if (currentSession.role === "administrator") {
        setOverview(await api("/api/admin/overview"));
      }
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const searchSequences = async () => {
    setWorking(true);
    setError("");
    setMessage("");
    try {
      const data = await api(
        `/api/bio/search?database=${encodeURIComponent(database)}&q=${encodeURIComponent(query)}`,
      );
      setResults(data.results || []);
      setMessage(`${data.results?.length || 0} public record(s) found.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setWorking(false);
    }
  };

  const insertSequence = async (record) => {
    setWorking(true);
    setError("");
    setMessage("");
    try {
      const data = await api("/api/bio/insert", {
        method: "POST",
        headers: { "X-CSRF-Token": sessionData.csrf_token },
        body: JSON.stringify({
          database_name: record.database_name,
          accession: record.accession,
          experiment_id: selectedExperiment,
          evidence_class: "candidate",
          relationship_label: "candidate public sequence evidence",
          interpretation: "Imported for administrator review. Association does not establish phenotype causality.",
        }),
      });
      setMessage(`${data.accession} inserted and linked to ${data.experiment_id}.`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setWorking(false);
    }
  };

  if (error && !sessionData) {
    return (
      <section className="admin-lab admin-locked">
        <LockKeyhole size={34} />
        <h2>Administrator or researcher sign-in required</h2>
        <p>{error}</p>
        <a href={`${API_BASE}/login`} target="_blank" rel="noreferrer">
          Open AgroQ sign in <ExternalLink size={16} />
        </a>
      </section>
    );
  }

  const isAdmin = sessionData?.role === "administrator";

  return (
    <section className="admin-lab">
      <header className="admin-lab__header">
        <div>
          <p className="eyebrow">Founder administration and evidence workspace</p>
          <h1>Admin & Sequence Lab</h1>
          <p>
            Manage AgroQ, search public DNA or protein records, insert and link them
            without copy-paste, review experiment gates, and export evidence.
          </p>
        </div>
        <div className="admin-identity">
          <ShieldCheck size={22} />
          <div>
            <strong>{sessionData?.display_name || "Loading..."}</strong>
            <span>{sessionData?.role || "checking access"}</span>
          </div>
        </div>
      </header>

      <div className="truth-banner">
        <span>Synthetic experiment demonstrations</span>
        <span>Public sequence references</span>
        <span>Field mode locked</span>
        <span>No gene editing</span>
      </div>

      {isAdmin && overview && (
        <div className="admin-stats">
          {Object.entries(overview.counts || {}).map(([label, value]) => (
            <article className="admin-stat-card" key={label}>
              {label.includes("sequence") ? <Dna size={19} /> : <Database size={19} />}
              <span>{label.replaceAll("_", " ")}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </div>
      )}

      <div className="admin-diagram-grid">
        <article>
          <h2>Founder control architecture</h2>
          <img src="/diagrams/admin-control-center.svg" alt="AgroQ founder control architecture" />
        </article>
        <article>
          <h2>Sequence evidence pipeline</h2>
          <img src="/diagrams/sequence-lookup-flow.svg" alt="AgroQ sequence lookup workflow" />
        </article>
      </div>

      <section className="sequence-console">
        <div className="section-heading">
          <div><p className="eyebrow">NCBI public sequence lookup</p><h2>Search, insert, link, and export</h2></div>
          <Activity size={22} />
        </div>
        <div className="sequence-search-row">
          <select value={database} onChange={(event) => setDatabase(event.target.value)}>
            <option value="nuccore">DNA / RNA — NCBI Nuccore</option>
            <option value="protein">Protein — NCBI Protein</option>
          </select>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Gene, protein, organism, or accession" />
          <select value={selectedExperiment} onChange={(event) => setSelectedExperiment(event.target.value)}>
            {experiments.map((experiment) => (
              <option key={experiment.experiment_id} value={experiment.experiment_id}>
                {experiment.experiment_id} — {experiment.title}
              </option>
            ))}
          </select>
          <button disabled={working} onClick={searchSequences}><Search size={17} /> Search</button>
        </div>
        {message && <p className="success-message"><CheckCircle2 size={16} /> {message}</p>}
        {error && <p className="error-message">{error}</p>}
        <div className="search-results">
          {results.map((record) => (
            <article key={`${record.database_name}-${record.accession}`}>
              <div><span className="data-badge">{record.database_name}</span> <strong>{record.accession}</strong></div>
              <h3>{record.title}</h3>
              <p>{record.organism || "Organism available after sequence fetch"}</p>
              <button disabled={working} onClick={() => insertSequence(record)}><UploadCloud size={16} /> Insert & link</button>
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="section-heading">
          <div><p className="eyebrow">Demonstration portfolio</p><h2>Three auditable experiments</h2></div>
          <FlaskConical size={22} />
        </div>
        <div className="experiment-grid">
          {experiments.map((experiment) => (
            <ExperimentCard
              key={experiment.experiment_id}
              experiment={experiment}
              csrfToken={sessionData?.csrf_token}
              isAdmin={isAdmin}
              reload={load}
            />
          ))}
        </div>
      </section>

      <section>
        <div className="section-heading"><div><p className="eyebrow">Saved library</p><h2>Provenance-preserving exports</h2></div><Dna size={22} /></div>
        <div className="sequence-library">
          {sequences.length === 0 && <p>No sequence records have been inserted yet.</p>}
          {sequences.map((sequence) => (
            <article key={sequence.sequence_id}>
              <strong>{sequence.accession}</strong>
              <span>{sequence.sequence_type} · {sequence.sequence_length.toLocaleString()}</span>
              <p>{sequence.title}</p>
              <small>Linked: {sequence.experiment_ids.join(", ") || "not linked"}</small>
              <div className="export-actions">
                {["fasta", "json", "csv"].map((format) => (
                  <a key={format} href={`${API_BASE}/api/bio/sequences/${sequence.sequence_id}/export?format=${format}`} target="_blank" rel="noreferrer">
                    <Download size={14} /> {format.toUpperCase()}
                  </a>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
