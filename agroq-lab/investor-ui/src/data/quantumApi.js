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

export async function listQuantumResearchOperations() {
  return quantumApi("/api/quantum/operations");
}

export async function createQuantumResearchOperation(payload) {
  return quantumApi("/api/quantum/operations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function ensureQuantumRunOperation(runId) {
  return quantumApi(
    `/api/quantum/runs/${encodeURIComponent(runId)}/operation`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export async function getQuantumResearchOperation(operationId) {
  return quantumApi(
    `/api/quantum/operations/${encodeURIComponent(operationId)}`,
  );
}

export async function attachQuantumRunToOperation(operationId, runId) {
  return quantumApi(
    `/api/quantum/operations/${encodeURIComponent(operationId)}/attach-run`,
    {
      method: "POST",
      body: JSON.stringify({ run_id: runId }),
    },
  );
}

export async function assignQuantumResearchOperation(operationId, payload) {
  return quantumApi(
    `/api/quantum/operations/${encodeURIComponent(operationId)}/assign`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function transitionQuantumResearchOperation(
  operationId,
  payload,
) {
  return quantumApi(
    `/api/quantum/operations/${encodeURIComponent(operationId)}/transition`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function updateQuantumReleaseChecklist(
  operationId,
  manual,
) {
  return quantumApi(
    `/api/quantum/operations/${encodeURIComponent(operationId)}/checklist`,
    {
      method: "POST",
      body: JSON.stringify({ manual }),
    },
  );
}

export async function downloadQuantumEvidenceBundle(operationId) {
  const response = await fetch(
    `/api/quantum/operations/${encodeURIComponent(operationId)}/evidence.zip`,
    { credentials: "same-origin" },
  );
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(
      payload.error || `Evidence bundle request failed (${response.status}).`,
    );
    error.status = response.status;
    throw error;
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  return {
    blob,
    filename: match?.[1] || `${operationId.toLowerCase()}-evidence.zip`,
    sha256: response.headers.get("X-AgroQ-SHA256"),
    bundleId: response.headers.get("X-AgroQ-Bundle-ID"),
  };
}

export async function getReleaseReadiness() {
  return quantumApi("/api/release/readiness");
}

export async function createReleaseReadinessBackup() {
  return quantumApi("/api/release/readiness/backup", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function controlledBetaSummary() {
  return quantumApi("/api/beta/operations/summary");
}

export async function createStagingCandidate(payload) {
  return quantumApi("/api/beta/staging-candidates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getStagingCandidate(candidateId) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}`,
  );
}

export async function updateStagingDeployment(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/deployment`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function recordStagingAcceptanceCheck(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/checks`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function createStagingPersistenceSentinel(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/sentinels`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function observeStagingPersistenceSentinel(
  candidateId,
  sentinelId,
  payload,
) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(
      candidateId,
    )}/sentinels/${encodeURIComponent(sentinelId)}/observe`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function decideStagingCandidate(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/decision`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function syncControlledBetaContacts() {
  return quantumApi("/api/beta/contacts/sync", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function createControlledBetaContact(payload) {
  return quantumApi("/api/beta/contacts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateControlledBetaContact(contactId, payload) {
  return quantumApi(`/api/beta/contacts/${encodeURIComponent(contactId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function createControlledBetaInterview(payload) {
  return quantumApi("/api/beta/interviews", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createPilotDiscoveryRecord(payload) {
  return quantumApi("/api/beta/pilots", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewPilotDiscoveryRecord(pilotId, payload) {
  return quantumApi(`/api/beta/pilots/${encodeURIComponent(pilotId)}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createControlledBetaClaim(payload) {
  return quantumApi("/api/beta/claims", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewControlledBetaClaim(claimId, payload) {
  return quantumApi(`/api/beta/claims/${encodeURIComponent(claimId)}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewAccessRequest(requestId, status) {
  return quantumApi(
    `/api/beta/access-requests/${encodeURIComponent(requestId)}/review`,
    {
      method: "POST",
      body: JSON.stringify({ status }),
    },
  );
}

export async function reviewBetaReservation(reservationId, status) {
  return quantumApi(
    `/api/beta/reservations/${encodeURIComponent(reservationId)}/review`,
    {
      method: "POST",
      body: JSON.stringify({ status }),
    },
  );
}

export async function updateControlledBetaEvidence(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/evidence`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function createControlledBetaYcUpdate(candidateId, payload) {
  return quantumApi(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/yc-update`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function updateControlledBetaInvitationPolicy(payload) {
  return quantumApi("/api/beta/invitation-policy", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function downloadControlledBetaEvidence(candidateId) {
  const response = await fetch(
    `/api/beta/staging-candidates/${encodeURIComponent(candidateId)}/evidence.zip`,
    { credentials: "same-origin" },
  );
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(
      payload.error || `Controlled-beta export failed (${response.status}).`,
    );
    error.status = response.status;
    throw error;
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  return {
    blob,
    filename:
      match?.[1] || `${candidateId.toLowerCase()}-controlled-beta-evidence.zip`,
    sha256: response.headers.get("X-AgroQ-SHA256"),
    exportId: response.headers.get("X-AgroQ-Export-ID"),
  };
}

export async function pilotOperationsSummary() {
  return quantumApi("/api/pilots/operations/summary");
}

export async function createPilotEnrollment(payload) {
  return quantumApi("/api/pilots/enrollments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPilotEnrollment(enrollmentId) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}`,
  );
}

export async function updatePilotOnboarding(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/onboarding`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function recordPilotAcknowledgment(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(
      enrollmentId,
    )}/acknowledgments`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function activatePilotEnrollment(enrollmentId, reason) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/activate`,
    { method: "POST", body: JSON.stringify({ reason }) },
  );
}

export async function submitPilotFeedback(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/feedback`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function submitPilotIncident(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/incidents`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function updatePilotIncident(incidentId, payload) {
  return quantumApi(
    `/api/pilots/incidents/${encodeURIComponent(incidentId)}/events`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function recordPilotMetric(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/metrics`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function decidePilotExit(enrollmentId, payload) {
  return quantumApi(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/decision`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function downloadPilotEvidence(enrollmentId) {
  const response = await fetch(
    `/api/pilots/enrollments/${encodeURIComponent(enrollmentId)}/evidence.zip`,
    { credentials: "same-origin" },
  );
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(
      payload.error || `Pilot evidence export failed (${response.status}).`,
    );
    error.status = response.status;
    throw error;
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  return {
    blob,
    filename: match?.[1] || `${enrollmentId.toLowerCase()}-q20-q22-evidence.zip`,
    sha256: response.headers.get("X-AgroQ-SHA256"),
    exportId: response.headers.get("X-AgroQ-Export-ID"),
  };
}
