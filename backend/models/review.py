from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReviewSection(BaseModel):
    title: str
    content: str


class LiteratureReview(BaseModel):
    session_id: str
    topic: str
    sections: list[ReviewSection]
    research_gaps: list[str] = []
    created_at: Optional[datetime] = None