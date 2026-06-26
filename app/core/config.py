from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database Settings (FastAPI will automatically find these in your .env file)
    db_user: str = "admin"
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "asset_management"

    # AI Settings
    openrouter_api_key: str

    @property
    def database_url(self) -> str:
        """Dynamically constructs the PostgreSQL URL from the variables above."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Tell Pydantic to read from the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create a global settings object to import anywhere in your app
settings = Settings()
