"""唐奇安通道突破（Donchian Breakout）。

海龟交易法则的核心思想：
    突破过去 N 日最高点 -> 买入（新趋势启动）
    跌破过去 M 日最低点 -> 卖出

这是 1983 年海龟实验里证明过的、最古老的系统化策略之一。
它和双均线同属趋势跟踪，但信号更"硬"——只认价格位置，不认斜率。
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase


class DonchianBreakout(StrategyBase):
    name = "donchian_breakout"

    def __init__(self, entry_window: int = 20, exit_window: int = 10):
        self.entry_window = entry_window
        self.exit_window = exit_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"]
        low = df["low"]

        upper = high.rolling(self.entry_window).max().shift(1)
        lower = low.rolling(self.exit_window).min().shift(1)

        close = df["close"]
        position = pd.Series(0, index=df.index, dtype=int)
        holding = 0
        for i in range(len(df)):
            if pd.isna(upper.iloc[i]):
                continue
            if holding == 0 and close.iloc[i] > upper.iloc[i]:
                holding = 1
            elif holding == 1 and close.iloc[i] < lower.iloc[i]:
                holding = 0
            position.iloc[i] = holding
        return position.rename(self.name)
