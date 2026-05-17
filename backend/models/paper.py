from pydantic import BaseModel
from typing import Optional


class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: Optional[str] = None
    authors: list[str] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    language: Optional[str] = "en"


class PaperQueryRequest(BaseModel):
    query: str
    language: str = "en"
    years: Optional[tuple[int, int]] = None
    max_papers: int = 50
    output_language: str = "en"
    disciplines: list[str] = []


class PaperQueryStatus(BaseModel):
    session_id: str
    stage: str
    progress: int
    papers_found: Optional[int] = None
    papers_analyzed: Optional[int] = None
    themes_identified: Optional[int] = None