# app/api/routers/query_router.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_query_service
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

query_router = APIRouter()


@query_router.post("/api/query")
async def query_handler(
    request: QueryRequest,
    query_service = Depends(get_query_service)
):
    return StreamingResponse(
        query_service.query(request.query),
        media_type="text/event-stream"
    )