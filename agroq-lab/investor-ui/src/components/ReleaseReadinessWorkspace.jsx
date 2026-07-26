import {
  AlertTriangle,
  CheckCircle2,
  DatabaseBackup,
  LoaderCircle,
  RefreshCw,
  Rocket,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  createReleaseReadinessBackup,
  getReleaseReadiness,
} from "../data/quantumApi";

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export default function ReleaseReadinessWorkspace() {
  const [readiness, setReadiness] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setBusy(true);
    setError("");
    try {
      const payload = await getReleaseReadiness();
      setReadiness(payload);
    } catch (caught) {
      setError(caught.message || "Q16 release readiness is unavailable.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const createBackup = async () => {
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const payload = await createReleaseReadinessBackup();
      setReadiness(payload.readiness);
      setMessage(
        `${payload.backup.filename} verified and recovery-tested successfully.`,
      );
    } catch (caught) {
      setError(caught.message || "Release backup verification failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="q16-stack">
      <section className="panel q16-hero">
        <Rocket size={34} />
        <div>
          <span className="eyebrow">Q16 · Release readiness</span>
          <h2>Deployment and Release Control Center</h2>
          <p>
            Validate database integrity, worker safety, deployment settings,
            verified backups, scientific gates, and research-release state
            before an operator explicitly starts staging deployment.
          </p>
        </div>
        <Badge tone={readiness?.ready ? "green" : "amber"}>
          {readiness?.ready ? "Release ready" : "Release blocked"}
        </Badge>
      </section>

      <section className="panel q16-toolbar">
        <div>
          <ShieldCheck size={18} />
          <span>
            This screen reports readiness only. It does not deploy, promote, or
            modify a remote service.
          </span>
        </div>
        <div>
          <button
            className="button button-secondary"
            type="button"
            onClick={refresh}
            disabled={busy}
          >
            {busy ? (
              <LoaderCircle className="q16-spin" size={17} />
            ) : (
              <RefreshCw size={17} />
            )}
            Refresh
          </button>
          <button
            className="button button-primary"
            type="button"
            onClick={createBackup}
            disabled={busy}
          >
            <DatabaseBackup size={17} />
            Verify release backup
          </button>
        </div>
      </section>

      {message && (
        <section className="panel q16-message q16-message-ok">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}
      {error && (
        <section className="panel q16-message q16-message-error">
          <XCircle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="q16-check-grid">
        {(readiness?.checks || []).map((check) => (
          <article className="panel" key={check.code}>
            {check.passed ? (
              <CheckCircle2 size={21} />
            ) : (
              <AlertTriangle size={21} />
            )}
            <div>
              <strong>{check.code.replaceAll("_", " ")}</strong>
              <p>{check.message}</p>
            </div>
            <Badge tone={check.passed ? "green" : "red"}>
              {check.passed ? "PASS" : "BLOCKED"}
            </Badge>
          </article>
        ))}
      </section>

      <section className="q16-grid">
        <article className="panel q16-card">
          <h3>Runtime</h3>
          <dl>
            <div>
              <dt>Mode</dt>
              <dd>{readiness?.runtime?.deployment_mode || "Unknown"}</dd>
            </div>
            <div>
              <dt>Workers</dt>
              <dd>{readiness?.runtime?.workers ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>Database</dt>
              <dd>{readiness?.database?.engine || "Unknown"}</dd>
            </div>
            <div>
              <dt>Integrity</dt>
              <dd>{readiness?.database?.integrity || "Unknown"}</dd>
            </div>
          </dl>
        </article>

        <article className="panel q16-card">
          <h3>Latest verified backup</h3>
          {readiness?.latest_backup ? (
            <dl>
              <div>
                <dt>File</dt>
                <dd>{readiness.latest_backup.filename}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{readiness.latest_backup.status}</dd>
              </div>
              <div>
                <dt>Size</dt>
                <dd>{readiness.latest_backup.size_bytes} bytes</dd>
              </div>
              <div>
                <dt>Verified</dt>
                <dd>{readiness.latest_backup.verified_at || "Not verified"}</dd>
              </div>
            </dl>
          ) : (
            <p>No backup has been recorded for this environment.</p>
          )}
        </article>
      </section>

      <section className="panel q16-boundary">
        <ShieldCheck size={22} />
        <div>
          <h3>Release boundary</h3>
          <p>
            A clean local preflight and successful CI establish release
            candidacy. Remote staging still requires an explicit deployment,
            service restart verification, HTTP smoke test, authenticated
            workflow review, and documented rollback checkpoint.
          </p>
        </div>
      </section>
    </div>
  );
}
