# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables (optional, for unbuffered output)
ENV PYTHONUNBUFFERED=1

# Command to run your app
CMD ["python", "main.py"]
