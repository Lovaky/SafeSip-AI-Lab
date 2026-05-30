from fastapi import APIRouter, Query

from app.services.pubmed_service import search_pubmed

router = APIRouter()


@router.get("/search-paper")
async def search_paper(
    query: str = Query(..., description="Search keyword")
):
    results = await search_pubmed(query)

    return {
        "query": query,
        "results": results,
    }
