FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY input.py input_backup.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set required environment variables (must be provided at runtime)
ENV EXTERNAL_API_KEY=""
ENV DB_USER=""
ENV DB_PASS=""
ENV SERVICE_TOKEN=""
ENV RSA_PRIVATE_KEY=""

# Create logs directory
RUN mkdir -p logs

# Default command
CMD ["python", "input.py"]
