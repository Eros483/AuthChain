# ----- main backend API entrypoint @ backend/main.py -----

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.endpoints import router as api_router
import uvicorn
from backend.utils.logger import get_logger

logger=get_logger(__name__)

app = FastAPI(
    title="AuthChain AI Agent API",
    description="Backend API for autonomous AI agent with human-in-the-loop approval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1", tags=["agent"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-agent-backend"}

if __name__ == "__main__":
    logger.info("Starting AuthChain AI Agent Backend API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)