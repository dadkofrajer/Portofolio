# Backend - Portfolio Analyzer API

FastAPI backend service for portfolio analysis.

## Structure

```
backend/
├── src/
│   └── portfolio/      # Portfolio analysis module
│       ├── api.py      # API routes
│       ├── models.py   # Pydantic models
│       ├── service.py  # Business logic
│       ├── constants.py # Constants and configuration
│       └── playbooks.json # Playbook definitions
├── tests/              # Test files
├── main.py             # FastAPI application entry point
└── requirements.txt    # Python dependencies
```

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up OpenAI API key:
```bash
# Create a .env file in the backend directory or project root
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

## Run

```bash
uvicorn main:app --reload
# visit http://127.0.0.1:8000/docs
```

## Tests

```bash
pytest -q
```

