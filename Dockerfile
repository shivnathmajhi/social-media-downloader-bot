FROM python:3.12-slim

# Install FFmpeg, ffprobe and required system tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL=/root/.deno
ENV PATH=/root/.deno/bin:$PATH

WORKDIR /app

# Install Python dependencies first for better Docker caching
COPY requirements.txt .

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Start Telegram bot
CMD ["python", "bot.py"]