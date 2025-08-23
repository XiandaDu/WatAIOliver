FROM python:3.10-slim
WORKDIR /app
RUN mkdir machine_learning
RUN mkdir tmp
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm -f /tmp/requirements.txt
COPY . /app/machine_learning
ENV PYTHONPATH=/app/machine_learning
EXPOSE 8002
CMD ["python", "-m", "uvicorn", "pdf_processor.main:app", "--host", "0.0.0.0", "--port", "8002"]