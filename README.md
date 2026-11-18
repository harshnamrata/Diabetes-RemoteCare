# RemoteCare AI: Diabetes-Risk Screening

**Prototype trained on SYNTHETIC data. Not clinically validated. Do not use to screen real patients.**
A screening aid only. It does not diagnose diabetes.

## Setup
    python -m venv .venv && source .venv/bin/activate   # Python 3.12
    pip install -r requirements.txt

## Train the model (only needed if models/ is missing)
    python scripts/train_model.py

## Run the app
    streamlit run app.py
Sidebar sections (defined in `app.py` with `st.navigation`): Home, Individual screening,
Regional screening, Learn about diabetes, Reports & history. Model metrics and project
information sit on the Home page.

## Regional demo data
    python scripts/make_regional_demo.py
Writes `data/sample/SYNTHETIC_regional_demo.csv` (synthetic records, fake region labels,
and deliberate errors). Use it to try the batch workflow.

## Run tests
    python -m pytest -q

## Structure
- `app.py`: navigation entry point
- `views/`: one file per section
- `src/config.py`: limits, defaults, labels, disclaimers
- `src/model_loader.py`: loads the saved pipeline once and checks it matches its metadata; never retrains or substitutes a model
- `src/validation.py`: input validation (errors block scoring; training-range mismatches are warnings)
- `src/prediction_service.py`: validate, score, and return a structured result
- `src/batch_processing.py`: CSV validation, row-level exclusions, batch scoring
- `src/regional_aggregation.py`: counts, percentages, ranking, small-sample flag
- `src/history_service.py`: session-only history (aggregate counts, no identifiers)
- `src/report_generator.py`: Markdown session report
- `src/ui_state.py`: session-state keys and helpers
- `scripts/train_model.py`: reproducible training and evaluation
- `models/`: trained artifact, metadata, evaluation report
- `docs/model_card.md`: intended use, results, limitations

## Security note
`models/remotecare_model.joblib` is a pickle-based artifact. Load only files produced by `train_model.py`.

## Known limits
- At the 0.5 threshold, the balanced-class model flags a larger share of records than the
  training base rate (about 27%). Regional percentages reflect that threshold choice.
- Single-user local app with no login (accepted for this prototype).
- Session-only history and reports; nothing is stored between sessions.
- Regional data are synthetic; the output is not a surveillance measure.
- The model was pickled with scikit-learn 1.8.0; `requirements.txt` pins that version.

## Quality and security
See `docs/qa_report.md` for test, coverage, lint, security and dependency results, and the defects fixed in Stage 7.

## Documentation
- `docs/architecture.md`: components, data flow, design decisions
- `docs/data_dictionary.md`: schema, allowed values, batch upload format
- `docs/model_card.md`: intended use, results, limitations
- `docs/privacy_and_security.md`: data handling, controls, known gaps
- `docs/deployment.md`: local run (tested) and hosted notes
- `docs/qa_report.md`: test, coverage, lint, security and dependency results
- `docs/requirements_checklist.md`: status of every requirement, with open items

## Status
Prototype complete for the academic scope, on synthetic data. Real-data use, hosting, and
browser/accessibility testing are open (see the requirements checklist).
