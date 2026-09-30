// All communication with the ML backend lives here.
// Request  (POST /predict): {N,P,K,temperature,humidity,ph,rainfall}  (numbers)
// Response (JSON)         : {"crop": "rice"}
const API = {
  async predict(data) {
    if (CONFIG.USE_MOCK) return mockPredict(data);
    const res = await fetch(CONFIG.API_BASE_URL + CONFIG.PREDICT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Server error (" + res.status + ")");
    const out = await res.json();
    return out.crop;
  }
};

// Temporary demo logic so the site works before the model is ready.
function mockPredict(d) {
  return new Promise(resolve => {
    let crop = "Wheat";
    if (d.rainfall >= 180 && d.humidity >= 75) crop = "Rice";
    else if (d.rainfall >= 120 && d.temperature <= 29 && d.N >= 60) crop = "Maize";
    else if (d.temperature >= 24 && d.rainfall < 150 && d.ph >= 6) crop = "Cotton";
    setTimeout(() => resolve(crop), 600);
  });
}
