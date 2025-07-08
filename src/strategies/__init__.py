"""
策略模块
包含各种量化交易策略的实现
"""

from .strategy_generator import StrategyGenerator
from .ma_strategy import MAStrategy

__all__ = ['StrategyGenerator', 'MAStrategy'] 