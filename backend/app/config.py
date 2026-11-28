
from pydantic_settings import BaseSettings, SettingsConfigDict
# """pydantic-settings is a Python library that reads configuration values from sources such as environment variables and .env files.

# BaseSettings is the base class that provides this configuration-reading functionality.

# SettingsConfigDict lets you configure how it reads those values."""

# You're creating your own configuration class called Settings.
# It inherits from BaseSettings, meaning it gets the functionality of reading configuration values.
class Settings(BaseSettings):
    DATABASE_URL: str
    MIGRATION_DATABASE_URL: str | None = None
    # Optional here so Alembic can load DB settings without API-only secrets.
    # The API entry point validates this before it starts serving requests.
    JWT_SECRET_KEY: str | None = None
    JWT_ISSUER: str = "pasaley-api"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_USE_TLS: bool = True
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env", #tells Pydantic Settings to read the .env file.
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings() #It creates an actual instance of your Settings class. 
#During creation, Pydantic Settings reads the available configuration sources and validates the required values.
