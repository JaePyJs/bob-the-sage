from fastapi import APIRouter

from backend.pipeline_store import get_session

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.get("/pipeline/{session_id}")
async def get_pipeline_status(session_id: str) -> dict:
    """Poll for pipeline status. Used by frontend instead of WebSocket."""
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found", "stage": "error"}

    return {
        "session_id": session["session_id"],
        "stage": session["stage"],
        "progress": session["progress"],
        "papers_found": session.get("papers_found", 0),
        "papers_analyzed": session.get("papers_analyzed", 0),
        "themes_identified": session.get("themes_identified", 0),
        "results": session.get("results"),
        "error": session.get("error"),
        "message": session.get("message", ""),
    }