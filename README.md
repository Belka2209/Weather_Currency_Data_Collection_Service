# Weather & Currency Data Collection Service

Сервис для автоматического сбора данных о погоде и курсах валют с публичных API и их сохранения в PostgreSQL базу данных с возможностью мониторинга и анализа.

## Описание

Этот сервис предназначен для периодического сбора актуальных данных о погоде и курсах валют с помощью публичных API (OpenWeatherMap и ExchangeRate-API). Все собранные данные сохраняются в PostgreSQL базе данных для дальнейшего анализа и использования. Сервис построен на современном фреймворке **FastAPI** с асинхронной архитектурой.

## Функциональные возможности

- **Сбор данных о погоде**: Получение информации о температуре, влажности, давлении и других параметрах с OpenWeatherMap API
- **Сбор данных о курсах валют**: Получение актуальных курсов валют с ExchangeRate-API
- **Хранение данных**: Сохранение всех запросов и ответов в связанных таблицах базы данных (requests и responses) с внешним ключом
- **Периодическая синхронизация**: Автоматический сбор данных с настраиваемым интервалом (по умолчанию 5 минут)
- **FastAPI эндпоинты**: REST API для доступа к данным и мониторинга
- **Интерактивная документация**: Автоматическая Swagger документация
- **Логирование**: Подробное логирование всех операций, ошибок и таймаутов в отдельный файл
- **Контейнеризация**: Полная поддержка Docker и Docker Compose для удобного развертывания
- **Мониторинг состояния**: Эндпоинт `/health` для проверки работоспособности сервиса
- **Ручной запуск сбора данных**: Эндпоинт `/collect` для инициации ручного сбора данных
- **Просмотр статистики**: Эндпоинт `/stats` для получения статистики по запросам
- **Доступ к истории запросов**: Эндпоинт `/requests` для получения истории всех запросов
- **Доступ к конкретному запросу**: Эндпоинт `/requests/{request_id}` для получения информации о конкретном запросе

## Технологии

- **FastAPI** 0.115+ - современный асинхронный веб-фреймворк
- **Python** 3.11
- **PostgreSQL** 15
- **Docker & Docker Compose**
- **Библиотеки**:
  - `httpx` - асинхронные HTTP запросы
  - `psycopg2-binary` - работа с PostgreSQL
  - `schedule` - планировщик задач
  - `pydantic` - валидация данных
  - `uvicorn` - ASGI сервер

## Архитектура

Сервис состоит из следующих компонентов:

- **FastAPI приложение**: Обрабатывает запросы и предоставляет REST API
- **Планировщик задач**: Фоновая задача для периодического сбора данных
- **База данных**: PostgreSQL для хранения исторических данных
- **API интеграции**: Внешние API для получения актуальной информации (OpenWeatherMap, ExchangeRate-API)
- **Система логирования**: Для отслеживания работы и диагностики проблем

## Требования

- Docker и Docker Compose (версия 2.0+)
- API ключ от OpenWeatherMap ([получить бесплатно](https://openweathermap.org/api))
- Доступ к интернету для обращения к внешним API

## Установка и запуск

### 1. Клонируйте репозиторий

   ```bash
   git clone https://github.com/Belka2209/Weather_Currency_Data_Collection_Service.git
   cd weather-currency-service
   ```

### 2. Создайте файл конфигурации `.env` на основе примера

   ```bash
   cp .env.example .env
   ```

### 3. Настройте переменные окружения в файле `.env`

## Database Configuration

```env
DB_NAME=apidata
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres        # Важно: имя сервиса, не localhost!
DB_PORT=5432

## OpenWeatherMap API

WEATHER_API_KEY=ваш_реальный_ключ_сюда
CITY=Moscow

## Currency API (не требует ключа)

CURRENCY_API_KEY=dummy

## Application Settings

REQUEST_INTERVAL=5      # интервал в минутах
```

### 4. Запустите через Docker Compose

   ```bash
   docker-compose up -d --build
   ```

### 5. Проверьте статус контейнеров

   ```bash
   docker-compose ps
   ```

### 6. Проверьте логи приложения

   ```bash
   docker-compose logs -f app
   ```

## Примеры SQL-запросов

### Получение последних запросов с ответами

```sql
SELECT
    r.id AS request_id,
    r.endpoint,
    r.request_time,
    r.status,
    res.response_data,
    res.response_time
FROM requests r
LEFT JOIN responses res ON r.id = res.request_id
ORDER BY r.request_time DESC
LIMIT 50;
```

### Последние данные о погоде

```sql
SELECT
    r.request_time,
    res.response_data->>'city' as city,
    res.response_data->>'temperature' as temperature,
    res.response_data->>'humidity' as humidity
FROM requests r
JOIN responses res ON r.id = res.request_id
WHERE r.endpoint = 'weather'
ORDER BY r.request_time DESC
LIMIT 5;
```

### Статистика по типам запросов

```sql
SELECT
    endpoint,
    COUNT(*) AS total_requests,
    MAX(request_time) AS last_request
FROM requests
GROUP BY endpoint;
```

### Ошибки за последние 24 часа

```sql
SELECT *
FROM requests
WHERE status != 200
  AND request_time >= NOW() - INTERVAL '24 hours';
```

## Структура базы данных

- **requests**: Информация о каждом выполненном запросе
  - id: Уникальный идентификатор
  - endpoint: Тип запроса (weather/currency)
  - request_time: Время выполнения запроса
  - status: HTTP статус ответа
  - error_message: Сообщение об ошибке (если есть)

- **responses**: Ответы от API
  - id: Уникальный идентификатор
  - request_id: Ссылка на соответствующий запрос
  - response_data: JSON данные ответа
  - response_time: Время получения ответа

## Настройка

Все основные настройки находятся в файле `.env`:

- `WEATHER_API_KEY`: API ключ для OpenWeatherMap
- `EXCHANGE_API_URL`: URL для получения курсов валют
- `WEATHER_API_URL`: URL для получения данных о погоде
- `REQUEST_INTERVAL`: Интервал между запросами в минутах
- `DATABASE_URL`: Строка подключения к базе данных

## Безопасность

- Все чувствительные данные хранятся в переменных окружения
- API ключи не хранятся в коде
- Все зависимости изолированы в Docker контейнерах

## Мониторинг и логирование

- Все запросы и ответы логируются в файл `error.log`
- Статусы ошибок и исключения фиксируются для диагностики
- Доступна детальная информация о времени выполнения запросов

## Разработка

Для локальной разработки:

1. Установите Python 3.8+
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте переменные окружения
4. Запустите приложение: `python app/main.py`
