"""AI 策略研究员 —— 把"和 AI 一起做量化"这件事产品化。

为什么这个模块存在？
    你关注 AI coding。但 AI coding 在量化里不是"让 AI 帮你写代码"这么浅，
    它是一种新的研究协作方式：
        人负责：提出直觉、判断市场结构、否决不切实际的想法、最终拍板；
        AI 负责：头脑风暴、查资料、把模糊想法翻译成数学和代码、debug、
                  从结果里找反直觉的 pattern。

这个文件给你 5 个可以直接复制到豆包/ChatGPT/Claude 里用的 Prompt 模板。
模板是"结构化思考"的脚手架——好的 Prompt 不是一句"帮我写个策略"，
而是把市场、假设、约束、可证伪方式一次说清楚。
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from textwrap import dedent


# ---------------------------------------------------------------------------
# 1. 策略假设工作表：任何策略在写代码前，先填这张表
# ---------------------------------------------------------------------------
@dataclass
class StrategyHypothesis:
    """一个可证伪的策略假设。

    量化圈有句话："先写结论，再找数据"。
    这个表逼你在写代码前把"你到底在赌什么"写清楚。
    如果哪一栏写不出来，说明这个想法还不成熟，不要急着回测。
    """
    market: str               # 哪个市场？（A股指数 / 美股个股 / 期货 / 加密）
    instrument: str           # 具体标的
    time_frame: str           # 日线 / 小时线 / tick
    core_belief: str          # 你到底相信什么？（例如："恐慌性暴跌后短期会均值回归"）
    economic_logic: str      # 为什么这个信念在现实里成立？（行为金融/流动性/制度原因）
    entry_rule: str           # 具体怎么买
    exit_rule: str            # 具体怎么卖（止盈/止损/时间止损）
    risk_controls: str        # 仓位上限？最大回撤止损？
    falsification: str        # 什么样的回测结果说明这个想法是错的？
    expected_edge: str        # 你预期它赚哪一段的钱？为什么别人没把它赚走？

    def to_prompt_block(self) -> str:
        return dedent(f"""
            【策略假设工作表】
            - 市场/标的：{self.market} / {self.instrument}
            - 周期：{self.time_frame}
            - 核心信念：{self.core_belief}
            - 现实逻辑：{self.economic_logic}
            - 入场规则：{self.entry_rule}
            - 出场规则：{self.exit_rule}
            - 风险控制：{self.risk_controls}
            - 可证伪条件：{self.falsification}
            - 预期超额来源：{self.expected_edge}
        """).strip()


# ---------------------------------------------------------------------------
# 2. 五个 Prompt 模板（直接复制粘贴）
# ---------------------------------------------------------------------------

PROMPT_BRAINSTORM = dedent("""
你是一位有 10 年经验的量化研究员，现在和我（软件工程背景，刚学量化）一起做研究。

我的背景：{your_background}
我关注的市场：{market}
我想找一类"行为金融驱动"的中短期策略（持有 1-10 天）。

请你：
1. 先不要写代码。先给我 5 个候选策略想法，每个想法用 3-5 句话说清楚：
   - 它在赌什么市场现象
   - 这个现象的现实来源（为什么别人没把它套利掉）
   - 大致的入场/出场逻辑
2. 然后用"可证伪性"给这 5 个想法打分（1-5），并告诉我哪个最值得先做、为什么。
3. 明确指出每个想法最可能失败的方式（样本内过拟合？交易成本？数据窥探？）。
""").strip()


PROMPT_DESIGN_FACTOR = dedent("""
你是量化因子挖掘专家。我想围绕"波动率突变"这个主题设计 3 个因子。

约束：
- 只能用日线 OHLCV 数据
- 因子值需要能解释未来 5 天的收益
- 不要用未来函数（shift 关系要清楚）
- 每个因子给出：数学定义、直觉、预期方向（正向/负向）、常见失效场景

输出格式：每个因子一段，包含公式（用文字+伪代码描述即可）。
最后给一张"这 3 个因子相关性预期"的小表。
""").strip()


PROMPT_CODE_REVIEW = dedent("""
下面是我写的回测代码。请你用"量化狙击手"的视角 review，重点找：
1. 未来函数（look-ahead bias）：信号是不是用了 T+1 才能看到的数据？
2. 成交假设是否过于乐观：成交价、滑点、手续费处理得对吗？
3. 幸存者偏差、前视偏差、数据泄露。
4. 边界条件：停牌、涨停买不进、跌停卖不出、涨跌停板。
5. 数学错误：年化、夏普、回撤的计算口径。

不要夸我。直接列问题，每条说"在哪一行、为什么错、怎么改"。

--- 我的代码开始 ---
{your_code}
--- 我的代码结束 ---
""").strip()


PROMPT_DIAGNOSE_BAD_BACKTEST = dedent("""
我的策略回测结果很差，请帮我诊断。不要直接给"加大参数"这种建议。

【回测设定】
- 标的：{instrument}
- 区间：{period}
- 策略逻辑：{logic}

【结果】
- 累计收益：{total_return}
- 年化夏普：{sharpe}
- 最大回撤：{max_dd}
- 胜率：{win_rate}
- 交易次数：{num_trades}

【我的观察】
{your_observations}

请按这个顺序帮我分析：
1. 这个结果在统计上是"正常的不好"还是"异常的不好"？
2. 最可能的三个原因（按概率排序），每个原因给出一个可以立刻验证的检查方法。
3. 我下一步应该改策略、换标的、还是直接放弃这个方向？
""").strip()


PROMPT_NEXT_STEP_ROADMAP = dedent("""
我是一名大二软件工程学生，正在实习量化。我已经：
- 能用 Python 写 pandas/numpy
- 跑通过一个简单的双均线回测
- 理解夏普、最大回撤、胜率
- 对 AI coding（用 LLM 辅助开发）很感兴趣

请帮我设计未来 6 个月的学习路线：
1. 我需要补哪些金融知识？（不要列书单，列"能动手练"的主题）
2. 我需要补哪些工程能力？（回测框架、数据库、部署、低延迟）
3. 每个月我应该能做出一个什么样的"作品"放进 GitHub？
4. 我应该在什么时间点开始投递实习？投什么类型的岗位？
5. 明确告诉我：以我的背景，最适合走"量化研究员"、"量化开发"、
   还是"AI+量化交叉"这条路？为什么？
""").strip()


# ---------------------------------------------------------------------------
# 3. 一个完整示例：用模板跑一遍
# ---------------------------------------------------------------------------
DEMO_HYPOTHESIS = StrategyHypothesis(
    market="A股",
    instrument="沪深300指数（演示数据）",
    time_frame="日线",
    core_belief="连续暴跌后，恐慌盘涌出导致价格短期超跌，随后 3-5 天会有均值回归",
    economic_logic="散户止损集中在整数关口，触发程序化抛售；
                   当卖压耗尽，做市商和抄底资金会推动价格反弹",
    entry_rule="5 日累计跌幅超过 8%，且当日成交量放大到 20 日均量 1.5 倍时买入",
    exit_rule="买入后涨 5% 止盈，或持有满 5 个交易日无条件平仓",
    risk_controls="单标的满仓，但连续两次亏损后暂停 5 个交易日",
    falsification="如果样本内胜率 < 45%，或扣完成本后期望收益 <= 0，放弃",
    expected_edge="这是一个短期行为金融异象，容量小、容量有限，
                   不适合大资金，但个人资金可以吃",
)


def print_demo_workflow() -> None:
    """演示：一次完整的 AI 协作研究长什么样。"""
    print("=" * 70)
    print("示例：把 DEMO_HYPOTHESIS 填进 Prompt 后，发给 AI")
    print("=" * 70)
    print(DEMO_HYPOTHESIS.to_prompt_block())
    print()
    print("然后接 PROMPT_CODE_REVIEW，把你写的策略代码贴进去……")


if __name__ == "__main__":
    print_demo_workflow()
    print("\n--- 五个 Prompt 模板都在本文件里，直接复制变量值即可 ---\n")
    for name in ["PROMPT_BRAINSTORM", "PROMPT_DESIGN_FACTOR",
                 "PROMPT_CODE_REVIEW", "PROMPT_DIAGNOSE_BAD_BACKTEST",
                 "PROMPT_NEXT_STEP_ROADMAP"]:
        print(f"\n>>> {name}")
        print(locals()[name][:200] + "...")
