FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CAMPUSONE_DATA_DIR=/data COOKIE_SECURE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data
EXPOSE 5000
CMD ["sh","-c","if [ \"${CAMPUSONE_DEMO_MODE:-0}\" = \"1\" ]; then python database/seed_demo.py; fi; exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 8 --timeout 60 app:app"]
