FROM python:3.12-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=150

WORKDIR /app

# Kopiuj requirements tylko z bieżącego folderu
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Kopiuj kod tylko z bieżącego folderu
COPY .. /app

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
