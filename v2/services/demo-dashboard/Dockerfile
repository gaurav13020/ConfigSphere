FROM python:3.12-slim

WORKDIR /app

COPY services/demo-dashboard/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/demo-dashboard /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]
