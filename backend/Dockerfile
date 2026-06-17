FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
