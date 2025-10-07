# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables (optional, for unbuffered output)
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for PostgreSQL to be ready..."\n\
while ! pg_isready -h postgres -p 5432 -U amrum_user; do\n\
  echo "PostgreSQL is unavailable - sleeping"\n\
  sleep 1\n\
done\n\
echo "PostgreSQL is ready!"\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting application..."\n\
python main.py' > /app/start.sh && chmod +x /app/start.sh

# Command to run your app
CMD ["/app/start.sh"]
