from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from app.database import Database
from app.scheduler import collector
from app.models import RequestResponse, HealthCheck
from app.logger_config import logger
from typing import List

db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application")
    try:
        # Инициализация БД
        db.init_db()
        logger.info("Database initialized successfully")
        
        # Запуск планировщика
        await collector.start()
        logger.info("Scheduler started successfully")
        
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down FastAPI application")
        await collector.stop()

app = FastAPI(
    title="Weather & Currency Data Collection Service",
    description="Сервис для сбора данных о погоде и курсах валют",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Weather & Currency Data Collection Service",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/requests",
            "/requests/{request_id}",
            "/stats",
            "/collect"
        ]
    }

@app.get("/health", response_model=HealthCheck, tags=["Monitoring"])
async def health_check():
    """Проверка состояния сервиса"""
    try:
        stats = db.get_stats()
        return HealthCheck(
            status="healthy",
            database="connected",
            last_weather=stats.get("last_weather"),
            last_currency=stats.get("last_currency"),
            total_requests=stats.get("total_requests", 0)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            database="disconnected",
            total_requests=0
        )

@app.get("/requests", response_model=List[RequestResponse], tags=["Data"])
async def get_requests(limit: int = 50):
    """Получить историю запросов"""
    try:
        results = db.get_join_query(limit)
        return results
    except Exception as e:
        logger.error(f"Error fetching requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/requests/{request_id}", response_model=RequestResponse, tags=["Data"])
async def get_request(request_id: int):
    """Получить конкретный запрос по ID"""
    try:
        results = db.get_join_query(limit=100)
        for result in results:
            if result["request_id"] == request_id:
                return result
        raise HTTPException(status_code=404, detail="Request not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Monitoring"])
async def get_statistics():
    """Получить статистику по запросам"""
    try:
        return db.get_stats()
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collect", tags=["Manual"])
async def manual_collect(background_tasks: BackgroundTasks):
    """Запустить ручной сбор данных"""
    async def run_collection():
        await collector.collect_data()
    
    background_tasks.add_task(run_collection)
    return {"message": "Data collection started in background"}

@app.get("/sql-example", tags=["Documentation"])
async def sql_example():
    """Пример SQL запроса с JOIN"""
    return {
        "sql_query": """
        SELECT 
            r.id as request_id,
            r.endpoint,
            r.request_time,
            r.status,
            res.response_data,
            res.response_time
        FROM requests r
        LEFT JOIN responses res ON r.id = res.request_id
        ORDER BY r.request_time DESC
        LIMIT 50;
        """,
        "description": "Выгружает историю запросов и полученные данные"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)