FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY machine_learning/pdf_processor/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
COPY machine_learning/ ./machine_learning/
ENV PYTHONPATH=/app/machine_learning
EXPOSE 8001
CMD ["python", "-m", "uvicorn", "pdf_processor.main:app", "--host", "0.0.0.0", "--port", "8001"]
