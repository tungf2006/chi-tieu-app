# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Version is defined once in `app/__init__.py` (`__version__`) and mirrored here.

## [Unreleased]

## [2.1.0] - 2026-08-21

### Added
- Streamlit frontend: transaction entry & list page (`frontend/streamlit_app.py`, Day 39).
- Charts & Forecasting page integrating `/reports/monthly/chart` and `/forecast` (Day 40).
- `budget` query parameter on `GET /forecast` for budget-vs-forecast comparison (Day 40).
- `CHANGELOG.md` and single-source `__version__` in `app/__init__.py` (Day 46).

### Changed
- Backend database switched to PostgreSQL via `docker-compose.yml` (`api` + `db` services, Day 35).
- README rewritten with architecture diagram, Docker getting-started, and API docs (Day 43–45).

### Fixed
- `StreamlitSecretNotFoundError` when no `secrets.toml` existed — replaced `st.secrets.get` with `os.getenv` (Day 39).

## [2.0.0] - 2026-08-11

### Added
- Month-end spending forecast with three models: Linear, Seasonal, ARIMA (`app/services/forecast.py`, Day 30).
- `GET /forecast` endpoint with `method` selector (`linear` | `seasonal` | `arima`).
- Forecast benchmark suite across 8 datasets (`tests/test_forecast_scenarios.py`).

## [1.0.0] - 2026-08-01

### Added
- Transaction CRUD, category CRUD, and filtering (`/transactions`, `/categories`).
- Auto-categorization from transaction note (regex).
- Monthly report summary and pie-chart image (`/reports/monthly`, `/reports/monthly/chart`).
- Dockerfile and initial `docker-compose.yml` (SQLite).
