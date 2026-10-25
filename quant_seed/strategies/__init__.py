from .base import StrategyBase
from .ma_cross import MACross
from .rsi_revert import RSIMeanRevert
from .momentum import DonchianBreakout
from .combo_ai import EnsembleVoting

ALL_STRATEGIES = [MACross, RSIMeanRevert, DonchianBreakout, EnsembleVoting]

__all__ = [
    "StrategyBase",
    "MACross",
    "RSIMeanRevert",
    "DonchianBreakout",
    "EnsembleVoting",
    "ALL_STRATEGIES",
]
