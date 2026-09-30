const $ = s => document.querySelector(s);
const KEYS = { history: "cr_history", last: "cr_last", user: "cr_user" };
const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const save = (k, v) => localStorage.setItem(k, JSON.stringify(v));
const ICONS = { rice: "🌾", maize: "🌽", cotton: "☁️", wheat: "🌾" };

// id must match the key your ML model / backend expects
const FIELDS = [
  ["N", "Nitrogen (N) (kg/ha)", "90", 0, 140], ["P", "Phosphorus (P) (kg/ha)", "42", 5, 145],
  ["K", "Potassium (K) (kg/ha)", "90", 5, 205], ["humidity", "Humidity (%)", "82", 10, 100],
  ["temperature", "Temperature (°C)", "25.6", 8, 44], ["rainfall", "Rainfall (mm)", "202", 20, 300],
  ["ph", "pH Value", "6.5", 3, 10]
];

function layout() {
  const page = document.body.dataset.page, user = load(KEYS.user, null);
  const links = [["index", "Home"], ["predict", "Predict"], ["history", "History"], ["about", "About"]];
  $("#site-header").innerHTML = `<header><div class="wrap"><a class="brand" href="index.html">🌱 CropRecommend</a>
    <nav>${links.map(([f, t]) => `<a href="${f}.html" class="${f === page ? "active" : ""}">${t}</a>`).join("")}</nav>
    ${user ? `<button class="btn" id="logout">Logout</button>` : `<a class="btn" href="login.html">Login</a>`}</div></header>`;
  $("#site-footer").innerHTML = `<footer>“Empowering Farmers with AI”</footer>`;
  $("#logout")?.addEventListener("click", () => { localStorage.removeItem(KEYS.user); location.href = "index.html"; });
}

function initPredict() {
  $("#fields").innerHTML = FIELDS.map(([id, lab, ph]) =>
    `<div><label for="${id}">${lab}</label><input id="${id}" type="number" step="any" placeholder="e.g. ${ph}"><div class="err" id="e-${id}"></div></div>`).join("");
  $("#form").addEventListener("submit", async e => {
    e.preventDefault(); $("#msg").textContent = "";
    const data = {}; let ok = true;
    FIELDS.forEach(([id, , , min, max]) => {
      const v = parseFloat($("#" + id).value), bad = isNaN(v) || v < min || v > max;
      $("#e-" + id).textContent = bad ? `Enter a value from ${min} to ${max}` : "";
      if (bad) ok = false; else data[id] = v;
    });
    if (!ok) return;
    const btn = $("#go"); btn.disabled = true; btn.textContent = "Predicting…";
    try {
      const crop = await API.predict(data);
      const rec = { ...data, crop, date: new Date().toISOString() };
      save(KEYS.last, rec);
      save(KEYS.history, [rec, ...load(KEYS.history, [])].slice(0, 100));
      location.href = "result.html";
    } catch (err) {
      $("#msg").textContent = "Could not get a prediction: " + err.message + ". Check that the server is running.";
      btn.disabled = false; btn.textContent = "Predict Crop";
    }
  });
}

function initResult() {
  const r = load(KEYS.last, null);
  if (!r) { location.href = "predict.html"; return; }
  $("#crop").textContent = r.crop;
  $("#crop-ico").textContent = ICONS[r.crop.toLowerCase()] || "🌱";
  $("#summary").innerHTML = FIELDS.map(([id, lab]) => `<tr><th>${lab}</th><td>${r[id]}</td></tr>`).join("");
}

function initHistory() {
  const rows = load(KEYS.history, []);
  $("#rows").innerHTML = rows.length ? rows.map((r, i) => `<tr><td>${i + 1}</td>
    <td>${new Date(r.date).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</td>
    <td>${r.N}</td><td>${r.P}</td><td>${r.K}</td><td>${r.temperature}</td><td>${r.humidity}</td>
    <td>${r.ph}</td><td>${r.rainfall}</td><td><b>${r.crop}</b></td></tr>`).join("")
    : `<tr><td colspan="10">No predictions yet. <a href="predict.html"><u>Make your first prediction</u></a>.</td></tr>`;
}

function initLogin() {
  document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach(x => x.classList.toggle("on", x === b));
    $("#auth-btn").textContent = b.dataset.m;
  }));
  $("#auth").addEventListener("submit", e => {
    e.preventDefault();
    // DEMO ONLY: replace with real backend auth (POST /login, /register)
    save(KEYS.user, { email: $("#email").value });
    location.href = "predict.html";
  });
}

layout();
({ predict: initPredict, result: initResult, history: initHistory, login: initLogin })[document.body.dataset.page]?.();
