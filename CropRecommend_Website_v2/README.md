# CropRecommend Website

The existing HTML/CSS/JavaScript frontend is served by Flask. User authentication and per-user prediction history remain backed by the existing SQLite database. Crop predictions use the fitted scikit-learn classifier saved in `crop_model.pkl`.

## Train / update the model

The training data is `Crop_recommendation.csv` in this project root. `train_model.py` follows the training notebook: features `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`; target `label`; stratified 80/20 split with `random_state=42`; Logistic Regression + StandardScaler, Decision Tree, 300-tree Random Forest, and SVM + StandardScaler with probability enabled. It prints each test accuracy, chooses the best model, and saves the fitted estimator, class labels, feature order, and split metadata to `crop_model.pkl`. The test split is used for evaluation only and is not used to fit models.

```powershell
Set-Location "C:\Users\dhaka\OneDrive\Desktop\fronthand\New folder (2)\CropRecommend_Website_v2"
.\.venv\Scripts\Activate.ps1
python train_model.py
```

Run training again only when intentionally regenerating the model artifact. The Flask app loads the bundle once during application startup, using a path relative to `app.py`.

## Run on Windows PowerShell

```powershell
Set-Location "C:\Users\dhaka\OneDrive\Desktop\fronthand\New folder (2)\CropRecommend_Website_v2"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python train_model.py
$secret = py -c "import secrets; print(secrets.token_hex(32))"
setx FLASK_SECRET_KEY $secret
$env:FLASK_SECRET_KEY = $secret
python app.py
```

Open `http://127.0.0.1:5000/`. Flask serves all existing pages and static assets; Live Server is not needed. `setx` persists the generated secret for future PowerShell windows. For later runs, open a new window and do not generate a new key. For production, use a securely stored persistent `FLASK_SECRET_KEY`, serve over HTTPS, set `COOKIE_SECURE=true`, and keep debug mode disabled. The SQLite database is created automatically in `instance/croprecommend.sqlite3`; run `python init_db.py` only when explicitly needed.

If PowerShell blocks venv activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell session and activate again.

## Prediction API and model output

`POST /api/predict` validates all seven numeric inputs, predicts with the loaded model, and persists the highest-ranked crop for the authenticated user using the existing predictions table. The response retains `prediction.predicted_crop` and adds `prediction.recommendations`, a list of the top three crops and their `probability_percent` values from `predict_proba()`. The Result page displays these estimates; probabilities are model outputs, not guarantees of field performance.

`GET /api/predictions/latest` returns that user's most recent saved inputs and recomputed top-three predictions. `GET /api/history` remains scoped to the authenticated server-side session. State-changing requests use the session CSRF token. Passwords are hashed; email ownership is not verified.

The model requires compatible package versions. `requirements.txt` pins scikit-learn to the version used to create the artifact; regenerate `crop_model.pkl` with the current environment when intentionally changing that version.
