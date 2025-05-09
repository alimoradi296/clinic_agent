import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMConfig(BaseModel):
    api_key: str
    model: str
    base_url:str

class BackendConfig(BaseModel):
    base_url: str
    api_key: str

class RedisConfig(BaseModel):
    host: str
    port: int
    password: str = None
    db: int = 0

class SecurityConfig(BaseModel):
    jwt_secret: str

class AppConfig(BaseModel):
    llm: LLMConfig
    backend: BackendConfig
    redis: RedisConfig
    security: SecurityConfig

def get_config() -> AppConfig:
    """Load and return the application configuration."""
    return AppConfig(
        llm=LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("BASE_URL","https://api.avalai.ir/v1")
        ),
        backend=BackendConfig(
            base_url=os.getenv("BACKEND_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("BACKEND_API_KEY", "1"),  # Default API key from the documentation
        ),
        redis=RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD", ""),
            db=int(os.getenv("REDIS_DB", 0)),
        ),
        security=SecurityConfig(
            jwt_secret=os.getenv("JWT_SECRET"),
        ),
    )

# Create a singleton config instance
config = get_config()