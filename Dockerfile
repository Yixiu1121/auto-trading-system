# 使用 Python 3.10 作為基礎鏡像
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Taipei

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  curl \
  wget \
  git \
  unzip \
  && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 下載並安裝富邦SDK
RUN wget https://www.fbs.com.tw/TradeAPI_SDK/fubon_binary/fubon_neo-2.2.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.zip \
  && unzip fubon_neo-2.2.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.zip \
  && pip install fubon_neo-2.2.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl \
  && rm fubon_neo-2.2.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.zip \
  && rm fubon_neo-2.2.4-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

# 複製應用程式代碼
COPY . .

# 創建必要的目錄
RUN mkdir -p /app/logs \
  && mkdir -p /app/data \
  && mkdir -p /app/certs

# 設置權限
RUN chmod +x /app/scripts/trading/*.py

# 暴露端口（如果需要 Web 界面）
EXPOSE 8000

# 設置健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# 默認命令
CMD ["python", "scripts/trading/run_auto_trading.py"]


