# PokéTest Arena

A Pokémon-themed Django learning website demonstrating automated testing with pytest, pytest-django, pytest-cov and the PokéAPI.

## Features
- Quiz gate before entering the arena.
- Pokémon lookup by name or National Pokédex number (for example `#013`).
- Pytest-themed mini-game.
- Educational content on the testing pyramid, unit/integration testing, fixtures, mocks and coverage limitations.
- Frontend Pytest Control Centre for local runs of the allow-listed test suites (all, unit, API and mocks).
- Actual test output, summary counts, duration and coverage percentage from pytest-cov.

## Setup

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Tests

```bash
pytest -v
pytest --cov=pokemon --cov-report=term-missing
pytest --cov=pokemon --cov-report=html
```

Open `htmlcov/index.html` for the HTML coverage report.

## Interactive runner safety

The browser dashboard calls a Django endpoint that accepts only fixed test suite names, uses `subprocess.run(..., shell=False)`, prevents concurrent runs and enforces a 90-second timeout. It is intentionally restricted to `DEBUG=True` for local classroom demonstrations. Do not expose this development test-runner endpoint on a public deployment. A hosted version should use an authenticated job worker with strict resource limits.

## Project structure

- `config/`: Django settings and routes
- `pokemon/services.py`: PokéAPI integration
- `pokemon/views.py`: website views, JSON API and local test runner
- `pokemon/tests/`: unit, API, mocking, validation, HTTP method and runner tests
- `templates/`: game-style web pages
- `static/`: CSS and JavaScript
