import os
from functools import lru_cache


class Settings:
    database_url: str
    redis_url: str
    jwt_secret: str
    access_token_ttl: int
    refresh_token_ttl: int
    allowed_origins: list[str]
    riegel_k: float
    weekly_volume_cap: float

    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/nra"
        )
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.access_token_ttl = int(os.getenv("ACCESS_TOKEN_TTL", "900"))
        self.refresh_token_ttl = int(os.getenv("REFRESH_TOKEN_TTL", "1209600"))
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        self.allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]
        self.riegel_k = float(os.getenv("RIEGEL_K", "1.06"))
        self.weekly_volume_cap = float(os.getenv("WEEKLY_VOLUME_CAP", "0.10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()

