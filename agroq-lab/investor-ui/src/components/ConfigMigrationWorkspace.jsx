import {
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  FileCode2,
  FolderCog,
  LoaderCircle,
  MessageSquareText,
  PackageCheck,
  Plug,
  RotateCcw,
  ScanSearch,
  Settings2,
  Sparkles,
} from "lucide-react";
import { useMemo, useState } from "react";

const detectedItems = [
  {
    id: "global-rules",
    scope: "Global",
    type: "Configuration",
    title: "Agent instructions",
    detail: "Personal preferences and shared operating rules",
    source: "Cursor",
    icon: Settings2,
  },
  {
    id: "project-rules",
    scope: "Project",
    type: "Configuration",
    title: "Project rules",
    detail: "Repository-specific instructions and conventions",
    source: ".cursor",
    icon: FolderCog,
  },
  {
    id: "project-skills",
    scope: "Project",
    type: "Skills",
    title: "Reusable workflows",
    detail: "Two project workflows ready to copy",
    source: ".agents/skills",
    icon: Sparkles,
  },
  {
    id: "global-plugins",
    scope: "Global",
    type: "Plugins",
    title: "Connected tools",
    detail: "Plugin references; connections require confirmation",
    source: "Agent settings",
    icon: Plug,
  },
  {
    id: "project-commands",
    scope: "Project",
    type: "Other",
    title: "Commands and hooks",
    detail: "Project commands, environment hints, and hooks",
    source: ".cursor",
    icon: FileCode2,
  },
];

const steps = [
  {
    icon: ScanSearch,
    title: "Find your existing setup",
    copy: "Codex scans supported coding agents for reusable settings.",
  },
  {
    icon: PackageCheck,
    title: "Review what to import",
    copy: "Choose global or project configuration, skills, plugins, and more.",
  },
  {
    icon: MessageSquareText,
    title: "Finish in a guided chat",
    copy: "Codex starts a new chat to walk you through the import.",
  },
];

function ProgressSteps({ stage }) {
  return (
    <ol className="migration-progress" aria-label="Migration progress">
      {steps.map(({ icon: Icon, title, copy }, index) => {
        const step = index + 1;
        const complete = step < stage;
        const active = step === stage;
        return (
          <li
            className={active ? "is-active" : complete ? "is-complete" : ""}
            key={title}
          >
            <span className="migration-step-icon">
              {complete ? <Check size={18} /> : <Icon size={19} />}
            </span>
            <div>
              <strong>{title}</strong>
              <p>{copy}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export default function ConfigMigrationWorkspace() {
  const [stage, setStage] = useState(1);
  const [scanning, setScanning] = useState(false);
  const [selected, setSelected] = useState(
    () => new Set(detectedItems.map((item) => item.id)),
  );
  const [imported, setImported] = useState(false);

  const selectedItems = useMemo(
    () => detectedItems.filter((item) => selected.has(item.id)),
    [selected],
  );

  const runScan = () => {
    setScanning(true);
    window.setTimeout(() => {
      setScanning(false);
      setStage(2);
    }, 700);
  };

  const toggleItem = (id) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const reset = () => {
    setStage(1);
    setImported(false);
    setSelected(new Set(detectedItems.map((item) => item.id)));
  };

  return (
    <section className="config-migration panel">
      <div className="migration-header">
        <div>
          <span className="eyebrow">Codex setup</span>
          <h2>Bring your existing setup to Codex</h2>
          <p>
            Find reusable agent settings, choose what to copy, and finish the
            migration with guided help.
          </p>
        </div>
        {stage > 1 && (
          <button className="text-button migration-reset" onClick={reset} type="button">
            <RotateCcw size={15} />
            Start over
          </button>
        )}
      </div>

      <ProgressSteps stage={stage} />

      {stage === 1 && (
        <div className="migration-stage migration-scan">
          <div className="migration-illustration" aria-hidden="true">
            <ScanSearch size={42} />
            <span><Settings2 size={20} /></span>
            <span><FileCode2 size={20} /></span>
            <span><Sparkles size={20} /></span>
          </div>
          <h3>Ready to scan</h3>
          <p>
            This checks known configuration locations. Nothing is copied or
            changed until you review the checklist.
          </p>
          <button
            className="button button-primary"
            disabled={scanning}
            onClick={runScan}
            type="button"
          >
            {scanning ? (
              <>
                <LoaderCircle className="migration-spinner" size={18} />
                Scanning…
              </>
            ) : (
              <>
                Scan for existing setup
                <ChevronRight size={18} />
              </>
            )}
          </button>
        </div>
      )}

      {stage === 2 && (
        <div className="migration-stage">
          <div className="migration-stage-heading">
            <div>
              <span className="migration-result-mark"><CheckCircle2 size={19} /></span>
              <div>
                <h3>5 items found</h3>
                <p>Review the checklist before opening the migration chat.</p>
              </div>
            </div>
            <button
              className="text-button"
              onClick={() =>
                setSelected(
                  selected.size === detectedItems.length
                    ? new Set()
                    : new Set(detectedItems.map((item) => item.id)),
                )
              }
              type="button"
            >
              {selected.size === detectedItems.length ? "Clear all" : "Select all"}
            </button>
          </div>

          <div className="migration-checklist">
            {detectedItems.map((item) => {
              const Icon = item.icon;
              const checked = selected.has(item.id);
              return (
                <button
                  aria-pressed={checked}
                  className={`migration-check-row ${checked ? "is-selected" : ""}`}
                  key={item.id}
                  onClick={() => toggleItem(item.id)}
                  type="button"
                >
                  <span className="migration-checkbox">
                    {checked ? <Check size={15} /> : <Circle size={14} />}
                  </span>
                  <span className="migration-item-icon"><Icon size={18} /></span>
                  <span className="migration-item-copy">
                    <span>
                      <strong>{item.title}</strong>
                      <small>{item.scope}</small>
                    </span>
                    <p>{item.detail}</p>
                  </span>
                  <span className="migration-source">
                    <small>{item.type}</small>
                    <strong>{item.source}</strong>
                  </span>
                </button>
              );
            })}
          </div>

          <div className="migration-actions">
            <p>{selected.size} of {detectedItems.length} items selected</p>
            <button
              className="button button-primary"
              disabled={!selected.size}
              onClick={() => setStage(3)}
              type="button"
            >
              Open migration chat
              <MessageSquareText size={18} />
            </button>
          </div>
        </div>
      )}

      {stage === 3 && (
        <div className="migration-stage migration-chat">
          <div className="migration-chat-bar">
            <span><Bot size={20} /></span>
            <div>
              <strong>Configuration migration</strong>
              <small>New guided chat · {selectedItems.length} items selected</small>
            </div>
          </div>

          <div className="migration-messages" aria-live="polite">
            <div className="migration-message">
              <span><Bot size={17} /></span>
              <div>
                <p>
                  I found {selectedItems.length} items you’d like to bring into
                  Codex. I’ll preserve their current scope and ask before
                  replacing anything.
                </p>
                <div className="migration-chat-summary">
                  {selectedItems.map((item) => (
                    <span key={item.id}>
                      <Check size={13} />
                      {item.scope}: {item.title}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {imported && (
              <div className="migration-message">
                <span><CheckCircle2 size={17} /></span>
                <div>
                  <p>
                    Import checklist complete. Your selected settings are ready
                    for final confirmation.
                  </p>
                  <strong className="migration-success">Ready to apply</strong>
                </div>
              </div>
            )}
          </div>

          <div className="migration-chat-actions">
            <button
              className="button button-secondary"
              onClick={() => setStage(2)}
              type="button"
            >
              Back to checklist
            </button>
            <button
              className="button button-primary"
              disabled={imported}
              onClick={() => setImported(true)}
              type="button"
            >
              {imported ? (
                <>
                  <Check size={18} />
                  Checklist complete
                </>
              ) : (
                <>
                  Continue migration
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
