#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試數據可視化腳本
展示K線圖、技術指標和買賣條件
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import seaborn as sns

# 設置中文字體
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.modules.strategies import BlueLongStrategy
from src.modules.technical_indicators import TechnicalIndicators


def create_test_data():
    """創建測試用的K線數據"""
    from .test_data_generator import test_data_generator

    return test_data_generator.create_bull_trend_data(periods=100, base_price=100.0)


def calculate_indicators(df):
    """計算技術指標"""
    from .test_data_generator import test_data_generator

    config = test_data_generator.get_test_config()

    tech_indicators = TechnicalIndicators(config)
    return tech_indicators.calculate_all_indicators(df)


def plot_kline_chart(df, df_with_indicators):
    """繪製K線圖和技術指標"""
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(15, 12), gridspec_kw={"height_ratios": [3, 1, 1]}
    )

    # 設置時間格式
    date_format = mdates.DateFormatter("%m-%d %H:%M")

    # 1. K線圖和均線
    ax1.set_title("測試數據 - K線圖與技術指標", fontsize=16, fontweight="bold")

    # 繪製K線圖
    for i in range(len(df)):
        date = df.index[i]
        open_price = df["open"].iloc[i]
        high = df["high"].iloc[i]
        low = df["low"].iloc[i]
        close = df["close"].iloc[i]

        # 繪製K線
        color = "red" if close > open_price else "green"
        ax1.plot([date, date], [low, high], color=color, linewidth=1)
        ax1.plot([date, date], [open_price, close], color=color, linewidth=3)

    # 繪製均線
    ax1.plot(
        df_with_indicators.index,
        df_with_indicators["blue_line"],
        color="blue",
        linewidth=2,
        label="小藍線（月線）",
    )
    ax1.plot(
        df_with_indicators.index,
        df_with_indicators["green_line"],
        color="green",
        linewidth=2,
        label="小綠線（季線）",
    )
    ax1.plot(
        df_with_indicators.index,
        df_with_indicators["orange_line"],
        color="orange",
        linewidth=2,
        label="小橘線（年線）",
    )

    ax1.set_ylabel("價格", fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(date_format)

    # 2. 成交量
    ax2.set_title("成交量", fontsize=14)
    ax2.bar(df.index, df["volume"], color="lightblue", alpha=0.7)
    ax2.set_ylabel("成交量", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(date_format)

    # 3. 技術指標
    ax3.set_title("技術指標", fontsize=14)

    # 趨勢強度
    ax3.plot(
        df_with_indicators.index,
        df_with_indicators["trend_strength"],
        color="purple",
        linewidth=2,
        label="趨勢強度",
    )

    # 乖離率
    ax3.plot(
        df_with_indicators.index,
        df_with_indicators["blue_deviation"],
        color="red",
        linewidth=2,
        label="藍線乖離率",
    )

    # 成交量比率
    ax3.plot(
        df_with_indicators.index,
        df_with_indicators["volume_ratio"],
        color="orange",
        linewidth=2,
        label="成交量比率",
    )

    ax3.set_ylabel("指標值", fontsize=12)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(date_format)

    plt.tight_layout()
    return fig


def plot_buy_sell_conditions(df_with_indicators, strategy):
    """繪製買賣條件分析"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("小藍多頭策略 - 買賣條件分析", fontsize=16, fontweight="bold")

    # 1. 均線排列檢查
    ax1 = axes[0, 0]
    ax1.set_title("均線排列檢查", fontsize=14)

    # 檢查每個時點的均線排列
    ma_alignment = []
    for i in range(len(df_with_indicators)):
        if i < 50:  # 需要足夠的數據
            ma_alignment.append(0)
            continue

        current = df_with_indicators.iloc[i]

        # 檢查是否為多頭排列且正斜率
        if (
            current["blue_line"] > current["green_line"] > current["orange_line"]
            and current["blue_slope"] > 0
            and current["green_slope"] > 0
            and current["orange_slope"] > 0
        ):
            ma_alignment.append(1)  # 符合條件
        else:
            ma_alignment.append(0)  # 不符合條件

    ax1.plot(df_with_indicators.index, ma_alignment, "o-", color="blue", markersize=4)
    ax1.set_ylabel("均線排列", fontsize=12)
    ax1.set_ylim(-0.1, 1.1)
    ax1.grid(True, alpha=0.3)

    # 2. 爆量突破檢查
    ax2 = axes[0, 1]
    ax2.set_title("爆量突破檢查", fontsize=14)

    volume_breakout = []
    for i in range(len(df_with_indicators)):
        if i < 50:
            volume_breakout.append(0)
            continue

        current = df_with_indicators.iloc[i]

        # 檢查是否爆量且突破前高
        if current["volume_ratio"] > 1.5:
            # 檢查是否突破前20根K線的高點
            recent_high = df_with_indicators["high"].iloc[max(0, i - 20) : i].max()
            if current["close"] > recent_high:
                volume_breakout.append(1)  # 符合條件
            else:
                volume_breakout.append(0.5)  # 爆量但未突破
        else:
            volume_breakout.append(0)  # 不符合條件

    ax2.plot(
        df_with_indicators.index, volume_breakout, "o-", color="green", markersize=4
    )
    ax2.set_ylabel("爆量突破", fontsize=12)
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3)

    # 3. 價格位置檢查
    ax3 = axes[1, 0]
    ax3.set_title("價格位置檢查", fontsize=14)

    price_position = []
    for i in range(len(df_with_indicators)):
        if i < 50:
            price_position.append(0)
            continue

        current = df_with_indicators.iloc[i]

        # 檢查是否站上小藍線且乖離適中
        if (
            current["close"] > current["blue_line"]
            and abs(current["blue_deviation"]) < 5.0
        ):
            price_position.append(1)  # 符合條件
        else:
            price_position.append(0)  # 不符合條件

    ax3.plot(df_with_indicators.index, price_position, "o-", color="red", markersize=4)
    ax3.set_ylabel("價格位置", fontsize=12)
    ax3.set_ylim(-0.1, 1.1)
    ax3.grid(True, alpha=0.3)

    # 4. 綜合信號強度
    ax4 = axes[1, 1]
    ax4.set_title("綜合信號強度", fontsize=14)

    signal_strength = []
    for i in range(len(df_with_indicators)):
        if i < 50:
            signal_strength.append(0)
            continue

        strength = strategy.calculate_signal_strength(df_with_indicators, i)
        signal_strength.append(strength)

    ax4.plot(
        df_with_indicators.index, signal_strength, "o-", color="purple", markersize=4
    )
    ax4.axhline(y=0.7, color="red", linestyle="--", alpha=0.7, label="信號閾值(0.7)")
    ax4.set_ylabel("信號強度", fontsize=12)
    ax4.set_ylim(-0.1, 1.1)
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_entry_exit_points(df_with_indicators, strategy):
    """繪製入場出場點位"""
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))

    # 繪製K線圖
    for i in range(len(df_with_indicators)):
        date = df_with_indicators.index[i]
        open_price = df_with_indicators["open"].iloc[i]
        high = df_with_indicators["high"].iloc[i]
        low = df_with_indicators["low"].iloc[i]
        close = df_with_indicators["close"].iloc[i]

        color = "red" if close > open_price else "green"
        ax.plot([date, date], [low, high], color=color, linewidth=1)
        ax.plot([date, date], [open_price, close], color=color, linewidth=3)

    # 繪製均線
    ax.plot(
        df_with_indicators.index,
        df_with_indicators["blue_line"],
        color="blue",
        linewidth=2,
        label="小藍線（月線）",
    )
    ax.plot(
        df_with_indicators.index,
        df_with_indicators["green_line"],
        color="green",
        linewidth=2,
        label="小綠線（季線）",
    )
    ax.plot(
        df_with_indicators.index,
        df_with_indicators["orange_line"],
        color="orange",
        linewidth=2,
        label="小橘線（年線）",
    )

    # 標記入場點位
    entry_points = []
    for i in range(50, len(df_with_indicators)):
        entry_valid, entry_price = strategy.check_entry_conditions(
            df_with_indicators, i
        )
        if entry_valid:
            entry_points.append((df_with_indicators.index[i], entry_price))

    if entry_points:
        entry_dates, entry_prices = zip(*entry_points)
        ax.scatter(
            entry_dates,
            entry_prices,
            color="red",
            s=100,
            marker="^",
            label=f"入場點位 ({len(entry_points)}個)",
            zorder=5,
        )

    # 標記出場點位（模擬持倉）
    exit_points = []
    for i in range(50, len(df_with_indicators)):
        position = {"entry_price": 110.0, "highest_price": 115.0}
        exit_valid, exit_reason = strategy.check_exit_conditions(
            df_with_indicators, i, position
        )
        if exit_valid:
            exit_points.append(
                (df_with_indicators.index[i], df_with_indicators["close"].iloc[i])
            )

    if exit_points:
        exit_dates, exit_prices = zip(*exit_points)
        ax.scatter(
            exit_dates,
            exit_prices,
            color="blue",
            s=100,
            marker="v",
            label=f"出場點位 ({len(exit_points)}個)",
            zorder=5,
        )

    ax.set_title("小藍多頭策略 - 入場出場點位分析", fontsize=16, fontweight="bold")
    ax.set_ylabel("價格", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_conditions_summary():
    """創建買賣條件摘要表格"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.axis("tight")
    ax.axis("off")

    # 買入條件表格
    buy_conditions = [
        ["條件", "檢查項目", "具體要求", "狀態"],
        ["1", "均線排列", "藍線 > 綠線 > 橘線 且 均為正斜率", "✅ 多頭排列"],
        ["2", "爆量突破", "成交量 > 前日1.5倍 且 突破前20根K線高點", "✅ 爆量確認"],
        ["3", "價格位置", "收盤價 > 小藍線 且 乖離率 < 5%", "✅ 站上均線"],
        ["4", "信號強度", "綜合信號強度 ≥ 0.7", "✅ 強信號"],
    ]

    # 賣出條件表格
    sell_conditions = [
        ["條件", "檢查項目", "具體要求", "狀態"],
        ["1", "停損信號", "連續3根K線無法站上小藍線", "⚠️ 風險控制"],
        ["2", "獲利了結", "與小藍線乖離率 > 8%", "💰 獲利保護"],
        ["3", "移動停利", "價格回調超過最高點5%", "📉 趨勢跟蹤"],
    ]

    # 繪製買入條件表格
    table1 = ax.table(
        cellText=buy_conditions,
        cellLoc="center",
        loc="upper left",
        colWidths=[0.1, 0.3, 0.4, 0.2],
    )
    table1.auto_set_font_size(False)
    table1.set_fontsize(12)
    table1.scale(1, 2)

    # 設置表格樣式
    for i in range(len(buy_conditions)):
        for j in range(len(buy_conditions[0])):
            if i == 0:  # 標題行
                table1[(i, j)].set_facecolor("#4CAF50")
                table1[(i, j)].set_text_props(weight="bold", color="white")
            else:
                if j == 3:  # 狀態列
                    if "✅" in buy_conditions[i][j]:
                        table1[(i, j)].set_facecolor("#E8F5E8")
                    else:
                        table1[(i, j)].set_facecolor("#FFF3E0")

    # 繪製賣出條件表格
    table2 = ax.table(
        cellText=sell_conditions,
        cellLoc="center",
        loc="lower left",
        colWidths=[0.1, 0.3, 0.4, 0.2],
    )
    table2.auto_set_font_size(False)
    table2.set_fontsize(12)
    table2.scale(1, 2)

    # 設置表格樣式
    for i in range(len(sell_conditions)):
        for j in range(len(sell_conditions[0])):
            if i == 0:  # 標題行
                table2[(i, j)].set_facecolor("#FF9800")
                table2[(i, j)].set_text_props(weight="bold", color="white")
            else:
                if j == 3:  # 狀態列
                    if "⚠️" in sell_conditions[i][j]:
                        table2[(i, j)].set_facecolor("#FFF3E0")
                    elif "💰" in sell_conditions[i][j]:
                        table2[(i, j)].set_facecolor("#E8F5E8")
                    else:
                        table2[(i, j)].set_facecolor("#FFEBEE")

    ax.set_title("小藍多頭策略 - 買賣條件摘要", fontsize=16, fontweight="bold", pad=20)

    plt.tight_layout()
    return fig


def main():
    """主函數"""
    print("🚀 開始創建測試數據可視化...")

    # 創建測試數據
    print("📊 創建測試數據...")
    df = create_test_data()

    # 計算技術指標
    print("🔧 計算技術指標...")
    df_with_indicators = calculate_indicators(df)

    # 初始化策略
    print("📈 初始化交易策略...")
    from .test_data_generator import test_data_generator

    config = test_data_generator.get_test_config()
    strategy = BlueLongStrategy(config)

    # 創建圖表
    print("🎨 創建可視化圖表...")

    # 1. K線圖和技術指標
    fig1 = plot_kline_chart(df, df_with_indicators)
    fig1.savefig("test_data_kline_chart.png", dpi=300, bbox_inches="tight")
    print("✅ 保存: test_data_kline_chart.png")

    # 2. 買賣條件分析
    fig2 = plot_buy_sell_conditions(df_with_indicators, strategy)
    fig2.savefig("buy_sell_conditions_analysis.png", dpi=300, bbox_inches="tight")
    print("✅ 保存: buy_sell_conditions_analysis.png")

    # 3. 入場出場點位
    fig3 = plot_entry_exit_points(df_with_indicators, strategy)
    fig3.savefig("entry_exit_points.png", dpi=300, bbox_inches="tight")
    print("✅ 保存: entry_exit_points.png")

    # 4. 條件摘要表格
    fig4 = create_conditions_summary()
    fig4.savefig("conditions_summary.png", dpi=300, bbox_inches="tight")
    print("✅ 保存: conditions_summary.png")

    print("\n🎉 所有圖表創建完成！")
    print("📁 請查看當前目錄下的PNG文件")

    # 顯示圖表
    plt.show()


if __name__ == "__main__":
    main()
