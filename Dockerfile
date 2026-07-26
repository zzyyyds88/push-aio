# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm main" > /etc/apt/sources.list \
    && echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm-updates main" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.ustc.edu.cn/debian-security/ bookworm-security main" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends tzdata ca-certificates \
    && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY README.md ./
RUN pip install --no-cache-dir --no-deps -e .

RUN mkdir -p /app/data
VOLUME /app/data

EXPOSE 8080
CMD ["python", "-m", "pushhub.main"]
