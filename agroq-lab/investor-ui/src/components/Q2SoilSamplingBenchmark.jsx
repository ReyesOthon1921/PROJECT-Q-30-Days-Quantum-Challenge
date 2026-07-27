import {
  AlertTriangle,
  Atom,
  BarChart3,
  CheckCircle2,
  CircuitBoard,
  Database,
  Download,
  FlaskConical,
  Gauge,
  Grid3X3,
  Play,
  RefreshCw,
  Save,
  Scale,
  ShieldCheck,
  Sigma,
  TestTube2,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  buildQ2ExperimentRecord,
  normalizeSoilSamplingProblem,
  q2SolverRows,
  quboMatrixToCsv,
  rowsToCsv,
  runQ2Benchmark,
} from "../data/q2SoilSamplingBenchmark";
import { persistQuantumExperiment } from "../data/quantumApi";

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function formatNumber(value, digits = 4) {
  if (value === null || value === undefined || value === "") return "—";
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : String(value);
}

function SolverCard({ title, eyebrow, icon: Icon, record, exactUtility, tone }) {
  const solution = record?.best;
  const relativeGap = record?.comparison?.relativeUtilityGap;
  const exactMatch = record?.comparison?.exactMatch;

  return (
    <article className={`panel q2-solver-card q2-solver-${tone}`}>
      <div className="q2-solver-heading">
        <div className="q2-solver-icon">
          <Icon size={20} />
        </div>
        <div>
          <span>{eyebrow}</span>
          <h3>{title}</h3>
        </div>
        <Badge tone={solution?.feasible ? "green" : "red"}>
          {solution?.feasible ? "Feasible" : "No result"}
        </Badge>
      </div>

      <div className="q2-solver-metrics">
        <div>
          <span>QUBO energy</span>
          <strong>{formatNumber(solution?.energy)}</strong>
        </div>
        <div>
          <span>Information utility</span>
          <strong>{formatNumber(solution?.utility)}</strong>
        </div>
        <div>
          <span>Budget used</span>
          <strong>{solution?.usedBudget ?? "—"}</strong>
        </div>
        <div>
          <span>Exact utility gap</span>
          <strong>
            {relativeGap === null || relativeGap === undefined
              ? "—"
              : `${(relativeGap * 100).toFixed(2)}%`}
          </strong>
        </div>
      </div>

      <div className="q2-selected-list">
        {(solution?.selected || []).map((candidate) => (
          <span key={candidate.id}>
            {candidate.id} · {candidate.zone}
          </span>
        ))}
      </div>

      <div className="q2-solver-footer">
        <span>
          {record?.objectiveEvaluations ??
            record?.parameterEvaluations ??
            "Reference"}{" "}
          evaluations
        </span>
        <Badge tone={exactMatch ? "green" : "amber"}>
          {exactMatch ? "Exact match" : `Exact utility ${formatNumber(exactUtility)}`}
        </Badge>
      </div>
    </article>
  );
}

function QuboMatrix({ result }) {
  const variables = result.qubo.variables;
  const matrix = result.qubo.matrix;
  const maxAbsolute = Math.max(
    1,
    ...matrix.flat().map((value) => Math.abs(value)),
  );

  return (
    <section className="panel q2-matrix-panel">
      <div className="q2-section-heading">
        <div>
          <span className="eyebrow">Frozen formulation</span>
          <h2>QUBO matrix and variable map</h2>
          <p>
            Selection variables are combined with binary slack variables so the
            sampling-budget inequality is represented as a quadratic equality penalty.
          </p>
        </div>
        <Badge tone="green">{result.qubo.quboTermCount} nonzero terms</Badge>
      </div>

      <div className="q2-variable-map">
        {variables.map((variable) => (
          <div key={variable.name}>
            <span>{variable.index}</span>
            <strong>{variable.name}</strong>
            <small>
              {variable.kind} · coefficient {variable.coefficient}
            </small>
          </div>
        ))}
      </div>

      <div className="q2-matrix-scroll">
        <table className="q2-matrix-table">
          <thead>
            <tr>
              <th>Variable</th>
              {variables.map((variable) => (
                <th key={variable.name}>{variable.index}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, rowIndex) => (
              <tr key={variables[rowIndex].name}>
                <th>{rowIndex}</th>
                {row.map((value, columnIndex) => {
                  const intensity = Math.min(1, Math.abs(value) / maxAbsolute);
                  return (
                    <td
                      key={`${rowIndex}-${columnIndex}`}
                      style={{ "--q2-cell-intensity": intensity }}
                      title={`${variables[rowIndex].name} × ${variables[columnIndex].name}: ${value}`}
                    >
                      {Math.abs(value) < 0.000001 ? "0" : value.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function Q2SoilSamplingBenchmark({ frozenProblem }) {
  const normalizedProblem = useMemo(
    () => normalizeSoilSamplingProblem(frozenProblem),
    [frozenProblem],
  );
  const [seed, setSeed] = useState(301);
  const [sampleBudget, setSampleBudget] = useState(2048);
  const [gridSize, setGridSize] = useState(13);
  const [penalty, setPenalty] = useState(6);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  const runBenchmark = async () => {
    setRunning(true);
    setMessage("");
    try {
      const completed = await runQ2Benchmark(normalizedProblem, {
        seed,
        sharedSampleBudget: sampleBudget,
        gridSize,
        penalty,
      });
      setResult(completed);
      setMessage(
        `${completed.experimentId} completed with exact, greedy, simulated-annealing, and QAOA p=1 results.`,
      );
    } catch (error) {
      setMessage(`Q2 failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  };

  const registerResult = async () => {
    if (!result) return;
    const record = buildQ2ExperimentRecord(result);
    const outcome = await persistQuantumExperiment(record);
    setMessage(outcome.message);
  };

  const exportJson = () => {
    if (!result) return;
    downloadFile(
      `${result.experimentId.toLowerCase()}-benchmark.json`,
      JSON.stringify(result, null, 2),
      "application/json",
    );
  };

  const exportSolverCsv = () => {
    if (!result) return;
    downloadFile(
      `${result.experimentId.toLowerCase()}-solver-results.csv`,
      rowsToCsv(q2SolverRows(result)),
      "text/csv",
    );
  };

  const exportQuboCsv = () => {
    if (!result) return;
    downloadFile(
      `${result.experimentId.toLowerCase()}-qubo-matrix.csv`,
      quboMatrixToCsv(result),
      "text/csv",
    );
  };

  const exactUtility = result?.solvers.exact.best?.utility ?? null;
  const topHistogram = result?.solvers.qaoa.histogram || [];
  const maxCount = Math.max(1, ...topHistogram.map((item) => item.count));

  return (
    <div className="q2-benchmark-stack">
      <section className="panel q2-hero">
        <div className="q2-hero-icon">
          <Atom size={32} />
        </div>
        <div>
          <span className="eyebrow">Q2 · Executable benchmark</span>
          <h2>Frozen Soil-Sampling QUBO</h2>
          <p>
            Build one frozen QUBO, solve it with exact enumeration, greedy selection,
            seeded simulated annealing, and an ideal p=1 QAOA statevector simulator,
            then compare feasibility and utility without making a hardware or
            quantum-advantage claim.
          </p>
        </div>
        <Badge tone={frozenProblem ? "green" : "amber"}>
          {normalizedProblem.sourceMode}
        </Badge>
      </section>

      {!frozenProblem && (
        <section className="panel q2-warning">
          <AlertTriangle size={20} />
          <div>
            <h3>No frozen Soil Biology problem was found</h3>
            <p>
              Q2 will use the registered six-candidate synthetic reference problem.
              Freeze a new problem in Soil Biology → Sampling Optimizer to replace it.
            </p>
          </div>
        </section>
      )}

      <section className="q2-layout">
        <article className="panel q2-controls">
          <div className="q2-section-heading">
            <div>
              <span className="eyebrow">Run controls</span>
              <h2>Matched benchmark configuration</h2>
            </div>
            <Gauge size={23} />
          </div>

          <label>
            Random seed
            <input
              type="number"
              value={seed}
              onChange={(event) => setSeed(Number(event.target.value))}
            />
          </label>

          <label>
            Shared stochastic sample budget
            <strong>{sampleBudget}</strong>
            <input
              type="range"
              min="512"
              max="8192"
              step="512"
              value={sampleBudget}
              onChange={(event) => setSampleBudget(Number(event.target.value))}
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
              max="25"
              step="2"
              value={gridSize}
              onChange={(event) => setGridSize(Number(event.target.value))}
            />
          </label>

          <label>
            Constraint penalty
            <strong>{penalty}</strong>
            <input
              type="range"
              min="2"
              max="20"
              step="1"
              value={penalty}
              onChange={(event) => setPenalty(Number(event.target.value))}
            />
          </label>

          <button
            className="button button-primary full-width"
            type="button"
            onClick={runBenchmark}
            disabled={running}
          >
            {running ? <RefreshCw className="q2-spin" size={18} /> : <Play size={18} />}
            {running ? "Running exact and statevector solvers…" : "Run Q2 benchmark"}
          </button>

          <div className="q2-control-boundary">
            <ShieldCheck size={18} />
            <span>
              Exact enumeration is the reference. Simulated annealing transitions and
              QAOA shots share the same stochastic budget; parameter evaluations are
              disclosed separately.
            </span>
          </div>
        </article>

        <article className="panel q2-problem-card">
          <div className="q2-section-heading">
            <div>
              <span className="eyebrow">Frozen dataset</span>
              <h2>{normalizedProblem.id}</h2>
            </div>
            <Database size={23} />
          </div>

          <div className="q2-problem-metrics">
            <div>
              <span>Candidates</span>
              <strong>{normalizedProblem.candidates.length}</strong>
            </div>
            <div>
              <span>Sampling budget</span>
              <strong>{normalizedProblem.budget}</strong>
            </div>
            <div>
              <span>Source mode</span>
              <strong>{normalizedProblem.sourceMode}</strong>
            </div>
          </div>

          <div className="q2-candidate-list">
            {normalizedProblem.candidates.map((candidate) => (
              <div key={candidate.id}>
                <span>{candidate.id}</span>
                <div>
                  <strong>{candidate.zone}</strong>
                  <small>{candidate.reason}</small>
                </div>
                <b>{candidate.value.toFixed(3)}</b>
                <em>cost {candidate.cost}</em>
              </div>
            ))}
          </div>
        </article>
      </section>

      {message && (
        <section className="panel q2-message">
          {message.startsWith("Q2 failed") ? (
            <X size={18} />
          ) : (
            <CheckCircle2 size={18} />
          )}
          <span>{message}</span>
        </section>
      )}

      {result && (
        <>
          <section className="q2-summary-grid">
            <article className="panel">
              <Grid3X3 size={20} />
              <span>Binary variables</span>
              <strong>{result.qubo.variables.length}</strong>
              <small>
                {result.problem.candidates.length} selection +{" "}
                {result.qubo.slackWeights.length} slack
              </small>
            </article>
            <article className="panel">
              <Sigma size={20} />
              <span>QUBO terms</span>
              <strong>{result.qubo.quboTermCount}</strong>
              <small>Linear and quadratic terms</small>
            </article>
            <article className="panel">
              <FlaskConical size={20} />
              <span>Exact states checked</span>
              <strong>{result.solvers.exact.stateCount}</strong>
              <small>
                Ground state feasible:{" "}
                {result.solvers.exact.quboGroundStateFeasible ? "yes" : "no"}
              </small>
            </article>
            <article className="panel">
              <CircuitBoard size={20} />
              <span>QAOA qubits</span>
              <strong>{result.solvers.qaoa.circuit?.qubits ?? "—"}</strong>
              <small>Ideal browser statevector</small>
            </article>
          </section>

          <section className="q2-solver-grid">
            <SolverCard
              title="Exact enumeration"
              eyebrow="Reference optimum"
              icon={Scale}
              record={result.solvers.exact}
              exactUtility={exactUtility}
              tone="exact"
            />
            <SolverCard
              title="Greedy baseline"
              eyebrow="Classical deterministic"
              icon={BarChart3}
              record={result.solvers.greedy}
              exactUtility={exactUtility}
              tone="greedy"
            />
            <SolverCard
              title="Simulated annealing"
              eyebrow="Classical stochastic"
              icon={TestTube2}
              record={result.solvers.simulatedAnnealing}
              exactUtility={exactUtility}
              tone="annealing"
            />
            <SolverCard
              title="QAOA p=1"
              eyebrow="Ideal quantum simulator"
              icon={Atom}
              record={result.solvers.qaoa}
              exactUtility={exactUtility}
              tone="qaoa"
            />
          </section>

          <section className="q2-layout">
            <article className="panel q2-audit-card">
              <div className="q2-section-heading">
                <div>
                  <span className="eyebrow">Matched-budget audit</span>
                  <h2>Comparison controls</h2>
                </div>
                <ShieldCheck size={23} />
              </div>
              <div className="q2-audit-list">
                <div>
                  <span>SA transitions</span>
                  <strong>
                    {result.matchedBudgetAudit.simulatedAnnealingTransitions}
                  </strong>
                </div>
                <div>
                  <span>QAOA shots</span>
                  <strong>{result.matchedBudgetAudit.qaoaMeasurementShots}</strong>
                </div>
                <div>
                  <span>QAOA parameter evaluations</span>
                  <strong>
                    {result.matchedBudgetAudit.qaoaParameterEvaluations}
                  </strong>
                </div>
                <div>
                  <span>Quantum hardware</span>
                  <strong>No</strong>
                </div>
                <div>
                  <span>Quantum advantage claimed</span>
                  <strong>No</strong>
                </div>
                <div>
                  <span>Human review</span>
                  <strong>Required</strong>
                </div>
              </div>
              <p>{result.matchedBudgetAudit.disclosure}</p>
            </article>

            <article className="panel q2-histogram-card">
              <div className="q2-section-heading">
                <div>
                  <span className="eyebrow">QAOA measurement preview</span>
                  <h2>Top sampled states</h2>
                </div>
                <Atom size={23} />
              </div>
              <div className="q2-histogram">
                {topHistogram.slice(0, 8).map((item) => (
                  <div key={item.state}>
                    <span>{item.bitstring}</span>
                    <div>
                      <i
                        style={{
                          width: `${Math.max(2, (item.count / maxCount) * 100)}%`,
                        }}
                      />
                    </div>
                    <strong>{item.count}</strong>
                    <Badge tone={item.feasible ? "green" : "red"}>
                      {item.feasible ? "feasible" : "violates"}
                    </Badge>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <QuboMatrix result={result} />

          <section className="panel q2-export-panel">
            <div>
              <span className="eyebrow">Evidence package</span>
              <h2>Register and export Q2</h2>
              <p>
                The Q1 record keeps the classical optimum, QAOA circuit estimates,
                dataset and QUBO hashes, matched-budget disclosure, claim controls, and
                pending human review.
              </p>
            </div>
            <div>
              <button className="button button-primary" type="button" onClick={registerResult}>
                <Save size={17} />
                Register completed Q2
              </button>
              <button className="button button-secondary" type="button" onClick={exportJson}>
                <Download size={17} />
                Benchmark JSON
              </button>
              <button className="button button-secondary" type="button" onClick={exportSolverCsv}>
                <Download size={17} />
                Solver CSV
              </button>
              <button className="button button-secondary" type="button" onClick={exportQuboCsv}>
                <Download size={17} />
                QUBO CSV
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
