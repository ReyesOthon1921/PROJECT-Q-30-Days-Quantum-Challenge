import assert from "node:assert/strict";
import {
  runQ3Irrigation,
  runQ4Graph,
} from "../src/data/quantumOptimizationSuite.js";
import {
  runQ5QuantumKernel,
  runQ6QuantumReservoir,
  runQ7AmplitudeEstimation,
} from "../src/data/quantumLearningSuite.js";
import {
  initialCryptoInventory,
  runQ8QuantumSensing,
  runQ9QuantumChemistry,
  runQ10PostQuantumSecurity,
} from "../src/data/quantumFrontierSuite.js";

const q3 = await runQ3Irrigation({
  seed: 301,
  sampleBudget: 512,
  gridSize: 7,
});
assert.equal(q3.sequence, "Q3");
assert.ok(q3.qubo.maxResidual < 1e-8);
assert.equal(q3.solvers.exact.best.feasible, true);
assert.equal(q3.solvers.simulatedAnnealing.best.feasible, true);
assert.equal(q3.solvers.qaoa.supported, true);
assert.equal(q3.controls.advantageClaim, false);

const q4 = await runQ4Graph({
  seed: 301,
  sampleBudget: 512,
  gridSize: 7,
});
assert.equal(q4.sequence, "Q4");
assert.ok(q4.maxCut.qubo.maxResidual < 1e-8);
assert.ok(q4.sensorPlacement.qubo.maxResidual < 1e-8);
assert.equal(q4.maxCut.exact.best.feasible, true);
assert.equal(q4.sensorPlacement.exact.best.feasible, true);

const q5 = await runQ5QuantumKernel({ seed: 301 });
assert.equal(q5.sequence, "Q5");
assert.ok(q5.classical.metrics.accuracy >= 0 && q5.classical.metrics.accuracy <= 1);
assert.ok(q5.quantum.metrics.accuracy >= 0 && q5.quantum.metrics.accuracy <= 1);
assert.equal(q5.quantum.qubits, 2);

const q6 = await runQ6QuantumReservoir({ seed: 301 });
assert.equal(q6.sequence, "Q6");
assert.ok(Number.isFinite(q6.methods.persistence.metrics.rmse));
assert.ok(Number.isFinite(q6.methods.classicalReservoir.metrics.rmse));
assert.ok(Number.isFinite(q6.methods.quantumReservoir.metrics.rmse));
assert.equal(q6.methods.quantumReservoir.qubits, 2);

const q7 = await runQ7AmplitudeEstimation({
  seed: 301,
  trueProbability: 0.18,
  shotsPerCircuit: 64,
});
assert.equal(q7.sequence, "Q7");
assert.ok(q7.monteCarlo.estimate >= 0 && q7.monteCarlo.estimate <= 1);
assert.ok(
  q7.maximumLikelihoodAmplitudeEstimation.estimate >= 0 &&
    q7.maximumLikelihoodAmplitudeEstimation.estimate <= 1,
);
assert.equal(q7.controls.speedupClaim, false);

const q8 = await runQ8QuantumSensing({
  seed: 301,
  fieldMicroTesla: 18,
  temperatureC: 28,
});
assert.equal(q8.sequence, "Q8");
assert.ok(q8.plantMagnetism.snr > 0);
assert.ok(Number.isFinite(q8.nvOdMr.estimate.fieldMicroTesla));
assert.equal(q8.controls.hardwareConnected, false);

const q9 = await runQ9QuantumChemistry();
assert.equal(q9.sequence, "Q9");
assert.ok(q9.vqe.absoluteError < 0.001);
assert.equal(q9.controls.chemistryGradeClaim, false);

const q10 = await runQ10PostQuantumSecurity(initialCryptoInventory);
assert.equal(q10.sequence, "Q10");
assert.equal(q10.standards.length, 3);
assert.ok(q10.readiness.percent >= 0 && q10.readiness.percent <= 100);
assert.equal(q10.controls.cryptographicImplementationIncluded, false);

console.log("Q3-Q10 self-test passed.");
console.log(
  JSON.stringify(
    {
      q3ExactObjective: q3.solvers.exact.best.objective,
      q4CutWeight: q4.maxCut.exact.best.cutWeight,
      q4SensorCoverage: q4.sensorPlacement.exact.best.coverageValue,
      q5ClassicalAccuracy: q5.classical.metrics.accuracy,
      q5QuantumAccuracy: q5.quantum.metrics.accuracy,
      q6ClassicalReservoirRmse: q6.methods.classicalReservoir.metrics.rmse,
      q6QuantumReservoirRmse: q6.methods.quantumReservoir.metrics.rmse,
      q7MonteCarloError: q7.monteCarlo.absoluteError,
      q7MlaeError: q7.maximumLikelihoodAmplitudeEstimation.absoluteError,
      q8PlantSnr: q8.plantMagnetism.snr,
      q9VqeError: q9.vqe.absoluteError,
      q10Readiness: q10.readiness.percent,
    },
    null,
    2,
  ),
);
