#!/usr/bin/env python3
"""
QuantMCP Main Entry - 模块化架构主入口
提供智能策略生成、回测分析、股票筛选等功能
"""

import logging
import traceback
import asyncio
from datetime import datetime

# 使用FastMCP 2.0
from fastmcp import FastMCP

# 导入模块化组件
from src.config import config
from src.utils.xtquant_client import xt_client
from src.tools import TradingTool, QMTStrategyTool

# 配置日志
import os

# 确保logs目录存在  
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quantmcp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("quantmcp")

def init_system():
    """初始化系统"""
    logger.info("=" * 50)
    logger.info("QuantMCP 模块化架构 v2.0 启动中...")
    logger.info("=" * 50)
    
    # 初始化XTQuant连接
    logger.info("正在初始化XTQuant连接...")
    try:
        if xt_client.connect():
            logger.info("[OK] XTQuant连接成功")
        else:
            logger.warning("[WARNING] XTQuant连接失败，将在离线模式下运行")
    except Exception as e:
        logger.error(f"[ERROR] XTQuant初始化失败: {e}")
    
    logger.info("[OK] 系统初始化完成")

# 创建FastMCP实例
mcp = FastMCP("QuantMCP量化交易助手")

# 初始化工具实例
trading_tool = TradingTool()
qmt_tool = QMTStrategyTool()

@mcp.tool()
def place_order(symbol: str, quantity: int, price: float, direction: str = "BUY") -> str:
    """简化下单工具
    
    用户只需要传入股票代码、数量和价格即可下单。
    
    Args:
        symbol: 股票代码，如 000001.SZ、600000.SH
        quantity: 买入股数（必须是100的整数倍）
        price: 下单价格
        direction: 交易方向，默认BUY买入，也可以是SELL卖出
    
    Returns:
        下单结果
    """
    try:
        logger.info(f"MCP调用: place_order({symbol}, {quantity}, {price}, {direction})")
        
        result = trading_tool.place_order(
            symbol=symbol,
            quantity=quantity,
            price=price,
            direction=direction
        )
        
        return result
        
    except Exception as e:
        logger.error(f"place_order执行失败: {e}")
        return f"[ERROR] 下单失败: {str(e)}"

@mcp.tool()
def cancel_order(order_id: str) -> str:
    """撤单工具
    
    Args:
        order_id: 订单ID
    
    Returns:
        撤单结果
    """
    try:
        logger.info(f"MCP调用: cancel_order({order_id})")
        
        result = trading_tool.cancel_order(order_id=order_id)
        
        return result
        
    except Exception as e:
        logger.error(f"cancel_order执行失败: {e}")
        return f"[ERROR] 撤单失败: {str(e)}"

@mcp.tool()
def save_qmt_strategy(strategy_name: str, code: str) -> str:
    """保存自定义策略代码到 QMT 本地策略目录"""
    try:
        logger.info(f"MCP调用: save_qmt_strategy({strategy_name})")
        return qmt_tool.save_strategy(strategy_name, code)
    except Exception as e:
        logger.error(f"save_qmt_strategy 执行失败: {e}")
        return f"[ERROR] 保存策略失败: {str(e)}"

@mcp.tool()
def generate_ma_strategy(symbol: str = "000001.SZ", short_period: int = 5, long_period: int = 20,
                         strategy_name: str | None = None) -> str:
    """生成并保存双均线策略示例"""
    try:
        logger.info("MCP调用: generate_ma_strategy")
        return qmt_tool.generate_ma_strategy(symbol, short_period, long_period, strategy_name)
    except Exception as e:
        logger.error(f"generate_ma_strategy 执行失败: {e}")
        return f"[ERROR] 生成策略失败: {str(e)}"

def main():
    """主函数"""
    try:
        # 初始化系统
        init_system()
        
        # 启动信息
        logger.info("[INFO] QuantMCP服务器启动信息:")
        logger.info(f"   * 服务地址: http://{config.server.host}:{config.server.port}")
        logger.info(f"   * 传输方式: {config.server.transport.upper()}")
        logger.info(f"   * XTQuant状态: {'已连接' if xt_client.is_connected() else '未连接'}")
        logger.info("   * 架构版本: 模块化架构 v2.0")
        
        # 启动SSE服务器
        logger.info(f"[START] QuantMCP Server starting on http://{config.server.host}:{config.server.port}")
        
        # 使用FastMCP 2.0的SSE传输方式运行
        mcp.run(
            transport=config.server.transport,
            host=config.server.host,
            port=config.server.port
        )
        
    except KeyboardInterrupt:
        logger.info("[STOP] 用户中断，服务器正在关闭...")
    except Exception as e:
        logger.error(f"[ERROR] 服务器错误: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        # 清理资源
        try:
            xt_client.disconnect()
            logger.info("[OK] 资源清理完成")
        except:
            pass

if __name__ == "__main__":
    main() 