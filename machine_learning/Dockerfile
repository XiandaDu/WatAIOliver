FROM python:3.10-slim
WORKDIR /app
RUN mkdir machine_learning
COPY . /app/machine_learning
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/machine_learning
EXPOSE 8002
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]