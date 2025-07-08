"""
交易执行工具
提供下单、撤单和持仓管理的MCP工具接口
"""

import logging
from datetime import datetime
from typing import Optional
from ..utils.xtquant_client import xt_client
from ..config import config

# 导入XTQuant交易相关模块
try:
    from xtquant.xttrader import XtQuantTrader
    from xtquant.xttype import StockAccount
    from xtquant import xtconstant
    XTQUANT_AVAILABLE = True
except ImportError:
    XTQUANT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("XTQuant交易模块未安装，将运行在模拟模式")

logger = logging.getLogger(__name__)

class TradingTool:
    """交易执行工具"""
    
    def __init__(self):
        self.trading_state = "NORMAL"
        
        # 从配置文件加载参数
        self.max_order_value = config.trading.max_order_value
        self.max_position_value = config.trading.max_position_value
        self.min_order_quantity = config.trading.min_order_quantity
        
        # XTQuant交易相关配置
        self.qmt_path = config.trading.qmt_path
        self.session_id = config.trading.session_id
        self.account_id = config.trading.account_id
        
        # 交易器实例
        self.trader = None
        self.account = None
        self._init_trader()
    
    def place_order(self, symbol: str, quantity: int, price: float, direction: str = "BUY") -> str:
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
            logger.info(f"执行下单: {symbol} {direction} {quantity}股 @{price}")
            
            # 检查交易状态
            if self.trading_state != "NORMAL":
                return f"[STOP] 交易状态异常: {self.trading_state}，无法执行交易"
            
            # 基本参数验证
            if not symbol or len(symbol) < 6:
                return "[ERROR] 股票代码格式错误"
            
            if quantity <= 0 or quantity % self.min_order_quantity != 0:
                return f"[ERROR] 数量必须是正数且为{self.min_order_quantity}的整数倍"
            
            if price <= 0:
                return "[ERROR] 价格必须大于0"
            
            if direction not in ['BUY', 'SELL']:
                return "[ERROR] 交易方向必须是BUY或SELL"
            
            # 检查交易器连接
            if not self._ensure_trader_ready():
                return "[ERROR] XTQuant交易器未就绪，无法执行交易"
            
            # 执行下单
            order_result = self._execute_simple_order(symbol, direction, quantity, price)
            
            # 生成简化报告
            return self._generate_simple_report(symbol, direction, quantity, price, order_result)
            
        except Exception as e:
            logger.error(f"下单执行失败: {e}")
            return f"[ERROR] 下单执行失败: {str(e)}"
    
    def cancel_order(self, order_id: str) -> str:
        """撤单工具
        
        Args:
            order_id: 订单ID
        
        Returns:
            撤单结果
        """
        
        try:
            logger.info(f"执行撤单: order_id={order_id}")
            
            if not order_id:
                return "[ERROR] 请提供订单ID"
            
            # 检查交易器连接
            if not self._ensure_trader_ready():
                return "[ERROR] XTQuant交易器未就绪，无法执行撤单"
            
            # 执行撤单
            result = self._execute_cancel_order(order_id)
            
            if result:
                return f"[OK] 订单 {order_id} 撤单成功"
            else:
                return f"[ERROR] 订单 {order_id} 撤单失败"
            
        except Exception as e:
            logger.error(f"撤单执行失败: {e}")
            return f"[ERROR] 撤单执行失败: {str(e)}"
    
    def get_positions(self, symbol: str = None) -> str:
        """查询持仓信息
        
        Args:
            symbol: 股票代码（可选）
        
        Returns:
            持仓信息
        """
        
        try:
            if not self._ensure_trader_ready():
                return "[ERROR] XTQuant交易器未就绪，无法查询持仓"
            
            if symbol:
                # 查询指定股票持仓
                position = self._get_single_position(symbol)
                if position:
                    return f"[POSITION] {symbol} 持仓: {position['quantity']}股, 成本价: {position['avg_price']:.2f}"
                else:
                    return f"[INFO] {symbol} 暂无持仓"
            else:
                return "[INFO] 请指定股票代码查询持仓"
            
        except Exception as e:
            logger.error(f"查询持仓失败: {e}")
            return f"[ERROR] 查询持仓失败: {str(e)}"
    
    def set_trading_state(self, state: str, reason: str = "") -> str:
        """设置交易状态
        
        Args:
            state: 交易状态 ('NORMAL', 'STOP')
            reason: 状态变更原因
        
        Returns:
            状态设置结果
        """
        
        valid_states = ['NORMAL', 'STOP']
        if state not in valid_states:
            return f"[ERROR] 无效的交易状态: {state}，有效状态: {valid_states}"
        
        old_state = self.trading_state
        self.trading_state = state
        
        logger.info(f"交易状态变更: {old_state} -> {state}, 原因: {reason}")
        
        return f"[OK] 交易状态已更新: {old_state} -> {state}\n原因: {reason}"
    
    # 私有方法
    
    def _init_trader(self):
        """初始化交易器"""
        if not XTQUANT_AVAILABLE:
            logger.warning("XTQuant不可用，交易功能将在模拟模式运行")
            return
        
        try:
            self.trader = XtQuantTrader(self.qmt_path, self.session_id)
            self.account = StockAccount(self.account_id)
            logger.info("XTQuant交易器初始化完成")
        except Exception as e:
            logger.error(f"XTQuant交易器初始化失败: {e}")
            self.trader = None
            self.account = None
    
    def _ensure_trader_ready(self):
        """确保交易器就绪"""
        if not XTQUANT_AVAILABLE or not self.trader or not self.account:
            return False
        
        try:
            # 检查连接状态，如果未连接则尝试连接
            if not hasattr(self.trader, '_connected') or not self.trader._connected:
                self.trader.start()
                if self.trader.connect() != 0:
                    logger.error("XTQuant连接失败")
                    return False
                if self.trader.subscribe(self.account) != 0:
                    logger.error("账户订阅失败")
                    return False
                self.trader._connected = True
                logger.info("XTQuant交易器连接成功")
            
            return True
        except Exception as e:
            logger.error(f"XTQuant交易器连接检查失败: {e}")
            return False
    
    def _get_current_price(self, symbol):
        """获取当前价格"""
        try:
            # 这里应该调用XTQuant接口获取实时价格
            # 临时返回固定价格用于测试
            price_map = {
                '000001.SZ': 10.50,
                '000002.SZ': 25.80,
                '600000.SH': 6.20,
                '600036.SH': 42.15
            }
            return price_map.get(symbol, 10.00)
        except:
            return None
    
    def _execute_simple_order(self, symbol, direction, quantity, price):
        """执行简化订单"""
        if not XTQUANT_AVAILABLE or not self.trader or not self.account:
            # 模拟模式 - 直接返回成功
            import random
            order_id = f"SIM{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"
            return {
                'success': True,
                'order_id': order_id,
                'message': '[模拟] 订单已提交'
            }
        
        try:
            # 转换方向
            xt_direction = xtconstant.STOCK_BUY if direction == 'BUY' else xtconstant.STOCK_SELL
            
            # 调用XTQuant下单接口
            order_id = self.trader.order_stock(
                self.account,           # 账户
                symbol,                 # 股票代码
                xt_direction,          # 买卖方向
                quantity,              # 数量
                xtconstant.FIX_PRICE,  # 限价单
                price,                 # 价格
                "QuantMCP",            # 策略名
                "Auto_Order"           # 备注
            )
            
            if order_id > 0:
                return {
                    'success': True,
                    'order_id': str(order_id),
                    'message': '订单已成功提交'
                }
            else:
                return {
                    'success': False,
                    'order_id': None,
                    'message': f'订单提交失败，错误代码: {order_id}'
                }
                
        except Exception as e:
            logger.error(f"执行订单失败: {e}")
            return {
                'success': False,
                'order_id': None,
                'message': f'订单执行异常: {str(e)}'
            }
    
    def _execute_cancel_order(self, order_id):
        """执行撤单"""
        if not XTQUANT_AVAILABLE or not self.trader or not self.account:
            # 模拟模式
            return True
        
        try:
            result = self.trader.cancel_order_stock(self.account, int(order_id))
            return result == 0
        except Exception as e:
            logger.error(f"执行撤单失败: {e}")
            return False
    
    def _get_single_position(self, symbol):
        """获取单个股票持仓"""
        if not XTQUANT_AVAILABLE or not self.trader or not self.account:
            # 模拟模式
            return None
        
        try:
            position = self.trader.query_stock_position(self.account, symbol)
            if position and getattr(position, 'volume', 0) > 0:
                return {
                    'quantity': getattr(position, 'volume', 0),
                    'avg_price': getattr(position, 'avg_price', 0)
                }
            return None
        except Exception as e:
            logger.error(f"查询持仓失败: {e}")
            return None
    
    def _generate_simple_report(self, symbol, direction, quantity, price, order_result):
        """生成简化报告"""
        report = f"[ORDER] 下单报告\n"
        report += "=" * 20 + "\n"
        report += f"股票代码: {symbol}\n"
        report += f"交易方向: {direction}\n"
        report += f"数量: {quantity}股\n"
        report += f"价格: {price:.2f}\n"
        report += f"金额: {price * quantity:.2f}\n"
        
        if order_result['success']:
            report += f"订单号: {order_result['order_id']}\n"
            report += f"状态: ✅ {order_result['message']}\n"
        else:
            report += f"状态: ❌ {order_result['message']}\n"
        
        return report 