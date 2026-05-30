from fastapi import APIRouter, HTTPException, Query, Request

from app.services.pubmed_service import (
    PubMedServiceError,
    check_pubmed_health,
    search_pubmed,
)

router = APIRouter()


@router.get("/search-paper")
async def search_paper(
    request: Request,
    query: str = Query(..., description="Search keyword"),
):
    request_id = getattr(request.state, "request_id", None)
    try:
        results = await search_pubmed(query, request_id=request_id)
    except PubMedServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.code,
                "message": exc.message,
                "request_id": request_id,
            },
        ) from exc

    return {
        "query": query,
        "request_id": request_id,
        "results": results,
    }


@router.get("/pubmed-health")
async def pubmed_health(request: Request):
    request_id = getattr(request.state, "request_id", None)
    try:
        result = await check_pubmed_health(request_id=request_id)
    except PubMedServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.code,
                "message": exc.message,
                "request_id": request_id,
            },
        ) from exc

    return {
        **result,
        "request_id": request_id,
    }
