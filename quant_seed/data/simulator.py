"""演示数据生成器。

为什么需要它？
    你现在没有 tushare/akshare token，也可能不想为了跑通项目去注册账号。
    这个模块用一段"有结构的随机过程"生成近似 A 股指数的日线数据，
    让你 0 外网依赖就能跑完整条链路。

数据从哪来（如果你以后想换真数据）？
    看 loader.py —— 它留好了 akshare 接口，一行切换。

生成原理（这本身就是量化的入门课）：
    1. 价格路径用分段的几何布朗运动（GBM）：
           dS = mu * S * dt + sigma * S * dW
       离散化：S_{t+1} = S_t * exp((mu - 0.5 sigma^2) dt + sigma sqrt(dt) Z)
    2. 三段不同的 mu：慢牛 → 急跌 → 震荡反弹，模拟牛熊切换。
    3. OHLC 在 close 的基础上重构，保证 high >= max(open, close)，
       low <= min(open, close)，K 线形态在数学上合法。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import DEMO_RANDOM_SEED


def generate_demo_prices(
    n_days: int = 504,
    start_price: float = 3500.0,
    start_date: str = "2024-01-02",
    seed: int = DEMO_RANDOM_SEED,
) -> pd.DataFrame:
    """生成一段"看起来像指数"的日线行情。

    返回 DataFrame，列：date, open, high, low, close, volume
    """
    rng = np.random.default_rng(seed)

    # 三段行情：(天数占比, 年化漂移 mu, 年化波动 sigma)
    # 第一阶段：慢牛（mu=12%, sigma=15%）
    # 第二阶段：中期回撤（mu=-20%, sigma=22%）
    # 第三阶段：震荡修复（mu=5%, sigma=12%）
    segments = [
        (int(n_days * 0.45), 0.12, 0.15),
        (int(n_days * 0.20), -0.20, 0.22),
        (n_days - int(n_days * 0.45) - int(n_days * 0.20), 0.05, 0.12),
    ]

    dt = 1.0 / 252.0
    closes = [start_price]
    for seg_len, mu, sigma in segments:
        # 这一段的日收益序列
        z = rng.standard_normal(seg_len)
        daily_ret = (mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * z
        # 注入一个缓慢的均值回归扰动，让数据不那么"完美随机"
        # 这样均值回归策略才有东西可吃
        shock = rng.standard_normal(seg_len) * 0.002
        daily_ret = daily_ret + shock
        for r in daily_ret:
            closes.append(closes[-1] * np.exp(r))
    closes = np.array(closes[1:])  # 去掉初始价

    # 由 close 重构 OHLC
    opens = np.empty_like(closes)
    highs = np.empty_like(closes)
    lows = np.empty_like(closes)
    # 开盘价 = 前一日收盘 * 小幅跳空
    opens[0] = start_price
    opens[1:] = closes[:-1] * (1 + rng.normal(0, 0.001, size=len(closes) - 1))

    # 当日振幅随机
    intraday_amp = np.abs(rng.normal(0, 0.008, size=len(closes)))
    highs = np.maximum(opens, closes) * (1 + intraday_amp)
    lows = np.minimum(opens, closes) * (1 - intraday_amp)

    # 成交量：波动大的日子量也大
    rets = np.diff(closes, prepend=start_price)
    base_vol = 2.5e8
    volume = (base_vol * (1 + 8 * np.abs(rets) / rets.std())).astype(np.int64)

    # 交易日序列：跳过周末
    dates = pd.bdate_range(start=start_date, periods=len(closes))

    df = pd.DataFrame(
        {
            "date": dates,
            "open": np.round(opens, 2),
            "high": np.round(highs, 2),
            "low": np.round(lows, 2),
            "close": np.round(closes, 2),
            "volume": volume,
        }
    )
    return df.reset_index(drop=True)


if __name__ == "__main__":
    # 直接跑这个文件可以快速预览数据
    df = generate_demo_prices()
    print(df.head())
    print("...")
    print(df.tail())
    print(f"\n区间：{df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}, "
          f"共 {len(df)} 个交易日")
    print(f"起 {df['close'].iloc[0]:.2f} -> 终 {df['close'].iloc[-1]:.2f}, "
          f"累计 {df['close'].iloc[-1]/df['close'].iloc[0]-1:+.2%}")
