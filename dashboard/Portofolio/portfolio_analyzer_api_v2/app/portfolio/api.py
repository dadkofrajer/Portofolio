from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from .models import (
    PortfolioAnalyzeRequest, PortfolioAnalyzeResponse,
    TestPlanRequest, TestPlanResponse,
    EligibilityCheckRequest, EligibilityCheckResponse
)
from .service import analyze_portfolio, plan_tests, check_eligibility

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.post("/analyze", response_model=PortfolioAnalyzeResponse)
def analyze(req: PortfolioAnalyzeRequest):
    try:
        result = analyze_portfolio(req)
        return jsonable_encoder(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyzer error: {e}")

test_router = APIRouter(prefix="/tests", tags=["tests"])

@test_router.post("/plan", response_model=TestPlanResponse)
def plan_test(req: TestPlanRequest):
    try:
        result = plan_tests(req)
        return jsonable_encoder(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test planning error: {e}")

eligibility_router = APIRouter(prefix="/eligibility", tags=["eligibility"])

@eligibility_router.post("/check", response_model=EligibilityCheckResponse)
def check(req: EligibilityCheckRequest):
    try:
        result = check_eligibility(req)
        return jsonable_encoder(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check error: {e}")
