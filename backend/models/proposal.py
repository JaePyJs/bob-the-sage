from pydantic import BaseModel


class ResearchProposal(BaseModel):
    session_id: str
    title: str
    discipline: str
    background: str
    gaps: list[str]
    methodology: str
    timeline_months: int
    budget_estimate: str
    format: str = "markdown"


class ProposalRequest(BaseModel):
    session_id: str
    discipline: str
    format: str = "latex"