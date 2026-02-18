from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class WeatherData(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    wind_speed: float

class CurrencyData(BaseModel):
    base: str
    date: str
    rates: Dict[str, float]

class RequestResponse(BaseModel):
    request_id: int
    endpoint: str
    request_time: datetime
    status: str
    response_data: Optional[Dict[str, Any]] = None
    response_time: Optional[datetime] = None

class HealthCheck(BaseModel):
    status: str
    database: str
    last_weather: Optional[datetime] = None
    last_currency: Optional[datetime] = None
    total_requests: int