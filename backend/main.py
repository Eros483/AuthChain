from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from backend.utils.logger import get_logger
from backend.utils.setup_sandbox import clean_environment, create_scaffolding, init_db

logger = get_logger(__name__)

logger.info("Pre-flight: Initializing Sandbox...")
clean_environment()
create_scaffolding()
init_db()

from backend.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("🚀 API Lifespan started")
    yield
    logger.info("🛑 API Lifespan shutting down")

app = FastAPI(
    title="AuthChain AI Agent API",
    description="Backend API for autonomous AI agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False, 
    )