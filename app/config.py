from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Keys
    WEATHER_API_KEY: str = ""
    CURRENCY_API_KEY: str = ""

    # API URLs
    WEATHER_API_URL: str = "http://api.openweathermap.org/data/2.5/weather"
    CURRENCY_API_URL: str = "https://api.exchangerate-api.com/v4/latest/USD"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "apidata"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # App settings
    REQUEST_INTERVAL: int = 5  # minutes
    CITY: str = "London"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
