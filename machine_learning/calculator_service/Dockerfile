# Use the official Python slim base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (for compiling SymPy)
RUN apt-get update && \
    apt-get install -y build-essential libgmp-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]