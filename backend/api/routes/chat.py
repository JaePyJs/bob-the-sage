from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])

# WebSocket logic will be implemented in websocket.py