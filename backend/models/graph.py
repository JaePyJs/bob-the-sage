from pydantic import BaseModel
from typing import Optional


class GraphNode(BaseModel):
    id: str
    label: str
    group: Optional[str] = None
    value: Optional[int] = None


class GraphEdge(BaseModel):
    from_id: str
    to_id: str
    weight: Optional[float] = None


class CitationGraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]