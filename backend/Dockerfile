FROM python:3.12-slim

WORKDIR /app

# First copy just requirements to leverage Docker cache
COPY ../requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . /app/

# Run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
