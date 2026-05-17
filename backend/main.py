from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import query, analyze, proposal, pipeline
from backend.api.websocket import router as websocket_router

app = FastAPI(title="SAGE Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(analyze.router)
app.include_router(proposal.router)
app.include_router(pipeline.router)
app.include_router(websocket_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sage-backend"}