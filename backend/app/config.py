from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FASO_", extra="ignore")

    database_url: str = "postgresql+psycopg://faso:faso@localhost:5434/faso"
    data_dir: Path = Path("data")

    admin_user: str = "admin"
    admin_password: str = "change-me"
    secret_key: str = "change-me-long-random"

    # Identification claire auprès des sites collectés (politesse)
    user_agent: str = "FasoCivic/0.1 (plateforme civique open source)"

    # Extraction LLM : mistral (tier gratuit) | anthropic — cf. extraction/conseil_ministres.py
    llm_provider: str = "mistral"
    mistral_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()
