# 專案結構說明

## 📁 目錄結構

```
vibe_coding/
├── 📄 main.py                    # 主程式入口
├── 📄 config.yaml               # 系統配置文件
├── 📄 requirements.txt          # Python 依賴包
├── 📄 README.md                 # 專案說明文件
├── 📄 docker-compose.yml        # Docker 容器配置
│
├── 📁 src/                      # 核心源代碼
│   ├── 📁 modules/              # 功能模組
│   │   ├── 📁 data_fetcher/     # 數據獲取模組
│   │   │   ├── finmind_fetcher.py
│   │   │   └── __init__.py
│   │   ├── 📁 technical_indicators/  # 技術指標模組
│   │   │   ├── calculator.py
│   │   │   ├── storage.py
│   │   │   ├── indicators.py
│   │   │   └── __init__.py
│   │   ├── 📁 strategies/       # 交易策略模組
│   │   │   ├── strategy_base.py
│   │   │   ├── blue_long.py
│   │   │   ├── blue_short.py
│   │   │   ├── executor.py
│   │   │   └── __init__.py
│   │   ├── 📁 database/         # 數據庫模組
│   │   │   ├── models.py
│   │   │   ├── init_db.py
│   │   │   └── __init__.py
│   │   ├── 📁 stock_pool/       # 股池管理模組
│   │   ├── 📁 risk_manager/     # 風險控制模組
│   │   ├── 📁 trader/           # 交易執行模組
│   │   └── 📁 monitor/          # 監控記錄模組
│
├── 📁 scripts/                  # 腳本文件
│   ├── 📁 data_migration/       # 數據遷移腳本
│   │   ├── data_migrate.py
│   │   ├── sync_daily_data.py
│   │   ├── calculate_indicators.py
│   │   └── debug_finmind_api.py
│   │
│   ├── 📁 visualization/        # 可視化腳本
│   │   ├── visualize_strategy_results.py
│   │   ├── visualize_strategy_analysis.py
│   │   └── visualize_test_data.py
│   │
│   ├── 📁 testing/              # 測試腳本
│   │   ├── run_tests.py
│   │   ├── test_blue_long_strategy.py
│   │   ├── test_blue_short_strategy.py
│   │   ├── test_technical_indicators.py
│   │   └── test_data_generator.py
│   │
│   └── 📁 setup/                # 設置腳本
│       ├── init_database.py
│       ├── configure_pgadmin.py
│       ├── start_db.sh
│       ├── stop_db.sh
│       └── init-scripts/
│           ├── 01-init-tables.sql
│           └── 02-configure-pgadmin.sql
│

│
├── 📁 docs/                     # 文檔文件
│   ├── 📁 api/                  # API 文檔
│   │   └── FINMIND_INTEGRATION_README.md
│   ├── 📁 deployment/           # 部署文檔
│   └── 📁 development/          # 開發文檔
│       ├── VISUALIZATION_README.md
│       ├── examples/
│       │   └── database_usage.py
│       └── PROJECT_STRUCTURE.md
│
├── 📁 data/                     # 數據文件
├── 📁 logs/                     # 日誌文件
│   ├── trading_system.log
│   ├── calculate_indicators.log
│   ├── data_migrate.log
│   └── ...
├── 📁 output/                   # 輸出文件
│   ├── strategy_analysis_*.png
│   ├── buy_sell_conditions_analysis.png
│   ├── conditions_summary.png
│   ├── entry_exit_points.png
│   └── test_data_kline_chart.png
└── 📁 venv/                     # Python 虛擬環境
```

## 📋 目錄說明

### 🎯 核心目錄

- **`main.py`**: 系統主入口，整合所有功能
- **`src/`**: 核心源代碼，包含所有業務邏輯
- **`config.yaml`**: 系統配置文件

### 🔧 腳本目錄 (`scripts/`)

- **`data_migration/`**: 數據遷移相關腳本

  - `data_migrate.py`: 主要數據遷移腳本
  - `sync_daily_data.py`: 每日數據同步
  - `calculate_indicators.py`: 技術指標計算
  - `debug_finmind_api.py`: API 調試工具

- **`visualization/`**: 可視化相關腳本

  - `visualize_strategy_results.py`: 策略結果可視化
  - `visualize_strategy_analysis.py`: 策略分析圖表
  - `visualize_test_data.py`: 測試數據可視化

- **`testing/`**: 測試相關腳本

  - `run_tests.py`: 測試執行器
  - `test_*.py`: 各種測試文件

- **`setup/`**: 環境設置腳本
  - `init_database.py`: 數據庫初始化
  - `start_db.sh` / `stop_db.sh`: 數據庫啟動/停止
  - `init-scripts/`: SQL 初始化腳本

### 📚 文檔目錄 (`docs/`)

- **`api/`**: API 集成文檔
- **`deployment/`**: 部署相關文檔
- **`development/`**: 開發相關文檔和範例

### 📊 數據目錄

- **`data/`**: 原始數據文件
- **`logs/`**: 系統運行日誌
- **`output/`**: 生成的圖表和報告

## 🚀 使用方式

### 主要功能

```bash
# 執行策略分析
python main.py --mode strategies --stock 2330

# 計算技術指標
python main.py --mode indicators --stock 2330

# 互動模式
python main.py --mode interactive
```

### 數據遷移

```bash
# 執行數據遷移
python scripts/data_migration/data_migrate.py

# 計算技術指標
python scripts/data_migration/calculate_indicators.py
```

### 可視化

```bash
# 生成策略分析圖表
python scripts/visualization/visualize_strategy_results.py
```

### 測試

```bash
# 執行所有測試
python scripts/testing/run_tests.py
```

### 環境設置

```bash
# 初始化數據庫
python scripts/setup/init_database.py

# 啟動數據庫
bash scripts/setup/start_db.sh
```

## 📝 開發規範

1. **模組化設計**: 每個功能都有獨立的模組
2. **清晰分層**: 腳本、工具、文檔分離
3. **統一入口**: 主要功能通過 `main.py` 執行
4. **完整文檔**: 每個目錄都有對應的文檔說明

## 🔄 維護指南

- 新增功能時，請將相關文件放入對應目錄
- 腳本文件統一放在 `scripts/` 下
- 文檔文件統一放在 `docs/` 下
- 保持目錄結構的清晰和一致性
