const queueKey = "agroqOfflineObservationQueueV2";

function newClientRequestId() {
  if (crypto.randomUUID) return `agroq-${crypto.randomUUID()}`;
  return `agroq-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getQueue() {
  try { return JSON.parse(localStorage.getItem(queueKey) || "[]"); }
  catch { return []; }
}

function setQueue(items) {
  localStorage.setItem(queueKey, JSON.stringify(items));
  updateQueueCount();
}

function updateQueueCount() {
  const el = document.getElementById("offline-queue-count");
  if (el) el.textContent = `Offline queue: ${getQueue().length}`;
}

function updateConnection() {
  const el = document.getElementById("connection-status");
  if (!el) return;
  const online = navigator.onLine;
  el.textContent = online ? "Gateway reachable" : "Offline — local queue active";
  el.dataset.online = online ? "true" : "false";
}

async function syncQueue() {
  const queue = getQueue();
  if (!queue.length) return;
  if (!navigator.onLine) {
    alert("The device is still offline. Entries remain safely queued in this browser.");
    return;
  }
  let remaining = queue;
  try {
    const response = await fetch("/api/sync/observations", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({items: queue})
    });
    if (response.ok) {
      const data = await response.json();
      const completed = new Set(data.results.filter((r) => ["applied", "resolved"].includes(r.status)).map((r) => r.client_request_id));
      remaining = queue.filter((item) => !completed.has(item.client_request_id));
    }
  } catch { remaining = queue; }
  setQueue(remaining);
  alert(remaining.length ? `${remaining.length} entries could not synchronize.` : "Offline observations synchronized.");
}

document.addEventListener("DOMContentLoaded", () => {
  updateConnection();
  updateQueueCount();

  const form = document.getElementById("observation-form");
  if (form) {
    form.addEventListener("submit", (event) => {
      if (navigator.onLine) return;
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form).entries());
      if (!data.observed_at) data.observed_at = new Date().toISOString();
      const queue = getQueue();
      queue.push({client_request_id: newClientRequestId(), queued_at: new Date().toISOString(), payload: data});
      setQueue(queue);
      form.reset();
      alert("Saved in the offline queue. Synchronize when the gateway is reachable.");
    });
  }

  const syncButton = document.getElementById("sync-offline");
  if (syncButton) syncButton.addEventListener("click", syncQueue);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/service-worker.js").catch(console.error);
  }
});

window.addEventListener("online", () => {
  updateConnection();
  syncQueue();
});
window.addEventListener("offline", updateConnection);
