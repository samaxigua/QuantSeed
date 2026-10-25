"""HTML 报告生成器。

跑完回测后，把所有图表和绩效数字拼成一个自包含的 HTML：
- 图片用 base64 内嵌，单文件可发给同学、可双击打开；
- 不依赖任何前端框架，纯 HTML+CSS；
- 配色克制（深蓝 + 灰），像一份真正的研究简报。
"""
from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..backtest.metrics import Performance


def _img_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _perf_row(name: str, p: Performance) -> str:
    return (
        f"<tr><td><b>{name}</b></td>"
        f"<td>{p.total_return:+.2%}</td>"
        f"<td>{p.annual_return:+.2%}</td>"
        f"<td>{p.annual_vol:.2%}</td>"
        f"<td>{p.sharpe:.2f}</td>"
        f"<td>{p.max_drawdown:.2%}</td>"
        f"<td>{p.win_rate:.2%}</td>"
        f"<td>{p.profit_factor:.2f}</td>"
        f"<td>{p.num_trades}</td></tr>"
    )


def build_html_report(
    results: dict[str, dict],   # {strategy_name: {"perf":..., "equity":..., "trades":..., "figs": {...}}}
    comparison_png: Path,
    out_path: Path,
    initial_cash: float,
) -> Path:
    """生成自包含 HTML。

    results 结构示例：
        {
          "ma_cross": {
             "perf": Performance(...),
             "equity": DataFrame,
             "trades": DataFrame,
             "figs": {"price": Path, "equity_bh": Path, "drawdown": Path, "pnl": Path}
          },
          ...
        }
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = "\n".join(_perf_row(name, r["perf"]) for name, r in results.items())

    # 每个策略的卡片
    cards = []
    for name, r in results.items():
        figs = r["figs"]
        perf = r["perf"]
        cards.append(f"""
        <div class="card">
          <h2>{name}</h2>
          <div class="metrics">
            <span>累计 <b>{perf.total_return:+.2%}</b></span>
            <span>夏普 <b>{perf.sharpe:.2f}</b></span>
            <span>回撤 <b>{perf.max_drawdown:.2%}</b></span>
            <span>交易 <b>{perf.num_trades}</b></span>
          </div>
          <img src="data:image/png;base64,{_img_b64(figs['price'])}"/>
          <img src="data:image/png;base64,{_img_b64(figs['equity_bh'])}"/>
          <img src="data:image/png;base64,{_img_b64(figs['drawdown'])}"/>
          <img src="data:image/png;base64,{_img_b64(figs['pnl'])}"/>
        </div>
        """)
    cards_html = "\n".join(cards)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>QuantSeed 回测报告</title>
<style>
  body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif;
         max-width: 1100px; margin: 30px auto; padding: 0 20px;
         color: #222; background: #fafafa; }}
  h1 {{ color: #1a3a6c; border-bottom: 3px solid #1a3a6c; padding-bottom: 8px; }}
  .meta {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff;
           font-size: 14px; margin-bottom: 30px; }}
  th, td {{ border: 1px solid #e0e0e0; padding: 8px 10px; text-align: right; }}
  th {{ background: #1a3a6c; color: #fff; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .card {{ background: #fff; padding: 20px; margin-bottom: 24px;
          border: 1px solid #e5e5e5; border-radius: 6px; }}
  .card h2 {{ color: #1a3a6c; margin-top: 0; }}
  .metrics span {{ display: inline-block; margin-right: 20px;
                  font-size: 14px; color: #555; }}
  img {{ width: 100%; margin: 10px 0; border: 1px solid #eee; }}
  .callout {{ background: #fff8e1; border-left: 4px solid #f9a825;
              padding: 12px 16px; margin: 20px 0; font-size: 14px; }}
  .good {{ color: #2e7d32; }}
  .bad {{ color: #c62828; }}
</style>
</head>
<body>
  <h1>QuantSeed 回测报告</h1>
  <div class="meta">生成时间：{now} ｜ 初始资金：{initial_cash:,.0f} ｜
        数据源：内置演示数据（可在 run.py 切换 akshare）</div>

  <h2>策略对比</h2>
  <table>
    <tr><th>策略</th><th>累计收益</th><th>年化</th><th>年化波动</th>
        <th>夏普</th><th>最大回撤</th><th>胜率</th><th>盈亏比</th><th>交易数</th></tr>
    {rows}
  </table>

  <h2>净值曲线对比</h2>
  <img src="data:image/png;base64,{_img_b64(comparison_png)}"/>

  <h2>分策略明细</h2>
  {cards_html}

  <div class="callout">
    <b>下一步提示：</b>这份报告用的是<b>演示数据</b>——它的目的是让你
    看懂整条链路（数据 → 信号 → 回测 → 绩效 → 可视化），不是给你一个
    能拿去实盘的策略。把 <code>run.py</code> 里的 <code>source="demo"</code>
    改成 <code>"akshare"</code>，再接真实指数，结论会完全不一样。
    然后打开 <code>quant_seed/ai_researcher/prompts.py</code>，
    用里面的 Prompt 模板让 AI 帮你设计下一个策略。
  </div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    return out_path
