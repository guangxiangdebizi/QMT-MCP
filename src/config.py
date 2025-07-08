"""
配置管理模块
统一管理QuantMCP的所有配置参数
支持环境变量配置
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = os.getenv("QUANTMCP_HOST", "127.0.0.1")
    port: int = int(os.getenv("QUANTMCP_PORT", "8000"))
    transport: str = os.getenv("QUANTMCP_TRANSPORT", "sse")  # 保持SSE传输，LangChain MCP适配器支持SSE
    
@dataclass
class StrategyConfig:
    """策略配置"""
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "000001.SZ")
    default_start_date: str = os.getenv("DEFAULT_START_DATE", "20240101")
    default_end_date: str = os.getenv("DEFAULT_END_DATE", "20241201")
    default_short_period: int = int(os.getenv("DEFAULT_SHORT_PERIOD", "5"))
    default_long_period: int = int(os.getenv("DEFAULT_LONG_PERIOD", "20"))
    
@dataclass
class ScreeningConfig:
    """筛选配置"""
    default_stock_list: List[str] = None
    default_date_range: str = "20241101-20241201"
    
    def __post_init__(self):
        if self.default_stock_list is None:
            self.default_stock_list = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"]

@dataclass 
class TradingConfig:
    """交易配置"""
    # XTQuant连接配置
    qmt_path: str = os.getenv("QMT_PATH", r"D:\国金QMT交易端模拟\userdata_mini")
    session_id: int = int(os.getenv("QMT_SESSION_ID", "13579"))
    account_id: str = os.getenv("QMT_ACCOUNT_ID", "55012417")
    
    # 风险控制配置
    max_order_value: float = float(os.getenv("MAX_ORDER_VALUE", "100000.0"))      # 单笔订单最大金额
    max_position_value: float = float(os.getenv("MAX_POSITION_VALUE", "500000.0"))   # 单标的最大持仓金额
    min_order_quantity: int = int(os.getenv("MIN_ORDER_QUANTITY", "100"))          # 最小下单数量
    
    # 交易配置
    default_strategy_name: str = "QuantMCP"
    default_remark: str = "MCP_Auto_Order"
    market_order_spread: float = float(os.getenv("MARKET_ORDER_SPREAD", "0.1"))       # 市价单价差比例（10%）

class Config:
    """全局配置管理器"""
    
    def __init__(self):
        self.server = ServerConfig()
        self.strategy = StrategyConfig()
        self.screening = ScreeningConfig()
        self.trading = TradingConfig()
        
    @classmethod
    def from_file(cls, config_path: str):
        """从配置文件加载配置"""
        # 预留接口，可以后续从JSON/YAML文件加载配置
        return cls()

# 全局配置实例
config = Config() 