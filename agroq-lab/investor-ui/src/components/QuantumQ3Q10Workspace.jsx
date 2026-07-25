import {
  Activity,
  Atom,
  BarChart3,
  Beaker,
  CheckCircle2,
  CircuitBoard,
  Database,
  Download,
  Droplets,
  FlaskConical,
  GitBranch,
  KeyRound,
  Network,
  Play,
  RadioTower,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";
import { useMemo, useState } from "react";
import { persistQuantumExperiment } from "../data/quantumApi";
import {
  buildOptimizationExperimentRecord,
  runQ3Irrigation,
  runQ4Graph,
} from "../data/quantumOptimizationSuite";
import {
  buildLearningExperimentRecord,
  runQ5QuantumKernel,
  runQ6QuantumReservoir,
  runQ7AmplitudeEstimation,
} from "../data/quantumLearningSuite";
import {
  buildFrontierExperimentRecord,
  initialCryptoInventory,
  postQuantumStandards,
  runQ8QuantumSensing,
  runQ9QuantumChemistry,
  runQ10PostQuantumSecurity,
  scoreCryptoInventory,
} from "../data/quantumFrontierSuite";

const phases = [
  {
    id: "Q3",
    title: "Irrigation Scheduling",
    icon: Droplets,
    group: "Optimization",
    description:
      "Physics-grounded multi-period water-balance QUBO reproduction on a transparent synthetic benchmark.",
  },
  {
    id: "Q4",
    title: "Graph & Sensor Placement",
    icon: Network,
    group: "Optimization",
    description:
      "MaxCut partitioning and sensor-placement QUBOs solved under the same exact, annealing, and QAOA workflow.",
  },
  {
    id: "Q5",
    title: "Quantum Kernel",
    icon: GitBranch,
    group: "Learning",
    description:
      "Stress classification using the same frozen split for a classical RBF kernel and a two-qubit fidelity kernel.",
  },
  {
    id: "Q6",
    title: "Quantum Reservoir",
    icon: Waves,
    group: "Learning",
    description:
      "Time-series forecasting benchmark across persistence, linear, classical reservoir, and simulated quantum reservoir models.",
  },
  {
    id: "Q7",
    title: "Amplitude Estimation",
    icon: Activity,
    group: "Probability",
    description:
      "Monte Carlo versus maximum-likelihood amplitude-estimation simulation for a known synthetic event probability.",
  },
  {
    id: "Q8",
    title: "Quantum Sensing",
    icon: RadioTower,
    group: "Frontier",
    description:
      "Synthetic plant biomagnetism and NV-center ODMR signal-processing workspace with explicit hardware boundaries.",
  },
  {
    id: "Q9",
    title: "Quantum Chemistry",
    icon: Beaker,
    group: "Frontier",
    description:
      "One-qubit educational VQE benchmark and staged molecular-resource registry.",
  },
  {
    id: "Q10",
    title: "Post-Quantum Security",
    icon: KeyRound,
    group: "Security",
    description:
      "NIST standards and crypto-agility migration registry; no cryptographic implementation is performed.",
  },
];

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function format(value, digits = 4) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : String(value);
}

function downloadJson(result) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${result.experimentId.toLowerCase()}-results.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function registerRecord(record) {
  return persistQuantumExperiment(record);
}

function MiniLineChart({ values, label }) {
  const width = 640;
  const height = 180;
  const padding = 18;
  const numbers = values.filter(Number.isFinite);
  const minimum = Math.min(...numbers);
  const maximum = Math.max(...numbers);
  const range = Math.max(1e-12, maximum - minimum);
  const points = values
    .map((value, index) => {
      const x =
        padding +
        (index / Math.max(1, values.length - 1)) * (width - 2 * padding);
      const y =
        height -
        padding -
        ((value - minimum) / range) * (height - 2 * padding);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="q-suite-chart">
      <span>{label}</span>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
        <polyline points={points} fill="none" />
      </svg>
      <div>
        <small>min {format(minimum)}</small>
        <small>max {format(maximum)}</small>
      </div>
    </div>
  );
}

function OptimizationSolverTable({ result, path = "solvers" }) {
  const collection =
    path === "solvers"
      ? result.solvers
      : result[path];
  const rows = [
    ["Exact", collection.exact],
    ["Simulated annealing", collection.simulatedAnnealing],
    ["QAOA p=1", collection.qaoa],
  ];

  return (
    <div className="q-suite-solver-table">
      {rows.map(([name, record]) => (
        <article key={name}>
          <div>
            <strong>{name}</strong>
            <Badge tone={record.best?.feasible === false ? "red" : "green"}>
              {record.best?.feasible === false ? "violates" : "feasible"}
            </Badge>
          </div>
          <span>Energy {format(record.best?.energy)}</span>
          <span>
            Objective{" "}
            {format(record.best?.objective ?? record.best?.cutWeight ?? record.best?.coverageValue)}
          </span>
          <span>
            Selected{" "}
            {record.best?.selected?.join?.(", ") ||
              record.best?.selectedIds?.join?.(", ") ||
              record.best?.partition1?.join?.(", ") ||
              "—"}
          </span>
        </article>
      ))}
    </div>
  );
}

function Q3Panel({ result }) {
  return (
    <div className="q-suite-results">
      <section className="q-suite-metric-grid">
        <article>
          <span>Variables</span>
          <strong>{result.qubo.variableNames.length}</strong>
        </article>
        <article>
          <span>QUBO residual</span>
          <strong>{format(result.qubo.maxResidual, 8)}</strong>
        </article>
        <article>
          <span>Water budget</span>
          <strong>{result.qubo.config.waterBudget}</strong>
        </article>
        <article>
          <span>Recent source</span>
          <strong>QRS-016</strong>
        </article>
      </section>
      <OptimizationSolverTable result={result} />
      <section className="panel q-suite-detail-card">
        <h3>Exact irrigation schedule</h3>
        <div className="q-suite-chip-list">
          {result.solvers.exact.best.schedule
            .filter((item) => item.irrigate)
            .map((item) => (
              <span key={item.variable}>
                {item.zone} · {item.period}
              </span>
            ))}
        </div>
        <p>
          Water used: {result.solvers.exact.best.waterUsed}. Stress score:{" "}
          {format(result.solvers.exact.best.stress)}. Adjacency overlaps:{" "}
          {result.solvers.exact.best.adjacencyOverlaps}.
        </p>
      </section>
    </div>
  );
}

function Q4Panel({ result }) {
  return (
    <div className="q-suite-results">
      <section className="q-suite-two-column">
        <article className="panel q-suite-detail-card">
          <span className="eyebrow">Graph partition</span>
          <h3>MaxCut benchmark</h3>
          <OptimizationSolverTable result={result} path="maxCut" />
          <p>
            Exact cut weight: {format(result.maxCut.exact.best.cutWeight)}.
          </p>
        </article>
        <article className="panel q-suite-detail-card">
          <span className="eyebrow">Sensor placement</span>
          <h3>Coverage and redundancy</h3>
          <OptimizationSolverTable result={result} path="sensorPlacement" />
          <p>
            Exact coverage value:{" "}
            {format(result.sensorPlacement.exact.best.coverageValue)}.
          </p>
        </article>
      </section>
    </div>
  );
}

function Q5Panel({ result }) {
  const methods = [
    ["Classical RBF", result.classical],
    ["Quantum fidelity", result.quantum],
  ];
  return (
    <div className="q-suite-results">
      <section className="q-suite-method-grid">
        {methods.map(([name, method]) => (
          <article className="panel" key={name}>
            <span>{name}</span>
            <strong>{(method.metrics.accuracy * 100).toFixed(1)}%</strong>
            <small>accuracy</small>
            <div>
              <em>F1 {(method.metrics.f1 * 100).toFixed(1)}%</em>
              <em>Recall {(method.metrics.recall * 100).toFixed(1)}%</em>
            </div>
          </article>
        ))}
      </section>
      <section className="panel q-suite-table-card">
        <h3>Frozen test split</h3>
        <div className="q-suite-scroll">
          <table>
            <thead>
              <tr>
                <th>Sample</th>
                <th>Actual</th>
                <th>Classical</th>
                <th>Quantum</th>
                <th>Moisture</th>
                <th>Temperature</th>
              </tr>
            </thead>
            <tbody>
              {result.testRows.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{row.actual}</td>
                  <td>{row.classical}</td>
                  <td>{row.quantum}</td>
                  <td>{format(row.moisture, 3)}</td>
                  <td>{format(row.temperature, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Q6Panel({ result }) {
  const methods = Object.entries(result.methods);
  return (
    <div className="q-suite-results">
      <section className="q-suite-method-grid">
        {methods.map(([name, method]) => (
          <article className="panel" key={name}>
            <span>{name.replace(/([A-Z])/g, " $1")}</span>
            <strong>{format(method.metrics.rmse, 5)}</strong>
            <small>RMSE</small>
            <div>
              <em>MAE {format(method.metrics.mae, 5)}</em>
              <em>R² {format(method.metrics.r2, 3)}</em>
            </div>
          </article>
        ))}
      </section>
      <MiniLineChart
        label="First 20 held-out targets and quantum-reservoir predictions"
        values={result.preview.flatMap((row) => [
          row.actual,
          row.quantumReservoir,
        ])}
      />
    </div>
  );
}

function Q7Panel({ result }) {
  return (
    <div className="q-suite-results">
      <section className="q-suite-two-column">
        <article className="panel q-suite-detail-card">
          <span className="eyebrow">Classical baseline</span>
          <h3>Monte Carlo</h3>
          <strong className="q-suite-big-number">
            {(result.monteCarlo.estimate * 100).toFixed(2)}%
          </strong>
          <p>
            Absolute error{" "}
            {(result.monteCarlo.absoluteError * 100).toFixed(2)} percentage
            points using {result.monteCarlo.queryCount} samples.
          </p>
        </article>
        <article className="panel q-suite-detail-card">
          <span className="eyebrow">Quantum algorithm simulation</span>
          <h3>Maximum-likelihood amplitude estimation</h3>
          <strong className="q-suite-big-number">
            {(
              result.maximumLikelihoodAmplitudeEstimation.estimate * 100
            ).toFixed(2)}
            %
          </strong>
          <p>
            Absolute error{" "}
            {(
              result.maximumLikelihoodAmplitudeEstimation.absoluteError * 100
            ).toFixed(2)}{" "}
            percentage points. State-preparation and oracle costs are excluded.
          </p>
        </article>
      </section>
      <section className="panel q-suite-table-card">
        <h3>Grover-power observations</h3>
        <div className="q-suite-observation-grid">
          {result.maximumLikelihoodAmplitudeEstimation.observations.map(
            (observation) => (
              <div key={observation.power}>
                <span>m = {observation.power}</span>
                <strong>
                  {observation.successes}/{observation.shots}
                </strong>
                <small>
                  modeled p {(observation.probability * 100).toFixed(1)}%
                </small>
              </div>
            ),
          )}
        </div>
      </section>
    </div>
  );
}

function Q8Panel({ result }) {
  return (
    <div className="q-suite-results">
      <section className="q-suite-metric-grid">
        <article>
          <span>Plant signal SNR</span>
          <strong>{format(result.plantMagnetism.snr, 2)}</strong>
        </article>
        <article>
          <span>Detected peak</span>
          <strong>{format(result.plantMagnetism.detectedPeakPt, 3)} pT</strong>
        </article>
        <article>
          <span>NV field error</span>
          <strong>
            {format(result.nvOdMr.estimate.fieldAbsoluteError, 3)} µT
          </strong>
        </article>
        <article>
          <span>Hardware connected</span>
          <strong>No</strong>
        </article>
      </section>
      <section className="q-suite-two-column">
        <MiniLineChart
          label="Synthetic plant biomagnetic trace"
          values={result.plantMagnetism.points.map((point) => point.filtered)}
        />
        <MiniLineChart
          label="Synthetic NV ODMR contrast"
          values={result.nvOdMr.points.map((point) => point.contrast)}
        />
      </section>
    </div>
  );
}

function Q9Panel({ result }) {
  return (
    <div className="q-suite-results">
      <section className="q-suite-metric-grid">
        <article>
          <span>Exact energy</span>
          <strong>{format(result.vqe.exactEnergy, 7)}</strong>
        </article>
        <article>
          <span>VQE energy</span>
          <strong>{format(result.vqe.variational.energy, 7)}</strong>
        </article>
        <article>
          <span>Absolute error</span>
          <strong>{format(result.vqe.absoluteError, 9)}</strong>
        </article>
        <article>
          <span>Logical qubits</span>
          <strong>1</strong>
        </article>
      </section>
      <MiniLineChart
        label="Educational VQE energy landscape"
        values={result.vqe.curve.map((point) => point.energy)}
      />
      <section className="panel q-suite-table-card">
        <h3>Resource-estimation ladder</h3>
        <div className="q-suite-scroll">
          <table>
            <thead>
              <tr>
                <th>System</th>
                <th>Logical qubits</th>
                <th>Pauli terms</th>
                <th>Stage</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {result.resources.map((row) => (
                <tr key={row.system}>
                  <td>{row.system}</td>
                  <td>{row.logicalQubits}</td>
                  <td>{row.estimatedPauliTerms}</td>
                  <td>{row.stage}</td>
                  <td>{row.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Q10Panel({ result, inventory, setInventory }) {
  const readiness = scoreCryptoInventory(inventory);
  const toggle = (id, field) => {
    setInventory((current) =>
      current.map((item) =>
        item.id === id ? { ...item, [field]: !item[field] } : item,
      ),
    );
  };

  return (
    <div className="q-suite-results">
      <section className="q-suite-metric-grid">
        <article>
          <span>Readiness</span>
          <strong>{readiness.percent}%</strong>
        </article>
        <article>
          <span>Inventory systems</span>
          <strong>{inventory.length}</strong>
        </article>
        <article>
          <span>Final NIST standards</span>
          <strong>{postQuantumStandards.length}</strong>
        </article>
        <article>
          <span>Production authorized</span>
          <strong>No</strong>
        </article>
      </section>
      <section className="panel q-suite-table-card">
        <h3>Post-quantum standards</h3>
        <div className="q-suite-standard-grid">
          {postQuantumStandards.map((standard) => (
            <div key={standard.standard}>
              <span>{standard.standard}</span>
              <strong>{standard.algorithm}</strong>
              <small>{standard.use}</small>
            </div>
          ))}
        </div>
      </section>
      <section className="panel q-suite-table-card">
        <h3>Crypto-agility inventory</h3>
        <div className="q-suite-scroll">
          <table>
            <thead>
              <tr>
                <th>System</th>
                <th>Stage</th>
                <th>Approved library</th>
                <th>Interop tested</th>
                <th>Rollback</th>
              </tr>
            </thead>
            <tbody>
              {inventory.map((item) => (
                <tr key={item.id}>
                  <td>{item.system}</td>
                  <td>{item.stage}</td>
                  {[
                    "approvedLibrarySelected",
                    "interoperabilityTested",
                    "rollbackDocumented",
                  ].map((field) => (
                    <td key={field}>
                      <button
                        className={`q-suite-check ${
                          item[field] ? "q-suite-check-on" : ""
                        }`}
                        type="button"
                        onClick={() => toggle(item.id, field)}
                      >
                        {item[field] ? (
                          <CheckCircle2 size={16} />
                        ) : (
                          <ShieldCheck size={16} />
                        )}
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {result && (
        <section className="panel q-suite-boundary">
          <ShieldCheck size={20} />
          <p>{result.boundary}</p>
        </section>
      )}
    </div>
  );
}

export default function QuantumQ3Q10Workspace() {
  const [activePhase, setActivePhase] = useState("Q3");
  const [results, setResults] = useState({});
  const [running, setRunning] = useState(null);
  const [message, setMessage] = useState("");
  const [inventory, setInventory] = useState(
    initialCryptoInventory.map((item) => ({ ...item })),
  );

  const phase = useMemo(
    () => phases.find((item) => item.id === activePhase),
    [activePhase],
  );

  const execute = async () => {
    setRunning(activePhase);
    setMessage("");
    try {
      let result;
      if (activePhase === "Q3") result = await runQ3Irrigation();
      else if (activePhase === "Q4") result = await runQ4Graph();
      else if (activePhase === "Q5") result = await runQ5QuantumKernel();
      else if (activePhase === "Q6") result = await runQ6QuantumReservoir();
      else if (activePhase === "Q7") result = await runQ7AmplitudeEstimation();
      else if (activePhase === "Q8") result = await runQ8QuantumSensing();
      else if (activePhase === "Q9") result = await runQ9QuantumChemistry();
      else result = await runQ10PostQuantumSecurity(inventory);

      setResults((current) => ({ ...current, [activePhase]: result }));
      setMessage(`${result.experimentId} completed.`);
    } catch (error) {
      setMessage(`${activePhase} failed: ${error.message}`);
    } finally {
      setRunning(null);
    }
  };

  const register = async () => {
    const result = results[activePhase];
    if (!result) return;
    const record =
      ["Q3", "Q4"].includes(activePhase)
        ? buildOptimizationExperimentRecord(result)
        : ["Q5", "Q6", "Q7"].includes(activePhase)
          ? buildLearningExperimentRecord(result)
          : buildFrontierExperimentRecord(result);
    const outcome = await registerRecord(record);
    setMessage(outcome.message);
  };

  const result = results[activePhase];
  const Icon = phase.icon;

  return (
    <div className="q-suite-workspace">
      <section className="panel q-suite-hero">
        <div className="q-suite-hero-icon">
          <Sparkles size={31} />
        </div>
        <div>
          <span className="eyebrow">Combined execution package</span>
          <h2>Q3–Q10 Quantum Research Suite</h2>
          <p>
            Eight modular experiments share one evidence, registration, export, and
            claim-control workflow. All current runs are synthetic, local, and
            simulator-based unless the phase is explicitly a standards registry.
          </p>
        </div>
        <Badge tone="green">8 phases integrated</Badge>
      </section>

      <div className="q-suite-phase-tabs">
        {phases.map(({ id, title, icon: PhaseIcon }) => (
          <button
            key={id}
            className={activePhase === id ? "q-suite-phase-active" : ""}
            type="button"
            onClick={() => {
              setActivePhase(id);
              setMessage("");
            }}
          >
            <PhaseIcon size={16} />
            <span>{id}</span>
            <small>{title}</small>
          </button>
        ))}
      </div>

      <section className="panel q-suite-phase-header">
        <div className="q-suite-phase-icon">
          <Icon size={28} />
        </div>
        <div>
          <span className="eyebrow">
            {phase.id} · {phase.group}
          </span>
          <h2>{phase.title}</h2>
          <p>{phase.description}</p>
        </div>
        <div className="q-suite-phase-actions">
          <button
            className="button button-primary"
            type="button"
            onClick={execute}
            disabled={running === activePhase}
          >
            {running === activePhase ? (
              <RefreshCw className="q-suite-spin" size={17} />
            ) : (
              <Play size={17} />
            )}
            {running === activePhase ? "Running…" : `Run ${activePhase}`}
          </button>
          {result && (
            <>
              <button
                className="button button-secondary"
                type="button"
                onClick={register}
              >
                <Save size={17} />
                Register in Q1
              </button>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => downloadJson(result)}
              >
                <Download size={17} />
                Export JSON
              </button>
            </>
          )}
        </div>
      </section>

      {message && (
        <section className="panel q-suite-message">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </section>
      )}

      {!result && (
        <section className="panel q-suite-empty">
          <FlaskConical size={32} />
          <h3>{activePhase} is ready to run</h3>
          <p>
            The run will remain local to this browser until its result is exported or
            registered in the Q1 experiment registry.
          </p>
        </section>
      )}

      {result && activePhase === "Q3" && <Q3Panel result={result} />}
      {result && activePhase === "Q4" && <Q4Panel result={result} />}
      {result && activePhase === "Q5" && <Q5Panel result={result} />}
      {result && activePhase === "Q6" && <Q6Panel result={result} />}
      {result && activePhase === "Q7" && <Q7Panel result={result} />}
      {result && activePhase === "Q8" && <Q8Panel result={result} />}
      {result && activePhase === "Q9" && <Q9Panel result={result} />}
      {activePhase === "Q10" && (
        <Q10Panel
          result={result}
          inventory={inventory}
          setInventory={setInventory}
        />
      )}

      <section className="panel q-suite-global-boundary">
        <ShieldCheck size={22} />
        <div>
          <h3>Global claim boundary</h3>
          <p>
            These modules are reproducible research prototypes. They do not establish
            quantum advantage, autonomous agricultural control, validated diagnostics,
            connected quantum sensors, chemistry-grade simulation, or production
            cryptographic migration.
          </p>
        </div>
      </section>
    </div>
  );
}
