# MeatFlow MVP

MeatFlow — минимальный MVP системы управления мясным производством.

Запуск локально (dev):

1. Установить зависимости:

   pip install -r requirements.txt

2. Запустить:

   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. Открыть:

   - Dashboard (работники): http://localhost:8000/
   - Панель управления: http://localhost:8000/panel

Настройка окружения:
- По умолчанию используется SQLite (./meatflow.db).
- Для использования внешней БД установите переменную окружения `DATABASE_URL`.

Docker:

  docker build -t meatflow .
  docker run -p 8000:8000 --name meatflow -v $(pwd)/meatflow.db:/app/meatflow.db meatflow

Файлы:
- `app/` — исходники приложения (FastAPI)
- `app/static/` — фронтенд (dashboard, panel)
- `START_MEATFLOW.ps1` — PowerShell скрипт для Windows

Дальше: можно добавить фильтрацию логов, аутентификацию, миграции Alembic.
