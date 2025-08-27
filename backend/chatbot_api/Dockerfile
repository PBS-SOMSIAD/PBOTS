FROM python:3.12-slim

WORKDIR /app

# Kopiuj requirements tylko z bieżącego folderu
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Kopiuj kod tylko z bieżącego folderu
COPY .. /app

# Run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
