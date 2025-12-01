# Portfolio Analyzer API

A FastAPI service for analyzing student portfolios with support for portfolio analysis, test planning, and eligibility checking.

## Project Structure

```
Portofolio/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   └── portfolio/   # Portfolio analysis module
│   ├── tests/           # Test files
│   ├── main.py          # FastAPI application entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js dashboard (formerly dashboard/)
├── examples/            # Example request JSON files
└── README.md
```

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up OpenAI API key:
```bash
# Create a .env file in the backend directory or project root
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```
Get your API key from https://platform.openai.com/api-keys

## Run Backend (local)

From the `backend` directory:
```bash
uvicorn main:app --reload
# visit http://127.0.0.1:8000/docs
```

Or from the project root:
```bash
cd backend
uvicorn main:app --reload
```

## Example API Usage

```bash
curl -X POST http://127.0.0.1:8000/portfolio/analyze \
  -H 'Content-Type: application/json' \
  --data @examples/request.json
```

## Tests

From the `backend` directory:
```bash
pytest -q
```

## Frontend

The frontend is a Next.js application located in the `frontend/` directory. See `frontend/README.md` for setup instructions.
