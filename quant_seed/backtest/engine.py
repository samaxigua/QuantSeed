"""向量化事件回测引擎。

设计哲学：
    这个引擎故意写得"笨"一点——用 for 循环逐日模拟，
    而不是极致向量化。原因有二：
      1. 你是软件工程学生，能一眼读懂每一天发生了什么；
      2. 回测里最隐蔽的 bug 就是"未来函数"和"成交价不对"，
         逐日模拟让你能打印任何一天的 cash/shares 来对账。

成交规则（写死在这里，不要在策略里改）：
    - T 日收盘后得到信号 position[T]；
    - T+1 日以 open[T+1] 成交；
    - 买入价 = open * (1 + slippage)，再扣 commission；
    - 卖出价 = open * (1 - slippage)，再扣 commission；
    - 满仓/空仓二元仓位（先不做部分仓位，把主线跑通）。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import BacktestConfig


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame   # date, close, position, cash, shares, equity, drawdown
    trades: pd.DataFrame         # 每笔完整交易（买入+卖出配对）
    config: BacktestConfig


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    config = config or BacktestConfig()

    df = df.reset_index(drop=True).copy()
    signals = pd.Series(signals.values, index=df.index).astype(int)

    # 信号 shift(1)：T 日信号 -> T+1 日开盘执行
    executed_position = signals.shift(1).fillna(0).astype(int)

    cash = config.initial_cash
    shares = 0.0
    equity_records = []
    open_trade = None   # 记录"未平仓"的那笔交易，卖出时配对

    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        target = executed_position.iloc[i]  # 今天开盘后应该持有的仓位

        # —— 1. 开盘：根据昨天的信号调仓 ——
        if target == 1 and shares == 0:
            # 买入（全部现金）
            buy_price = row["open"] * (1 + config.slippage)
            # 可买股数（A股100股一手，这里简化为整股，演示用）
            shares = cash / buy_price
            commission = cash * config.commission
            cash = cash - shares * buy_price - commission
            open_trade = {
                "buy_date": row["date"],
                "buy_price": buy_price,
                "shares": shares,
                "buy_commission": commission,
            }
        elif target == 0 and shares > 0:
            # 卖出（全部）
            sell_price = row["open"] * (1 - config.slippage)
            proceeds = shares * sell_price
            commission = proceeds * config.commission
            cash = proceeds - commission
            if open_trade is not None:
                pnl = (sell_price - open_trade["buy_price"]) * open_trade["shares"] \
                      - open_trade["buy_commission"] - commission
                trades.append({
                    **open_trade,
                    "sell_date": row["date"],
                    "sell_price": sell_price,
                    "sell_commission": commission,
                    "pnl": pnl,
                    "return_pct": sell_price / open_trade["buy_price"] - 1,
                    "holding_days": i - df.index[df["date"] == open_trade["buy_date"]][0],
                })
            shares = 0.0
            open_trade = None

        # —— 2. 收盘：盯市 ——
        equity = cash + shares * row["close"]
        equity_records.append({
            "date": row["date"],
            "close": row["close"],
            "position": target,
            "cash": cash,
            "shares": shares,
            "equity": equity,
        })

    equity_df = pd.DataFrame(equity_records)
    # 回撤
    rolling_max = equity_df["equity"].cummax()
    equity_df["drawdown"] = equity_df["equity"] / rolling_max - 1.0

    trades_df = pd.DataFrame(trades)
    return BacktestResult(equity_curve=equity_df, trades=trades_df, config=config)
