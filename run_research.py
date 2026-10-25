"""研究模式：跨指数对比 + 样本外检验。

    python run_research.py

这是断墨寻径方法论在量化里的直接应用：
    - 沪深300 上好 = 拟合好；创业板指上也好 = 真泛化
    - train 上好 = 拟合；test 上好 = 真学习
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from quant_seed.data import load_prices
from quant_seed.strategies import (
    MACross, RSIMeanRevert, DonchianBreakout, RSIWithStops, EnsembleVoting,
)
from quant_seed.backtest import run_backtest, compute_performance, walk_forward_split
from quant_seed.config import BacktestConfig


def main():
    cfg = BacktestConfig()
    strategies = [
        MACross(), RSIMeanRevert(), DonchianBreakout(),
        RSIWithStops(), EnsembleVoting(),
    ]
    indexes = [("000300", "沪深300"), ("399006", "创业板指")]

    lines = ["=" * 70,
             "QuantSeed 泛化检验报告",
             "用断墨寻径的话说：旧数据上赚钱叫拟合，新数据上也赚钱才叫学习",
             "=" * 70]

    for sym, name in indexes:
        df = load_prices("akshare", sym, "2023-01-01")
        bh = df.close.iloc[-1] / df.close.iloc[0] - 1
        lines.append(f"\n{'='*50}")
        lines.append(f"【{name} {sym}】 {df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}, B&H={bh:+.2%}")
        lines.append(f"{'='*50}")

        for S in strategies:
            sig = S.generate_signals(df)
            # 全样本
            bt = run_backtest(df, sig, cfg)
            p = compute_performance(bt.equity_curve, bt.trades, cfg)
            # 样本内外
            oos = walk_forward_split(df, sig, 0.7, cfg)
            lines.append(f"\n  {S.name}:")
            lines.append(f"    全样本:   ret={p.total_return:+7.2%} sharpe={p.sharpe:5.2f} maxdd={p.max_drawdown:7.2%}")
            lines.append(f"    train(70%): ret={oos.train_perf.total_return:+7.2%} sharpe={oos.train_perf.sharpe:5.2f}  [{oos.train_period}]")
            lines.append(f"    test(30%):  ret={oos.test_perf.total_return:+7.2%} sharpe={oos.test_perf.sharpe:5.2f}  [{oos.test_period}]")
            # 泛化判断
            if oos.train_perf.total_return > 0 and oos.test_perf.total_return > 0:
                verdict = "✓ 样本内外都赚——可能真有 edge"
            elif oos.train_perf.total_return > 0 and oos.test_perf.total_return < 0:
                verdict = "✗ 训练好测试崩——典型过拟合"
            else:
                verdict = "— 训练就不行"
            lines.append(f"    判定: {verdict}")

    out = "\n".join(lines)
    (PROJECT_ROOT / "results" / "research_report.txt").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
