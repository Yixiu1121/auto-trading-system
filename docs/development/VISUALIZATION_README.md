# 測試數據可視化模組說明

## 🎯 模組優化概述

本次優化將原本分散在各個測試文件中的測試數據生成邏輯統一抽取到 `TestDataGenerator` 類中，實現了代碼的模組化和重用。

## 📁 文件結構

```
src/tests/
├── test_data_generator.py          # 🆕 測試數據生成器（共用模組）
├── visualize_test_data.py          # 📊 基礎可視化腳本
├── visualize_strategy_analysis.py  # 🆕 策略分析可視化腳本
├── test_technical_indicators.py    # ✅ 技術指標測試
└── test_blue_long_strategy.py      # ✅ 策略測試
```

## 🔧 主要優化內容

### 1. **TestDataGenerator 類** 🆕

- **統一數據生成**：將原本分散的測試數據創建邏輯集中管理
- **多場景支持**：支持多頭趨勢、空頭趨勢、橫盤整理、突破形態等不同市場場景
- **配置管理**：統一的測試配置管理，避免重複定義

#### 主要方法：

```python
# 多頭趨勢數據
create_bull_trend_data(periods=100, base_price=100.0)

# 空頭趨勢數據
create_bear_trend_data(periods=100, base_price=100.0)

# 橫盤整理數據
create_sideways_data(periods=100, base_price=100.0)

# 突破形態數據
create_breakout_data(periods=100, base_price=100.0)

# 獲取測試配置
get_test_config()
```

### 2. **代碼重用優化** ✅

- **消除重複**：原本 `_create_test_data()` 方法在多個文件中重複定義
- **統一接口**：所有測試文件都使用相同的數據生成接口
- **易於維護**：數據生成邏輯的修改只需要在一個地方進行

#### 優化前：

```python
# 每個測試文件都有自己的 _create_test_data 方法
def _create_test_data(self) -> pd.DataFrame:
    # 重複的數據創建邏輯...
    pass
```

#### 優化後：

```python
# 使用統一的數據生成器
def _create_test_data(self) -> pd.DataFrame:
    from .test_data_generator import test_data_generator
    return test_data_generator.create_bull_trend_data(periods=100, base_price=100.0)
```

### 3. **可視化腳本優化** 📊

- **模組化設計**：可視化邏輯與數據生成邏輯分離
- **多場景分析**：支持不同市場場景的策略表現分析
- **圖表豐富**：提供 K 線圖、技術指標、買賣條件等多維度分析

## 🚀 使用方法

### 1. **運行基礎可視化**

```bash
cd src/tests
python visualize_test_data.py
```

### 2. **運行策略分析可視化**

```bash
cd src/tests
python visualize_strategy_analysis.py
```

### 3. **在測試中使用**

```python
from .test_data_generator import test_data_generator

# 創建多頭趨勢數據
df = test_data_generator.create_bull_trend_data(periods=100)

# 創建突破形態數據
df = test_data_generator.create_breakout_data(periods=100)

# 獲取測試配置
config = test_data_generator.get_test_config()
```

## 📊 可視化輸出

### 基礎可視化腳本輸出：

- `test_data_kline_chart.png` - K 線圖與技術指標
- `buy_sell_conditions_analysis.png` - 買賣條件分析
- `entry_exit_points.png` - 入場出場點位
- `conditions_summary.png` - 條件摘要表格

### 策略分析可視化腳本輸出：

- `strategy_analysis_bull_trend.png` - 多頭趨勢分析
- `strategy_analysis_breakout.png` - 突破形態分析
- `strategy_analysis_sideways.png` - 橫盤整理分析
- `strategy_conditions_summary.png` - 策略條件摘要

## 🎨 圖表特色

### 1. **多維度分析**

- **K 線圖與均線**：直觀展示價格走勢和技術指標
- **成交量分析**：結合成交量比率，識別爆量突破
- **條件檢查**：實時檢查各項買賣條件
- **信號強度**：綜合評分系統

### 2. **場景對比**

- **多頭趨勢**：適合入場的市場環境
- **突破形態**：關鍵突破點的識別
- **橫盤整理**：不適合交易的市場環境

### 3. **條件可視化**

- **均線排列**：檢查藍綠橘均線的多頭排列
- **爆量突破**：識別成交量異常和價格突破
- **價格位置**：確認價格與均線的關係
- **信號強度**：綜合評分達到入場標準

## 🔍 技術特點

### 1. **模組化設計**

- 數據生成與可視化邏輯分離
- 易於擴展新的測試場景
- 配置參數統一管理

### 2. **性能優化**

- 避免重複計算技術指標
- 智能的數據緩存機制
- 高效的圖表渲染

### 3. **可維護性**

- 清晰的代碼結構
- 統一的命名規範
- 完整的文檔說明

## 🚀 未來擴展

### 1. **新增測試場景**

- 震盪市場數據
- 極端市場數據
- 真實市場數據模擬

### 2. **增強可視化**

- 3D 圖表展示
- 交互式圖表
- 實時數據更新

### 3. **策略對比**

- 多策略性能對比
- 回測結果可視化
- 風險收益分析

## 📝 注意事項

1. **字體設置**：確保系統支持中文字體顯示
2. **依賴安裝**：需要安裝 matplotlib、seaborn 等可視化庫
3. **路徑設置**：運行腳本時需要正確的 Python 路徑配置
4. **內存使用**：大量數據可視化時注意內存使用情況

---

通過這次優化，我們實現了測試數據生成的模組化，提高了代碼的可維護性和重用性，同時增強了可視化分析的豐富性和實用性。
