FROM python:3.11-slim
WORKDIR /app
COPY scanner.py ./
ENTRYPOINT ["python", "scanner.py"]
CMD ["."]
