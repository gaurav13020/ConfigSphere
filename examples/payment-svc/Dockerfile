FROM python:3.11-slim

WORKDIR /app

# sdk/ and app source are both provided from project root build context
COPY sdk/python /sdk
RUN pip install --no-cache-dir /sdk flask requests

COPY examples/payment-svc/ /app/

EXPOSE 5001
CMD ["python", "app.py"]
