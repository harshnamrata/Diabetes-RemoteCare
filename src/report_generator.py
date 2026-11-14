"""Build a session report (Markdown). Contains model/dataset facts, evaluation, session
history and aggregated regional ranking. It contains no patient-level records."""
from __future__ import annotations

import math

import pandas as pd

from src.config import DISCLAIMER, MODEL_NOTICE
from src.history_service import HISTORY_COLUMNS, session_totals


def _cell(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    text = str(value)
    # Region names are user-supplied: neutralise characters that would break the table.
    text = text.replace("|", "/").replace("\n", " ").replace("\r", " ")
    for ch in "[]<>`":
        text = text.replace(ch, "")  # no links, images, or raw HTML from user text
    return text.strip()


def _table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def build_markdown_report(metadata: dict, evaluation: dict, history: list[dict],
                          last_batch: dict | None, generated_at: str) -> str:
    ds = metadata["dataset"]
    cfg = metadata["training_config"]
    selected = evaluation["selected_model"]
    out: list[str] = []

    out.append("# RemoteCare AI: Session Report")
    out.append(f"Generated (UTC): {generated_at}")
    out.append("")
    out.append(f"> **{MODEL_NOTICE}**")
    out.append(f"> {DISCLAIMER}")
    out.append("")

    out.append("## 1. Model and dataset")
    out.append(_table(["Item", "Value"], [
        ["Model version", metadata["model_version"]],
        ["Selected model", selected],
        ["Trained (UTC)", metadata["trained_at_utc"]],
        ["Training data", f"{ds['file']} (synthetic: {ds['is_synthetic']})"],
        ["Rows / predictors", f"{ds['rows']} / {ds['predictors']}"],
        ["Duplicate rows / missing values", f"{ds['duplicate_rows']} / {ds['missing_values']}"],
        ["Target (positive class)", f"{metadata['target']['column']} ({metadata['target']['positive_class']})"],
        ["Decision threshold", cfg["decision_threshold"]],
        ["Dataset SHA-256", ds["sha256"]],
        ["scikit-learn / Python", f"{metadata['environment']['sklearn']} / {metadata['environment']['python']}"],
    ]))
    out.append("")
    out.append(f"Schema note: {ds['schema_note']}")
    out.append("")

    out.append(f"## 2. Evaluation summary (test set, n = {evaluation['test_set_size']})")
    rows = []
    for name, r in evaluation["test_set_results"].items():
        cm = r["confusion_matrix"]
        rows.append([f"{name}{' (selected)' if name == selected else ''}",
                     f"{r['accuracy']:.3f}", f"{r['precision']:.3f}", f"{r['recall']:.3f}",
                     f"{r['f1']:.3f}", f"{r['roc_auc']:.3f}", f"{r['false_positive_rate']:.3f}",
                     f"{cm['tp']} / {cm['fp']} / {cm['tn']} / {cm['fn']}"])
    out.append(_table(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "FPR",
                       "TP / FP / TN / FN"], rows))
    out.append("")
    out.append(f"Selection criterion: {evaluation['selection_criterion']}.")
    out.append("")

    totals = session_totals(history)
    out.append("## 3. Session screening summary")
    out.append(f"- Screening operations: {totals['operations']}")
    out.append(f"- Completed operations: {totals['completed']}")
    out.append(f"- Records scored: {totals['records_scored']:,}")
    out.append(f"- Records flagged as higher risk: {totals['records_flagged']:,}")
    out.append("")

    out.append("## 4. Session history")
    if history:
        frame = pd.DataFrame(history, columns=HISTORY_COLUMNS)
        out.append(_table(HISTORY_COLUMNS, frame.values.tolist()))
    else:
        out.append("No screening operations were recorded this session.")
    out.append("")

    out.append("## 5. Regional ranking (latest batch)")
    if last_batch is None:
        out.append("No regional batch was processed this session.")
    else:
        s = last_batch["summary"]
        out.append(f"Batch processed (UTC): {last_batch['timestamp']}. "
                   f"Received {last_batch['received']:,}, scored {last_batch['scored']:,}, "
                   f"excluded {last_batch['excluded']:,}, flagged {last_batch['flagged']:,}.")
        out.append("")
        out.append(_table(list(s.columns), s.values.tolist()))
        out.append("")
        out.append("Counts are records the model flagged, not population prevalence. Regions "
                   "marked as small samples should be read with caution. Region labels are "
                   "as supplied in the uploaded file.")
    out.append("")

    out.append("## 6. Limitations")
    out.append("- Trained and evaluated on synthetic data; metrics do not describe real populations.")
    out.append("- Model probabilities are estimates and are not calibrated personal risks.")
    out.append("- Session history and this report are held only for the current session.")
    out.append("- Not validated for clinical use; not a diagnosis.")
    out.append("")
    return "\n".join(out)
