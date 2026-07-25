export function seededRandom(seedInput = 301) {
  let seed = Math.trunc(Number(seedInput) || 301) >>> 0;
  return () => {
    seed += 0x6d2b79f5;
    let value = seed;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export function normalRandom(random) {
  const u1 = Math.max(1e-12, random());
  const u2 = random();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

export function bitsFromState(state, size) {
  return Array.from({ length: size }, (_, index) => (state >> index) & 1);
}

export function stateFromBits(bits) {
  return bits.reduce(
    (state, bit, index) => state | ((bit ? 1 : 0) << index),
    0,
  );
}

export function evaluateQubo(bits, qubo) {
  let energy = qubo.constant || 0;
  for (let left = 0; left < bits.length; left += 1) {
    if (!bits[left]) continue;
    energy += qubo.matrix[left][left];
    for (let right = left + 1; right < bits.length; right += 1) {
      if (bits[right]) energy += qubo.matrix[left][right];
    }
  }
  return energy;
}

export function fitQuadraticEnergy(variableNames, objective) {
  const size = variableNames.length;
  const zero = Array(size).fill(0);
  const constant = objective(zero);
  const matrix = Array.from({ length: size }, () => Array(size).fill(0));

  for (let index = 0; index < size; index += 1) {
    const bits = Array(size).fill(0);
    bits[index] = 1;
    matrix[index][index] = objective(bits) - constant;
  }

  for (let left = 0; left < size; left += 1) {
    for (let right = left + 1; right < size; right += 1) {
      const bits = Array(size).fill(0);
      bits[left] = 1;
      bits[right] = 1;
      matrix[left][right] =
        objective(bits) -
        constant -
        matrix[left][left] -
        matrix[right][right];
    }
  }

  let maxResidual = 0;
  for (let state = 0; state < 2 ** size; state += 1) {
    const bits = bitsFromState(state, size);
    maxResidual = Math.max(
      maxResidual,
      Math.abs(objective(bits) - evaluateQubo(bits, { matrix, constant })),
    );
  }

  return {
    variableNames,
    matrix,
    constant,
    maxResidual,
    termCount:
      matrix.reduce(
        (count, row, left) =>
          count +
          row.reduce(
            (inner, value, right) =>
              inner + (right >= left && Math.abs(value) > 1e-12 ? 1 : 0),
            0,
          ),
        0,
      ),
  };
}

export function exactSolveQubo(qubo, decode = null) {
  const size = qubo.variableNames.length;
  let best = null;

  for (let state = 0; state < 2 ** size; state += 1) {
    const bits = bitsFromState(state, size);
    const energy = evaluateQubo(bits, qubo);
    const decoded = decode ? decode(bits) : {};
    const record = { bits, state, energy, ...decoded };
    if (
      (!best || energy < best.energy - 1e-12) &&
      decoded.feasible !== false
    ) {
      best = record;
    }
  }

  return {
    algorithm: "Exact enumeration",
    objectiveEvaluations: 2 ** size,
    best,
  };
}

export function simulatedAnnealingQubo(
  qubo,
  decode = null,
  options = {},
) {
  const size = qubo.variableNames.length;
  const steps = Math.max(64, Math.round(Number(options.steps) || 2048));
  const seed = Math.round(Number(options.seed) || 301);
  const random = seededRandom(seed);
  const startTemperature = Number(options.startTemperature) || 4;
  const endTemperature = Number(options.endTemperature) || 0.01;
  let bits = Array.from({ length: size }, () => (random() < 0.5 ? 1 : 0));
  let current = {
    bits,
    energy: evaluateQubo(bits, qubo),
    ...(decode ? decode(bits) : {}),
  };
  let best = current.feasible === false ? null : current;
  let accepted = 0;

  for (let step = 0; step < steps; step += 1) {
    const progress = steps === 1 ? 1 : step / (steps - 1);
    const temperature =
      startTemperature * (endTemperature / startTemperature) ** progress;
    const nextBits = [...bits];
    const flip = Math.floor(random() * size);
    nextBits[flip] = nextBits[flip] ? 0 : 1;
    const next = {
      bits: nextBits,
      energy: evaluateQubo(nextBits, qubo),
      ...(decode ? decode(nextBits) : {}),
    };
    const delta = next.energy - current.energy;

    if (delta <= 0 || random() < Math.exp(-delta / temperature)) {
      bits = nextBits;
      current = next;
      accepted += 1;
    }

    if (
      current.feasible !== false &&
      (!best || current.energy < best.energy - 1e-12)
    ) {
      best = current;
    }
  }

  return {
    algorithm: "Seeded simulated annealing",
    seed,
    steps,
    acceptedMoves: accepted,
    acceptanceRate: accepted / steps,
    objectiveEvaluations: steps + 1,
    best,
  };
}

function applyCostLayer(real, imaginary, energies, gamma) {
  for (let state = 0; state < real.length; state += 1) {
    const phase = -gamma * energies[state];
    const cosine = Math.cos(phase);
    const sine = Math.sin(phase);
    const oldReal = real[state];
    const oldImaginary = imaginary[state];
    real[state] = oldReal * cosine - oldImaginary * sine;
    imaginary[state] = oldReal * sine + oldImaginary * cosine;
  }
}

function applyMixerLayer(real, imaginary, qubits, beta) {
  const cosine = Math.cos(beta);
  const sine = Math.sin(beta);

  for (let qubit = 0; qubit < qubits; qubit += 1) {
    const mask = 1 << qubit;
    for (let state = 0; state < real.length; state += 1) {
      if (state & mask) continue;
      const paired = state | mask;
      const aReal = real[state];
      const aImaginary = imaginary[state];
      const bReal = real[paired];
      const bImaginary = imaginary[paired];

      real[state] = cosine * aReal + sine * bImaginary;
      imaginary[state] = cosine * aImaginary - sine * bReal;
      real[paired] = cosine * bReal + sine * aImaginary;
      imaginary[paired] = cosine * bImaginary - sine * aReal;
    }
  }
}

function statevectorProbabilities(energies, qubits, gamma, beta) {
  const size = energies.length;
  const amplitude = 1 / Math.sqrt(size);
  const real = new Float64Array(size);
  const imaginary = new Float64Array(size);
  real.fill(amplitude);
  applyCostLayer(real, imaginary, energies, gamma);
  applyMixerLayer(real, imaginary, qubits, beta);

  const probabilities = new Float64Array(size);
  for (let index = 0; index < size; index += 1) {
    probabilities[index] = real[index] ** 2 + imaginary[index] ** 2;
  }
  return probabilities;
}

function expectation(probabilities, values) {
  let total = 0;
  for (let index = 0; index < probabilities.length; index += 1) {
    total += probabilities[index] * values[index];
  }
  return total;
}

function cumulative(probabilities) {
  const output = new Float64Array(probabilities.length);
  let sum = 0;
  for (let index = 0; index < probabilities.length; index += 1) {
    sum += probabilities[index];
    output[index] = sum;
  }
  output[output.length - 1] = 1;
  return output;
}

function drawState(cdf, random) {
  const target = random();
  let left = 0;
  let right = cdf.length - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (target <= cdf[middle]) right = middle;
    else left = middle + 1;
  }
  return left;
}

export function qaoaP1Qubo(
  qubo,
  decode = null,
  options = {},
) {
  const qubits = qubo.variableNames.length;
  if (qubits > 12) {
    return {
      algorithm: "QAOA p=1 ideal statevector",
      supported: false,
      reason: "Browser suite limits statevector experiments to 12 qubits.",
      best: null,
    };
  }

  const stateCount = 2 ** qubits;
  const rawEnergies = Float64Array.from(
    { length: stateCount },
    (_, state) => evaluateQubo(bitsFromState(state, qubits), qubo),
  );
  const minimum = Math.min(...rawEnergies);
  const maximum = Math.max(...rawEnergies);
  const range = Math.max(1e-12, maximum - minimum);
  const energies = Float64Array.from(
    rawEnergies,
    (value) => (value - minimum) / range,
  );
  const gridSize = Math.max(
    5,
    Math.min(25, Math.round(Number(options.gridSize) || 11)),
  );
  let bestParameters = null;
  let bestProbabilities = null;

  for (let gammaIndex = 0; gammaIndex < gridSize; gammaIndex += 1) {
    const gamma = (2 * Math.PI * gammaIndex) / gridSize;
    for (let betaIndex = 0; betaIndex < gridSize; betaIndex += 1) {
      const beta = (Math.PI * betaIndex) / (2 * (gridSize - 1));
      const probabilities = statevectorProbabilities(
        energies,
        qubits,
        gamma,
        beta,
      );
      const score = expectation(probabilities, energies);
      if (!bestParameters || score < bestParameters.expectation) {
        bestParameters = { gamma, beta, expectation: score };
        bestProbabilities = probabilities;
      }
    }
  }

  const shots = Math.max(128, Math.round(Number(options.shots) || 2048));
  const seed = Math.round(Number(options.seed) || 301);
  const random = seededRandom(seed);
  const cdf = cumulative(bestProbabilities);
  const counts = new Map();

  for (let shot = 0; shot < shots; shot += 1) {
    const state = drawState(cdf, random);
    counts.set(state, (counts.get(state) || 0) + 1);
  }

  let best = null;
  const histogram = [...counts.entries()]
    .map(([state, count]) => {
      const bits = bitsFromState(state, qubits);
      const decoded = decode ? decode(bits) : {};
      const record = {
        state,
        bits,
        bitstring: bits.slice().reverse().join(""),
        count,
        probability: count / shots,
        energy: evaluateQubo(bits, qubo),
        ...decoded,
      };
      if (
        record.feasible !== false &&
        (!best || record.energy < best.energy - 1e-12)
      ) {
        best = record;
      }
      return record;
    })
    .sort((left, right) => right.count - left.count)
    .slice(0, 12);

  const nonzeroQuadratic = qubo.matrix.reduce(
    (count, row, left) =>
      count +
      row.reduce(
        (inner, value, right) =>
          inner +
          (right > left && Math.abs(value) > 1e-12 ? 1 : 0),
        0,
      ),
    0,
  );

  return {
    algorithm: "QAOA p=1 ideal statevector",
    supported: true,
    seed,
    shots,
    gridSize,
    parameterEvaluations: gridSize ** 2,
    gamma: bestParameters.gamma,
    beta: bestParameters.beta,
    normalizedExpectation: bestParameters.expectation,
    rawExpectation: expectation(bestProbabilities, rawEnergies),
    best,
    histogram,
    circuit: {
      qubits,
      ansatz: "QAOA p=1",
      estimatedDepth: 3 + nonzeroQuadratic * 2,
      estimatedTwoQubitGates: nonzeroQuadratic * 2,
      backend: "Browser ideal statevector",
      noiseModel: "None",
      estimateBoundary:
        "Counts are formulation-level estimates before device transpilation.",
    },
  };
}

export function solveLinearSystem(matrix, vector) {
  const size = vector.length;
  const augmented = matrix.map((row, index) => [...row, vector[index]]);

  for (let pivot = 0; pivot < size; pivot += 1) {
    let best = pivot;
    for (let row = pivot + 1; row < size; row += 1) {
      if (Math.abs(augmented[row][pivot]) > Math.abs(augmented[best][pivot])) {
        best = row;
      }
    }
    [augmented[pivot], augmented[best]] = [
      augmented[best],
      augmented[pivot],
    ];

    const divisor = augmented[pivot][pivot];
    if (Math.abs(divisor) < 1e-12) {
      throw new Error("Singular linear system.");
    }
    for (let column = pivot; column <= size; column += 1) {
      augmented[pivot][column] /= divisor;
    }

    for (let row = 0; row < size; row += 1) {
      if (row === pivot) continue;
      const factor = augmented[row][pivot];
      for (let column = pivot; column <= size; column += 1) {
        augmented[row][column] -= factor * augmented[pivot][column];
      }
    }
  }

  return augmented.map((row) => row[size]);
}

export function ridgeRegression(features, targets, lambda = 0.01) {
  const rows = features.length;
  const columns = features[0].length;
  const xtx = Array.from({ length: columns }, () => Array(columns).fill(0));
  const xty = Array(columns).fill(0);

  for (let row = 0; row < rows; row += 1) {
    for (let left = 0; left < columns; left += 1) {
      xty[left] += features[row][left] * targets[row];
      for (let right = 0; right < columns; right += 1) {
        xtx[left][right] += features[row][left] * features[row][right];
      }
    }
  }

  for (let index = 0; index < columns; index += 1) {
    xtx[index][index] += lambda;
  }

  return solveLinearSystem(xtx, xty);
}

export function predictLinear(features, weights) {
  return features.map((row) =>
    row.reduce((sum, value, index) => sum + value * weights[index], 0),
  );
}

export function regressionMetrics(actual, predicted) {
  const errors = actual.map((value, index) => predicted[index] - value);
  const mae =
    errors.reduce((sum, value) => sum + Math.abs(value), 0) / errors.length;
  const rmse = Math.sqrt(
    errors.reduce((sum, value) => sum + value ** 2, 0) / errors.length,
  );
  const mean = actual.reduce((sum, value) => sum + value, 0) / actual.length;
  const ssTotal = actual.reduce((sum, value) => sum + (value - mean) ** 2, 0);
  const ssResidual = errors.reduce((sum, value) => sum + value ** 2, 0);

  return {
    mae,
    rmse,
    r2: ssTotal === 0 ? 0 : 1 - ssResidual / ssTotal,
  };
}

export function classificationMetrics(actual, predicted) {
  let tp = 0;
  let tn = 0;
  let fp = 0;
  let fn = 0;
  actual.forEach((value, index) => {
    if (value === 1 && predicted[index] === 1) tp += 1;
    else if (value === 0 && predicted[index] === 0) tn += 1;
    else if (value === 0 && predicted[index] === 1) fp += 1;
    else fn += 1;
  });
  const accuracy = (tp + tn) / actual.length;
  const precision = tp + fp === 0 ? 0 : tp / (tp + fp);
  const recall = tp + fn === 0 ? 0 : tp / (tp + fn);
  const f1 =
    precision + recall === 0
      ? 0
      : (2 * precision * recall) / (precision + recall);
  return { accuracy, precision, recall, f1, tp, tn, fp, fn };
}

export function kernelRidgeClassifier(
  trainX,
  trainY,
  testX,
  kernel,
  lambda = 0.1,
) {
  const labels = trainY.map((value) => (value === 1 ? 1 : -1));
  const gram = trainX.map((left, row) =>
    trainX.map(
      (right, column) =>
        kernel(left, right) + (row === column ? lambda : 0),
    ),
  );
  const alpha = solveLinearSystem(gram, labels);
  const scores = testX.map((sample) =>
    trainX.reduce(
      (sum, trainSample, index) =>
        sum + alpha[index] * kernel(trainSample, sample),
      0,
    ),
  );
  return {
    scores,
    predictions: scores.map((score) => (score >= 0 ? 1 : 0)),
    alpha,
  };
}

export async function sha256(value) {
  const text =
    typeof value === "string" ? value : JSON.stringify(value);
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return `sha256:${Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")}`;
}

export function rowsToCsv(rows) {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    const text = String(value ?? "");
    return /[",\n]/.test(text)
      ? `"${text.replaceAll('"', '""')}"`
      : text;
  };
  return [
    headers.join(","),
    ...rows.map((row) =>
      headers.map((header) => escape(row[header])).join(","),
    ),
  ].join("\n");
}
