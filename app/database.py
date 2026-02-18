import psycopg2
import json
import os
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.config import settings
from app.logger_config import logger
from typing import List, Dict, Any

class Database:
    def __init__(self):
        self.conn_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "dbname": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "client_encoding": "UTF8",  # Явно указываем кодировку
            "options": "-c client_encoding=UTF8"  # Дополнительная опция
        }

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            # Пробуем подключиться с разными настройками кодировки
            try:
                conn = psycopg2.connect(**self.conn_params)
            except UnicodeDecodeError:
                # Если не получается, пробуем без указания кодировки
                params = self.conn_params.copy()
                del params["client_encoding"]
                del params["options"]
                conn = psycopg2.connect(**params)
                
                # Устанавливаем кодировку после подключения
                conn.set_client_encoding('UTF8')
            
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_db(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Создание таблицы requests
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS requests (
                            id SERIAL PRIMARY KEY,
                            endpoint VARCHAR(50) NOT NULL,
                            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20)
                        )
                    """)
                    
                    # Создание таблицы responses
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS responses (
                            id SERIAL PRIMARY KEY,
                            request_id INTEGER REFERENCES requests(id) ON DELETE CASCADE,
                            response_data JSONB NOT NULL,
                            response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Индексы для оптимизации
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_requests_time 
                        ON requests(request_time)
                    """)
                    
                    conn.commit()
                    logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    # Остальные методы остаются без изменений
    def save_weather_data(self, weather_data: Dict, city: str) -> int:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO requests (endpoint, status) VALUES (%s, %s) RETURNING id",
                        ("weather", "success"),
                    )
                    request_id = cur.fetchone()[0]

                    response_data = {
                        "city": city,
                        "temperature": round(weather_data["main"]["temp"] - 273.15, 2),
                        "feels_like": round(weather_data["main"]["feels_like"] - 273.15, 2),
                        "humidity": weather_data["main"]["humidity"],
                        "pressure": weather_data["main"]["pressure"],
                        "description": weather_data["weather"][0]["description"],
                        "wind_speed": weather_data["wind"]["speed"],
                    }

                    response_json = json.dumps(response_data, ensure_ascii=False)
                    
                    cur.execute(
                        "INSERT INTO responses (request_id, response_data) VALUES (%s, %s::jsonb)",
                        (request_id, response_json),
                    )
                    
                    conn.commit()
                    logger.info(f"Weather data for {city} saved successfully")
                    return request_id
        except Exception as e:
            logger.error(f"Error saving weather data: {e}")
            raise

    def save_currency_data(self, currency_data: Dict, base_currency: str) -> int:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO requests (endpoint, status) VALUES (%s, %s) RETURNING id",
                        ("currency", "success"),
                    )
                    request_id = cur.fetchone()[0]

                    main_currencies = ["EUR", "GBP", "JPY", "RUB", "CNY", "USD"]
                    filtered_rates = {}
                    
                    rates = currency_data.get("rates", {})
                    for currency in main_currencies:
                        if currency in rates:
                            filtered_rates[currency] = rates[currency]

                    response_data = {
                        "base": base_currency,
                        "date": currency_data.get("date", ""),
                        "rates": filtered_rates,
                    }

                    response_json = json.dumps(response_data, ensure_ascii=False)
                    
                    cur.execute(
                        "INSERT INTO responses (request_id, response_data) VALUES (%s, %s::jsonb)",
                        (request_id, response_json),
                    )
                    
                    conn.commit()
                    logger.info("Currency data saved successfully")
                    return request_id
        except Exception as e:
            logger.error(f"Error saving currency data: {e}")
            raise

    def get_join_query(self, limit: int = 50) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
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
                        LIMIT %s
                    """, (limit,))
                    
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error executing JOIN query: {e}")
            return []

    def get_stats(self) -> Dict:
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT COUNT(*) as total FROM requests")
                    total = cur.fetchone()["total"]
                    
                    cur.execute("""
                        SELECT endpoint, status, COUNT(*) as count 
                        FROM requests 
                        GROUP BY endpoint, status
                    """)
                    stats = cur.fetchall()
                    
                    cur.execute("""
                        SELECT MAX(request_time) as last_weather 
                        FROM requests 
                        WHERE endpoint = 'weather' AND status = 'success'
                    """)
                    last_weather = cur.fetchone()["last_weather"]
                    
                    cur.execute("""
                        SELECT MAX(request_time) as last_currency 
                        FROM requests 
                        WHERE endpoint = 'currency' AND status = 'success'
                    """)
                    last_currency = cur.fetchone()["last_currency"]
                    
                    return {
                        "total_requests": total,
                        "statistics": stats,
                        "last_weather": last_weather,
                        "last_currency": last_currency
                    }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}