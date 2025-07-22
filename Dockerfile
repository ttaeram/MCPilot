FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . . 

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]