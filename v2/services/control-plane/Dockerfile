FROM python:3.12-slim

WORKDIR /app

COPY services/control-plane/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/control-plane /app
COPY shared /shared

ENV PYTHONPATH=/app:/shared

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8100"]
