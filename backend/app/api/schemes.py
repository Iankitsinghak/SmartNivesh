from fastapi import APIRouter, HTTPException
from app.schemas.scheme import SchemeRoutingRequest, SchemeRoutingResponse
from app.services.schemes.scheme_router import determine_scheme_applicability

router = APIRouter(prefix="/api/schemes", tags=["Scheme Router"])

@router.post("/route", response_model=SchemeRoutingResponse)
async def route_scheme_endpoint(request: SchemeRoutingRequest):
    """
    Evaluates financial intelligence outputs and deterministically routes the user
    to the applicable financing scheme without fabricating eligibility.
    """
    try:
        response = determine_scheme_applicability(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))
