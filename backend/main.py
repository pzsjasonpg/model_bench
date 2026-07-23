"""FastAPI application entry point for the model benchmark backend."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import tests, test_types, data
from .ws.logs import ws_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB; Shutdown: cleanup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized. Server ready.")
    yield
    logger.info("Server shutting down.")


app = FastAPI(
    title="Model Bench API",
    description="Backend API for model benchmark testing platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tests.router)
app.include_router(test_types.router)
app.include_router(data.router)


# ── WebSocket endpoint ────────────────────────────────────────────────

@app.websocket("/ws/tests/{test_id}")
async def websocket_test_logs(ws: WebSocket, test_id: int):
    """Stream real-time logs for a test run."""
    await ws_manager.connect(test_id, ws)
    try:
        # Keep connection alive - receive messages (client can send ping)
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(test_id, ws)


# ── Health check ─────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=38081, reload=False)
