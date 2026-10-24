const PRIVATE_PAGES = ["predict.html", "result.html", "history.html"];
const INPUT_LABELS = [
  ["nitrogen", "Nitrogen (N)", "kg/ha"],
  ["phosphorus", "Phosphorus (P)", "kg/ha"],
  ["potassium", "Potassium (K)", "kg/ha"],
  ["temperature", "Temperature", "°C"],
  ["humidity", "Humidity", "%"],
  ["ph", "Soil pH", ""],
  ["rainfall", "Rainfall", "mm"]
];

function currentPage() {
  return location.pathname.split("/").pop() || "index.html";
}

async function apiRequest(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (options.method && options.method !== "GET") {
    const csrfResponse = await fetch("/api/csrf");
    const csrf = await csrfResponse.json();
    if (!csrfResponse.ok) throw new Error(csrf.error || "Could not prepare a secure request.");
    headers["X-CSRF-Token"] = csrf.csrf_token;
  }

  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "The request could not be completed.");
  return data;
}

function showMessage(element, text, type = "error") {
  if (!element) return;
  element.className = `login-message ${type}`;
  element.textContent = text;
}

function setLoading(button, loading, label) {
  if (!button) return;
  if (loading) {
    button.dataset.originalText = button.textContent;
    button.disabled = true;
    button.textContent = label;
  } else {
    button.disabled = false;
    button.textContent = button.dataset.originalText || button.textContent;
  }
}

async function logout() {
  try {
    await apiRequest("/api/logout", { method: "POST", body: "{}" });
    location.href = "login.html";
  } catch (error) {
    window.alert(error.message);
  }
}

function setupAuthUI(user) {
  const button = document.querySelector("#authButton");
  const badge = document.querySelector("#userBadge");
  if (button) {
    button.textContent = user ? "Logout" : "Login";
    button.onclick = user ? logout : () => { location.href = "login.html"; };
  }
  if (badge) {
    badge.textContent = user ? `👤 ${user.name || user.email}` : "";
    badge.classList.toggle("show", !!user);
  }
}

function setupAuthForms(user) {
  const loginForm = document.querySelector("#loginForm");
  const registerForm = document.querySelector("#registerForm");
  const loginPanel = document.querySelector("#loginPanel");
  const registerPanel = document.querySelector("#registerPanel");
  const showRegister = document.querySelector("#showRegister");
  const showLogin = document.querySelector("#showLogin");

  if (user && currentPage() === "login.html") {
    location.href = "predict.html";
    return;
  }

  if (showRegister) showRegister.addEventListener("click", () => {
    loginPanel.hidden = true;
    registerPanel.hidden = false;
  });
  if (showLogin) showLogin.addEventListener("click", () => {
    registerPanel.hidden = true;
    loginPanel.hidden = false;
  });

  if (loginForm) loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.querySelector("#loginMessage");
    const button = loginForm.querySelector('button[type="submit"]');
    setLoading(button, true, "Logging in...");
    try {
      await apiRequest("/api/login", {
        method: "POST",
        body: JSON.stringify({
          email: loginForm.elements.email.value.trim(),
          password: loginForm.elements.password.value
        })
      });
      showMessage(message, "Login successful. Redirecting...", "success");
      location.href = "predict.html";
    } catch (error) {
      showMessage(message, error.message);
    } finally {
      setLoading(button, false);
    }
  });

  if (registerForm) registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.querySelector("#registerMessage");
    const button = registerForm.querySelector('button[type="submit"]');
    setLoading(button, true, "Creating account...");
    try {
      const email = registerForm.elements.email.value.trim();
      await apiRequest("/api/register", {
        method: "POST",
        body: JSON.stringify({
          name: registerForm.elements.name.value.trim(),
          email,
          password: registerForm.elements.password.value
        })
      });
      registerForm.reset();
      registerPanel.hidden = true;
      loginPanel.hidden = false;
      document.querySelector("#loginForm").elements.email.value = email;
      showMessage(document.querySelector("#loginMessage"), "Account created. Please log in.", "success");
    } catch (error) {
      showMessage(message, error.message);
    } finally {
      setLoading(button, false);
    }
  });
}

function setupPrediction() {
  const form = document.querySelector("#predictionForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    let message = document.querySelector("#predictionMessage");
    if (!message) {
      message = document.createElement("div");
      message.className = "login-message";
      message.id = "predictionMessage";
      form.append(message);
    }

    const formValues = new FormData(form);
    const values = {
      nitrogen: formValues.get("n"),
      phosphorus: formValues.get("p"),
      potassium: formValues.get("k"),
      temperature: formValues.get("temperature"),
      humidity: formValues.get("humidity"),
      ph: formValues.get("ph"),
      rainfall: formValues.get("rainfall")
    };

    setLoading(button, true, "Running crop model...");
    try {
      await apiRequest("/api/predict", { method: "POST", body: JSON.stringify(values) });
      location.href = "result.html";
    } catch (error) {
      showMessage(message, error.message);
    } finally {
      setLoading(button, false);
    }
  });
}

function renderInputs(container, inputs) {
  container.replaceChildren();
  for (const [key, label, unit] of INPUT_LABELS) {
    const row = document.createElement("div");
    const name = document.createElement("span");
    const value = document.createElement("strong");
    row.className = "data-row";
    name.textContent = label;
    value.textContent = `${inputs[key]}${unit ? ` ${unit}` : ""}`;
    row.append(name, value);
    container.append(row);
  }
}

async function setupResult() {
  const target = document.querySelector("[data-result]");
  if (!target) return;
  try {
    const result = await apiRequest("/api/predictions/latest");
    document.querySelector("[data-crop]").textContent = result.predicted_crop;
    document.querySelector("[data-reason]").textContent =
      "Top recommendations from the trained model. Model probabilities are estimates, not guarantees.";
    const recommendationList = document.querySelector("[data-recommendations]");
    recommendationList.replaceChildren();
    result.recommendations.forEach((recommendation, index) => {
      const row = document.createElement("div");
      const crop = document.createElement("span");
      const probability = document.createElement("strong");
      row.className = "data-row";
      crop.textContent = `${index + 1}. ${recommendation.crop}`;
      probability.textContent = `${recommendation.probability_percent}% model probability`;
      row.append(crop, probability);
      recommendationList.append(row);
    });
    renderInputs(document.querySelector("[data-inputs]"), result);
  } catch (error) {
    target.replaceChildren();
    const card = document.createElement("section");
    const heading = document.createElement("h2");
    const message = document.createElement("p");
    const link = document.createElement("a");
    card.className = "card";
    heading.textContent = "No prediction available";
    message.className = "result-text";
    message.textContent = error.message;
    link.className = "primary-btn";
    link.href = "predict.html";
    link.textContent = "Go to Prediction";
    card.append(heading, message, link);
    target.append(card);
  }
}

async function setupHistory() {
  const table = document.querySelector("[data-history]");
  if (!table) return;
  try {
    const response = await apiRequest("/api/history");
    table.replaceChildren();
    if (!response.predictions.length) {
      const row = table.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 8;
      cell.className = "history-empty";
      cell.textContent = "No prediction history yet. Submit a prediction to get started.";
      return;
    }

    response.predictions.forEach((record, index) => {
      const row = table.insertRow();
      const cells = [
        index + 1,
        new Date(`${record.created_at}Z`).toLocaleString(),
        record.nitrogen,
        record.phosphorus,
        record.potassium,
        record.temperature,
        record.humidity,
        record.predicted_crop
      ];
      cells.forEach((value) => {
        const cell = row.insertCell();
        cell.textContent = value;
      });
    });
  } catch (error) {
    table.replaceChildren();
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 8;
    cell.className = "history-empty";
    cell.textContent = `Unable to load history: ${error.message}`;
  }
}

async function initialize() {
  let user = null;
  try {
    const response = await apiRequest("/api/session");
    user = response.user;
  } catch (error) {
    console.error("Could not check the login session:", error);
  }

  setupAuthUI(user);
  if (PRIVATE_PAGES.includes(currentPage()) && !user) {
    location.href = "login.html";
    return;
  }
  setupAuthForms(user);
  setupPrediction();
  await Promise.all([setupResult(), setupHistory()]);
}

document.addEventListener("DOMContentLoaded", initialize);
