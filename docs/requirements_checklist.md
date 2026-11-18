# Requirements Verification Checklist

Status key:
- **Done (tested)**: implemented and covered by automated tests.
- **Done (not browser-tested)**: implemented; only server and AppTest checks were run.
- **Partial**: implemented in part; the gap is stated.
- **Blocked**: needs an input or decision outside this build.
- **Not in scope**: deliberately excluded for the prototype, with the reason.

## Dataset and preparation
| Requirement | Status | Evidence / note |
|---|---|---|
| Inspect dataset, verify target and features | Done (synthetic) | `data_dictionary.md`; real file not provided |
| Confirm real Diabetes Dataset 2019 provenance, licence, record count | **Blocked** | Needs the real CSV upload |
| Select one dataset and document why | Done | Synthetic stand-in with the expected schema, approved by the user |
| Column names match the real dataset | **Blocked** | Names are from the PPT and recall; verify against the real file |
| Duplicate, missing-value and class-balance checks | Done (tested) | `train_model.validate`; positive rate 26.6% |
| Dataset SHA-256 recorded | Done (tested) | `model_metadata.json` |

## Machine learning
| Requirement | Status | Evidence / note |
|---|---|---|
| Logistic Regression, Decision Tree, Random Forest | Done | `scripts/train_model.py` |
| 80/20 stratified split, fixed seed | Done (tested) | `train_model.py`; metadata records seed 42 |
| Preprocessing fitted on training data only (no leakage) | Done (tested) | Single sklearn Pipeline per model |
| Model selection on training data, test set used once | Done | CV on training set; `evaluation_report.json` |
| Accuracy, precision, recall, F1, ROC-AUC, confusion matrix | Done (tested) | `evaluation_report.json`; Home page, Model at a glance tab |
| Recall prioritised, precision and FPR reported | Done | Selection criterion stated in metadata and on page |
| Reproducible training | Done | Seed, versions and dataset hash recorded |
| Artifact integrity (hash, schema) | Done (tested) | `test_security.py`, `test_prediction.py` |
| Retraining at runtime | Not done by design | Model loads once; no runtime training |
| Class-imbalance handling | Done | `class_weight="balanced"`; effect on flag rate reported in README |
| Feature-level insights / explainability (PPT slide 12) | **Partial** | Not implemented. Listed as future scope |

## Individual screening
| Requirement | Status | Evidence / note |
|---|---|---|
| Form with schema-driven inputs, units and help text | Done | `views/individual.py`, `config.FIELD_INFO` |
| Required, type, range and category validation | Done (tested) | `test_validation.py` |
| Result with classification, probability and disclaimer | Done (tested) | `test_app.py` |
| Probability caveat (not calibrated) | Done | Shown on every result |
| Submit, Reset and loading indicator | Done (tested) | Spinner and reset tested |
| Graceful prediction error handling | Done (tested) | `test_edge_cases.py` |
| Plain-language explanation of unfamiliar terms | Partial | Help text per field; not a full glossary |

## Regional batch screening
| Requirement | Status | Evidence / note |
|---|---|---|
| CSV upload with type, size and structure checks | Done (tested) | `test_regional.py` |
| Required and extra column handling | Done (tested) | Extra columns reported |
| Row-level validation with explicit errors | Done (tested) | Excluded rows listed with line numbers |
| Duplicate detection | Done (tested) | First occurrence kept |
| Same pipeline as individual screening | Done (tested) | Probability equality test |
| Region table: valid, flagged, %, invalid | Done (tested) | `test_regional.py` |
| % formula and zero-valid-record safety | Done (tested) | Percentage and zero-valid tests |
| Ranking by count and by percentage | Done (tested) | Rank divergence test |
| Count vs percentage distinction, small-sample flag | Done | Explained on page; `Small sample` column |
| Charts from actual predictions | Done | Bar charts; values come from the summary table |
| Downloads (summary and processed results) | Done (tested) | Privacy-limited columns; formula-safe export |

## Dashboard, reports and history
| Requirement | Status | Evidence / note |
|---|---|---|
| Dashboard with navigation, model info, disclaimer | Done | `views/home.py` |
| Statistics from actual session data, empty states | Done | Session counts and empty-state messages |
| Model evaluation summary from saved results | Done | Read from `evaluation_report.json` |
| Session history with minimal fields | Done (tested) | Six fields; no identifiers |
| Persistent history with access controls | **Not in scope** | Session-only by decision; documented |
| Downloadable model and session report | Done (tested) | Markdown report; sanitised user text |
| Log without patient values | Done (tested) | Individual path tested |

## Architecture, security and privacy
| Requirement | Status | Evidence / note |
|---|---|---|
| Modular structure (UI, validation, inference, aggregation, reports) | Done | `views/`, `src/` |
| Authentication and roles | **Not in scope** | Single-user local prototype, accepted by the user |
| Role-based access enforcement | **Not in scope** | Depends on authentication |
| Database (SQLite / PostgreSQL) | **Not in scope** | Session-only design |
| Secrets not in repository | Done | Secret scan clean; `.gitignore`; `.env.example` |
| Upload limits and malformed-file handling | Done (tested) | 5 MB, 10,000 rows, UTF-8 check |
| CSV formula injection protection | Done (tested) | `export_safety.py` |
| Privacy and security documentation | Done | `docs/privacy_and_security.md` |
| Healthcare law compliance | **Not claimed** | Not assessed; stated in docs |

## Testing and quality
| Requirement | Status | Evidence / note |
|---|---|---|
| pytest suite covering critical logic | Done | 100 tests passing |
| Coverage of `src/` | Done | 98% line coverage |
| Lint and security scan | Done | pyflakes clean; bandit no issues |
| Dependency vulnerability scan | Done | pip-audit: none known at time of run |
| Browser UI testing, accessibility (WCAG), responsive layout | **Open** | Needs a browser and manual review |
| Load testing | **Open** | Not run |

## Deployment and documentation
| Requirement | Status | Evidence / note |
|---|---|---|
| Local install and run, verified in a fresh environment | Done (tested) | Clean venv: install, 100 tests, server HTTP 200 |
| README with install and run steps | Done | `README.md` |
| Architecture, data dictionary, model card, privacy docs | Done | `docs/` |
| Hosted deployment | **Open** | Documented, not tested |
| Container packaging | **Not in scope** | Not built, not claimed |
| CI pipeline | **Not in scope** | Not configured |

## Open items for the user
1. Provide the real Diabetes Dataset 2019 CSV, then verify column names, licence and target definition.
2. Confirm the `SoundSleep` meaning against the dataset documentation.
3. Correct the PPT footer ("BIT Durg" vs "BIT Mesra" on slide 10).
4. Complete a browser walkthrough and accessibility review before submission.
5. Decide whether feature-importance explanations (PPT slide 12) are required for submission.
