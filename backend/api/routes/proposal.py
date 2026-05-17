from fastapi import APIRouter
from uuid import uuid4

from backend.models.proposal import ResearchProposal, ProposalRequest

router = APIRouter(prefix="/api", tags=["proposal"])


@router.post("/generate-proposal")
async def generate_proposal(payload: ProposalRequest) -> ResearchProposal:
    return ResearchProposal(
        session_id=str(uuid4()),
        title=f"Auto-generated proposal for {payload.discipline} research",
        discipline=payload.discipline,
        background="Placeholder background section.",
        gaps=["Gap 1 placeholder", "Gap 2 placeholder"],
        methodology="Placeholder methodology section.",
        timeline_months=18,
        budget_estimate="$250,000",
        format=payload.format,
    )