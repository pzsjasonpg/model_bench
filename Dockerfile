# 使用Ubuntu 22.04作为基础镜像
FROM docker.1ms.run/ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LANG=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    LANGUAGE=zh_CN.UTF-8 \
    PATH="/root/.local/bin:$PATH"

# 安装系统依赖，包括中文字体和常用工具
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh && \
    # 配置默认中文字体
    echo "export LANG=zh_CN.UTF-8" >> /root/.bashrc && \
    echo "export LC_ALL=zh_CN.UTF-8" >> /root/.bashrc

# 添加deadsnakes PPA并安装Python 3.9
RUN apt-get update && \
    apt-get install -y python3.9 python3.9-venv python3.9-dev python3.9-pip && \
    rm -rf /var/lib/apt/lists/*

# 正确设置Python版本别名
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
    # 创建python指向python3的软链接（解决python命令不存在问题）
    ln -s /usr/bin/python3 /usr/bin/python && \
    # 验证Python版本
    python --version && \
    python3 --version

# 创建并激活虚拟环境
RUN python -m venv /opt/venv && \
    # 升级pip到最新版本
    /opt/venv/bin/pip install --upgrade pip setuptools wheel

# 将虚拟环境加入PATH（确保后续命令使用虚拟环境中的Python）
ENV PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 复制项目代码到容器
COPY . /app

# 安装依赖（使用虚拟环境中的pip）
RUN pip install --no-cache-dir -r requirements.txt

# 确保Python输出无缓冲
ENV PYTHONUNBUFFERED=1

# 设置入口命令
CMD ["python", "-m", "src.main"]