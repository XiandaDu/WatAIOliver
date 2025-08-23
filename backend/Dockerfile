FROM python:3.10-slim
WORKDIR /app
RUN mkdir backend
RUN mkdir tmp
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm -f /tmp/requirements.txt
COPY . /app/backend
ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]