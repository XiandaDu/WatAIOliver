FROM python:3.10-slim
WORKDIR /app
RUN mkdir backend
COPY . /app/backend
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]