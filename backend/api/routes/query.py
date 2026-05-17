from fastapi import APIRouter
from uuid import uuid4

from backend.models.paper import PaperQueryRequest
from backend.pipeline_store import create_session, run_pipeline

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
async def start_query(payload: PaperQueryRequest) -> dict:
    session_id = str(uuid4())
    create_session(session_id, payload.query, max_papers=payload.max_papers, disciplines=payload.disciplines or None)
    # Start pipeline in background
    run_pipeline(session_id)
    return {
        "session_id": session_id,
        "status": "processing",
        "websocket_url": f"ws://localhost:8000/api/chat/{session_id}",
    }