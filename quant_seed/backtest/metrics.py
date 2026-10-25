"""绩效指标。

所有指标都基于净值曲线 equity（初始资金 config.initial_cash）。
注意：
    - 年化 = (1 + total_return) ** (252 / n_days) - 1
    - 夏普 = (年化收益 - 无风险利率) / 年化波动
    - 最大回撤 = min(equity / cummax(equity) - 1)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from ..config import BacktestConfig


@dataclass
class Performance:
    total_return: float
    annual_return: float
    annual_vol: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    profit_factor: float       # 平均盈利 / 平均亏损的绝对值
    num_trades: int
    exposure: float            # 持仓时间占比

    def as_dict(self) -> dict:
        return asdict(self)

    def pretty(self) -> str:
        return (
            f"累计收益   : {self.total_return:+.2%}\n"
            f"年化收益   : {self.annual_return:+.2%}\n"
            f"年化波动   : {self.annual_vol:.2%}\n"
            f"夏普比率   : {self.sharpe:.2f}\n"
            f"最大回撤   : {self.max_drawdown:.2%}\n"
            f"胜率       : {self.win_rate:.2%}\n"
            f"盈亏比     : {self.profit_factor:.2f}\n"
            f"交易次数   : {self.num_trades}\n"
            f"仓位时间占比: {self.exposure:.2%}"
        )


def compute_performance(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> Performance:
    config = config or BacktestConfig

    eq = equity_curve["equity"].values
    n = len(eq)
    if n < 2:
        raise ValueError("净值曲线太短")

    total_return = eq[-1] / eq[0] - 1.0
    years = n / config.trading_days_per_year
    annual_return = (eq[-1] / eq[0]) ** (1 / years) - 1.0 if years > 0 else 0.0

    daily_ret = np.diff(eq) / eq[:-1]
    annual_vol = daily_ret.std() * np.sqrt(config.trading_days_per_year)
    sharpe = (annual_return - config.risk_free_rate) / annual_vol if annual_vol > 0 else 0.0

    rolling_max = np.maximum.accumulate(eq)
    max_dd = np.min(eq / rolling_max - 1.0)

    exposure = float((equity_curve["position"] > 0).mean())

    if len(trades) > 0:
        wins = trades[trades["pnl"] > 0]["pnl"]
        losses = trades[trades["pnl"] <= 0]["pnl"]
        win_rate = len(wins) / len(trades)
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else np.nan
        profit_factor = avg_win / avg_loss if avg_loss and not np.isnan(avg_loss) and avg_loss > 0 else np.nan
        num_trades = len(trades)
    else:
        win_rate = float("nan")
        profit_factor = float("nan")
        num_trades = 0

    return Performance(
        total_return=total_return,
        annual_return=annual_return,
        annual_vol=annual_vol,
        sharpe=sharpe,
        max_drawdown=max_dd,
        win_rate=win_rate,
        profit_factor=profit_factor,
        num_trades=num_trades,
        exposure=exposure,
    )
