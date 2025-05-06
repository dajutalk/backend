from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    Database_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
