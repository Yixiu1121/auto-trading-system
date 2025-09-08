# Docker 部署指南

本指南將幫助你在虛擬機上部署完整的自動交易系統。

## 📋 系統要求

### 硬件要求

- **CPU**: 2 核心以上
- **記憶體**: 4GB 以上
- **硬碟**: 20GB 以上可用空間
- **網路**: 穩定的網路連接

### 軟件要求

- **操作系統**: Ubuntu 20.04+ / CentOS 7+ / RHEL 7+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 🚀 快速部署

### 1. 安裝 Docker

```bash
# 下載並執行 Docker 安裝腳本
chmod +x scripts/deployment/install_docker.sh
./scripts/deployment/install_docker.sh
```

### 2. 配置系統

```bash
# 編輯配置文件
cp config.yaml.example config.yaml
vim config.yaml
```

### 3. 完整部署

```bash
# 執行完整部署
chmod +x scripts/deployment/deploy.sh
./scripts/deployment/deploy.sh deploy
```

## 📁 目錄結構

```
vibe_coding/
├── Dockerfile                 # Docker 鏡像定義
├── docker-compose.yml         # Docker Compose 配置
├── .dockerignore             # Docker 忽略文件
├── config.yaml               # 系統配置文件
├── requirements.txt          # Python 依賴
├── scripts/
│   ├── deployment/
│   │   ├── deploy.sh         # 部署腳本
│   │   └── install_docker.sh  # Docker 安裝腳本
│   ├── trading/              # 交易相關腳本
│   ├── data/                 # 數據處理腳本
│   └── analysis/             # 分析腳本
├── src/                      # 源代碼
├── logs/                     # 日誌文件
├── data/                     # 數據文件
└── certs/                    # 憑證文件
```

## 🔧 詳細配置

### 環境變數

在 `docker-compose.yml` 中設置的環境變數：

```yaml
environment:
  - PYTHONPATH=/app/src
  - TZ=Asia/Taipei
  - DB_HOST=postgres
  - DB_PORT=5432
  - DB_NAME=trading_system
  - DB_USER=trading_user
  - DB_PASSWORD=trading_password123
  - REDIS_HOST=redis
  - REDIS_PORT=6379
```

### 數據庫配置

```yaml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: trading_system
    POSTGRES_USER: trading_user
    POSTGRES_PASSWORD: trading_password123
  ports:
    - '5432:5432'
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### Redis 配置

```yaml
redis:
  image: redis:7-alpine
  ports:
    - '6379:6379'
  volumes:
    - redis_data:/data
```

## 🎯 部署選項

### 完整部署

```bash
./scripts/deployment/deploy.sh deploy
```

### 分步驟部署

1. **啟動數據庫**

```bash
docker-compose up -d postgres redis
```

2. **數據遷移**

```bash
./scripts/deployment/deploy.sh migrate
```

3. **計算技術指標**

```bash
./scripts/deployment/deploy.sh indicators
```

4. **執行策略分析**

```bash
./scripts/deployment/deploy.sh strategies
```

5. **啟動自動交易**

```bash
./scripts/deployment/deploy.sh start
```

## 📊 監控和管理

### 檢查服務狀態

```bash
./scripts/deployment/deploy.sh status
```

### 查看日誌

```bash
./scripts/deployment/deploy.sh logs
```

### 重啟服務

```bash
./scripts/deployment/deploy.sh restart
```

### 停止服務

```bash
./scripts/deployment/deploy.sh stop
```

## 🔍 故障排除

### 常見問題

1. **Docker 權限問題**

```bash
# 將用戶添加到 docker 組
sudo usermod -aG docker $USER
newgrp docker
```

2. **端口衝突**

```bash
# 檢查端口使用情況
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
```

3. **磁碟空間不足**

```bash
# 清理 Docker 資源
./scripts/deployment/deploy.sh cleanup
```

4. **網路連接問題**

```bash
# 檢查容器網路
docker network ls
docker network inspect vibe_coding_trading_network
```

### 日誌分析

```bash
# 查看特定服務日誌
docker-compose logs trading_system
docker-compose logs postgres
docker-compose logs redis

# 實時監控日誌
docker-compose logs -f trading_system
```

## 🔐 安全配置

### 憑證管理

1. **創建憑證目錄**

```bash
mkdir -p certs
chmod 700 certs
```

2. **放置富邦證券憑證**

```bash
# 將富邦證券憑證文件放入 certs 目錄
cp /path/to/your/cert.pem certs/
```

3. **更新配置文件**

```yaml
fubon:
  cert_filepath: '/app/certs/cert.pem'
```

### 環境變數

使用 `.env` 文件存儲敏感信息：

```bash
# 創建 .env 文件
cat > .env << EOF
FUBON_ID=your_id
FUBON_PWD=your_password
FUBON_CERTPWD=your_cert_password
FUBON_TARGET_ACCOUNT=your_account
FINMIND_TOKEN=your_finmind_token
EOF

# 設置權限
chmod 600 .env
```

## 📈 性能優化

### 資源限制

在 `docker-compose.yml` 中添加資源限制：

```yaml
trading_system:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

### 數據庫優化

```yaml
postgres:
  environment:
    POSTGRES_DB: trading_system
    POSTGRES_USER: trading_user
    POSTGRES_PASSWORD: trading_password123
    # 性能優化參數
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_WORK_MEM: 4MB
```

## 🔄 備份和恢復

### 數據庫備份

```bash
# 創建備份
docker-compose exec postgres pg_dump -U trading_user trading_system > backup.sql

# 恢復備份
docker-compose exec -T postgres psql -U trading_user trading_system < backup.sql
```

### 完整系統備份

```bash
# 備份數據卷
docker run --rm -v vibe_coding_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# 恢復數據卷
docker run --rm -v vibe_coding_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## 🚨 緊急處理

### 系統故障

1. **停止所有服務**

```bash
./scripts/deployment/deploy.sh stop
```

2. **檢查錯誤日誌**

```bash
docker-compose logs --tail=100
```

3. **重啟服務**

```bash
./scripts/deployment/deploy.sh restart
```

### 數據恢復

```bash
# 從備份恢復
docker-compose down
docker volume rm vibe_coding_postgres_data
docker-compose up -d postgres
# 恢復備份數據
```

## 📞 支持

如果遇到問題，請檢查：

1. **日誌文件**: `logs/` 目錄
2. **Docker 日誌**: `docker-compose logs`
3. **系統資源**: `docker stats`
4. **網路連接**: `docker network inspect`

## 🎉 部署完成

部署完成後，系統將自動：

- ✅ 啟動 PostgreSQL 數據庫
- ✅ 啟動 Redis 緩存
- ✅ 初始化數據庫結構
- ✅ 執行數據遷移
- ✅ 計算技術指標
- ✅ 執行策略分析
- ✅ 啟動自動交易系統

系統將在交易時間自動監控市場並執行交易策略！


