// ===== ONLY FILE YOU CHANGE TO CONNECT THE ML MODEL =====
const CONFIG = {
  USE_MOCK: true,                        // true = demo rules in browser, false = call real backend
  API_BASE_URL: "http://127.0.0.1:8000", // your FastAPI / Flask server
  PREDICT_ENDPOINT: "/predict"           // POST
};
