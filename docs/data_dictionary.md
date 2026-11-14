# Data Dictionary

**Dataset:** `data/sample/synthetic_diabetes_2019.csv`. **SYNTHETIC.** Generated to follow the expected Diabetes Dataset 2019 schema.
Column names are unverified against the real dataset. Verify them before any real-data use.

Rows: 1,250. Predictors: 17. Duplicate rows: 0. Missing values: 0.
SHA-256: `52e3475fe260e1b7de3b43e2a58b40f9d2a7196f69121a46707ba5a619432d54`

## Target
| Column | Values | Positive class | Notes |
|---|---|---|---|
| `Diabetic` | Yes / No | Yes (encoded 1) | Synthetic label from a probabilistic latent-risk generator. Not a clinical outcome. |

## Predictors
Entry limits are data-entry sanity checks, not clinical thresholds. "Observed in training data" shows
the range in the synthetic training set; values outside it are accepted with a warning.

| Column | Meaning | Type | Allowed values | Observed in training data |
|---|---|---|---|---|
| `Age` | Age (years) | integer | 18 to 100 (entry limits) | 18 to 80 |
| `Gender` | Gender | category | Female, Male | all listed values |
| `Family_Diabetes` | Family history of diabetes | category | No, Yes | all listed values |
| `highBP` | High blood pressure | category | No, Yes | all listed values |
| `PhysicallyActive` | Physical activity per day | category | less than half an hour, more than half an hour, none, one hour or more | all listed values |
| `BMI` | BMI (kg/m²) | number | 10 to 70 (entry limits) | 15 to 42 |
| `Smoking` | Smoking | category | No, Yes | all listed values |
| `Alcohol` | Alcohol use | category | No, Yes | all listed values |
| `Sleep` | Sleep (hours) | number | 0 to 24 (entry limits) | 3 to 10 |
| `SoundSleep` | Sound sleep (hours) | number | 0 to 24 (entry limits) | 1.3 to 10 |
| `RegularMedicine` | Regular medication | category | No, Yes | all listed values |
| `JunkFood` | Junk food intake | category | Never, Occasionally, Often | all listed values |
| `Stress` | Stress level | category | Always, Not at all, Sometimes, Very often | all listed values |
| `BPLevel` | Blood-pressure level | category | high, low, normal | all listed values |
| `Pregnancies` | Pregnancies | integer | 0 to 20 (entry limits) | 0 to 6 |
| `Pdiabetes` | Prediabetes | category | No, Yes | all listed values |
| `UriationFreq` | Urination frequency | category | Not much, Quite often | all listed values |

## Batch upload format
- First column `Region` (required, text, up to 64 characters). Labels are supplied by the user.
- Then the 17 predictors above, named exactly as shown.
- Extra columns are ignored and reported. The target column is not required.
- Encoding: UTF-8 (a byte-order mark is accepted). Size up to 5 MB and 10,000 rows.

## Derived fields in outputs
| Field | Where | Meaning |
|---|---|---|
| `Probability` | Processed results | Model-estimated probability of the positive class (0 to 1), rounded to 3 decimals. Not calibrated. |
| `Flagged` | Processed results | Yes if probability ≥ decision threshold (0.5). |
| `At-risk %` | Regional summary | Flagged ÷ valid records in the region × 100. Blank when no valid records. |
| `Small sample` | Regional summary | True when a region has fewer than 30 valid records. |
