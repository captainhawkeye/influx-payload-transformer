# Stage 1: Build stage
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.9-slim
WORKDIR /app
RUN useradd -u 1001 -m influx-payload-transformer
USER influx-payload-transformer
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 5100
CMD ["python3", "run.py"]