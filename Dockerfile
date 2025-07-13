FROM python:3.11-slim
WORKDIR /app
COPY scanner.py /app/scanner.py
CMD ["python", "scanner.py"]
