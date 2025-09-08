#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略分析可視化腳本
專注於展示小藍多頭策略的各種測試場景
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 設置中文字體
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.modules.strategies import BlueLongStrategy
from src.modules.technical_indicators import TechnicalIndicators
from .test_data_generator import test_data_generator


def create_strategy_analysis_plots():
    """創建策略分析圖表"""

    # 創建不同場景的測試數據
    scenarios = {
        "bull_trend": {
            "name": "多頭趨勢",
            "data": test_data_generator.create_bull_trend_data(periods=100),
            "description": "藍綠橘均線呈多頭排列，價格穩步上漲",
        },
        "breakout": {
            "name": "突破形態",
            "data": test_data_generator.create_breakout_data(periods=100),
            "description": "前期橫盤整理，後期突破上漲",
        },
        "sideways": {
            "name": "橫盤整理",
            "data": test_data_generator.create_sideways_data(periods=100),
            "description": "價格在區間內震盪，均線趨於平緩",
        },
    }

    # 獲取測試配置
    config = test_data_generator.get_test_config()

    # 創建圖表
    for scenario_key, scenario in scenarios.items():
        print(f"📊 分析場景: {scenario['name']}")

        # 計算技術指標
        tech_indicators = TechnicalIndicators(config)
        df_with_indicators = tech_indicators.calculate_all_indicators(scenario["data"])

        # 初始化策略
        strategy = BlueLongStrategy(config)

        # 創建分析圖表
        fig = create_scenario_analysis_plot(
            df_with_indicators, strategy, scenario["name"], scenario["description"]
        )

        # 保存圖表
        filename = f"strategy_analysis_{scenario_key}.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"✅ 保存: {filename}")

        plt.close(fig)

    print("\n🎉 所有策略分析圖表創建完成！")


def create_scenario_analysis_plot(
    df_with_indicators, strategy, scenario_name, description
):
    """創建單個場景的分析圖表"""

    fig, axes = plt.subplots(3, 2, figsize=(18, 15))
    fig.suptitle(
        f"小藍多頭策略分析 - {scenario_name}\n{description}",
        fontsize=16,
        fontweight="bold",
    )

    # 1. K線圖和均線
    ax1 = axes[0, 0]
    ax1.set_title("K線圖與均線", fontsize=14)

    # 繪製K線圖
    for i in range(len(df_with_indicators)):
        date = df_with_indicators.index[i]
        open_price = df_with_indicators["open"].iloc[i]
        high = df_with_indicators["high"].iloc[i]
        low = df_with_indicators["low"].iloc[i]
        close = df_with_indicators["close"].iloc[i]

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

    # 2. 成交量
    ax2 = axes[0, 1]
    ax2.set_title("成交量分析", fontsize=14)

    # 成交量柱狀圖
    ax2.bar(
        df_with_indicators.index,
        df_with_indicators["volume"],
        color="lightblue",
        alpha=0.7,
        label="成交量",
    )

    # 成交量比率
    ax2_twin = ax2.twinx()
    ax2_twin.plot(
        df_with_indicators.index,
        df_with_indicators["volume_ratio"],
        color="orange",
        linewidth=2,
        label="成交量比率",
    )
    ax2_twin.axhline(
        y=1.5, color="red", linestyle="--", alpha=0.7, label="爆量閾值(1.5)"
    )

    ax2.set_ylabel("成交量", fontsize=12)
    ax2_twin.set_ylabel("成交量比率", fontsize=12)
    ax2.legend(loc="upper left", fontsize=10)
    ax2_twin.legend(loc="upper right", fontsize=10)
    ax2.grid(True, alpha=0.3)

    # 3. 均線排列檢查
    ax3 = axes[1, 0]
    ax3.set_title("均線排列檢查", fontsize=14)

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

    ax3.plot(df_with_indicators.index, ma_alignment, "o-", color="blue", markersize=4)
    ax3.set_ylabel("均線排列", fontsize=12)
    ax3.set_ylim(-0.1, 1.1)
    ax3.grid(True, alpha=0.3)

    # 4. 價格位置檢查
    ax4 = axes[1, 1]
    ax4.set_title("價格位置檢查", fontsize=14)

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

    ax4.plot(df_with_indicators.index, price_position, "o-", color="red", markersize=4)
    ax4.set_ylabel("價格位置", fontsize=12)
    ax4.set_ylim(-0.1, 1.1)
    ax4.grid(True, alpha=0.3)

    # 5. 信號強度
    ax5 = axes[2, 0]
    ax5.set_title("信號強度分析", fontsize=14)

    signal_strength = []
    for i in range(len(df_with_indicators)):
        if i < 50:
            signal_strength.append(0)
            continue

        strength = strategy.calculate_signal_strength(df_with_indicators, i)
        signal_strength.append(strength)

    ax5.plot(
        df_with_indicators.index, signal_strength, "o-", color="purple", markersize=4
    )
    ax5.axhline(y=0.7, color="red", linestyle="--", alpha=0.7, label="信號閾值(0.7)")
    ax5.set_ylabel("信號強度", fontsize=12)
    ax5.set_ylim(-0.1, 1.1)
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3)

    # 6. 入場信號
    ax6 = axes[2, 1]
    ax6.set_title("入場信號分析", fontsize=14)

    entry_signals = []
    for i in range(50, len(df_with_indicators)):
        entry_valid, entry_price = strategy.check_entry_conditions(
            df_with_indicators, i
        )
        if entry_valid:
            entry_signals.append((df_with_indicators.index[i], entry_price))

    if entry_signals:
        entry_dates, entry_prices = zip(*entry_signals)
        ax6.scatter(
            entry_dates,
            entry_prices,
            color="red",
            s=100,
            marker="^",
            label=f"入場信號 ({len(entry_signals)}個)",
            zorder=5,
        )

    # 繪製價格線
    ax6.plot(
        df_with_indicators.index,
        df_with_indicators["close"],
        color="black",
        linewidth=1,
        alpha=0.7,
        label="收盤價",
    )

    ax6.set_ylabel("價格", fontsize=12)
    ax6.legend(fontsize=10)
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_conditions_summary_table():
    """創建買賣條件摘要表格"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.axis("tight")
    ax.axis("off")

    # 買入條件表格
    buy_conditions = [
        ["條件", "檢查項目", "具體要求", "狀態"],
        ["1", "均線排列", "藍線 > 綠線 > 橘線 且 均為正斜率", "PASS 多頭排列"],
        ["2", "爆量突破", "成交量 > 前日1.5倍 且 突破前20根K線高點", "PASS 爆量確認"],
        ["3", "價格位置", "收盤價 > 小藍線 且 乖離率 < 5%", "PASS 站上均線"],
        ["4", "信號強度", "綜合信號強度 >= 0.7", "PASS 強信號"],
    ]

    # 賣出條件表格
    sell_conditions = [
        ["條件", "檢查項目", "具體要求", "狀態"],
        ["1", "停損信號", "連續3根K線無法站上小藍線", "WARN 風險控制"],
        ["2", "獲利了結", "與小藍乖離率 > 8%", "PROFIT 獲利保護"],
        ["3", "移動停利", "價格回調超過最高點5%", "TREND 趨勢跟蹤"],
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
                    if "PASS" in buy_conditions[i][j]:
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
                    if "WARN" in sell_conditions[i][j]:
                        table2[(i, j)].set_facecolor("#FFF3E0")
                    elif "PROFIT" in sell_conditions[i][j]:
                        table2[(i, j)].set_facecolor("#E8F5E8")
                    else:
                        table2[(i, j)].set_facecolor("#FFEBEE")

    ax.set_title("小藍多頭策略 - 買賣條件摘要", fontsize=16, fontweight="bold", pad=20)

    plt.tight_layout()
    return fig


def main():
    """主函數"""
    print("🚀 開始創建策略分析可視化...")

    # 1. 創建各種場景的策略分析圖表
    print("📊 創建策略分析圖表...")
    create_strategy_analysis_plots()

    # 2. 創建條件摘要表格
    print("📋 創建條件摘要表格...")
    fig_summary = create_conditions_summary_table()
    fig_summary.savefig("strategy_conditions_summary.png", dpi=300, bbox_inches="tight")
    print("✅ 保存: strategy_conditions_summary.png")

    print("\n🎉 所有圖表創建完成！")
    print("📁 請查看當前目錄下的PNG文件")

    # 顯示摘要表格
    plt.show()


if __name__ == "__main__":
    main()
