# Model Card: RemoteCare AI Diabetes-Risk Classifier (v1.0.0-synthetic)

## Important
**This model was trained on SYNTHETIC data.** Its metrics describe the data generator and say nothing about diabetes in any real population. It is not clinically validated and must not be used to screen real patients.

## Intended use
Decision-support prototype for an academic minor project. Flags records for further assessment; it does not diagnose.

## Data
- File: `data/sample/synthetic_diabetes_2019.csv` (synthetic, sha256 `52e3475fe260e1b7...`)
- Rows: 1250; predictors: 17; duplicates: 0; missing: 0
- Target: `Diabetic` (positive = Yes, encoded 1)
- Positive class in training: 1000 train / 250 test records (stratified 80/20)

## Method
- Candidates: Logistic Regression, Decision Tree (max depth 5), Random Forest (300 trees); all `class_weight='balanced'`
- Single sklearn Pipeline per model: StandardScaler (numeric), OneHotEncoder (categorical), fitted on training data only
- Selection: highest mean 5-fold CV recall on training set; tie-break F1
- Test set scored once per model; decision threshold 0.5

## Results (synthetic test set, n=250)
| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | FPR | TP / FP / TN / FN |
|---|---|---|---|---|---|---|---|
| LogisticRegression (selected) | 0.660 | 0.406 | 0.621 | 0.491 | 0.709 | 0.326 | 41 / 60 / 124 / 25 |
| DecisionTree | 0.624 | 0.370 | 0.606 | 0.460 | 0.636 | 0.370 | 40 / 68 / 116 / 26 |
| RandomForest | 0.756 | 0.692 | 0.136 | 0.228 | 0.684 | 0.022 | 9 / 4 / 180 / 57 |

Selected model 5-fold CV on training set: recall 0.665, precision 0.425, F1 0.518, ROC-AUC 0.729.

## Interpretation
- The selected model catches about 62% of positive records in the test set, at the cost of a false-positive rate of 33%. Missed cases (FN = 25) are the priority concern for screening.
- Random Forest has the highest precision and lowest false-positive rate but misses most positives at this threshold. It is not selected because recall is the primary criterion.
- Results are modest (ROC-AUC about 0.71), which is expected for a synthetic generator with moderate signal.

## Limitations and risks
- Synthetic labels; no external validation.
- Feature names are unverified against the real Diabetes Dataset 2019.
- Threshold 0.5 is not calibrated for any clinical use.
- Probabilities are model estimates, not calibrated personal risk.
- Joblib artifacts can execute code when loaded; load only trusted files.

## Reproduce
`python scripts/train_model.py` (seed 42, sklearn 1.8.0, Python 3.12.3)
