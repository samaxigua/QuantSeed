"""统一数据入口。

你以后接真实数据（akshare/tushare/聚宽/Wind），只需要改这一个文件，
上层的策略、回测、报告代码一行都不用动。这就是软件工程里说的
"依赖倒置"——上层不该知道数据从哪来。

真实数据会自动缓存到 results/cache/ 下，第二次跑秒出，
不用每次都去请求新浪。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .simulator import generate_demo_prices


CACHE_DIR = Path(__file__).resolve().parents[2] / "results" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# 新浪指数代码前缀映射
_SINA_PREFIX = {
    "000300": "sh",   # 沪深300
    "000905": "sh",   # 中证500
    "000001": "sh",   # 上证指数
    "399001": "sz",   # 深证成指
    "399006": "sz",   # 创业板指
}


def load_prices(
    source: str = "demo",
    symbol: str = "000300",
    start_date: str = "2023-01-01",
    end_date: str | None = None,
) -> pd.DataFrame:
    """加载日线行情。

    Parameters
    ----------
    source : str
        "demo"   -> 内置演示数据（默认，开箱即跑）
        "akshare"-> 真实 A 股指数日线（新浪源）
    symbol : str
        指数代码，例如 "000300"（沪深300）、"000905"（中证500）、"399006"（创业板指）
    start_date, end_date : str
        日期区间，格式 "YYYY-MM-DD"
    """
    if source == "demo":
        return generate_demo_prices()

    if source == "akshare":
        end = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")
        cache_key = f"ak_{symbol}_{start_date}_{end}.csv"
        cache_path = CACHE_DIR / cache_key
        if cache_path.exists():
            df = pd.read_csv(cache_path, parse_dates=["date"])
            return df.reset_index(drop=True)

        df = _fetch_from_akshare(symbol, start_date, end)
        df.to_csv(cache_path, index=False, encoding="utf-8-sig")
        return df

    raise ValueError(f"未知数据源：{source}")


def _fetch_from_akshare(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """从 akshare（新浪源）拉取指数日线，统一列名。"""
    try:
        import akshare as ak  # type: ignore
    except ImportError as e:
        raise ImportError(
            "需要 akshare：python -m pip install akshare\n"
            "或者先用默认的 source='demo' 跑通整个项目。"
        ) from e

    prefix = _SINA_PREFIX.get(symbol, "sh")
    sina_symbol = f"{prefix}{symbol}"

    try:
        raw = ak.stock_zh_index_daily(symbol=sina_symbol)
    except Exception as e:
        raise RuntimeError(
            f"akshare 拉取 {sina_symbol} 失败：{e}\n"
            f"可能是网络问题，检查能否访问新浪财经。"
        ) from e

    if raw is None or len(raw) == 0:
        raise RuntimeError(f"akshare 返回空数据：symbol={sina_symbol}")

    # 新浪源列名已经是 date/open/high/low/close/volume，直接用
    df = raw[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 按日期过滤
    df = df[(df["date"] >= pd.Timestamp(start_date)) &
            (df["date"] <= pd.Timestamp(end_date))].reset_index(drop=True)

    if len(df) < 100:
        raise RuntimeError(
            f"过滤后只有 {len(df)} 条数据，太少了。"
            f"检查 start_date={start_date} end_date={end_date} 是否合理。"
        )
    return df
