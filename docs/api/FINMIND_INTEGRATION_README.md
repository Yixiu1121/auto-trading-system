# FinMind 數據獲取器整合說明

## 概述

本模組整合了 FinMind API，用於自動獲取台灣股票市場的歷史和實時數據，並將數據存儲到 PostgreSQL 數據庫中。

## 功能特性

- **自動數據獲取**: 從 FinMind API 獲取股票 OHLCV 數據
- **數據庫存儲**: 自動將數據存儲到 PostgreSQL 數據庫
- **每日同步**: 支持每日自動更新最新數據
- **批量處理**: 支持批量處理多支股票
- **錯誤處理**: 完善的錯誤處理和重試機制
- **健康檢查**: 提供 API 和數據庫連接狀態檢查

## 安裝和配置

### 1. 安裝依賴

```bash
pip install requests pandas psycopg2-binary schedule loguru pyyaml
```

### 2. 獲取 FinMind API Token

1. 訪問 [FinMind](https://finmindtrade.com/)
2. 註冊帳號並登錄
3. 在個人設置中獲取 API Token

### 3. 設置環境變量

```bash
export FINMIND_TOKEN="your_finmind_api_token_here"
```

或者將 token 添加到 `config.yaml` 文件中：

```yaml
finmind:
  api_token: 'your_finmind_api_token_here'
  base_url: 'https://api.finmindtrade.com'
  timeout: 30
  retry_count: 3
  retry_delay: 1
```

### 4. 配置數據庫

確保 `config.yaml` 中的數據庫配置正確：

```yaml
database:
  host: 'localhost'
  port: 5432
  database: 'trading_system'
  user: 'trading_user'
  password: 'trading_password'
```

## 使用方法

### 1. 基本使用

```python
from src.modules.data_fetcher import FinMindFetcher
import yaml

# 加載配置
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 創建數據獲取器
fetcher = FinMindFetcher(config)

# 獲取股票列表
stocks = fetcher.get_stock_list()

# 獲取單支股票數據
df = fetcher.get_stock_data("2330", "2024-01-01", "2024-01-31")

# 存儲數據到數據庫
fetcher.connect_database()
fetcher.store_stock_data("2330", df)
fetcher.close_database()
```

### 2. 初始化數據庫

```python
# 初始化數據庫，獲取過去30天的數據
fetcher.initialize_database(days_back=30)

# 或者指定特定股票
fetcher.initialize_database(stock_ids=["2330", "2317", "2454"], days_back=30)
```

### 3. 每日數據更新

```python
# 更新所有股票的每日數據
fetcher.update_daily_data()

# 或者更新特定股票
fetcher.update_daily_data(stock_ids=["2330", "2317"])
```

## 腳本使用

### 1. 測試腳本

```bash
# 測試基本功能
python test_finmind_fetcher.py
```

### 2. 數據同步腳本

```bash
# 執行初始數據同步
python sync_daily_data.py init

# 執行一次每日數據同步
python sync_daily_data.py daily

# 啟動定時調度器（每日14:00自動同步）
python sync_daily_data.py schedule

# 交互模式
python sync_daily_data.py
```

## API 端點

FinMind API 提供以下主要端點：

- **股票信息**: `/api/v4/stock_info` - 獲取股票基本信息
- **股票價格**: `/api/v4/stock_price` - 獲取股票 OHLCV 數據
- **財務數據**: `/api/v4/financial_statement` - 獲取財務報表數據
- **技術指標**: `/api/v4/technical_indicator` - 獲取技術指標數據

## 數據格式

### 股票價格數據

```json
{
  "date": "2024-01-15",
  "open": 100.5,
  "high": 102.3,
  "low": 99.8,
  "close": 101.2,
  "volume": 1500000
}
```

### 股票信息數據

```json
{
  "stock_id": "2330",
  "name": "台積電",
  "industry": "半導體業",
  "market": "TSE"
}
```

## 錯誤處理

### 常見錯誤

1. **API Token 無效**

   - 檢查環境變量 `FINMIND_TOKEN` 是否正確設置
   - 確認 Token 是否過期

2. **數據庫連接失敗**

   - 檢查 PostgreSQL 服務是否運行
   - 確認數據庫連接參數是否正確

3. **API 請求超時**
   - 檢查網絡連接
   - 調整 `timeout` 參數

### 重試機制

系統內建重試機制，當 API 請求失敗時會自動重試：

```yaml
finmind:
  retry_count: 3 # 重試次數
  retry_delay: 1 # 重試間隔（秒）
```

## 性能優化

### 1. 批量處理

- 使用 `initialize_database()` 批量處理多支股票
- 避免頻繁的單個 API 請求

### 2. 請求頻率控制

- 系統自動控制 API 請求頻率（0.5 秒間隔）
- 避免觸發 API 限制

### 3. 數據庫優化

- 使用 UPSERT 語句避免重複數據
- 建立適當的索引提高查詢性能

## 監控和日誌

### 日誌配置

日誌文件位置：`logs/daily_sync.log`

日誌格式：

```
2024-01-15 14:00:00 | INFO | 開始同步每日數據
2024-01-15 14:00:01 | INFO | 成功獲取 2330 的 1 筆數據
2024-01-15 14:00:02 | INFO | 每日數據同步完成
```

### 健康檢查

```python
# 檢查系統健康狀態
health_status = fetcher.health_check()
print(f"API 狀態: {health_status['api_status']}")
print(f"數據庫狀態: {health_status['database_status']}")
```

## 注意事項

1. **API 限制**: 注意 FinMind API 的請求頻率限制
2. **數據質量**: 驗證獲取的數據完整性和準確性
3. **備份策略**: 定期備份數據庫中的重要數據
4. **監控告警**: 設置監控告警，及時發現數據同步問題

## 故障排除

### 1. 檢查 API 連接

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://api.finmindtrade.com/api/v4/stock_info?dataset=TaiwanStockInfo"
```

### 2. 檢查數據庫連接

```bash
psql -h localhost -U trading_user -d trading_system
```

### 3. 查看日誌

```bash
tail -f logs/daily_sync.log
```

## 更新日誌

- **v1.0.0**: 初始版本，支持基本的數據獲取和存儲功能
- **v1.1.0**: 添加每日數據同步和定時調度功能
- **v1.2.0**: 優化錯誤處理和重試機制

## 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個模組。

## 授權

本模組遵循項目的整體授權條款。
