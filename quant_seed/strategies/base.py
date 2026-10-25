"""策略基类。

写新策略的方式：
    1. 继承 StrategyBase
    2. 设一个 name
    3. 实现 generate_signals(df) -> pd.Series
       返回值里：1 = 当日收盘后希望持有多头，0 = 空仓。

约定（非常重要，决定了回测不会"作弊"）：
    信号在 T 日收盘后才能看到 T 日的 close、high、low；
    回测引擎会自动把信号 shift(1)，在 T+1 日开盘成交。
    所以你这里直接用 T 日数据算就行，不要自己做未来函数的事。
"""
from __future__ import annotations

import pandas as pd


class StrategyBase:
    name: str = "base"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError
