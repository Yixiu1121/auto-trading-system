# 富邦證券 SDK 安裝指南

## 📋 概述

本系統使用富邦證券提供的 `fubon_neo.sdk` 進行自動交易。如果 SDK 未安裝，系統會自動降級為模擬模式。

## 🔧 安裝方式

### 方式一：從 PyPI 安裝（如果可用）

```bash
pip install fubon-neo-sdk
```

### 方式二：從 GitHub 安裝

```bash
# 克隆富邦證券 API 教學倉庫
git clone https://github.com/Tradepm/-API.git
cd -API/20240418_新一代API_Python自動下單小幫手

# 安裝 SDK
pip install -e .
```

### 方式三：手動安裝

如果上述方式都不可用，可以手動下載並安裝：

```bash
# 下載 SDK 文件
wget https://github.com/Tradepm/-API/raw/main/20240418_新一代API_Python自動下單小幫手/fubon_neo_sdk.zip

# 解壓並安裝
unzip fubon_neo_sdk.zip
cd fubon_neo_sdk
pip install -e .
```

## ✅ 驗證安裝

安裝完成後，運行以下命令驗證：

```bash
python -c "from fubon_neo.sdk import FubonNeoAPI; print('SDK 安裝成功')"
```

如果沒有錯誤，說明安裝成功。

## 🔧 配置登入憑證

在 `config.yaml` 中配置你的富邦證券登入憑證：

```yaml
fubon:
  # 登入憑證
  id: 'YOUR_ID' # 請填入實際的登入 ID
  pwd: 'YOUR_PASSWORD' # 請填入實際的登入密碼
  cert_filepath: 'YOUR_CERT_PATH' # 請填入憑證檔案路徑
  certpwd: 'YOUR_CERT_PASSWORD' # 請填入憑證密碼
  target_account: 'YOUR_ACCOUNT' # 請填入目標交易帳號

  # 交易設定
  trading:
    max_order_amount: 100000 # 最大單筆訂單金額
    min_order_quantity: 1000 # 最小訂單數量
    max_positions: 5 # 最大同時持倉數
```

### 環境變數配置（推薦）

為了安全起見，建議使用環境變數存儲敏感信息。創建 `.env` 文件：

```bash
# .env 文件
ID=your_login_id
PWD=your_login_password
CPATH=/path/to/your/certificate.p12
CPWD=your_certificate_password
ACCOUNT=your_target_account
TRADELIST=/path/to/trade_list.xlsx
```

## 🧪 測試連接

運行測試腳本驗證 API 連接：

```bash
python scripts/trading/test_fubon_api.py
```

## 📚 SDK 功能

### 主要功能

1. **帳戶管理**

   - 獲取帳戶信息
   - 查詢持倉
   - 獲取訂單列表

2. **交易功能**

   - 下單（限價單/市價單）
   - 取消訂單
   - 查詢訂單狀態

3. **市場數據**

   - 獲取實時價格
   - 查詢市場數據
   - 獲取歷史數據

4. **交易條件檢查**
   - 檢查買賣條件
   - 驗證市場開盤狀態

### 使用範例

```python
from fubon_neo.sdk import FubonSDK
from fubon_neo.sdk import Order
from fubon_neo.constant import OrderType, TimeInForce, PriceType, MarketType, BSAction

# 初始化 SDK
sdk = FubonSDK()

# 登入
response = sdk.login(
    id="YOUR_ID",
    pwd="YOUR_PASSWORD",
    cert_filepath="YOUR_CERT_PATH",
    certpwd="YOUR_CERT_PASSWORD"
)

# 設置帳號
accounts = response.data
active_account = None
for account in accounts:
    if "YOUR_ACCOUNT" == account.account:
        active_account = account
        break

# 建立行情連線
sdk.init_realtime()

# 下單
order = Order(
    buy_sell=BSAction.Buy,
    symbol="2330",
    price=800.0,
    quantity=1000,
    market_type=MarketType.Common,
    price_type=PriceType.Limit,
    time_in_force=TimeInForce.ROD,
    order_type=OrderType.Stock,
)

result = sdk.stock.place_order(active_account, order)
```

## ⚠️ 注意事項

1. **API 憑證安全**

   - 請妥善保管 API 憑證
   - 不要將憑證提交到版本控制系統
   - 建議使用環境變數存儲敏感信息

2. **交易風險**

   - 請在模擬環境中充分測試
   - 了解交易風險，謹慎使用自動交易
   - 設置適當的風險控制參數

3. **網絡連接**
   - 確保網絡連接穩定
   - 設置適當的超時時間
   - 處理網絡異常情況

## 🔍 故障排除

### 常見問題

1. **SDK 安裝失敗**

   ```bash
   # 檢查 Python 版本
   python --version

   # 更新 pip
   pip install --upgrade pip

   # 清理緩存
   pip cache purge
   ```

2. **API 連接失敗**

   - 檢查 API 憑證是否正確
   - 確認網絡連接正常
   - 檢查防火牆設置

3. **下單失敗**
   - 檢查帳戶餘額
   - 確認股票代碼正確
   - 檢查交易時間

### 調試工具

```bash
# 測試 SDK 導入
python -c "import fubon_neo.sdk; print('SDK 可用')"

# 測試 API 連接
python scripts/trading/test_fubon_api.py

# 查看詳細日誌
tail -f logs/test_fubon_api.log
```

## 📞 支援

如果遇到問題，請：

1. 檢查日誌文件中的錯誤信息
2. 確認 SDK 版本是否正確
3. 聯繫富邦證券技術支援
4. 參考官方文檔和範例

---

**⚠️ 重要提醒：**

- 請在模擬環境中充分測試後再進行真實交易
- 了解交易風險，謹慎使用自動交易功能
- 定期檢查系統運行狀態和交易記錄
