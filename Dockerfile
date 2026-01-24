FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# non-root user for safety
RUN addgroup --system app && adduser --system --ingroup app app || true
USER app
ENTRYPOINT ["python","auto_test.py"]
