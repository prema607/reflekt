from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()  # exports .env to os.environ so cloudinary picks up CLOUDINARY_URL

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mongo_uri: str = ""
    mongodb_db: str = "vto"
    redis_url: str = ""
    cloudinary_url: str = ""
    huggingface_api_token: str = ""
    hf_endpoint_url: str = ""
    allowed_origins: str = "http://localhost:5000"
    auth_required: bool = False
    firebase_credentials: str = "serviceAccount.json"
    admin_uids: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
