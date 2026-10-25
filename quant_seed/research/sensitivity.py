"""参数敏感性分析。

断墨寻径第三课讲：
    过拟合的标志是——你为了拟合旧数据，挑了一组"恰好"最优的参数。
    真正稳健的策略，它的绩效曲面应该是"高原"而不是"尖峰"。

这个模块做的事：
    1. 对 RSI 的 (low, high) 参数做网格搜索
    2. 对双均线的 (fast, slow) 参数做网格搜索
    3. 画热力图：看绩效是尖峰还是高原
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..data import load_prices
from ..backtest import run_backtest, compute_performance
from ..config import BacktestConfig
from ..strategies import MACross, RSIMeanRevert

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _rsi_grid(df: pd.DataFrame, cfg: BacktestConfig,
              lows=range(20, 41, 5), highs=range(60, 81, 5)) -> pd.DataFrame:
    """网格搜索 RSI 参数。"""
    rows = []
    for lo in lows:
        for hi in highs:
            if lo >= hi:
                continue
            s = RSIMeanRevert(low=float(lo), high=float(hi))
            sig = s.generate_signals(df)
            bt = run_backtest(df, sig, cfg)
            p = compute_performance(bt.equity_curve, bt.trades, cfg)
            rows.append({"low": lo, "high": hi, "ret": p.total_return, "sharpe": p.sharpe})
    return pd.DataFrame(rows)


def _ma_grid(df: pd.DataFrame, cfg: BacktestConfig,
             fasts=range(5, 31, 5), slows=range(20, 101, 10)) -> pd.DataFrame:
    rows = []
    for f in fasts:
        for s in slows:
            if f >= s:
                continue
            strat = MACross(fast=f, slow=s)
            sig = strat.generate_signals(df)
            bt = run_backtest(df, sig, cfg)
            perf = compute_performance(bt.equity_curve, bt.trades, cfg)
            rows.append({"fast": f, "slow": s, "ret": perf.total_return, "sharpe": perf.sharpe})
    return pd.DataFrame(rows)


def plot_heatmap(grid: pd.DataFrame, x_col: str, y_col: str, value_col: str,
                 title: str, out_path: Path) -> Path:
    pivot = grid.pivot(index=y_col, columns=x_col, values=value_col)
    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", origin="lower")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title)
    # 标注数值
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=8, color="black")
    plt.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def run_sensitivity(out_dir: Path) -> dict:
    cfg = BacktestConfig()
    df = load_prices("akshare", "000300", "2023-01-01")

    print("  搜索 RSI 参数...")
    rsi_grid = _rsi_grid(df, cfg)
    p1 = plot_heatmap(rsi_grid, "low", "high", "sharpe",
                      "RSI 参数敏感性（颜色=夏普）", out_dir / "heatmap_rsi.png")
    p2 = plot_heatmap(rsi_grid, "low", "high", "ret",
                      "RSI 参数敏感性（颜色=累计收益）", out_dir / "heatmap_rsi_ret.png")

    print("  搜索双均线参数...")
    ma_grid = _ma_grid(df, cfg)
    p3 = plot_heatmap(ma_grid, "fast", "slow", "sharpe",
                      "双均线参数敏感性（颜色=夏普）", out_dir / "heatmap_ma.png")
    p4 = plot_heatmap(ma_grid, "fast", "slow", "ret",
                      "双均线参数敏感性（颜色=累计收益）", out_dir / "heatmap_ma_ret.png")

    return {"rsi": rsi_grid, "ma": ma_grid, "figures": [p1, p2, p3, p4]}


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "results"
    out.mkdir(exist_ok=True)
    res = run_sensitivity(out)
    print("\nRSI 最优参数:")
    print(res["rsi"].sort_values("sharpe", ascending=False).head(5))
    print("\nMA 最优参数:")
    print(res["ma"].sort_values("sharpe", ascending=False).head(5))
