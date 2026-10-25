"""全局配置：费率、初始资金、随机种子。

集中放在这里是有意为之——量化系统里，"假设"比代码本身更容易出错。
把所有可调参数收到一处，方便你做敏感性分析（sensitivity analysis）。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 1_000_000.0   # 初始资金 100 万
    commission: float = 0.0003          # 双边手续费 万三（券商普遍水平）
    slippage: float = 0.001             # 滑点 千一（市价单的保守估计）
    trading_days_per_year: int = 252    # A股年交易日
    risk_free_rate: float = 0.02        # 无风险利率（用于夏普）


# 演示数据的随机种子：固定它，你今天跑和下周跑结果完全一致，
# 这是可复现研究（reproducible research）的底线。
DEMO_RANDOM_SEED = 42

# 结果输出目录（相对项目根）
RESULTS_DIR = "results"
