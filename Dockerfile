FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN python -m venv $VENV_PATH \
    && $VENV_PATH/bin/pip install --no-cache-dir --upgrade pip \
    && $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt

COPY auth_service/ ./auth_service/
COPY authentication/ ./authentication/
COPY permissions.json manage.py ./
COPY tests/ ./tests/

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/venv

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder $VENV_PATH $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

COPY --from=builder /app /app

EXPOSE 8005

CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]
