const API_BASE = import.meta.env.VITE_AGROQ_API_BASE || "";

async function requestJson(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }

  return response.json();
}

export async function loadBackendSnapshot() {
  try {
    const [health, exported] = await Promise.all([
      requestJson("/api/health"),
      requestJson("/api/export/all.json"),
    ]);
    return {
      connected: true,
      health,
      exported,
      error: null,
    };
  } catch (error) {
    return {
      connected: false,
      health: null,
      exported: null,
      error: error instanceof Error ? error.message : "Backend unavailable",
    };
  }
}
