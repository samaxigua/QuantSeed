from .base import StrategyBase
from .ma_cross import MACross
from .rsi_revert import RSIMeanRevert
from .momentum import DonchianBreakout
from .trend_filtered_rsi import RSIWithStops
from .regime_switch import RegimeSwitch
from .combo_ai import EnsembleVoting

ALL_STRATEGIES = [MACross, RSIMeanRevert, DonchianBreakout, RSIWithStops, RegimeSwitch, EnsembleVoting]

__all__ = [
    "StrategyBase",
    "MACross",
    "RSIMeanRevert",
    "DonchianBreakout",
    "RSIWithStops",
    "RegimeSwitch",
    "EnsembleVoting",
    "ALL_STRATEGIES",
]
