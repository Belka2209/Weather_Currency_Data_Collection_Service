import asyncio
import httpx
from app.config import settings
from app.database import Database
from app.logger_config import logger

class DataCollector:
    def __init__(self):
        self.db = Database()
        self.client = None
        self.running = False
        self._task = None

    async def start(self):
        """Инициализация клиента и запуск планировщика"""
        self.client = httpx.AsyncClient(timeout=10.0)
        self.running = True
        logger.info(f"Starting scheduler with interval {settings.REQUEST_INTERVAL} minutes")
        
        # Запускаем планировщик как фоновую задачу
        self._task = asyncio.create_task(self._run_scheduler())
        
    async def _run_scheduler(self):
        """Внутренний метод планировщика"""
        try:
            # Первый сбор сразу
            await self.collect_data()
            
            while self.running:
                await asyncio.sleep(settings.REQUEST_INTERVAL * 60)
                if self.running:
                    await self.collect_data()
        except asyncio.CancelledError:
            logger.info("Scheduler task was cancelled")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")

    async def fetch_weather(self):
        try:
            if not self.client:
                return
                
            params = {"q": settings.CITY, "appid": settings.WEATHER_API_KEY}
            logger.info(f"Fetching weather data for {settings.CITY}")
            
            response = await self.client.get(settings.WEATHER_API_URL, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            request_id = self.db.save_weather_data(weather_data, settings.CITY)
            logger.info(f"Weather data saved with request_id: {request_id}")
            
        except httpx.TimeoutException as e:
            logger.error(f"Weather API timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e}")
        except Exception as e:
            logger.error(f"Weather API error: {e}")

    async def fetch_currency(self):
        try:
            if not self.client:
                return
                
            logger.info("Fetching currency data")
            response = await self.client.get(settings.CURRENCY_API_URL)
            response.raise_for_status()
            
            currency_data = response.json()
            request_id = self.db.save_currency_data(currency_data, "USD")
            logger.info(f"Currency data saved with request_id: {request_id}")
            
        except httpx.TimeoutException as e:
            logger.error(f"Currency API timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Currency API HTTP error: {e}")
        except Exception as e:
            logger.error(f"Currency API error: {e}")

    async def collect_data(self):
        """Ручной сбор данных"""
        logger.info("Starting data collection cycle")
        await self.fetch_weather()
        await self.fetch_currency()

    async def stop(self):
        """Остановка планировщика"""
        logger.info("Stopping scheduler...")
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            
        if self.client:
            await self.client.aclose()
            
        logger.info("Scheduler stopped")

# Создаем глобальный экземпляр
collector = DataCollector()