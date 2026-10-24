"""Train and save the best crop classifier using the project training notebook."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "Crop_recommendation.csv"
MODEL_PATH = ROOT / "crop_model.pkl"
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
REQUIRED_COLUMNS = FEATURE_COLUMNS + ["label"]


def train_model():
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Training dataset not found: {DATASET_PATH}. Place Crop_recommendation.csv in the project root."
        )

    crop = pd.read_csv(DATASET_PATH)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in crop.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required notebook columns: {', '.join(missing_columns)}")
    if crop[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Dataset contains missing values in training feature or label columns.")

    X = crop[FEATURE_COLUMNS]
    y = crop["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    # Keep the estimators and preprocessing identical to the training notebook.
    models = {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, random_state=42)),
        ]),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
        ),
        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            ("model", SVC(probability=True, random_state=42)),
        ]),
    }

    trained_models = {}
    accuracies = {}
    for name, estimator in models.items():
        estimator.fit(X_train, y_train)
        accuracies[name] = float(accuracy_score(y_test, estimator.predict(X_test)))
        trained_models[name] = estimator

    best_model_name = max(accuracies, key=accuracies.get)
    best_model = trained_models[best_model_name]
    bundle = {
        "model": best_model,
        "model_name": best_model_name,
        "feature_columns": FEATURE_COLUMNS,
        "classes": best_model.classes_.tolist(),
        "test_accuracy": accuracies[best_model_name],
        "test_accuracies": accuracies,
        "training_split": {
            "test_size": 0.20,
            "random_state": 42,
            "stratify": True,
        },
    }
    joblib.dump(bundle, MODEL_PATH)

    print("Test accuracy comparison:")
    for name, accuracy in sorted(accuracies.items(), key=lambda item: item[1], reverse=True):
        print(f"  {name}: {accuracy * 100:.2f}%")
    print(f"Selected: {best_model_name} ({accuracies[best_model_name] * 100:.2f}%)")
    print(f"Saved fitted model to: {MODEL_PATH}")
    return bundle


if __name__ == "__main__":
    train_model()
