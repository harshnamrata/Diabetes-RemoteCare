# QA and Security Review (Stage 7)

Scope: static analysis, automated tests, coverage, security review, server start check.
Date: 11 November 2026 (sandbox run). All results below are from actual runs.

## Results

| Check | Tool | Result |
|---|---|---|
| Automated tests | pytest | 100 passed, 0 failed, 0 skipped |
| Line coverage (src/) | pytest-cov | 98% (436 statements, 9 missed) |
| Static analysis | pyflakes | Clean |
| Security lint | bandit (app, src, views, scripts) | No issues |
| Dependency vulnerabilities | pip-audit on requirements.txt | No known vulnerabilities at time of run |
| Hardcoded secrets | grep scan (py, toml, md, txt) | None found |
| App server start | streamlit run (headless) | HTTP 200, no tracebacks |

Not run: browser-based UI testing, accessibility audit (WCAG), responsive layout testing at
multiple viewport widths, and load testing. These need a human or browser tooling and remain open.

## Defects found and fixed in this stage

1. **CSV formula injection (security).** Region names from uploads were written unchanged into
   downloadable CSVs. A value such as `=HYPERLINK(...)` could run as a formula in spreadsheet
   software. Fixed: risky leading characters are neutralised in every CSV download, with tests.
2. **No integrity check on the model file (security).** The pickle-based artifact was loaded
   without verification. Fixed: training records a SHA-256 hash in the metadata, and the loader
   refuses to unpickle a file whose hash does not match. Tests cover tampered and unhashed artifacts.
3. **Malformed Streamlit configuration (defect).** `.streamlit/config.toml` was invalid TOML.
   Streamlit ignored it silently, so the 5 MB upload limit and telemetry opt-out were not applied.
   Fixed, and the test now parses the TOML rather than matching text.
4. **Data validation used `assert` (defect).** Python strips asserts under `-O`, so training
   checks could be skipped. Replaced with explicit exceptions.
5. **Markdown injection in the session report (security, low).** User-supplied region names could
   insert links, images or HTML into the report preview. Fixed: those characters are removed from
   user text, with tests.
6. **Privacy wording (accuracy).** The About page implied uploads are never buffered. Streamlit may
   buffer uploads temporarily. The text now states this.
7. Minor: an unused import in a test, and two lint issues in test files. Fixed.

## Known open risks (accepted for the academic prototype, to be addressed in deployment)

- **Pickle deserialisation.** The integrity check reduces risk but does not make untrusted
  artifacts safe. Only artifacts produced by the training script should be used.
- **No authentication or authorisation.** Single-user local prototype, accepted in scope.
- **Uploads may be buffered by Streamlit** (see defect 6). A hosted deployment needs review.
- **Usage telemetry** is disabled in `.streamlit/config.toml`.
- **Synthetic data only.** Metrics do not describe real populations, and the model is not
  clinically validated.
- **scikit-learn version pinning.** The artifact requires scikit-learn 1.8.0. A different version
  may load with warnings or produce different results, so the pin in requirements.txt matters.

## Verification of security controls

- Formula neutralisation: tests for each risky prefix, plus an end-to-end export test.
- Artifact integrity: tests for tampering, missing hash, and schema mismatch.
- Output privacy: processed results export only row, region, probability and flag. Session
  reports contain aggregates and history counts only. A test checks that default feature values
  do not appear in the report.
- Logging: model-loading and prediction failures log the exception type only. A test checks that
  feature values do not appear in logs.
