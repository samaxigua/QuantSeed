"""可视化模块。

统一用 matplotlib 输出 PNG，方便后面嵌进 HTML 报告。
Windows 下中文用 Microsoft YaHei，避免乱码。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无窗口后端，脚本里直接存图
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 中文字体
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_price_with_trades(
    df: pd.DataFrame,
    trades: pd.DataFrame,
    title: str,
    out_path: Path,
) -> Path:
    """价格折线 + 买入(绿▲) / 卖出(红▼) 标记。"""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(df["date"], df["close"], color="#333", lw=1.2, label="收盘价")

    if len(trades) > 0:
        ax.scatter(trades["buy_date"], trades["buy_price"],
                   marker="^", color="#d62728", s=60, zorder=5, label="买入")
        ax.scatter(trades["sell_date"], trades["sell_price"],
                   marker="v", color="#2ca02c", s=60, zorder=5, label="卖出")

    ax.set_title(title, fontsize=13)
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def plot_equity_vs_bh(
    equity: pd.DataFrame,
    initial_cash: float,
    title: str,
    out_path: Path,
) -> Path:
    """策略净值 vs 买入持有基准。"""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(equity["date"], equity["equity"], color="#1f77b4", lw=1.5, label="策略净值")

    # 买入持有：第一天开盘全仓买入，一直持有
    first_close = equity["close"].iloc[0]
    bh_equity = equity["close"] / first_close * initial_cash
    ax.plot(equity["date"], bh_equity, color="#999", lw=1.2, ls="--", label="买入持有基准")

    ax.set_title(title, fontsize=13)
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def plot_drawdown(equity: pd.DataFrame, title: str, out_path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.fill_between(equity["date"], equity["drawdown"] * 100, 0,
                    color="#d62728", alpha=0.4)
    ax.set_title(f"{title} — 回撤 (%)", fontsize=12)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def plot_strategy_comparison(
    equity_dict: dict[str, pd.DataFrame],
    initial_cash: float,
    title: str,
    out_path: Path,
) -> Path:
    """多条策略净值曲线画在一张图上。"""
    fig, ax = plt.subplots(figsize=(11, 5))
    for name, eq in equity_dict.items():
        ax.plot(eq["date"], eq["equity"] / initial_cash, lw=1.5, label=name)
    # 基准
    first_eq = next(iter(equity_dict.values()))
    ax.plot(first_eq["date"], first_eq["close"] / first_eq["close"].iloc[0],
            color="#999", ls="--", lw=1, label="买入持有")
    ax.set_title(title, fontsize=13)
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def plot_trade_pnl(trades: pd.DataFrame, title: str, out_path: Path) -> Path:
    """每笔交易收益分布。"""
    if len(trades) == 0:
        # 没有交易就生成一张空白占位
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "回测期间没有完整交易", ha="center", va="center")
        ax.set_axis_off()
        fig.savefig(out_path, dpi=130)
        plt.close(fig)
        return out_path

    fig, ax = plt.subplots(figsize=(8, 3.5))
    rets = trades["return_pct"] * 100
    colors = ["#2ca02c" if r > 0 else "#d62728" for r in rets]
    ax.bar(range(len(rets)), rets, color=colors, alpha=0.8)
    ax.axhline(0, color="#333", lw=0.8)
    ax.set_title(f"{title} — 每笔交易收益率 (%)", fontsize=12)
    ax.set_xlabel("交易序号")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path
