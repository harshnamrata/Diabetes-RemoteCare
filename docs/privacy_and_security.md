# Privacy and Security

**Status: prototype.** The application has not been assessed against any healthcare privacy law
and must not be used with real patient data without that assessment, governance, and clinical
validation.

## Data handled
| Data | Source | Where it lives | Retained? |
|---|---|---|---|
| Individual feature values | Form entry | Session memory during submit | No. Only the result object is kept, and it holds no feature values. |
| Batch CSV | Upload | Memory during processing; Streamlit may buffer it temporarily | The app never writes it to disk. Not kept after processing. |
| Per-row results | Processing | Session memory | Available for download only; not stored. |
| Session history | App | Session memory | Counts and status only. Cleared when the session ends or on Clear. |
| Session report | App | Generated on request | Not stored. Contains aggregates and history counts, no patient records. |

## Data minimisation
- No names, phone numbers, addresses, or other identifiers are requested or stored.
- Processed-results export contains only row number, region, probability and flag.
- History entries have exactly six fields: timestamp, mode, three counts and status
  (tested).
- Log lines record exception types, never feature values (tested for the individual path).

## Security controls
| Risk | Control | Verified by |
|---|---|---|
| Malicious model file (pickle) | SHA-256 recorded at training; load refused on mismatch | `test_security.py` |
| Model/schema drift | Feature order checked against the pipeline before use | `test_prediction.py` |
| Spreadsheet formula injection | Risky leading characters neutralised in CSV downloads | `test_security.py` |
| Markdown or HTML injection in reports | Brackets, angle brackets and backticks stripped from user text | `test_security.py` |
| Oversized uploads | 5 MB check in code and `maxUploadSize = 5` in Streamlit config | `test_regional.py`, `test_security.py` |
| Malformed input | Structured errors; never silently dropped | `test_regional.py` |
| Telemetry | `gatherUsageStats = false` | `test_security.py` |
| Hardcoded secrets | None. Secret scan clean | `docs/qa_report.md` |
| Dependency vulnerabilities | pip-audit clean at time of run | `docs/qa_report.md` |

## Known gaps (must be addressed before any real deployment)
- **No authentication or authorisation.** Anyone who can reach the server can screen individuals
  and upload files. Roles, login, and audit logging are needed.
- **No transport security configured.** Deployments must serve the app over HTTPS.
- **Pickle deserialisation.** The hash check reduces but does not remove the risk. Model artifacts
  must come only from a trusted training pipeline with controlled write access.
- **Upload buffering.** Streamlit may buffer uploads on disk. A hosted deployment should confirm
  where that happens and set retention accordingly.
- **No audit trail.** Session history is not an audit log, and it is not persisted.
- **Synthetic data only.** Regional results and metrics are not evidence about real populations.
- **No clinical validation or governance.** Clinical use needs validation on representative data,
  clinical oversight, and a documented safety process.

## Responsible use
- Results are screening prompts. They are not diagnoses and cannot confirm or rule out diabetes.
- Probabilities are model estimates and are not calibrated personal risks.
- Regional percentages reflect the model's flags, not population prevalence.
- Users should see the disclaimer alongside every result (implemented on all result views).
