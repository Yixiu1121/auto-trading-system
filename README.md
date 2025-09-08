# Vibe Coding - Automated Trading System

一個基於藍線空頭策略的自動化交易系統，整合富邦證券 API 和 FinMind 數據源。

## 功能特色

- **藍線空頭策略**: 基於小藍線的空頭交易策略，當價格跌破小藍線且呈負斜率時產生放空信號
- **FinMind 數據整合**: 自動獲取每日股票數據並存儲到 PostgreSQL 數據庫
- **技術指標計算**: 計算藍綠橘三線、斜率、乖離率、成交量比率等技術指標
- **富邦證券 API**: 整合富邦證券 API 進行實時交易
- **Docker 部署**: 支持 Docker 容器化部署到虛擬機

## 技術架構

- **Python 3.10+**
- **PostgreSQL**: 數據存儲
- **Redis**: 緩存和消息隊列
- **Docker & Docker Compose**: 容器化部署
- **Poetry**: 依賴管理

## 安裝與設置

### 前置需求

- Python 3.10+
- Poetry
- PostgreSQL
- Redis (可選)

### 使用 Poetry 安裝

1. 克隆項目：

```bash
git clone <repository-url>
cd vibe_coding
```

2. 安裝依賴：

```bash
poetry install
```

3. 激活虛擬環境：

```bash
poetry shell
```

4. 安裝富邦 SDK (需要手動下載)：

```bash
# 下載 fubon_neo SDK 到 Downloads 目錄
poetry run pip install /Users/yixiu/Downloads/fubon_neo-2.2.4-cp37-abi3-macosx_11_0_arm64.whl
```

### 配置

1. 複製配置文件：

```bash
cp config.yaml.example config.yaml
```

2. 編輯 `config.yaml` 文件，設置：
   - FinMind API 配置
   - PostgreSQL 數據庫連接
   - 富邦證券 API 憑證
   - 交易策略參數

### 數據庫初始化

```bash
poetry run python src/modules/database/init_db.py
```

## 使用方法

### 數據遷移

```bash
poetry run python scripts/data_migration/data_migrate.py
```

### 計算技術指標

```bash
poetry run python scripts/data_migration/calculate_indicators.py
```

### 執行策略

```bash
poetry run python main.py strategies
```

### 自動交易

```bash
poetry run python scripts/trading/run_auto_trading.py
```

## Docker 部署

### 本地測試

```bash
docker-compose up -d
```

### 部署到虛擬機

```bash
# 使用部署腳本
./scripts/deployment/deploy.sh deploy
```

## 項目結構

```
vibe_coding/
├── src/
│   ├── modules/
│   │   ├── strategies/          # 交易策略
│   │   ├── data_fetcher/        # 數據獲取
│   │   ├── database/            # 數據庫模型
│   │   ├── technical_indicators/ # 技術指標
│   │   └── trading/             # 交易模塊
│   └── tests/                   # 測試文件
├── scripts/
│   ├── data_migration/          # 數據遷移腳本
│   ├── trading/                 # 交易腳本
│   └── deployment/              # 部署腳本
├── docs/                        # 文檔
├── config.yaml                  # 配置文件
├── pyproject.toml               # Poetry 配置
├── Dockerfile                   # Docker 配置
└── docker-compose.yml           # Docker Compose 配置
```

## 開發

### 添加新依賴

```bash
poetry add package-name
```

### 添加開發依賴

```bash
poetry add --group dev package-name
```

### 運行測試

```bash
poetry run pytest
```

### 代碼格式化

```bash
poetry run black src/
poetry run flake8 src/
```

## 注意事項

- 富邦 SDK 需要手動下載並安裝
- 確保 PostgreSQL 數據庫已正確配置
- 交易前請在測試環境中驗證策略
- 請遵守相關金融法規和風險管理原則

## 授權

MIT License
