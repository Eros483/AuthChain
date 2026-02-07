# ----- importable configurations @ src/core/config.py -----
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

load_dotenv()

class Settings(BaseSettings):
    """
    Central management for settings and configurations
    Reads .env file
    - Gemini API Key
    - Local LLM usage flag and model name
    """
    USE_LOCAL_LLM: bool = False 
    LOCAL_MODEL_NAME: str = "llama3.1"

    GEMINI_API_KEY: str=os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY: str=os.getenv("OPENROUTER_API_KEY")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    CORS_ORIGINS: list = ["http://localhost:3000"]

settings = Settings()