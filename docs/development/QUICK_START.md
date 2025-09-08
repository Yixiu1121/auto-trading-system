# 快速開始指南

## 🚀 快速上手

### 1. 環境準備

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動數據庫
bash scripts/setup/start_db.sh
```

### 2. 初始化系統

```bash
# 初始化數據庫
python scripts/setup/init_database.py

# 遷移數據
python scripts/data_migration/data_migrate.py

# 計算技術指標
python scripts/data_migration/calculate_indicators.py
```

### 3. 執行策略

```bash
# 執行策略分析
python main.py --mode strategies --stock 2330

# 互動模式
python main.py --mode interactive
```

## 📋 常用命令

### 主要功能

| 功能     | 命令                                            |
| -------- | ----------------------------------------------- |
| 策略分析 | `python main.py --mode strategies --stock 2330` |
| 技術指標 | `python main.py --mode indicators --stock 2330` |
| 互動模式 | `python main.py --mode interactive`             |

### 數據管理

| 功能     | 命令                                                    |
| -------- | ------------------------------------------------------- |
| 數據遷移 | `python scripts/data_migration/data_migrate.py`         |
| 計算指標 | `python scripts/data_migration/calculate_indicators.py` |
| 每日同步 | `python scripts/data_migration/sync_daily_data.py`      |

### 可視化

| 功能       | 命令                                                         |
| ---------- | ------------------------------------------------------------ |
| 策略分析圖 | `python scripts/visualization/visualize_strategy_results.py` |
| 測試數據圖 | `python scripts/visualization/visualize_test_data.py`        |

### 測試

| 功能         | 命令                                                 |
| ------------ | ---------------------------------------------------- |
| 執行測試     | `python scripts/testing/run_tests.py`                |
| 藍線多頭測試 | `python scripts/testing/test_blue_long_strategy.py`  |
| 藍線空頭測試 | `python scripts/testing/test_blue_short_strategy.py` |

### 環境管理

| 功能         | 命令                                    |
| ------------ | --------------------------------------- |
| 啟動數據庫   | `bash scripts/setup/start_db.sh`        |
| 停止數據庫   | `bash scripts/setup/stop_db.sh`         |
| 初始化數據庫 | `python scripts/setup/init_database.py` |

## 🔧 配置文件

主要配置文件：`config.yaml`

```yaml
database:
  host: localhost
  port: 5432
  database: trading_system
  user: trading_user
  password: trading_password123

finmind:
  token: your_finmind_token
  base_url: https://api.finmindtrade.com
```

## 📊 輸出文件

- **日誌文件**: `logs/` 目錄
- **圖表文件**: `output/` 目錄
- **數據文件**: `data/` 目錄

## 🆘 故障排除

### 常見問題

1. **數據庫連接失敗**

   ```bash
   # 檢查數據庫狀態
   bash scripts/setup/start_db.sh
   ```

2. **API 請求失敗**

   ```bash
   # 測試 API 連接
   python scripts/data_migration/debug_finmind_api.py
   ```

3. **策略執行錯誤**
   ```bash
   # 檢查數據完整性
   python scripts/testing/run_tests.py
   ```

## 📚 更多文檔

- [專案結構說明](PROJECT_STRUCTURE.md)
- [API 集成文檔](../api/FINMIND_INTEGRATION_README.md)
- [可視化文檔](VISUALIZATION_README.md)


