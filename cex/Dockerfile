# 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到工作目录
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir schedule requests

# 安装 Supervisor
RUN apt-get update && \
    apt-get install -y --no-install-recommends supervisor && \
    rm -rf /var/lib/apt/lists/*

# 复制 Supervisor 配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 启动 Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]