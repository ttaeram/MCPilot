FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
COPY app/ ./app/

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]