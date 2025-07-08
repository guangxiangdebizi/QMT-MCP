"""
策略生成器模块
统一管理和生成各种量化策略
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

from .ma_strategy import MAStrategy
from ..utils.xtquant_client import xt_client
from ..utils.data_handler import DataHandler

logger = logging.getLogger(__name__)

class StrategyGenerator:
    """策略生成器"""
    
    def __init__(self):
        self.data_handler = DataHandler()
        
    def generate_strategy(
        self,
        strategy_type: str,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> str:
        """生成策略并执行回测"""
        
        try:
            # 验证输入参数
            if not self.data_handler.validate_symbol(symbol):
                return f"[ERROR] 股票代码格式错误: {symbol}"
            
            if not self.data_handler.validate_date(start_date):
                return f"[ERROR] 开始日期格式错误: {start_date}"
                
            if not self.data_handler.validate_date(end_date):
                return f"[ERROR] 结束日期格式错误: {end_date}"
            
            # 获取股票数据
            try:
                data = xt_client.get_market_data(symbol, start_date, end_date)
                if data is None:
                    if not xt_client.is_connected():
                        return f"[ERROR] XTQuant未连接，请确保迅投QMT客户端已启动并登录"
                    else:
                        return f"[ERROR] 获取{symbol}数据失败\n\n[TIPS] 可能的原因：\n" \
                               f"   1. 股票在{start_date}-{end_date}期间停牌或退市\n" \
                               f"   2. 股票代码不存在或已更名\n" \
                               f"   3. XTQuant数据权限不包含此股票\n" \
                               f"   4. 日期范围无效或超出数据覆盖范围\n\n" \
                               f"[SUGGEST] 建议：\n" \
                               f"   - 使用确认可用的股票代码（如000001.SZ、600519.SH）\n" \
                               f"   - 调整日期范围或使用数据诊断工具进一步分析"
                        
            except ConnectionError as e:
                return f"[ERROR] 连接错误: {str(e)}"
            except Exception as e:
                return f"[ERROR] 获取数据失败: {str(e)}"
            
            # 验证和清洗数据
            if not self.data_handler.validate_market_data(data):
                return f"[ERROR] 获取到的{symbol}数据格式无效或为空"
            
            data = self.data_handler.clean_market_data(data)
            if data.empty:
                return f"[ERROR] 清洗后的{symbol}数据为空"
            
            # 根据策略类型生成策略
            if strategy_type == 'ma_cross':
                return self._generate_ma_strategy(data, symbol, start_date, end_date, **kwargs)
            elif strategy_type == 'macd':
                return self._generate_macd_strategy(data, symbol, start_date, end_date, **kwargs)
            elif strategy_type == 'rsi':
                return self._generate_rsi_strategy(data, symbol, start_date, end_date, **kwargs)
            else:
                return f"[ERROR] 不支持的策略类型: {strategy_type}，支持的类型: ma_cross, macd, rsi"
                
        except Exception as e:
            logger.error(f"策略生成失败: {e}")
            return f"[ERROR] 策略生成失败: {str(e)}"
    
    def _generate_ma_strategy(
        self, 
        data: pd.DataFrame, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        **kwargs
    ) -> str:
        """生成双均线策略"""
        
        short_period = kwargs.get('short_period', 5)
        long_period = kwargs.get('long_period', 20)
        
        # 验证参数
        if short_period >= long_period:
            return f"[ERROR] 短期均线周期({short_period})必须小于长期均线周期({long_period})"
        
        if long_period >= len(data):
            return f"[ERROR] 长期均线周期({long_period})不能超过数据长度({len(data)})"
        
        try:
            # 创建策略实例
            strategy = MAStrategy(short_period=short_period, long_period=long_period)
            
            # 执行回测
            backtest_result = strategy.backtest(data)
            
            if not backtest_result['success']:
                return f"[ERROR] 策略回测失败: {backtest_result['error']}"
            
            metrics = backtest_result['metrics']
            
            if 'error' in metrics:
                return f"[ERROR] 策略计算失败: {metrics['error']}"
            
            # 生成报告
            result_text = f"[OK] 双均线策略生成成功！\n\n"
            result_text += f"[DATA] 股票信息: {symbol}\n"
            result_text += f"[DATE] 数据期间: {start_date} 至 {end_date}\n"
            result_text += f"[CHART] 数据条数: {len(data)} 条\n"
            result_text += f"[DATA] 交易天数: {metrics['trading_days']} 天\n\n"
            
            result_text += f"[TARGET] 双均线策略参数:\n"
            result_text += f"   * 短期均线: {short_period}日\n"
            result_text += f"   * 长期均线: {long_period}日\n\n"
            
            result_text += f"[CHART] 策略表现:\n"
            result_text += f"   * 总收益率: {self.data_handler.format_percentage(metrics['final_return'])}\n"
            result_text += f"   * 年化收益率: {self.data_handler.format_percentage(metrics['annual_return'])}\n"
            result_text += f"   * 最大回撤: {self.data_handler.format_percentage(metrics['max_drawdown'])}\n"
            result_text += f"   * 年化波动率: {self.data_handler.format_percentage(metrics['volatility'])}\n"
            result_text += f"   * 夏普比率: {self.data_handler.format_number(metrics['sharpe_ratio'])}\n"
            result_text += f"   * 交易次数: {metrics['total_trades']}\n"
            result_text += f"   * 胜率: {self.data_handler.format_percentage(metrics['win_rate'])}\n\n"
            
            # 策略评价
            result_text += self._evaluate_strategy(metrics)
            
            return result_text
            
        except Exception as e:
            logger.error(f"双均线策略生成失败: {e}")
            return f"[ERROR] 双均线策略生成失败: {str(e)}"
    
    def _generate_macd_strategy(self, data: pd.DataFrame, symbol: str, start_date: str, end_date: str, **kwargs) -> str:
        """生成MACD策略"""
        return f"[DEV] MACD策略功能开发中...\n\n[DATA] 股票: {symbol}\n[DATE] 期间: {start_date} 至 {end_date}\n[TIP] 敬请期待更多技术指标策略！"
    
    def _generate_rsi_strategy(self, data: pd.DataFrame, symbol: str, start_date: str, end_date: str, **kwargs) -> str:
        """生成RSI策略"""
        return f"[DEV] RSI策略功能开发中...\n\n[DATA] 股票: {symbol}\n[DATE] 期间: {start_date} 至 {end_date}\n[TIP] 敬请期待更多技术指标策略！"
    
    def _evaluate_strategy(self, metrics: Dict[str, Any]) -> str:
        """评价策略表现"""
        evaluation = "[TIP] 策略评价:\n"
        
        # 收益评价
        annual_return = metrics.get('annual_return', 0)
        if annual_return > 0.15:
            evaluation += "   [OK] 年化收益优秀，超过15%\n"
        elif annual_return > 0.08:
            evaluation += "   [OK] 年化收益良好，超过8%\n"
        elif annual_return > 0:
            evaluation += "   [WARNING] 年化收益一般，建议优化参数\n"
        else:
            evaluation += "   [ERROR] 策略产生亏损，需要重新设计\n"
        
        # 风险评价
        max_drawdown = abs(metrics.get('max_drawdown', 0))
        if max_drawdown < 0.05:
            evaluation += "   [OK] 风险控制优秀，最大回撤小于5%\n"
        elif max_drawdown < 0.1:
            evaluation += "   [WARNING] 风险控制中等，最大回撤在5-10%之间\n"
        elif max_drawdown < 0.2:
            evaluation += "   [WARNING] 风险较高，最大回撤在10-20%之间\n"
        else:
            evaluation += "   [ERROR] 风险很高，最大回撤超过20%\n"
        
        # 夏普比率评价
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        if sharpe_ratio > 1.5:
            evaluation += "   [OK] 夏普比率优秀，风险调整后收益很好\n"
        elif sharpe_ratio > 1.0:
            evaluation += "   [OK] 夏普比率良好，风险调整后收益不错\n"
        elif sharpe_ratio > 0.5:
            evaluation += "   [WARNING] 夏普比率一般，收益风险比有待提升\n"
        else:
            evaluation += "   [ERROR] 夏普比率偏低，策略效率不高\n"
        
        # 胜率评价
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.6:
            evaluation += "   [OK] 胜率优秀，超过60%\n"
        elif win_rate > 0.5:
            evaluation += "   [OK] 胜率良好，超过50%\n"
        else:
            evaluation += "   [WARNING] 胜率偏低，建议结合其他指标\n"
        
        return evaluation 