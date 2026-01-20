FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Install Python libraries + Gunicorn
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

COPY . .

# Set timezone for Scheduler
ENV TZ=Europe/Warsaw
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 5000

CMD ["sh", "start.sh"]