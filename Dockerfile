FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Default port (Railway overrides with $PORT)
ENV PORT=5002

# Run with gunicorn using shell form to expand $PORT
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 src.server:app
