# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目代码到容器
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 配置环境变量
ENV PYTHONUNBUFFERED=1

# 设置入口命令
CMD ["python", "-m", "src.main"]