# Portfolio Analyzer API (v2)

Minimal FastAPI service implementing the `/portfolio/analyze` endpoint per the v2 spec.

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
# Create a .env file in the project root
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```
Get your API key from https://platform.openai.com/api-keys

## Run (local)

```bash
uvicorn app.main:app --reload
# visit http://127.0.0.1:8000/docs
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/portfolio/analyze \  -H 'Content-Type: application/json' \  --data @examples/request.json
```

## Tests

```bash
pytest -q
```
