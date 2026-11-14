# Deployment

## Supported today: local run (tested)
Requirements: Python 3.12, a virtual environment, and the packages in `requirements.txt`.

    python3.12 -m venv .venv
    source .venv/bin/activate            # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m pytest -q                  # expected: all tests pass
    streamlit run app.py                 # opens at http://localhost:8501

The model files in `models/` are included, so `scripts/train_model.py` is only needed to rebuild
them. Rebuilding gives the same metrics for the same seed, but the `trained_at_utc` timestamp and
the artifact hash will change.

## Configuration
- `.streamlit/config.toml`: upload limit (5 MB) and telemetry off. Both are tested.
- `.env.example`: documents that the app needs no secrets. The application does not currently
  read environment variables.
- Do not commit real credentials. None are used.

## Hosted deployment (not yet tested)
Streamlit Community Cloud or a similar host can run `app.py` directly from a repository.
Before hosting anything:
1. Use synthetic data only. Real patient data requires the controls in
   `docs/privacy_and_security.md` (authentication, HTTPS, audit logging, governance).
2. Confirm the host's upload handling and retention, because Streamlit may buffer uploads.
3. Confirm that the `models/` directory is served read-only and that the hash check passes after
   deployment.
4. Pin Python 3.12 and the versions in `requirements.txt` (scikit-learn 1.8.0 is required for the
   saved artifact).

## Not provided
- No Dockerfile is included. Container packaging has not been built or tested, so it is not claimed.
- No CI pipeline is configured.
- No persistent storage or database migrations, because the prototype is session-only.
