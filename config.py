from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_NAME: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
