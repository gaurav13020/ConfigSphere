FROM python:3.12-slim

WORKDIR /app

COPY services/worker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/worker /app
COPY shared /shared

ENV PYTHONPATH=/app:/shared

CMD ["python", "-m", "app.main"]
