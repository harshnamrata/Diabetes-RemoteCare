# Architecture

RemoteCare AI is a single Streamlit application. Streamlit calls Python modules directly, so no
separate API or JavaScript frontend is needed.

```
User (browser)
   |
   v
Streamlit app (app.py: navigation, st.Page list)
   |
   +-- views/            one file per section
   |     overview, individual, regional, model_performance, reports_history, about
   |
   v
src/ service layer
   |
   +-- model_loader.py       load pipeline once; verify SHA-256 and feature schema
   +-- validation.py         per-record rules; errors block scoring, warnings do not
   +-- prediction_service.py individual: validate -> score -> structured result
   +-- batch_processing.py   file checks -> row checks -> one batch score -> summary
   +-- regional_aggregation.py  counts, percentages, ranking, small-sample flag
   +-- history_service.py    session-only aggregate history
   +-- report_generator.py   Markdown session report
   +-- export_safety.py      neutralises spreadsheet formulas in CSV downloads
   +-- ui_state.py           session-state keys and helpers
   +-- config.py             limits, defaults, labels, notices
   |
   v
models/  remotecare_model.joblib  (sklearn Pipeline: scaler + one-hot + classifier)
         model_metadata.json      (schema, ranges, threshold, artifact hash)
         evaluation_report.json   (CV and test metrics for all candidates)
```

## Key design decisions
- **One model, two modes.** Individual and regional screening both call the same pipeline
  through `records_to_frame`, so preprocessing cannot diverge between modes.
- **Ranking uses classifier outputs only.** The regional ranking is counts and percentages of
  model flags, not a separate score.
- **Schema comes from the model metadata.** Forms and batch validation read the feature schema
  saved at training time, so they cannot drift from the model.
- **Load once, never retrain at runtime.** `load_model` is cached per process. It refuses to load
  an artifact whose hash does not match the recorded hash, and it does not substitute another model.
- **Session-only state.** History, the latest regional summary and the upload fingerprint live in
  Streamlit session state. Nothing is written to a database or to disk by the app.
- **Errors are structured.** Services return result objects with a status (`ok`, `invalid`,
  `rejected`, `unavailable`, `error`), so the UI never shows a partial or misleading result.

## Data flow: batch screening
1. Upload bytes are checked for extension, size, encoding and CSV structure.
2. Required columns are checked. Extra columns are ignored and reported.
3. Each row is checked for region, duplicates and feature rules. Errors exclude the row;
   warnings do not.
4. Valid rows are scored in one call to the saved pipeline.
5. Results are aggregated by region. Each upload is logged to history once, using a fingerprint.
6. CSV downloads are passed through the formula-neutralising export step.

## Testing layers
- Unit tests: validation, prediction service, batch processing, aggregation, history, reports,
  export safety, model-loader failure paths.
- Streamlit AppTest tests: each page renders, forms validate and submit, history is logged,
  reset and clear work.
- Script tests: training validation and demo-file shape.
- See `docs/qa_report.md` for measured results.

## Known architectural limits
- Single process. `lru_cache` and session state are per process and per browser session.
- No database, authentication, or multi-user isolation (accepted for the prototype).
- Batch processing loads the whole file in memory (bounded at 5 MB and 10,000 rows).
