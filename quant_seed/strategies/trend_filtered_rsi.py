"""RSI 带止损策略（改进版）。

原始 RSI 均值回归只有"RSI>70 才卖"这一个退出条件。
问题：如果买入后继续暴跌，没有任何保护。

这个版本加了两个保护：
    1. 硬止损：从买入价跌 5% 立刻卖（不扛）
    2. 时间止损：持有满 10 个交易日，不管赚没赚都卖（释放资金）

这是真实交易和学术回测的最大区别——实盘里你必须有风控。
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase
from .rsi_revert import _rsi


class RSIWithStops(StrategyBase):
    name = "rsi_with_stops"

    def __init__(self, rsi_period: int = 14, rsi_low: float = 30,
                 rsi_high: float = 70, stop_loss: float = -0.05,
                 max_hold_days: int = 10):
        self.rsi_period = rsi_period
        self.rsi_low = rsi_low
        self.rsi_high = rsi_high
        self.stop_loss = stop_loss
        self.max_hold_days = max_hold_days

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        rsi = _rsi(close, self.rsi_period)

        position = pd.Series(0, index=df.index, dtype=int)
        holding = 0
        buy_price = 0.0
        days_held = 0

        for i in range(len(df)):
            if pd.isna(rsi.iloc[i]):
                continue
            price = close.iloc[i]

            if holding == 0:
                if rsi.iloc[i] < self.rsi_low:
                    holding = 1
                    buy_price = price
                    days_held = 0
            else:
                days_held += 1
                pnl = price / buy_price - 1
                # 退出条件：RSI 超买 / 硬止损 / 时间到
                if rsi.iloc[i] > self.rsi_high or pnl <= self.stop_loss \
                        or days_held >= self.max_hold_days:
                    holding = 0
                    buy_price = 0.0
                    days_held = 0
            position.iloc[i] = holding
        return position.rename(self.name)
