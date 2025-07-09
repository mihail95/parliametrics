FROM python:3.11-slim
WORKDIR /worker

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV PYTHONPATH=/app/backend
CMD ["python", "worker.py"]