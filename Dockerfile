FROM ubuntu:22.04

# Suppress interactive apt prompts
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    xvfb \
    sqlite3 \
    jq \
    && add-apt-repository -y ppa:xtradeb/apps \
    && apt-get update \
    && apt-get install -y \
    ungoogled-chromium \
    chromium-chromedriver \
    libnss3 libgbm1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 libxss1 libxtst6 libxshmfence1 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (CPU only)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY . /app
WORKDIR /app

# Pull the model at build time (makes container startup faster)
# RUN ollama serve & sleep 5 && ollama pull phi3:3.8b

CMD ["python3", "nexus_prime.py", "--run-hours", "10"]
