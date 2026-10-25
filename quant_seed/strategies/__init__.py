from .base import StrategyBase
from .ma_cross import MACross
from .rsi_revert import RSIMeanRevert
from .momentum import DonchianBreakout
from .trend_filtered_rsi import RSIWithStops
from .combo_ai import EnsembleVoting

ALL_STRATEGIES = [MACross, RSIMeanRevert, DonchianBreakout, RSIWithStops, EnsembleVoting]

__all__ = [
    "StrategyBase",
    "MACross",
    "RSIMeanRevert",
    "DonchianBreakout",
    "RSIWithStops",
    "EnsembleVoting",
    "ALL_STRATEGIES",
]
