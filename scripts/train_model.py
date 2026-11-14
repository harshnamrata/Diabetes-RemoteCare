"""
Train, compare, and evaluate diabetes-risk classifiers on the SYNTHETIC dataset.

Protocol:
  1. Validate the dataset.
  2. 80/20 stratified train/test split (fixed random_state).
  3. Each candidate is one sklearn Pipeline (ColumnTransformer + classifier),
     so scaling and encoding are fitted on training folds only.
  4. Model selection uses 5-fold stratified CV on the TRAINING set only,
     ranked by recall, tie-broken by F1.
  5. The test set is scored once per model, for reporting only.
"""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample" / "synthetic_diabetes_2019.csv"
MODEL_DIR = ROOT / "models"
MODEL_VERSION = "1.0.0-synthetic"
SEED = 42
TARGET = "Diabetic"
POS_LABEL = "Yes"
NUMERIC = ["Age", "BMI", "Sleep", "SoundSleep", "Pregnancies"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(df: pd.DataFrame) -> dict:
    if TARGET not in df.columns:
        raise ValueError("target column missing")
    if not set(df[TARGET].unique()) <= {"Yes", "No"}:
        raise ValueError("unexpected target labels")
    if int(df.isna().sum().sum()) != 0:
        raise ValueError("missing values present")
    return {"rows": len(df), "predictors": df.shape[1] - 1,
            "duplicate_rows": int(df.duplicated().sum()), "missing_values": 0}


def build_pipeline(clf, categorical):
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])
    return Pipeline([("pre", pre), ("clf", clf)])


def metrics(y_true, y_pred, y_score) -> dict:
    # labels=[0, 1] gives ravel() order tn, fp, fn, tp
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=1, zero_division=0),
        "f1": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_score),
        "false_positive_rate": fp / (fp + tn) if (fp + tn) else 0.0,
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)},
    }


def main():
    df = pd.read_csv(DATA_PATH)
    data_info = validate(df)
    X = df.drop(columns=[TARGET])
    y = (df[TARGET] == POS_LABEL).astype(int)  # Yes -> 1 (positive), No -> 0
    categorical = [c for c in X.columns if c not in NUMERIC]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)

    candidates = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=SEED),
        "DecisionTree": DecisionTreeClassifier(
            max_depth=5, class_weight="balanced", random_state=SEED),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=SEED, n_jobs=-1),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_results, test_results, fitted = {}, {}, {}
    for name, clf in candidates.items():
        pipe = build_pipeline(clf, categorical)
        cvr = cross_validate(pipe, X_train, y_train, cv=cv,
                             scoring=["recall", "precision", "f1", "roc_auc"], n_jobs=-1)
        cv_results[name] = {k.replace("test_", ""): float(v.mean())
                            for k, v in cvr.items() if k.startswith("test_")}
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
        y_pred = pipe.predict(X_test)
        y_score = pipe.predict_proba(X_test)[:, 1]
        test_results[name] = metrics(y_test, y_pred, y_score)

    # Selection uses TRAINING-set CV only: highest mean recall, tie-break F1.
    selected = max(cv_results, key=lambda n: (cv_results[n]["recall"], cv_results[n]["f1"]))
    final = fitted[selected]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final, MODEL_DIR / "remotecare_model.joblib")

    feature_schema = {
        "numeric": NUMERIC,
        "ranges": {c: [float(X[c].min()), float(X[c].max())] for c in NUMERIC},
        "categorical": {c: sorted(df[c].unique().tolist()) for c in categorical},
        "order": list(X.columns),
    }
    evaluation = {
        "selected_model": selected,
        "selection_criterion": "highest mean 5-fold CV recall on training set; tie-break F1",
        "cv_on_training_set": cv_results,
        "test_set_results": test_results,
        "test_set_size": int(len(y_test)),
        "train_set_size": int(len(y_train)),
    }
    metadata = {
        "project": "RemoteCare AI",
        "model_version": MODEL_VERSION,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected_model": selected,
        "dataset": {
            "file": "data/sample/synthetic_diabetes_2019.csv",
            "is_synthetic": True,
            "sha256": sha256(DATA_PATH),
            "schema_note": "Column names follow Diabetes Dataset 2019 as referenced in the PPT; "
                           "verify against the real file before real-data use.",
            **data_info,
        },
        "target": {"column": TARGET, "positive_class": POS_LABEL, "encoded_as": "1 = Yes, 0 = No",
                   "definition": "Synthetic label from a probabilistic latent-risk generator"},
        "feature_schema": feature_schema,
        "training_config": {"test_size": 0.2, "stratified": True, "seed": SEED,
                            "cv_folds": 5, "decision_threshold": 0.5,
                            "class_weight": "balanced",
                            "preprocessing": "StandardScaler (numeric), OneHotEncoder "
                                             "(categorical), fit on training data only"},
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__},
        "security_note": "Only load model artifacts from trusted sources; joblib/pickle can execute code.",
    }
    metadata["artifact"] = {
        "file": "models/remotecare_model.joblib",
        "sha256": sha256(MODEL_DIR / "remotecare_model.joblib"),
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    (MODEL_DIR / "evaluation_report.json").write_text(json.dumps(evaluation, indent=2))

    print(f"Selected: {selected}\n")
    print("CV on training set (mean):")
    for n, r in cv_results.items():
        print(f"  {n:20s} recall={r['recall']:.3f} precision={r['precision']:.3f} "
              f"f1={r['f1']:.3f} roc_auc={r['roc_auc']:.3f}")
    print("\nTest set (reported once):")
    for n, r in test_results.items():
        cm = r["confusion_matrix"]
        print(f"  {n:20s} acc={r['accuracy']:.3f} prec={r['precision']:.3f} "
              f"rec={r['recall']:.3f} f1={r['f1']:.3f} auc={r['roc_auc']:.3f} "
              f"FPR={r['false_positive_rate']:.3f} "
              f"CM(tp={cm['tp']},fp={cm['fp']},tn={cm['tn']},fn={cm['fn']})")


if __name__ == "__main__":
    main()
