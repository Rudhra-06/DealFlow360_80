from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):

    """Application configuration settings loaded from environment variables or .env file."""

    APP_NAME: str = "DealFlow360 API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Database Connection Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dealflow360"

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "replace-with-a-strong-local-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Development & Demo User Bootstrap Configuration
    DEMO_USER_PASSWORD: str = "replace-with-local-demo-password"

    # Optional full DATABASE_URL override
    DATABASE_URL: str | None = None

    POSTGRES_TEST_DB: str = "dealflow360_test"
    TEST_DATABASE_URL: str | None = None


    @property
    def async_database_url(self) -> str:
        """Assembles and returns the asyncpg-compatible PostgreSQL database URL safely."""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def async_test_database_url(self) -> str:
        """Assembles and returns the asyncpg-compatible PostgreSQL test database URL safely."""
        if self.TEST_DATABASE_URL:
            if self.TEST_DATABASE_URL.startswith("postgresql://"):
                return self.TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.TEST_DATABASE_URL
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_TEST_DB,
        ).render_as_string(hide_password=False)


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
