"""双均线策略（Golden Cross / Death Cross）。

最经典的趋势跟踪策略，几乎所有量化入门课的第一个例子。
逻辑：
    快线 = 收盘价的短周期均线
    慢线 = 收盘价的长周期均线
    快线上穿慢线 -> 买入
    快线下穿慢线 -> 卖出

它赚的是"趋势持续"的钱，在震荡市里会被反复打脸（whipsaw）。
这就是为什么你需要看多个策略、以及后面那个"AI 组合策略"。
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase


class MACross(StrategyBase):
    name = "ma_cross"

    def __init__(self, fast: int = 20, slow: int = 60):
        if fast >= slow:
            raise ValueError(f"快线({fast})必须小于慢线({slow})")
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        ma_fast = close.rolling(self.fast).mean()
        ma_slow = close.rolling(self.slow).mean()

        # 1 = 快线在慢线上方（持仓），0 = 下方（空仓）
        position = (ma_fast > ma_slow).astype(int)
        # 前 slow 天均线没算出来，不持仓
        position.iloc[: self.slow] = 0
        return position.rename(self.name)
