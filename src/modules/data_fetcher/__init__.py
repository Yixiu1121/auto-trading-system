#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據獲取模組
負責從 FinMind API 獲取股票數據並存儲到數據庫
"""

from .finmind_fetcher import FinMindFetcher

__all__ = ["FinMindFetcher"]


