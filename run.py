"""一键运行入口。

用法：
    python run.py                                  # 默认演示数据
    python run.py akshare                          # 沪深300真实数据
    python run.py akshare 000905                     # 中证500
    python run.py akshare 000300 2022-01-01         # 指定起止日期
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许直接 `python run.py` 运行
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from quant_seed.config import BacktestConfig, RESULTS_DIR
from quant_seed.data import load_prices
from quant_seed.strategies import (
    MACross, RSIMeanRevert, DonchianBreakout, RSIWithStops, EnsembleVoting,
)
from quant_seed.backtest import run_backtest, compute_performance
from quant_seed.viz import (
    plot_price_with_trades,
    plot_equity_vs_bh,
    plot_drawdown,
    plot_strategy_comparison,
    plot_trade_pnl,
)
from quant_seed.report import build_html_report


def main(source: str = "demo", symbol: str = "000300",
         start_date: str = "2023-01-01") -> None:
    cfg = BacktestConfig()
    results_dir = PROJECT_ROOT / RESULTS_DIR
    results_dir.mkdir(exist_ok=True)

    print(f"[1/5] 加载数据（source={source}, symbol={symbol}）...")
    df = load_prices(source=source, symbol=symbol, start_date=start_date)
    print(f"      {len(df)} 个交易日，{df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}")
    print(f"      起 {df['close'].iloc[0]:.2f} -> 终 {df['close'].iloc[-1]:.2f}, "
          f"累计 {df['close'].iloc[-1]/df['close'].iloc[0]-1:+.2%}")

    strategies = [
        MACross(fast=20, slow=60),
        RSIMeanRevert(),
        DonchianBreakout(),
        RSIWithStops(),
        EnsembleVoting(),
    ]

    results = {}
    equity_dict = {}

    print("[2/5] 跑回测...")
    for strat in strategies:
        signals = strat.generate_signals(df)
        bt = run_backtest(df, signals, cfg)
        perf = compute_performance(bt.equity_curve, bt.trades, cfg)
        results[strat.name] = {
            "perf": perf,
            "equity": bt.equity_curve,
            "trades": bt.trades,
        }
        equity_dict[strat.name] = bt.equity_curve
        print(f"      {strat.name:20s} 累计{perf.total_return:+7.2%}  "
              f"夏普{perf.sharpe:5.2f}  回撤{perf.max_drawdown:7.2%}  "
              f"交易{perf.num_trades}笔")

    print("[3/5] 画图...")
    for name, r in results.items():
        figs = {
            "price": results_dir / f"{name}_price.png",
            "equity_bh": results_dir / f"{name}_equity.png",
            "drawdown": results_dir / f"{name}_drawdown.png",
            "pnl": results_dir / f"{name}_pnl.png",
        }
        plot_price_with_trades(df, r["trades"], f"{name} — 价格与交易点", figs["price"])
        plot_equity_vs_bh(r["equity"], cfg.initial_cash, f"{name} — 策略 vs 买入持有", figs["equity_bh"])
        plot_drawdown(r["equity"], name, figs["drawdown"])
        plot_trade_pnl(r["trades"], name, figs["pnl"])
        r["figs"] = figs

    comparison_png = results_dir / "comparison.png"
    plot_strategy_comparison(equity_dict, cfg.initial_cash,
                             f"全部策略净值对比（{source}:{symbol}）", comparison_png)

    print("[4/5] 生成 HTML 报告...")
    report_path = results_dir / "report.html"
    build_html_report(results, comparison_png, report_path, cfg.initial_cash)

    print("[5/5] 完成。")
    print(f"\n>>> 打开报告：{report_path}")
    print(f">>> 浏览器里看：file:///{report_path.as_posix()}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "demo"
    sym = sys.argv[2] if len(sys.argv) > 2 else "000300"
    sd = sys.argv[3] if len(sys.argv) > 3 else "2023-01-01"
    main(source=src, symbol=sym, start_date=sd)
