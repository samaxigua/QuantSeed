"""AI 启发的组合策略。

这个策略本身不是 AI 训练出来的，它演示的是"因子合成"思想——
这正是现在量化基金和 AI 量化研究员每天在做的事：

    1. 把多个"想法"（因子/信号）各自跑一遍；
    2. 让它们投票（voting / weighting）；
    3. 合成一个更稳健的仓位。

为什么投票有用？
    任何单一策略都有它的"范式盲区"：
        双均线在震荡里被反复打脸；
        RSI 在单边行情里过早抄底/逃顶；
        唐奇安在横盘里频繁假突破。
    当三个信号的错误不同步时，合成曲线会比任何单一策略都平滑。
    ——这就是"分散化是量化唯一的免费午餐"。

如果你以后真的接 LLM，让它做的事也类似：
    输入市场状态 -> 输出每个子策略的权重。
"""
from __future__ import annotations

import pandas as pd

from .base import StrategyBase
from .ma_cross import MACross
from .rsi_revert import RSIMeanRevert
from .momentum import DonchianBreakout


class EnsembleVoting(StrategyBase):
    name = "ensemble_voting"

    def __init__(self, min_votes: int = 2):
        """至少 min_votes 个子策略同时看多，才持仓。"""
        self.min_votes = min_votes
        self.sub_strategies = [
            MACross(fast=20, slow=60),
            RSIMeanRevert(),
            DonchianBreakout(),
        ]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        votes = []
        for s in self.sub_strategies:
            votes.append(s.generate_signals(df).rename(s.name))
        vote_df = pd.concat(votes, axis=1)
        score = vote_df.sum(axis=1)
        position = (score >= self.min_votes).astype(int)
        return position.rename(self.name)
