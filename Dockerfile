FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y cron tzdata && rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
COPY cron/2fa-cron /etc/cron.d/2fa-cron
RUN sed -i 's/\r$//' /etc/cron.d/2fa-cron
RUN chmod 0644 /etc/cron.d/2fa-cron && crontab /etc/cron.d/2fa-cron
RUN mkdir -p /data /cron && chmod 755 /data /cron
RUN echo '#!/bin/bash\ncron\nuvicorn main:app --host 0.0.0.0 --port 8080' > start.sh && chmod +x start.sh
EXPOSE 8080
CMD ["./start.sh"]