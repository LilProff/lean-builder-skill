FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Cloud Run sets PORT; 8080 is the local default.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
