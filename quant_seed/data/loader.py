"""统一数据入口。

支持：
    - A股指数：沪深300、中证500、创业板指（新浪源）
    - 美股指数：标普500(.INX)、纳斯达克(.IXIC)、道琼斯(.DJI)（新浪源）
    - 演示数据：内置 GBM 生成，0 外网依赖

真实数据自动缓存到 results/cache/，第二次跑秒出。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .simulator import generate_demo_prices


CACHE_DIR = Path(__file__).resolve().parents[2] / "results" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# A股新浪代码前缀
_A_PREFIX = {
    "000300": "sh", "000905": "sh", "000001": "sh",
    "399001": "sz", "399006": "sz",
}

# 美股新浪代码
_US_SYMBOLS = {
    "SPX": ".INX",     # 标普500
    "IXIC": ".IXIC",   # 纳斯达克综合
    "DJI": ".DJI",     # 道琼斯
    "NDX": ".NDX",     # 纳斯达克100
}


def load_prices(
    source: str = "demo",
    symbol: str = "000300",
    start_date: str = "2023-01-01",
    end_date: str | None = None,
) -> pd.DataFrame:
    """加载日线行情。

    source:
        "demo"    -> 内置演示数据
        "akshare" -> A股指数（symbol=000300/399006 等）
        "us"      -> 美股指数（symbol=SPX/IXIC/DJI/NDX）
    """
    if source == "demo":
        return generate_demo_prices()

    end = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
    cache_key = f"{source}_{symbol}_{start_date}_{end}.csv"
    cache_path = CACHE_DIR / cache_key
    if cache_path.exists():
        df = pd.read_csv(cache_path, parse_dates=["date"])
        return df.reset_index(drop=True)

    if source == "akshare":
        df = _fetch_a_share(symbol, start_date, end)
    elif source == "us":
        df = _fetch_us(symbol, start_date, end)
    else:
        raise ValueError(f"未知数据源：{source}")

    df.to_csv(cache_path, index=False, encoding="utf-8-sig")
    return df


def _fetch_a_share(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    import akshare as ak
    prefix = _A_PREFIX.get(symbol, "sh")
    raw = ak.stock_zh_index_daily(symbol=f"{prefix}{symbol}")
    df = raw[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    return _filter(df, start_date, end_date)


def _fetch_us(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    import akshare as ak
    sina_sym = _US_SYMBOLS.get(symbol.upper(), symbol)
    raw = ak.index_us_stock_sina(symbol=sina_sym)
    # 新浪美股列名：date/open/high/low/close/volume/amount
    df = raw[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    return _filter(df, start_date, end_date)


def _filter(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df = df[(df["date"] >= pd.Timestamp(start_date)) &
            (df["date"] <= pd.Timestamp(end_date))].reset_index(drop=True)
    if len(df) < 100:
        raise RuntimeError(f"过滤后只有 {len(df)} 条数据，太少了。")
    return df
