FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/server.py .

# Railway assigns PORT dynamically
ENV PORT=8080

# Run with gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 server:app
