"""Flask API and page server for the CropRecommend application."""

import hmac
import joblib
import math
import logging
import numpy as np
import os
import pandas as pd
import re
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, current_app, g, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
INPUT_TO_FEATURE = {
    "nitrogen": "N",
    "phosphorus": "P",
    "potassium": "K",
    "temperature": "temperature",
    "humidity": "humidity",
    "ph": "ph",
    "rainfall": "rainfall",
}
PAGE_NAMES = {"index.html", "login.html", "predict.html", "result.html", "history.html", "about.html"}
INPUT_LIMITS = {
    "nitrogen": (0, 1000),
    "phosphorus": (0, 1000),
    "potassium": (0, 1000),
    "temperature": (-20, 60),
    "humidity": (0, 100),
    "ph": (0, 14),
    "rainfall": (0, 5000),
}
DEMO_CROPS = ("Rice", "Maize", "Wheat", "Sugarcane", "Groundnut")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_db():
    """Open a request-scoped SQLite connection with foreign keys enabled."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db(app):
    """Create tables on startup; this is also safe to run repeatedly."""
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(app.config["DATABASE"])
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                nitrogen REAL NOT NULL,
                phosphorus REAL NOT NULL,
                potassium REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                ph REAL NOT NULL,
                rainfall REAL NOT NULL,
                predicted_crop TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS predictions_user_created
                ON predictions(user_id, created_at DESC, id DESC);
            """
        )
        connection.commit()
    finally:
        connection.close()


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def require_csrf():
    expected = session.get("csrf_token")
    received = request.headers.get("X-CSRF-Token", "")
    if not expected or not hmac.compare_digest(expected, received):
        return jsonify(error="Your request could not be verified. Refresh the page and try again."), 400
    return None


def require_auth():
    user = get_current_user()
    if user is None:
        return None, (jsonify(error="Please log in to continue."), 401)
    return user, None


def prediction_record(row):
    return {
        "id": row["id"],
        "nitrogen": row["nitrogen"],
        "phosphorus": row["phosphorus"],
        "potassium": row["potassium"],
        "temperature": row["temperature"],
        "humidity": row["humidity"],
        "ph": row["ph"],
        "rainfall": row["rainfall"],
        "predicted_crop": row["predicted_crop"],
        "created_at": row["created_at"],
        "mode": "ml",
    }


def load_model_bundle(model_path):
    """Load and validate the trained model once while the Flask app starts."""
    try:
        bundle = joblib.load(model_path)
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Trained crop model not found at {model_path}. Run train_model.py first."
        ) from error
    except Exception as error:
        raise RuntimeError(
            f"Could not load the trained crop model at {model_path}; check its Python package versions."
        ) from error

    required_keys = {"model", "model_name", "feature_columns", "classes", "test_accuracy"}
    if not isinstance(bundle, dict) or not required_keys.issubset(bundle):
        raise RuntimeError(f"Model artifact at {model_path} has an unsupported format. Run train_model.py.")
    if bundle["feature_columns"] != FEATURE_COLUMNS:
        raise RuntimeError(
            f"Model artifact feature order does not match the API at {model_path}. Run train_model.py."
        )
    model = bundle["model"]
    if not callable(getattr(model, "predict", None)) or not callable(getattr(model, "predict_proba", None)):
        raise RuntimeError(f"Model artifact at {model_path} must support predict() and predict_proba().")
    return bundle


def recommend_top_3(bundle, inputs):
    """Return the notebook's top-three predict_proba recommendations."""
    feature_values = [inputs[key] for key in INPUT_TO_FEATURE]
    input_frame = pd.DataFrame([feature_values], columns=FEATURE_COLUMNS)
    model = bundle["model"]
    probabilities = model.predict_proba(input_frame)[0]
    classes = model.classes_
    top_indices = np.argsort(probabilities)[::-1][:3]
    return [
        {
            "crop": str(classes[index]),
            "probability_percent": round(float(probabilities[index]) * 100, 2),
        }
        for index in top_indices
    ]


def validate_prediction(data):
    if not isinstance(data, dict):
        return None, "Send prediction inputs as a JSON object."
    validated = {}
    for field, (minimum, maximum) in INPUT_LIMITS.items():
        value = data.get(field)
        if isinstance(value, bool):
            return None, f"{field} must be a number between {minimum} and {maximum}."
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None, f"{field} must be a number between {minimum} and {maximum}."
        if not math.isfinite(number) or not minimum <= number <= maximum:
            return None, f"{field} must be a number between {minimum} and {maximum}."
        validated[field] = number
    return validated, None


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.environ.get("CROP_RECOMMEND_DATABASE", str(ROOT / "instance" / "croprecommend.sqlite3")),
        MODEL_PATH=str(ROOT / "crop_model.pkl"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "").lower() == "true",
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    app.config["MODEL_BUNDLE"] = app.config.get("MODEL_BUNDLE") or load_model_bundle(app.config["MODEL_PATH"])
    init_db(app)
    app.teardown_appcontext(close_db)

    @app.get("/")
    def home():
        return send_from_directory(ROOT, "index.html")

    @app.get("/<page>")
    def pages(page):
        if page not in PAGE_NAMES:
            return jsonify(error="Page not found."), 404
        return send_from_directory(ROOT, page)

    @app.get("/css/<path:filename>")
    def styles(filename):
        return send_from_directory(ROOT / "css", filename)

    @app.get("/js/<path:filename>")
    def scripts(filename):
        return send_from_directory(ROOT / "js", filename)

    @app.get("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(ROOT / "assets", filename)

    @app.get("/api/csrf")
    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return jsonify(csrf_token=session["csrf_token"])

    @app.get("/api/session")
    def session_status():
        user = get_current_user()
        return jsonify(user={"id": user["id"], "name": user["name"], "email": user["email"]} if user else None)

    @app.post("/api/register")
    def register():
        csrf_error = require_csrf()
        if csrf_error:
            return csrf_error
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send registration details as a JSON object."), 400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            return jsonify(error="Name is required and must be at most 100 characters."), 400
        if not isinstance(email, str) or len(email.strip()) > 254 or not EMAIL_PATTERN.fullmatch(email.strip()):
            return jsonify(error="Enter a valid email address."), 400
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            return jsonify(error="Password must be between 8 and 128 characters."), 400

        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return jsonify(error="An account with that email already exists."), 409
        return jsonify(message="Account created. Please log in.", user_id=cursor.lastrowid), 201

    @app.post("/api/login")
    def login():
        csrf_error = require_csrf()
        if csrf_error:
            return csrf_error
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send login details as a JSON object."), 400
        email = data.get("email")
        password = data.get("password")
        if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email.strip()):
            return jsonify(error="Enter a valid email address and password."), 400
        if not isinstance(password, str) or not password:
            return jsonify(error="Enter a valid email address and password."), 400
        user = get_db().execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip(),),
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify(error="Email or password is incorrect."), 401

        session.clear()
        session["user_id"] = user["id"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        return jsonify(user={"id": user["id"], "name": user["name"], "email": user["email"]})

    @app.post("/api/logout")
    def logout():
        csrf_error = require_csrf()
        if csrf_error:
            return csrf_error
        session.clear()
        return jsonify(message="You have been logged out.")

    @app.post("/api/predict")
    def predict():
        user, auth_error = require_auth()
        if auth_error:
            return auth_error
        csrf_error = require_csrf()
        if csrf_error:
            return csrf_error
        inputs, error = validate_prediction(request.get_json(silent=True))
        if error:
            return jsonify(error=error), 400

        recommendations = recommend_top_3(current_app.config["MODEL_BUNDLE"], inputs)
        crop = recommendations[0]["crop"]
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO predictions (
                user_id, nitrogen, phosphorus, potassium, temperature,
                humidity, ph, rainfall, predicted_crop
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], inputs["nitrogen"], inputs["phosphorus"], inputs["potassium"],
                inputs["temperature"], inputs["humidity"], inputs["ph"], inputs["rainfall"], crop,
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM predictions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        result = prediction_record(row)
        result["recommendations"] = recommendations
        return jsonify(prediction=result), 201

    @app.get("/api/predictions/latest")
    def latest_prediction():
        user, auth_error = require_auth()
        if auth_error:
            return auth_error
        row = get_db().execute(
            "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (user["id"],),
        ).fetchone()
        if row is None:
            return jsonify(error="No saved prediction yet. Submit a prediction first."), 404
        result = prediction_record(row)
        inputs = {
            "nitrogen": row["nitrogen"],
            "phosphorus": row["phosphorus"],
            "potassium": row["potassium"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "ph": row["ph"],
            "rainfall": row["rainfall"],
        }
        result["recommendations"] = recommend_top_3(current_app.config["MODEL_BUNDLE"], inputs)
        return jsonify(result)

    @app.get("/api/history")
    def history():
        user, auth_error = require_auth()
        if auth_error:
            return auth_error
        rows = get_db().execute(
            "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (user["id"],),
        ).fetchall()
        return jsonify(predictions=[prediction_record(row) for row in rows])

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            if request.path.startswith("/api/"):
                return jsonify(error=error.description), error.code
            return error
        app.logger.exception("Unhandled request error")
        if request.path.startswith("/api/"):
            return jsonify(error="An internal server error occurred."), 500
        return "An internal server error occurred.", 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true")
