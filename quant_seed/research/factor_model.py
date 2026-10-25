"""多因子模型 + IC 分析。

断墨寻径第二课讲：
    归纳学习是从多个实例中找共性。多因子模型就是把多个"想法"
    （因子）各自的预测力量化，然后合成。

因子定义（全部只用 OHLCV）：
    1. momentum_20: 过去20日收益率
    2. volatility_20: 过去20日收益率标准差（低波动异象）
    3. rsi_14: RSI
    4. ma_slope: 20日均线斜率（趋势强度）
    5. volume_ratio: 当前量 / 20日均量

IC = 因子值与未来5日收益的 Spearman 相关系数。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ..data import load_prices

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def compute_factors(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    volume = df["volume"]

    factors = pd.DataFrame(index=df.index)
    # 1. 20日动量
    factors["momentum_20"] = close.pct_change(20)
    # 2. 20日波动（取负，因为低波动异象）
    factors["volatility_20"] = -close.pct_change().rolling(20).std()
    # 3. RSI 14
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    factors["rsi_14"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    # 4. 20日均线斜率
    ma20 = close.rolling(20).mean()
    factors["ma_slope"] = ma20.pct_change(5)
    # 5. 量比
    factors["volume_ratio"] = volume / volume.rolling(20).mean()
    return factors


def forward_returns(df: pd.DataFrame, horizon: int = 5) -> pd.Series:
    return df["close"].shift(-horizon) / df["close"] - 1


def ic_analysis(factors: pd.DataFrame, fwd_ret: pd.Series) -> pd.DataFrame:
    """逐期计算 IC，再求均值和 IR。"""
    records = []
    for col in factors.columns:
        ics = []
        for i in range(len(factors)):
            if pd.isna(factors[col].iloc[i]) or pd.isna(fwd_ret.iloc[i]):
                continue
            window = slice(max(0, i-60), i+1)
            x = factors[col].iloc[window].dropna()
            y = fwd_ret.iloc[window].loc[x.index]
            if len(x) < 30:
                continue
            ic, _ = spearmanr(x, y)
            ics.append(ic)
        ics = pd.Series(ics).dropna()
        records.append({
            "factor": col,
            "ic_mean": ics.mean(),
            "ic_std": ics.std(),
            "ir": ics.mean() / ics.std() if ics.std() > 0 else 0,
            "ic_positive_ratio": (ics > 0).mean(),
        })
    return pd.DataFrame(records)


def plot_ic(ic_df: pd.DataFrame, out_path: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    ic_df.plot.bar(x="factor", y="ic_mean", ax=axes[0], color="#1f77b4", legend=False)
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set_title("因子 IC 均值")
    axes[0].set_ylabel("IC")
    ic_df.plot.bar(x="factor", y="ir", ax=axes[1], color="#ff7f0e", legend=False)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_title("因子 IR（IC均值/IC标准差）")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def run_factor_research(out_dir: Path) -> pd.DataFrame:
    df = load_prices("akshare", "000300", "2023-01-01")
    factors = compute_factors(df)
    fwd = forward_returns(df, horizon=5)
    ic_df = ic_analysis(factors, fwd)
    plot_ic(ic_df, out_dir / "factor_ic.png")
    return ic_df


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "results"
    ic = run_factor_research(out)
    print(ic.to_string(index=False))
