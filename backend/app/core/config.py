from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./buyerflow.db"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 720
    cors_origins: str = "http://localhost:5173"
    admin_username: str = "admin"
    admin_password: str = "change-me"
    telegram_bot_token: str | None = None
    telegram_admin_chat_id: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()
