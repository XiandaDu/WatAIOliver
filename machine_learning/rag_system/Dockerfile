FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY machine_learning/rag_system/requirements.txt ./requirements.txt
# 如果你需要 constraints.txt，请自行 COPY 并在下一行加 -c constraints.txt
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
COPY machine_learning/ ./machine_learning/
ENV PYTHONPATH=/app/machine_learning
EXPOSE 8002
CMD ["python", "-m", "uvicorn", "rag_system.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
