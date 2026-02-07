# -----  LLM handler @ backend/core/llm_factory.py -----

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from backend.core.config import settings

from backend.utils.logger import get_logger

logger=get_logger(__name__)

def get_llm():
    """
    Returns the configured LLM backend (Gemini or Local).
    """
    if settings.USE_LOCAL_LLM:
        logger.info(f"LOADING LOCAL MODEL: {settings.LOCAL_MODEL_NAME}")

        return ChatOllama(
            model=settings.LOCAL_MODEL_NAME,
            temperature=0,
        )
    
    else:
        logger.info("LOADING GEMINI CLOUD MODEL")
        return ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash-lite",
            api_key=settings.GEMINI_API_KEY
        )
