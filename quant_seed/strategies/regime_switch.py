"""Regime-Switching 策略：根据市场状态自动选策略。

从数据归纳出的规律（见 results/_regime_analysis.txt）：
    - 高波动 + 负动量 = 恐慌期 → 用 RSI 均值回归
    - 低波动 + 正动量 = 平静上涨 → 用双均线趋势跟踪
    - 其他 → 空仓

这就是断墨寻径里说的"输入→规律→输出"：
    输入：当前波动率、当前动量
    规律：两个阈值判断市场状态
    输出：应该用哪个策略
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase
from .rsi_revert import RSIMeanRevert
from .ma_cross import MACross


class RegimeSwitch(StrategyBase):
    name = "regime_switch"

    def __init__(self, vol_threshold: float = 0.20, momentum_threshold: float = 0.0):
        self.vol_threshold = vol_threshold
        self.momentum_threshold = momentum_threshold
        self.rsi = RSIMeanRevert(low=20, high=80)
        self.ma = MACross(fast=20, slow=60)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        vol = close.pct_change().rolling(20).std() * (252 ** 0.5)
        mom = close.pct_change(20)

        rsi_sig = self.rsi.generate_signals(df)
        ma_sig = self.ma.generate_signals(df)

        position = pd.Series(0, index=df.index, dtype=int)
        for i in range(len(df)):
            if pd.isna(vol.iloc[i]) or pd.isna(mom.iloc[i]):
                continue
            if vol.iloc[i] > self.vol_threshold and mom.iloc[i] < self.momentum_threshold:
                # 恐慌期：用 RSI
                position.iloc[i] = rsi_sig.iloc[i]
            elif vol.iloc[i] < self.vol_threshold and mom.iloc[i] > self.momentum_threshold:
                # 平静上涨：用趋势跟踪
                position.iloc[i] = ma_sig.iloc[i]
            else:
                position.iloc[i] = 0
        return position.rename(self.name)
