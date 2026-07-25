import assert from "node:assert/strict";
import {
  buildQ2ExperimentRecord,
  buildSoilSamplingQubo,
  exactEnumerateQubo,
  greedySoilSampling,
  qaoaP1Statevector,
  referenceSoilSamplingProblem,
  runQ2Benchmark,
  simulatedAnnealingQubo,
} from "../src/data/q2SoilSamplingBenchmark.js";

const qubo = buildSoilSamplingQubo(referenceSoilSamplingProblem, {
  penalty: 6,
});

assert.equal(qubo.problem.candidates.length, 6);
assert.equal(qubo.variables.length, 9);
assert.ok(qubo.quboTermCount > 0);

const exact = exactEnumerateQubo(qubo);
const greedy = greedySoilSampling(qubo);
const annealing = simulatedAnnealingQubo(qubo, {
  steps: 512,
  seed: 301,
});
const qaoa = qaoaP1Statevector(qubo, {
  shots: 512,
  gridSize: 7,
  seed: 301,
});

assert.equal(exact.best.feasible, true);
assert.equal(exact.quboGroundStateFeasible, true);
assert.equal(greedy.best.feasible, true);
assert.equal(annealing.best.feasible, true);
assert.equal(qaoa.supported, true);
assert.equal(qaoa.best.feasible, true);
assert.ok(exact.best.utility + 1e-9 >= greedy.best.utility);
assert.ok(exact.best.utility + 1e-9 >= annealing.best.utility);
assert.ok(exact.best.utility + 1e-9 >= qaoa.best.utility);

const result = await runQ2Benchmark(referenceSoilSamplingProblem, {
  sharedSampleBudget: 512,
  gridSize: 7,
  seed: 301,
  penalty: 6,
});

assert.match(result.datasetHash, /^sha256:[0-9a-f]{64}$/);
assert.match(result.quboHash, /^sha256:[0-9a-f]{64}$/);
assert.equal(result.controls.quantumHardwareUsed, false);
assert.equal(result.controls.quantumAdvantageClaim, false);
assert.equal(
  result.matchedBudgetAudit.simulatedAnnealingTransitions,
  result.matchedBudgetAudit.qaoaMeasurementShots,
);

const registryRecord = buildQ2ExperimentRecord(result, "self-test");
assert.equal(registryRecord.sequence, "Q2");
assert.equal(registryRecord.status, "Simulation complete");
assert.equal(registryRecord.metrics.feasible, true);
assert.equal(registryRecord.claimControls.advantageClaim, false);
assert.equal(registryRecord.humanReview.required, true);

console.log("Q2 self-test passed.");
console.log(
  JSON.stringify(
    {
      variables: qubo.variables.length,
      terms: qubo.quboTermCount,
      exactUtility: exact.best.utility,
      greedyUtility: greedy.best.utility,
      annealingUtility: annealing.best.utility,
      qaoaUtility: qaoa.best.utility,
      qaoaQubits: qaoa.circuit.qubits,
      datasetHash: result.datasetHash,
      quboHash: result.quboHash,
    },
    null,
    2,
  ),
);
