FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .

# 创建非root用户
RUN useradd -m -u 1000 mcpuser
USER mcpuser

# 运行MCP服务器
CMD ["python", "main.py"]