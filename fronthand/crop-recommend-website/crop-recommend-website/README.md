# CropRecommend Website

Pages: index (Home), predict, result, history, about, login (optional).
Open `index.html` in a browser. No install needed.

## Structure
- `css/style.css`  – all styling
- `js/config.js`   – settings (mock on/off, backend URL)  <-- edit this
- `js/api.js`      – the ONLY place that talks to the ML backend
- `js/main.js`     – page logic (form, result, history, login)
- `assets/`        – put images here

## Connect your ML model later
1. Build a backend (FastAPI or Flask) with `POST /predict`.
2. Request JSON:  `{"N":90,"P":42,"K":90,"temperature":25.6,"humidity":82,"ph":6.5,"rainfall":202}`
3. Response JSON: `{"crop":"rice"}`
4. In `js/config.js` set `USE_MOCK: false` and your `API_BASE_URL`.
5. Enable CORS on the backend (FastAPI: CORSMiddleware).

Now, history is saved in browser localStorage. Later, save it in MySQL
and load it in `initHistory()` from a `GET /history` endpoint.
Login is a demo only; replace it with real authentication.
