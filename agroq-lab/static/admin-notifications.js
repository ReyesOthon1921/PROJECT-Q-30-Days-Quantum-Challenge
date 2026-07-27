(() => {
  const state = {
    csrfToken: "",
    preferences: null,
  };

  const list = document.getElementById("notification-list");
  const unreadCount = document.getElementById("unread-count");
  const form = document.getElementById("notification-preferences");
  const pushResult = document.getElementById("push-result");
  const saveStatus = document.getElementById("settings-save-status");

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  }

  function setCheckbox(name, value) {
    const field = form.elements.namedItem(name);
    if (field && !field.disabled) {
      field.checked = Boolean(value);
    }
  }

  function loadPreferences(preferences) {
    if (!preferences) return;
    state.preferences = preferences;
    [
      "in_app_enabled",
      "email_enabled",
      "webhook_enabled",
      "web_push_enabled",
      "notify_login_success",
      "notify_login_failure",
      "notify_access_changes",
      "notify_password_changes",
    ].forEach((name) => setCheckbox(name, preferences[name]));
    form.elements.email_address.value = preferences.email_address || "";
    form.elements.digest_mode.value = preferences.digest_mode || "immediate";
  }

  function renderNotifications(items) {
    if (!items.length) {
      list.innerHTML = "<p>No administrator notifications yet.</p>";
      return;
    }
    list.innerHTML = items
      .map((item) => {
        const unread = !item.acknowledged_at;
        return `
          <article class="notification-card ${unread ? "unread" : ""} ${escapeHtml(item.severity)}">
            <span class="notification-card__badge">${escapeHtml(item.severity)}</span>
            <div>
              <h3>${escapeHtml(item.title)}</h3>
              <p>${escapeHtml(item.body)}</p>
              <small>
                ${escapeHtml(item.event_type)} ·
                ${escapeHtml(new Date(item.created_at).toLocaleString())}
              </small>
            </div>
            ${
              unread
                ? `<button class="button button--secondary" type="button" data-ack="${escapeHtml(item.event_id)}">Reviewed</button>`
                : "<span>Reviewed</span>"
            }
          </article>
        `;
      })
      .join("");
  }

  async function refresh() {
    try {
      const data = await api("/api/admin/notifications?limit=100");
      state.csrfToken = data.csrf_token;
      unreadCount.textContent = data.unread_count;
      loadPreferences(data.preferences);
      renderNotifications(data.notifications);
    } catch (error) {
      list.innerHTML = `<p>Notification center error: ${escapeHtml(error.message)}</p>`;
    }
  }

  list.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-ack]");
    if (!button) return;
    button.disabled = true;
    try {
      await api(
        `/api/admin/notifications/${encodeURIComponent(button.dataset.ack)}/acknowledge`,
        {
          method: "POST",
          headers: { "X-CSRF-Token": state.csrfToken },
          body: "{}",
        },
      );
      await refresh();
    } catch (error) {
      alert(error.message);
      button.disabled = false;
    }
  });

  document.getElementById("acknowledge-all").addEventListener("click", async () => {
    await api("/api/admin/notifications/acknowledge-all", {
      method: "POST",
      headers: { "X-CSRF-Token": state.csrfToken },
      body: "{}",
    });
    await refresh();
  });

  document.getElementById("test-notification").addEventListener("click", async () => {
    await api("/api/admin/notifications/test", {
      method: "POST",
      headers: { "X-CSRF-Token": state.csrfToken },
      body: "{}",
    });
    await refresh();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    saveStatus.textContent = "Saving…";
    const data = new FormData(form);
    const payload = {
      in_app_enabled: data.has("in_app_enabled"),
      email_enabled: data.has("email_enabled"),
      email_address: data.get("email_address"),
      webhook_enabled: data.has("webhook_enabled"),
      web_push_enabled: data.has("web_push_enabled"),
      notify_login_success: data.has("notify_login_success"),
      notify_login_failure: data.has("notify_login_failure"),
      notify_access_changes: data.has("notify_access_changes"),
      notify_password_changes: data.has("notify_password_changes"),
      digest_mode: data.get("digest_mode"),
    };
    try {
      await api("/api/admin/notification-preferences", {
        method: "POST",
        headers: { "X-CSRF-Token": state.csrfToken },
        body: JSON.stringify(payload),
      });
      saveStatus.textContent = "Settings saved.";
      await refresh();
    } catch (error) {
      saveStatus.textContent = `Could not save: ${error.message}`;
    }
  });

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replaceAll("-", "+")
      .replaceAll("_", "/");
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
  }

  document.getElementById("enable-phone-push").addEventListener("click", async () => {
    pushResult.textContent = "";
    try {
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        throw new Error("This browser does not support Web Push.");
      }
      const config = await api("/api/admin/push/config");
      if (!config.configured) {
        throw new Error(
          "Web Push keys are not configured yet. In-app notifications still work.",
        );
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw new Error("Notification permission was not granted.");
      }
      const registration = await navigator.serviceWorker.register(
        "/admin-notification-sw.js",
        { scope: "/" },
      );
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(config.public_key),
      });
      const payload = subscription.toJSON();
      payload.device_label = navigator.userAgent.includes("Mobile")
        ? "Administrator mobile device"
        : "Administrator browser";
      await api("/api/admin/push/subscribe", {
        method: "POST",
        headers: { "X-CSRF-Token": state.csrfToken },
        body: JSON.stringify(payload),
      });
      pushResult.textContent =
        "This device is subscribed. Background delivery starts after HTTPS and the notification worker are configured.";
    } catch (error) {
      pushResult.textContent = error.message;
    }
  });

  refresh();
  window.setInterval(refresh, 15000);
})();
