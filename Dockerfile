# One image, two entrypoints: `api` (default CMD) and `worker` (command override
# in docker-compose.yml). Python 3.12 to match CI and MILESTONE.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first so the layer caches across code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Default entrypoint = the API. The worker service overrides this with
# `python -m worker` (see docker-compose.yml).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
