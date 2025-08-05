# 使用官方 Python 運行時作為基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=${PORT:-8501}
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 暴露端口
EXPOSE ${PORT:-8501}

# 設置健康檢查
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health

# 運行應用程式
CMD ["streamlit", "run", "texas_holdem_enhanced_ui.py", "--server.port=8501", "--server.address=0.0.0.0", "--theme.base=dark"]