from fastapi import FastAPI
from app.portfolio.api import router as portfolio_router, test_router, eligibility_router

app = FastAPI(title="Portfolio Analyzer API", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

app.include_router(portfolio_router)
app.include_router(test_router)
app.include_router(eligibility_router)
