"""样本外检验（Walk-Forward 思想的简化版）。

断墨寻径第三课讲：
    拟合 = 满足旧数据；学习 = 泛化到新数据。
    过拟合 = 旧数据好，新数据差。
    抑制方法 = 用没见过的数据验证。

这个模块把数据切成两段：
    train: 前 70%（用来"发现"策略，虽然我们这里策略是固定的）
    test:  后 30%（模拟未来，检验策略是否真的有泛化能力）

如果一个策略在 train 上好、test 上崩了，那它就是过拟合。
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .engine import run_backtest, BacktestResult
from .metrics import compute_performance, Performance
from ..config import BacktestConfig


@dataclass
class OOSResult:
    train_perf: Performance
    test_perf: Performance
    train_period: str
    test_period: str

    def as_dict(self) -> dict:
        return {
            "train": self.train_perf.as_dict(),
            "test": self.test_perf.as_dict(),
            "train_period": self.train_period,
            "test_period": self.test_period,
        }


def walk_forward_split(
    df: pd.DataFrame,
    signals: pd.Series,
    train_ratio: float = 0.7,
    config: BacktestConfig | None = None,
) -> OOSResult:
    """简单的样本内外检验。

    注意：这不是完整的 walk-forward（那需要滚动调参），
    只是一个"切两半看泛化"的最小可行版本。
    """
    config = config or BacktestConfig()
    n = len(df)
    split = int(n * train_ratio)

    train_df = df.iloc[:split].reset_index(drop=True)
    train_sig = signals.iloc[:split].reset_index(drop=True)
    test_df = df.iloc[split:].reset_index(drop=True)
    test_sig = signals.iloc[split:].reset_index(drop=True)

    bt_train = run_backtest(train_df, train_sig, config)
    bt_test = run_backtest(test_df, test_sig, config)

    p_train = compute_performance(bt_train.equity_curve, bt_train.trades, config)
    p_test = compute_performance(bt_test.equity_curve, bt_test.trades, config)

    return OOSResult(
        train_perf=p_train,
        test_perf=p_test,
        train_period=f"{train_df['date'].iloc[0].date()} ~ {train_df['date'].iloc[-1].date()}",
        test_period=f"{test_df['date'].iloc[0].date()} ~ {test_df['date'].iloc[-1].date()}",
    )
