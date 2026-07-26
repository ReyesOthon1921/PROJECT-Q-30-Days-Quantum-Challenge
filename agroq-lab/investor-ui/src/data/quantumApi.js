const LOCAL_STORAGE_KEY = "agroq-quantum-experiment-registry-v1";

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    const error = new Error(
      payload.error || `Quantum backend request failed (${response.status}).`,
    );
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

export async function quantumApi(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  return parseResponse(response);
}

export function readLocalQuantumExperiments() {
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeLocalQuantumExperiment(record) {
  const current = readLocalQuantumExperiments();
  const updated = [
    record,
    ...current.filter(
      (item) =>
        (item.experimentId || item.experiment_id) !==
        (record.experimentId || record.experiment_id),
    ),
  ];
  window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export async function persistQuantumExperiment(record) {
  try {
    const payload = await quantumApi("/api/quantum/experiments", {
      method: "POST",
      body: JSON.stringify(record),
    });
    writeLocalQuantumExperiment(record);
    return {
      persistent: true,
      experiment: payload.experiment,
      message: `${payload.experiment.experiment_id} saved to the AgroQ database.`,
    };
  } catch (error) {
    writeLocalQuantumExperiment(record);
    if (error.status === 401) {
      return {
        persistent: false,
        authenticationRequired: true,
        message:
          "Saved in this browser only. Sign in to AgroQ, then register again for persistent database storage.",
      };
    }
    if (error.status === 403) {
      return {
        persistent: false,
        permissionRequired: true,
        message:
          "Saved in this browser only. Persistent registration requires an administrator or researcher account.",
      };
    }
    return {
      persistent: false,
      error,
      message:
        "Saved in this browser only because the persistent quantum backend was unavailable.",
    };
  }
}

export async function listPersistentQuantumExperiments() {
  return quantumApi("/api/quantum/experiments");
}

export async function listQuantumDatasets() {
  return quantumApi("/api/quantum/datasets");
}

export async function freezeQuantumDataset(payload) {
  return quantumApi("/api/quantum/datasets/freeze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runPersistentQuantumExperiment(
  experimentId,
  configuration = {},
) {
  return quantumApi(
    `/api/quantum/experiments/${encodeURIComponent(experimentId)}/runs`,
    {
      method: "POST",
      body: JSON.stringify({
        configuration,
        run_budget: {
          solution_samples: configuration.run_budget || 2048,
          matched_across_solvers: true,
        },
      }),
    },
  );
}

export async function reviewPersistentQuantumRun(runId, decision, notes) {
  return quantumApi(
    `/api/quantum/runs/${encodeURIComponent(runId)}/review`,
    {
      method: "POST",
      body: JSON.stringify({ decision, notes }),
    },
  );
}

export async function quantumBackendHealth() {
  return quantumApi("/api/quantum/health");
}

export async function attachQuantumDataset(experimentId, datasetId) {
  return quantumApi(
    `/api/quantum/experiments/${encodeURIComponent(
      experimentId,
    )}/dataset`,
    {
      method: "POST",
      body: JSON.stringify({ dataset_id: datasetId }),
    },
  );
}

export async function quantumValidationSummary() {
  return quantumApi("/api/quantum/validation/summary");
}

export async function verifyPersistentQuantumDataset(datasetId) {
  return quantumApi(
    `/api/quantum/datasets/${encodeURIComponent(datasetId)}/verify`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function validatePersistentQuantumRun(
  runId,
  includeReplay = false,
) {
  return quantumApi(
    `/api/quantum/runs/${encodeURIComponent(runId)}/validate`,
    {
      method: "POST",
      body: JSON.stringify({ include_replay: includeReplay }),
    },
  );
}

export async function replayPersistentQuantumRun(runId) {
  return quantumApi(
    `/api/quantum/runs/${encodeURIComponent(runId)}/replay`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function quantumRunValidationHistory(runId) {
  return quantumApi(
    `/api/quantum/runs/${encodeURIComponent(runId)}/validation`,
  );
}
