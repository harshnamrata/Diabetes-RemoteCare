"""Model performance: values come from models/evaluation_report.json, not hardcoded."""
import pandas as pd
import streamlit as st

from src.config import MODEL_NOTICE
from src.model_loader import ModelUnavailableError, load_evaluation
from src.ui_state import ensure_state

ensure_state()
st.title("Model Performance")
st.warning(MODEL_NOTICE)

try:
    ev = load_evaluation()
except ModelUnavailableError as exc:
    st.error(str(exc))
    st.stop()

selected = ev["selected_model"]
st.write(f"**Selected model:** {selected}. Selection criterion: {ev['selection_criterion']}.")
st.caption(f"Train set: {ev['train_set_size']:,} records. Test set: {ev['test_set_size']:,} records "
           "(stratified 80/20). The test set was scored once per model and not used for selection.")


def label(name: str) -> str:
    return f"{name} (selected)" if name == selected else name


st.subheader("Cross-validation on the training set (selection basis)")
cv_rows = {label(n): {"Recall": r["recall"], "Precision": r["precision"],
                      "F1": r["f1"], "ROC-AUC": r["roc_auc"]}
           for n, r in ev["cv_on_training_set"].items()}
st.dataframe(pd.DataFrame(cv_rows).T.round(3), width="stretch")

st.subheader("Held-out test set")
test_rows = {}
for n, r in ev["test_set_results"].items():
    cm = r["confusion_matrix"]
    test_rows[label(n)] = {"Accuracy": r["accuracy"], "Precision": r["precision"],
                           "Recall": r["recall"], "F1": r["f1"], "ROC-AUC": r["roc_auc"],
                           "False-positive rate": r["false_positive_rate"],
                           "TP": cm["tp"], "FP": cm["fp"], "TN": cm["tn"], "FN": cm["fn"]}
test_df = pd.DataFrame(test_rows).T
st.dataframe(test_df.round(3), width="stretch")

st.subheader("Recall and precision on the test set")
st.bar_chart(test_df[["Recall", "Precision"]])

st.subheader(f"Confusion matrix: {selected}")
cm = ev["test_set_results"][selected]["confusion_matrix"]
st.table(pd.DataFrame(
    [[cm["tp"], cm["fn"]], [cm["fp"], cm["tn"]]],
    index=["Actually Yes (positive)", "Actually No"],
    columns=["Predicted Yes", "Predicted No"]))

st.subheader("How to read these results")
st.markdown(
    "- **Recall** is the share of positive records the model flags. Missed positives (false "
    "negatives) are the main concern in screening, so recall is the primary selection criterion.\n"
    "- **Precision** is the share of flagged records that are truly positive. Low precision means "
    "more false alarms, which costs follow-up time.\n"
    "- **ROC-AUC** measures ranking quality across all thresholds, independent of the 0.5 cut-off.\n"
    "- Accuracy is less informative here because the positive class is the minority.\n"
    "- All figures come from synthetic data and show how the pipeline behaves, not how it would "
    "perform on real patients.")
