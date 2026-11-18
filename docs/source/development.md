# Development

Contributions to KBWS are welcome and appreciated! This guide will help you get started with development and contributing changes.

## Development Setup

### Using pixi (Recommended)

```bash
# Clone the repository
git clone https://github.com/LANL-seismoacoustics/kbws.git
cd kbws

# Install development environment
pixi install
pixi shell -e dev
```

### Using Pip

```bash
# Clone the repository
git clone https://github.com/LANL-seismoacoustics/kbws.git
cd kbws

# Install in editable mode
pip install -e .
```

## Development Workflow

### Running the Service

```bash
# Direct Python (with hot reload)
python -m kbws

# Via uvicorn (more control)
uvicorn kbws.main:app --host 0.0.0.0 --port 8000 --reload

# With docker-compose (hot reload enabled)
docker-compose up --build
```

The `--reload` flag enables automatic reloading when code changes are detected.

### Running Tests

KBWS uses pytest for testing. All tests use mocked database connections - **no database required**:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_event.py

# Run specific test
pytest -k test_event_format_xml

# Verbose output
pytest -v

# With coverage report
pytest --cov=kbws --cov-report=html
```

### Building Documentation

Use the Pixi development environment for documentation dependencies:

```bash
pixi run -e dev build-docs       # Build HTML documentation
pixi run -e dev serve-docs       # Live-reloading preview
```

The equivalent Make targets can be run from `docs/` after activating the
environment:

```bash
pixi shell -e dev
cd docs
make html
make livehtml
make apidocs                  # Regenerate API reference, when needed
```

Narrative documentation lives under `docs/source/`; add new pages to the
appropriate Sphinx toctree. Use Markdown for narrative pages and reStructuredText
only when Sphinx directives require it. Static assets belong in
`docs/source/_static/` and should use filenames without spaces.

## Architecture Overview

### Project Structure

```
kbws/
├── kbws/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy models
│   ├── logging.py           # Centralized logging
│   ├── formats.py           # Response format handlers
│   ├── models/              # Request parameter models
│   │   ├── event.py
│   │   ├── station.py
│   │   ├── dataselect.py
│   │   └── availability.py
│   └── routes/              # API endpoints
│       ├── event.py
│       ├── station.py
│       ├── dataselect.py
│       └── availability.py
├── tests/
│   ├── conftest.py          # Test fixtures and mocks
│   ├── test_event.py
│   ├── test_station.py
│   ├── test_dataselect.py
│   └── test_availability.py
├── docs/
│   └── source/
│       ├── conf.py
│       ├── index.md
│       └── ...
├── pixi.toml               # Modern package management
├── docker-compose.yml       # Container dev setup
└── .env.example            # Example configuration
```

### Key Components

**Entry Point (`main.py`):**
- FastAPI application instance
- Route mounting
- CORS middleware
- Error handlers

**Database Models (`database.py`):**
- Dynamically creates SQLAlchemy models from Pisces KB Core schema
- Table names injected from `.env` at import time
- Each model overrides `__tablename__` with configured value

**Routes (`routes/*.py`):**
- One file per FDSN service (event, station, dataselect, availability)
- Version constants at module level
- Routes prefixed with `/fdsnws/<service>/<major_version>/`

**Format Handlers (`formats.py`):**
- All response format logic (QuakeML, MiniSEED, SAC, CSS, SQL)
- Centralized after refactor from individual route files

**Request Models (`models/*.py`):**
- Pydantic models for request validation
- Automatic OpenAPI documentation generation
- Type coercion and validation

