from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SECRET_KEY: str
    DATABASE_URL: str = "sqlite:////app/data/papersync.db"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"
    APP_ENV: str = "production"
    APP_USERNAME: str = "admin"
    APP_PASSWORD: str


settings = AppConfig()
