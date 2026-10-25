"""RSI 均值回归策略。

RSI（Relative Strength Index）衡量最近涨跌的相对强度，取值 0~100。
    RSI < 30  -> 超卖，可能反弹 -> 买入
    RSI > 70  -> 超买，可能回落 -> 卖出

它和双均线是两种世界观：
    趋势跟踪："强者恒强"
    均值回归："物极必反"
在一个真市场里，这两种力量交替主导。这就是策略组合的意义。
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder 平滑（EMA 的变种）
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - 100 / (1 + rs)


class RSIMeanRevert(StrategyBase):
    name = "rsi_revert"

    def __init__(self, period: int = 14, low: float = 30, high: float = 70):
        self.period = period
        self.low = low
        self.high = high

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi = _rsi(df["close"], self.period)

        # 状态机：默认空仓，跌破 low 后买入，涨到 high 后卖出。
        # 这比"每天根据 rsi 直接判仓位"更贴近真实交易——
        # 你不会因为 RSI 在 31 就立刻又卖又买。
        position = pd.Series(0, index=df.index, dtype=int)
        holding = 0
        for i, r in enumerate(rsi):
            if pd.isna(r):
                continue
            if holding == 0 and r < self.low:
                holding = 1
            elif holding == 1 and r > self.high:
                holding = 0
            position.iloc[i] = holding
        return position.rename(self.name)
