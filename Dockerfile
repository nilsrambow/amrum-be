# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy and install Python dependencies as root
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create startup script with correct postgres hostname
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Waiting for PostgreSQL to be ready..."\n\
while  pg_isready -h postgres -p 5432 -U "$POSTGRES_USER"; do\n\
  echo "PostgreSQL is unavailable - sleeping"\n\
  sleep 2\n\
done\n\
echo "PostgreSQL is ready!"\n\
# echo "Running database migrations..."\n\
# alembic upgrade head\n\
echo "Starting application..."\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown appuser:appuser /app/start.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting application..."\n\
python main.py' > /app/start.sh && chmod +x /app/start.sh

# Command to run your app
CMD ["/app/start.sh"]
