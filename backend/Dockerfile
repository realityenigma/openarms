FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

COPY backend/armswideopen /app/armswideopen
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir \
      fastapi==0.109.0 \
      uvicorn==0.27.0 \
      pydantic==2.5.3 \
      pydantic-settings==2.1.0 \
      sqlalchemy==2.0.23 \
      psycopg2-binary==2.9.9 \
      python-multipart==0.0.6 \
      python-jose==3.3.0 \
      passlib==1.7.4 \
      bcrypt==4.1.1 \
      gitpython==3.1.40 \
      requests==2.31.0 \
      aiofiles==23.2.1 \
      email-validator==2.1.0.post1

RUN useradd -m -u 10001 appuser && mkdir -p /app/storage && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "armswideopen.main:app", "--host", "0.0.0.0", "--port", "8000"]
