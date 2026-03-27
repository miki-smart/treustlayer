FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# entrypoint: run migrations, seed, then start server
CMD ["sh", "-c", "alembic upgrade head && python3 seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
