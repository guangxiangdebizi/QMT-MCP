import os
from datetime import datetime

class QMTStrategyTool:
    """将策略代码保存到 QMT 本地量化策略目录的工具。

    默认目录通过环境变量 QMT_STRATEGY_DIR 指定，若未设置则使用
    `D:\国金QMT交易端模拟\mpython`。
    """

    def __init__(self, strategy_dir: str | None = None):
        # 默认目录：如果未指定且未设置环境变量，则使用国金QMT交易端的 mpython 目录
        default_dir = r"D:\国金QMT交易端模拟\mpython"
        self.strategy_dir = strategy_dir or os.getenv("QMT_STRATEGY_DIR", default_dir)
        os.makedirs(self.strategy_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 通用保存方法
    # ------------------------------------------------------------------
    def save_strategy(self, strategy_name: str, code: str) -> str:
        """保存用户提供的策略代码到 QMT 策略目录，并自动注册到 QMT。

        Args:
            strategy_name: 文件名，不需要扩展名，自动加 `.py`
            code: 完整的 Python 策略代码内容
        Returns:
            保存结果信息
        """
        filename = f"{strategy_name}.py" if not strategy_name.endswith(".py") else strategy_name
        path = os.path.join(self.strategy_dir, filename)
        
        # 保存文件
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # QMT会在启动时自动扫描策略目录，无需手动注册
        return f"[OK] 策略已保存到QMT策略目录: {path}\n[INFO] 重启QMT后可在策略列表中看到新策略"

    # ------------------------------------------------------------------
    # 示例：双均线策略生成
    # ------------------------------------------------------------------
    def generate_ma_strategy(self, symbol: str = "000001.SZ", short_period: int = 5, long_period: int = 20,
                             strategy_name: str | None = None) -> str:
        """生成并保存一个简单的双均线回测策略示例。"""
        strategy_name = strategy_name or f"ma_{short_period}_{long_period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        code = f'''# -*- coding: utf-8 -*-
"""
QMT 双均线策略示例，由 QuantMCP 自动生成
"""
import pandas as pd

def init(context):
    context.symbol = "{symbol}"
    context.short_period = {short_period}
    context.long_period = {long_period}

def handle_bar(context, bar_dict):
    data = context.history(context.symbol, '1d', {long_period}+1)
    if len(data) < {long_period}:
        return
    close = data['close']
    ma_short = close.rolling({short_period}).mean().iloc[-1]
    ma_long = close.rolling({long_period}).mean().iloc[-1]
    pos = context.position(context.symbol).volume

    if ma_short > ma_long and pos == 0:
        context.order_target_percent(context.symbol, 1)
    elif ma_short < ma_long and pos > 0:
        context.order_target_percent(context.symbol, 0)
'''
        return self.save_strategy(strategy_name, code) 