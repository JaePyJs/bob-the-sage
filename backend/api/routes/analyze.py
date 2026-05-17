from fastapi import APIRouter
from datetime import datetime

from backend.models.review import LiteratureReview, ReviewSection

router = APIRouter(prefix="/api", tags=["analyze"])


@router.get("/analyze/{session_id}")
async def get_analysis(session_id: str) -> LiteratureReview:
    return LiteratureReview(
        session_id=session_id,
        topic="Placeholder Analysis",
        sections=[
            ReviewSection(title="Introduction", content="Introduction section placeholder."),
            ReviewSection(title="Methodology Trends", content="Methodology trends placeholder."),
            ReviewSection(title="Key Findings", content="Key findings placeholder."),
            ReviewSection(title="Conclusions", content="Conclusions placeholder."),
        ],
        research_gaps=[],
        created_at=datetime.now(),
    )