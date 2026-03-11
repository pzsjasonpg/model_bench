# 使用Python 3.9作为基础镜像
#FROM docker.1ms.run/python:3.9-slim
FROM docker.1ms.run/ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANGUAGE=zh_CN.UTF-8 \
    TZ=Asia/Shanghai \
    PATH="/root/.local/bin:$PATH"

# 安装系统依赖，包括中文字体和常用工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    gnupg2 \
    software-properties-common \
    git \
    wget \
    build-essential \
    iputils-ping \
    net-tools \
    iproute2 \
    dnsutils \
    curl \
    vim \
    nano \
    less \
    htop \
    procps \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    language-pack-zh-hans \
    locales \
    sudo \
    rsync \
    zip \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 配置中文语言环境
RUN locale-gen zh_CN.UTF-8 && \
    update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh

# 添加deadsnakes PPA并安装Python 3.9
RUN add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.9 \
    python3.9-venv \
    python3.9-dev \
    python3.9-distutils \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 设置Python 3.9为默认Python版本
# 设置 Python 3.9 为默认版本，同时映射 python 和 python3 命令
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

# 验证Python版本
RUN python --version && python3 --version

# 创建虚拟环境
#RUN python -m venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 复制项目代码到容器
COPY requirements.txt /app

# 安装依赖
RUN python -m pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    python -m pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
ENV PYTHONUNBUFFERED=1

# 设置入口命令
CMD ["python", "-m", "src.main"]