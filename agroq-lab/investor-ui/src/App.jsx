import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Beaker,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  CloudOff,
  Cpu,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  Grid3X3,
  Layers3,
  Leaf,
  Menu,
  Network,
  Orbit,
  RadioTower,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Sprout,
  TestTube2,
  Users,
  Waves,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import AcreScene from "./components/AcreScene";
import AccessPage from "./components/AccessPage";
import ResearchCreditsPage from "./components/ResearchCreditsPage";
import SoilBiologyPage from "./components/SoilBiologyPage";
import NetworkGraph from "./components/NetworkGraph";
import Sparkline from "./components/Sparkline";
import {
  activity,
  architectureLayers,
  createScenarioView,
  experiments,
  phaseRoadmap,
  recommendations,
  scenarios,
  tasks,
} from "./data/demoData";
import { loadBackendSnapshot } from "./lib/api";

import AdminLabPage from "./components/AdminLabPage";
const navigation = [
  { id: "overview", label: "Overview", icon: Grid3X3 },
  { id: "acre", label: "3D Digital Acre", icon: Orbit },
  { id: "soil-biology", label: "Soil Biology (SFW)", icon: Sprout },
  { id: "experiments", label: "Experiments", icon: FlaskConical },
  { id: "operations", label: "Operations", icon: Activity },
  { id: "intelligence", label: "AI & Graphs", icon: BrainCircuit },
  { id: "quantum", label: "Quantum Lab", icon: Cpu },
  { id: "access", label: "Access & Community", icon: Users },
  { id: "credits", label: "Research & Thanks", icon: BookOpen },
  { id: "admin-lab", label: "Admin & Sequence Lab", icon: Users },
  { id: "system", label: "System", icon: Layers3 },
];

const trendValues = {
  moisture: [27, 26, 25, 24, 22, 23, 21, 20],
  health: [94, 93, 92, 91, 90, 88, 89, 87],
  temperature: [22, 23, 24, 25, 27, 28, 27, 26],
};

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function MetricCard({ label, value, note, icon: Icon, trend, tone }) {
  return (
    <article className="metric-card panel">
      <div className="metric-icon">
        <Icon size={19} />
      </div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
      {trend && <Sparkline values={trend} tone={tone} />}
    </article>
  );
}

function Panel({ title, eyebrow, actions, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2>{title}</h2>
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

function OverviewPage({
  zoneData,
  scenarioKey,
  backend,
  onLaunchWalkthrough,
  onViewBoundaries,
}) {
  const averageMoisture = Math.round(
    zoneData.reduce((sum, zone) => sum + zone.moisture, 0) / zoneData.length,
  );
  const averageHealth = Math.round(
    zoneData.reduce((sum, zone) => sum + zone.health, 0) / zoneData.length,
  );
  const attentionCount = zoneData.filter((zone) => zone.status !== "Stable").length;

  return (
    <div className="page-stack">
      <section className="hero-grid">
        <motion.div
          className="hero-copy"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="hero-kicker">
            <Sparkles size={17} />
            Quantum-AI Living Systems Lab
          </div>
          <h1>
            One digital acre.
            <span> Every decision traceable.</span>
          </h1>
          <p>
            AgroQ combines manual field operations, synthetic sensing, local-edge
            workflows, experiment intelligence, classical optimization, and a
            quantum-research lane inside one auditable platform.
          </p>
          <div className="hero-actions">
            <button
              className="button button-primary"
              onClick={onLaunchWalkthrough}
            >
              Launch investor walkthrough
              <ChevronRight size={18} />
            </button>
            <button
              className="button button-secondary"
              onClick={onViewBoundaries}
            >
              <ShieldCheck size={18} />
              View control boundaries
            </button>
          </div>
          <div className="hero-status">
            <Badge>Investor prototype</Badge>
            <Badge tone="amber">Synthetic data</Badge>
            <Badge tone={backend.connected ? "green" : "slate"}>
              {backend.connected ? "Backend connected" : "Demo fallback active"}
            </Badge>
          </div>
        </motion.div>

        <div className="hero-visual panel">
          <div className="orbital-rings">
            <div className="orbital-center">
              <Leaf size={36} />
              <strong>AgroQ</strong>
              <span>Decision Intelligence</span>
            </div>
            {[
              { label: "Manual", icon: Sprout },
              { label: "Edge", icon: RadioTower },
              { label: "AI", icon: BrainCircuit },
              { label: "Graph", icon: Network },
              { label: "QUBO", icon: Cpu },
            ].map(({ label, icon: Icon }, index) => (
              <div
                key={label}
                className={`orbit-node orbit-node-${index + 1}`}
              >
                <Icon size={17} />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard
          label="Average soil moisture"
          value={`${averageMoisture}%`}
          note={`Scenario: ${scenarios[scenarioKey].label}`}
          icon={Waves}
          trend={trendValues.moisture}
          tone="#5cf1a0"
        />
        <MetricCard
          label="Acre health index"
          value={`${averageHealth}`}
          note="Synthetic composite score"
          icon={Gauge}
          trend={trendValues.health}
          tone="#80c4ff"
        />
        <MetricCard
          label="Plots needing review"
          value={attentionCount}
          note="Human review remains required"
          icon={ShieldCheck}
        />
        <MetricCard
          label="Active experiments"
          value={experiments.length}
          note="Manual + simulation workflows"
          icon={FlaskConical}
        />
      </section>

      <section className="two-column">
        <Panel
          title="Current experiments"
          eyebrow="Research operations"
          actions={<button className="text-button">Open registry</button>}
        >
          <div className="experiment-list">
            {experiments.map((experiment) => (
              <div className="experiment-row" key={experiment.id}>
                <div className="experiment-marker">
                  <TestTube2 size={17} />
                </div>
                <div className="experiment-main">
                  <strong>{experiment.name}</strong>
                  <span>
                    {experiment.stage} · {experiment.samples} samples ·{" "}
                    {experiment.plots} plots
                  </span>
                  <div className="progress">
                    <div style={{ width: `${experiment.progress}%` }} />
                  </div>
                </div>
                <b>{experiment.progress}%</b>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Recommendation queue" eyebrow="Human decision gate">
          <div className="recommendation-list">
            {recommendations.map((recommendation) => (
              <div className="recommendation-row" key={recommendation.id}>
                <div>
                  <Badge
                    tone={
                      recommendation.priority === "High"
                        ? "red"
                        : recommendation.priority === "Medium"
                          ? "amber"
                          : "slate"
                    }
                  >
                    {recommendation.priority}
                  </Badge>
                  <strong>{recommendation.title}</strong>
                  <p>{recommendation.rationale}</p>
                </div>
                <button className="icon-button" aria-label="Open recommendation">
                  <ChevronRight size={18} />
                </button>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}

function AcrePage({ zoneData, selectedZone, setSelectedZone, scenarioKey }) {
  return (
    <div className="page-stack">
      <section className="acre-layout">
        <Panel
          className="acre-panel"
          title="Interactive acre digital twin"
          eyebrow="Phase 3 prototype"
          actions={
            <div className="legend">
              <span><i className="legend-dot stable" /> Stable</span>
              <span><i className="legend-dot attention" /> Attention</span>
            </div>
          }
        >
          <AcreScene
            zones={zoneData}
            selectedZone={selectedZone}
            onSelect={setSelectedZone}
            offline={scenarioKey === "outage"}
          />
        </Panel>

        <Panel
          className="zone-panel"
          title={selectedZone?.name || "Select a plot"}
          eyebrow="Plot detail"
        >
          {selectedZone ? (
            <div className="zone-details">
              <div className="zone-status-line">
                <Badge tone={selectedZone.status === "Stable" ? "green" : "amber"}>
                  {selectedZone.status}
                </Badge>
                <span>{selectedZone.type}</span>
              </div>
              <div className="zone-score-grid">
                <div>
                  <span>Moisture</span>
                  <strong>{selectedZone.moisture}%</strong>
                </div>
                <div>
                  <span>Health</span>
                  <strong>{selectedZone.health}</strong>
                </div>
                <div>
                  <span>Temperature</span>
                  <strong>{selectedZone.temperature}°C</strong>
                </div>
              </div>
              <div className="detail-block">
                <span>Linked experiment</span>
                <strong>{selectedZone.experiment}</strong>
              </div>
              <div className="detail-block">
                <span>Evidence mode</span>
                <strong>Synthetic demonstration</strong>
              </div>
              <button className="button button-primary full-width">
                Open plot workspace
                <ChevronRight size={18} />
              </button>
            </div>
          ) : (
            <div className="empty-state">
              <Orbit size={36} />
              <p>Select a plot in the 3D acre to inspect its operating state.</p>
            </div>
          )}
        </Panel>
      </section>
    </div>
  );
}

function ExperimentsPage() {
  return (
    <div className="page-stack">
      <section className="metrics-grid">
        <MetricCard label="Active protocols" value="3" note="1 control · 2 treatments" icon={Beaker} />
        <MetricCard label="Synthetic samples" value="59" note="Chain-of-custody demonstration" icon={TestTube2} />
        <MetricCard label="Outcome links" value="24" note="Observation-to-decision traceability" icon={GitBranch} />
        <MetricCard label="Data quality" value="91%" note="Demo completeness score" icon={CheckCircle2} />
      </section>

      <Panel title="Experiment portfolio" eyebrow="Phase 3–5 research workspace">
        <div className="experiment-cards">
          {experiments.map((experiment, index) => (
            <motion.article
              key={experiment.id}
              className="experiment-card"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
            >
              <div className="card-topline">
                <Badge tone={experiment.stage === "Active" ? "green" : "slate"}>
                  {experiment.stage}
                </Badge>
                <span>{experiment.id}</span>
              </div>
              <h3>{experiment.name}</h3>
              <div className="experiment-stat-grid">
                <div><span>Progress</span><strong>{experiment.progress}%</strong></div>
                <div><span>Samples</span><strong>{experiment.samples}</strong></div>
                <div><span>Plots</span><strong>{experiment.plots}</strong></div>
              </div>
              <div className="progress large">
                <div style={{ width: `${experiment.progress}%` }} />
              </div>
              <button className="button button-secondary full-width">
                View experimental evidence
              </button>
            </motion.article>
          ))}
        </div>
      </Panel>

      <section className="two-column">
        <Panel title="Outcome comparison" eyebrow="Synthetic benchmark">
          <div className="bar-chart">
            {[
              ["Control", 62],
              ["Compost", 76],
              ["Beneficial", 88],
              ["Calibration", 69],
            ].map(([label, value]) => (
              <div className="bar-row" key={label}>
                <span>{label}</span>
                <div className="bar-track">
                  <div style={{ width: `${value}%` }} />
                </div>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Evidence chain" eyebrow="Scientific traceability">
          <div className="evidence-chain">
            {[
              "Protocol version frozen",
              "Plot assignment recorded",
              "Observation provenance stored",
              "Decision linked to evidence",
              "Outcome compared with baseline",
            ].map((item, index) => (
              <div key={item}>
                <span>{index + 1}</span>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}

function OperationsPage({ scenarioKey }) {
  return (
    <div className="page-stack">
      <section className="metrics-grid">
        <MetricCard label="Gateway" value={scenarioKey === "outage" ? "Local" : "Online"} note="Local-first operation" icon={RadioTower} />
        <MetricCard label="Open tasks" value="3" note="Human-owned workflow" icon={Activity} />
        <MetricCard label="Queued sync items" value={scenarioKey === "outage" ? "8" : "0"} note="Offline-capable queue" icon={RefreshCw} />
        <MetricCard label="Backups" value="Verified" note="Recovery-copy workflow" icon={Database} />
      </section>

      <section className="two-column">
        <Panel title="Manual work queue" eyebrow="Field operations">
          <div className="task-table">
            {tasks.map((task) => (
              <div className="task-row" key={task.title}>
                <div className={`priority priority-${task.priority.toLowerCase()}`} />
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.owner}</span>
                </div>
                <Badge tone="slate">{task.status}</Badge>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Gateway activity" eyebrow="Local edge timeline">
          <div className="timeline">
            {activity.map((item, index) => (
              <div key={item}>
                <span className="timeline-dot" />
                <div>
                  <strong>{item}</strong>
                  <small>{index + 1} minute{index ? "s" : ""} ago · synthetic</small>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <div id="control-boundaries">
        <Panel title="Operational control boundary" eyebrow="Human-supervised automation">
        <div className="control-grid">
          {[
            ["Manual observations", "Enabled", "green"],
            ["Synthetic sensor feeds", "Enabled", "green"],
            ["Recommendation generation", "Enabled", "green"],
            ["Automatic field actuation", "Disabled", "red"],
            ["Phase 3 physical devices", "Not authorized", "amber"],
            ["Audit and export", "Enabled", "green"],
          ].map(([label, value, tone]) => (
            <div className="control-row" key={label}>
              <span>{label}</span>
              <Badge tone={tone}>{value}</Badge>
            </div>
          ))}
        </div>
        </Panel>
      </div>
    </div>
  );
}

function IntelligencePage({ selectedZone }) {
  return (
    <div className="page-stack">
      <section className="metrics-grid">
        <MetricCard label="Anomaly score" value="0.18" note="Laplacian demo score" icon={Network} />
        <MetricCard label="Forecast horizon" value="7 days" note="Synthetic baseline forecast" icon={BarChart3} />
        <MetricCard label="Candidate samples" value="4" note="Active-sampling shortlist" icon={CircleDot} />
        <MetricCard label="Recommendations" value="3" note="All require human review" icon={BrainCircuit} />
      </section>

      <section className="two-column">
        <Panel title="Spatial interaction graph" eyebrow="Phase 5 prototype">
          <NetworkGraph activeZone={selectedZone} />
          <p className="panel-note">
            Plot adjacency and gateway links support spatial anomaly scoring and
            active-sampling recommendations.
          </p>
        </Panel>

        <Panel title="Forecast preview" eyebrow="Phase 4 prototype">
          <div className="forecast-stack">
            <div>
              <span>Soil moisture</span>
              <strong>Declining</strong>
              <Sparkline values={[28, 27, 27, 25, 23, 22, 20, 19]} />
            </div>
            <div>
              <span>Canopy health</span>
              <strong>Stable</strong>
              <Sparkline values={[86, 87, 86, 88, 89, 88, 90, 89]} tone="#80c4ff" />
            </div>
            <div>
              <span>Inspection priority</span>
              <strong>Increasing</strong>
              <Sparkline values={[1, 1, 2, 2, 3, 4, 5, 6]} tone="#f3b96c" />
            </div>
          </div>
        </Panel>
      </section>

      <Panel title="Active sampling recommendations" eyebrow="Experiment intelligence">
        <div className="sampling-grid">
          {[
            ["Compost Treatment", "High", "Low moisture + high uncertainty"],
            ["Calibration Zone", "High", "Virtual-node drift"],
            ["North Control", "Normal", "Baseline reference continuity"],
            ["Beneficial Zone", "Normal", "Healthy trend confirmation"],
          ].map(([zone, priority, reason]) => (
            <article className="sampling-card" key={zone}>
              <div className="card-topline">
                <Badge tone={priority === "High" ? "red" : "slate"}>{priority}</Badge>
                <CircleDot size={18} />
              </div>
              <h3>{zone}</h3>
              <p>{reason}</p>
              <button className="text-button">Add to manual plan</button>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function QuantumPage({ frozenProblem }) {
  return (
    <div className="page-stack">
      <section className="quantum-hero panel">
        <div>
          <span className="eyebrow">Phase 6 prototype</span>
          <h2>Quantum-ready optimization workspace</h2>
          <p>
            Compare a classical baseline, quantum-inspired search, and a simulator
            run using the same frozen synthetic benchmark. No quantum-advantage
            claim is made.
          </p>
        </div>
        <div className="quantum-orb">
          <Zap size={36} />
        </div>
      </section>

      {frozenProblem && (
        <section className="panel quantum-frozen-problem">
          <div className="quantum-frozen-heading">
            <div>
              <span>Frozen Soil Biology problem</span>
              <h3>{frozenProblem.id}</h3>
            </div>
            <Badge tone="green">Dataset frozen</Badge>
          </div>
          <div className="quantum-frozen-grid">
            <div>
              <span>Candidate samples</span>
              <strong>{frozenProblem.candidates?.length || 0}</strong>
            </div>
            <div>
              <span>Sampling budget</span>
              <strong>{frozenProblem.budget}</strong>
            </div>
            <div>
              <span>Classical selection</span>
              <strong>{frozenProblem.classicalSelection?.length || 0}</strong>
            </div>
            <div>
              <span>Classical score</span>
              <strong>{frozenProblem.classicalScore}</strong>
            </div>
          </div>
          <div className="quantum-frozen-selection">
            {(frozenProblem.classicalSelection || []).map((sampleId) => (
              <span key={sampleId}>{sampleId}</span>
            ))}
          </div>
          <p className="panel-note">
            The same candidates, budget, weights, constraints, and classical baseline are
            preserved for quantum-inspired and simulator comparison. No quantum-advantage
            claim is made.
          </p>
        </section>
      )}

      <section className="metrics-grid">
        <MetricCard label="Decision variables" value="16" note="Plot-task assignment demo" icon={Grid3X3} />
        <MetricCard label="QUBO terms" value="58" note="Synthetic objective" icon={GitBranch} />
        <MetricCard label="Classical best" value="-14.8" note="Reference score" icon={BarChart3} />
        <MetricCard label="Simulator best" value="-14.2" note="Matched-budget preview" icon={Cpu} />
      </section>

      <section className="three-column">
        {[
          {
            title: "Classical baseline",
            icon: BarChart3,
            status: "Complete",
            copy: "Greedy and simulated-annealing reference results.",
            score: "-14.8",
          },
          {
            title: "Quantum-inspired",
            icon: BrainCircuit,
            status: "Complete",
            copy: "Synthetic hybrid search under the same budget.",
            score: "-14.5",
          },
          {
            title: "Quantum simulator",
            icon: Cpu,
            status: "Preview",
            copy: "QAOA-style simulator record with no hardware claim.",
            score: "-14.2",
          },
        ].map(({ title, icon: Icon, status, copy, score }) => (
          <article className="solver-card panel" key={title}>
            <div className="solver-icon"><Icon size={24} /></div>
            <Badge tone={status === "Complete" ? "green" : "amber"}>{status}</Badge>
            <h3>{title}</h3>
            <p>{copy}</p>
            <div className="solver-score">
              <span>Objective</span>
              <strong>{score}</strong>
            </div>
          </article>
        ))}
      </section>

      <section className="two-column">
        <Panel title="Optimization objective" eyebrow="Synthetic QUBO">
          <div className="qubo-matrix">
            {Array.from({ length: 8 }).map((_, row) =>
              Array.from({ length: 8 }).map((__, column) => (
                <span
                  key={`${row}-${column}`}
                  style={{
                    opacity:
                      row === column ? 1 : ((row + column) % 3 === 0 ? 0.65 : 0.18),
                  }}
                />
              )),
            )}
          </div>
        </Panel>

        <Panel title="Research controls" eyebrow="Evidence discipline">
          <div className="control-grid">
            <div className="control-row"><span>Benchmark dataset frozen</span><Badge>Yes</Badge></div>
            <div className="control-row"><span>Classical comparison included</span><Badge>Yes</Badge></div>
            <div className="control-row"><span>Simulator seed recorded</span><Badge>Yes</Badge></div>
            <div className="control-row"><span>QPU hardware used</span><Badge tone="slate">No</Badge></div>
            <div className="control-row"><span>Advantage claim</span><Badge tone="slate">None</Badge></div>
          </div>
        </Panel>
      </section>
    </div>
  );
}

function SystemPage({ backend }) {
  return (
    <div className="page-stack">
      <section className="metrics-grid">
        <MetricCard label="Application mode" value="Prototype" note="Investor demonstration" icon={Sparkles} />
        <MetricCard label="Data mode" value="Synthetic" note="Not field validation" icon={Database} />
        <MetricCard label="Backend status" value={backend.connected ? "Connected" : "Fallback"} note={backend.error || "Existing AgroQ API"} icon={RadioTower} />
        <MetricCard label="Control model" value="Human-first" note="No direct actuation" icon={ShieldCheck} />
      </section>

      <section className="two-column">
        <Panel title="Integrated architecture" eyebrow="Full-stack platform">
          <div className="architecture-stack">
            {architectureLayers.map((layer, index) => (
              <div key={layer}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{layer}</strong>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Prototype release boundary" eyebrow="Current truth">
          <div className="release-boundary">
            <CheckCircle2 size={36} />
            <h3>Ready for investor demonstration</h3>
            <p>
              The UI, synthetic workflows, analytics previews, graph workspace,
              and quantum research lane can be demonstrated without claiming
              real field validation.
            </p>
            <div className="release-tags">
              <Badge>Demo ready</Badge>
              <Badge tone="amber">Beta preparation</Badge>
              <Badge tone="slate">Field validation later</Badge>
            </div>
          </div>
        </Panel>
      </section>

      <Panel title="Phases 3–6 prototype roadmap" eyebrow="Accelerated build">
        <div className="roadmap">
          {phaseRoadmap.map((phase, index) => (
            <div className="roadmap-row" key={phase.phase}>
              <div className="roadmap-index">{index + 3}</div>
              <div>
                <span>{phase.phase}</span>
                <strong>{phase.title}</strong>
                <p>{phase.detail}</p>
              </div>
              <Badge tone="green">{phase.status}</Badge>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [scenarioKey, setScenarioKey] = useState("baseline");
  const [selectedZone, setSelectedZone] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [backend, setBackend] = useState({
    connected: false,
    health: null,
    exported: null,
    error: "Checking backend",
  });
  const [frozenSamplingProblem, setFrozenSamplingProblem] = useState(() => {
    try {
      const saved = window.localStorage.getItem(
        "agroq-frozen-soil-sampling-problem",
      );
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const zoneData = useMemo(() => createScenarioView(scenarioKey), [scenarioKey]);

  useEffect(() => {
    setSelectedZone((current) => {
      if (!current) return null;
      return zoneData.find((zone) => zone.id === current.id) || null;
    });
  }, [zoneData]);

  useEffect(() => {
    loadBackendSnapshot().then(setBackend);
  }, []);

  const launchInvestorWalkthrough = () => {
    setScenarioKey("baseline");
    setActivePage("acre");
    setSidebarOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const viewControlBoundaries = () => {
    setActivePage("operations");
    setSidebarOpen(false);
    window.setTimeout(() => {
      document.getElementById("control-boundaries")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 250);
  };

  const activeLabel =
    navigation.find((item) => item.id === activePage)?.label || "Overview";

  let content;
  if (activePage === "overview") {
    content = (
      <OverviewPage
        zoneData={zoneData}
        scenarioKey={scenarioKey}
        backend={backend}
        onLaunchWalkthrough={launchInvestorWalkthrough}
        onViewBoundaries={viewControlBoundaries}
      />
    );
  } else if (activePage === "acre") {
    content = (
      <AcrePage
        zoneData={zoneData}
        selectedZone={selectedZone}
        setSelectedZone={setSelectedZone}
        scenarioKey={scenarioKey}
      />
    );
  } else if (activePage === "soil-biology") {
    content = (
      <SoilBiologyPage
        onOpenExperiments={() => {
          setActivePage("experiments");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
        onOpenOperations={() => {
          setActivePage("operations");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
        onFreezeProblem={setFrozenSamplingProblem}
        onOpenQuantum={() => {
          setActivePage("quantum");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      />
    );
  } else if (activePage === "experiments") {
    content = <ExperimentsPage />;
  } else if (activePage === "operations") {
    content = <OperationsPage scenarioKey={scenarioKey} />;
  } else if (activePage === "intelligence") {
    content = <IntelligencePage selectedZone={selectedZone} />;
  } else if (activePage === "quantum") {
    content = <QuantumPage frozenProblem={frozenSamplingProblem} />;
  } else if (activePage === "access") {
    content = <AccessPage />;
  } else if (activePage === "credits") {
    content = <ResearchCreditsPage />;
  } else if (activePage === "admin-lab") {
    content = <AdminLabPage />;
  } else {
    content = <SystemPage backend={backend} />;
  }

  return (
    <div className="app-shell">
      <AnimatePresence>
        {(sidebarOpen || window.innerWidth > 980) && (
          <motion.aside
            className={`sidebar ${sidebarOpen ? "sidebar-mobile-open" : ""}`}
            initial={{ x: -24, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -24, opacity: 0 }}
          >
            <div className="brand-block">
              <div className="brand-mark">
                <Leaf size={24} />
              </div>
              <div>
                <strong>AgroQ</strong>
                <span>Living Systems Lab</span>
              </div>
              <button
                className="mobile-close"
                onClick={() => setSidebarOpen(false)}
                aria-label="Close navigation"
              >
                <X size={20} />
              </button>
            </div>

            <nav>
              {navigation.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  className={activePage === id ? "nav-active" : ""}
                  onClick={() => {
                    setActivePage(id);
                    setSidebarOpen(false);
                  }}
                >
                  <Icon size={19} />
                  <span>{label}</span>
                </button>
              ))}
            </nav>

            <div className="sidebar-bottom">
              <div className="mode-card">
                <div>
                  <span className="live-dot" />
                  Prototype online
                </div>
                <small>Investor demo · synthetic evidence</small>
              </div>
              <div className="user-card">
                <div className="avatar">OR</div>
                <div>
                  <strong>Othon Reyes Jr.</strong>
                  <span>Founder · Research Lead</span>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <main className="main-shell">
        <header className="topbar">
          <button
            className="menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={22} />
          </button>
          <div>
            <span className="topbar-eyebrow">AgroQ investor prototype</span>
            <h2>{activeLabel}</h2>
          </div>

          <div className="scenario-control">
            <label htmlFor="scenario">Scenario</label>
            <select
              id="scenario"
              value={scenarioKey}
              onChange={(event) => setScenarioKey(event.target.value)}
            >
              {Object.entries(scenarios).map(([key, scenario]) => (
                <option key={key} value={key}>
                  {scenario.label}
                </option>
              ))}
            </select>
          </div>

          <div className="topbar-pills">
            <Badge tone="amber">Synthetic</Badge>
            <Badge tone="slate">Field mode locked</Badge>
          </div>
        </header>

        <div className="content-wrap">
          <AnimatePresence mode="wait">
            <motion.div
              key={activePage}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.22 }}
            >
              {content}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
