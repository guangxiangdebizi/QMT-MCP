"""
双均线策略模块
实现双均线交叉策略的计算和分析
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MAStrategy:
    """双均线策略实现"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        self.short_period = short_period
        self.long_period = long_period
        
    def calculate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算交易信号"""
        if data is None or data.empty:
            raise ValueError("数据不能为空")
        
        data = data.copy()
        
        # 计算均线
        data['ma_short'] = data['close'].rolling(window=self.short_period).mean()
        data['ma_long'] = data['close'].rolling(window=self.long_period).mean()
        
        # 生成交易信号
        data['signal'] = 0
        data.loc[data['ma_short'] > data['ma_long'], 'signal'] = 1  # 买入信号
        data.loc[data['ma_short'] < data['ma_long'], 'signal'] = -1  # 卖出信号
        
        # 标记信号变化点
        data['signal_change'] = data['signal'].diff()
        data['buy_signal'] = (data['signal_change'] == 2) | (data['signal_change'] == 1)
        data['sell_signal'] = (data['signal_change'] == -2) | (data['signal_change'] == -1)
        
        return data
    
    def calculate_returns(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算收益率"""
        data = data.copy()
        
        # 计算基础收益率
        data['returns'] = data['close'].pct_change()
        
        # 计算策略收益率（信号滞后一期）
        data['strategy_returns'] = data['signal'].shift(1) * data['returns']
        
        # 计算累计收益
        data['cumulative_returns'] = (1 + data['returns'].fillna(0)).cumprod()
        data['cumulative_strategy_returns'] = (1 + data['strategy_returns'].fillna(0)).cumprod()
        
        return data
    
    def calculate_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """计算策略绩效指标"""
        try:
            # 确保数据包含必要的列
            if 'strategy_returns' not in data.columns:
                data = self.calculate_returns(data)
            
            strategy_returns = data['strategy_returns'].dropna()
            cumulative_returns = data['cumulative_strategy_returns'].dropna()
            
            if len(strategy_returns) == 0:
                return {'error': '没有有效的策略收益数据'}
            
            # 总收益率
            final_return = cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0
            
            # 年化收益率
            trading_days = len(strategy_returns)
            annual_return = (1 + final_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
            
            # 最大回撤
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min()
            
            # 波动率
            volatility = strategy_returns.std() * np.sqrt(252) if len(strategy_returns) > 1 else 0
            
            # 夏普比率 (假设无风险利率为3%)
            risk_free_rate = 0.03
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # 交易统计
            signals = data['signal'].diff()
            total_trades = int((signals != 0).sum())
            
            # 胜率
            winning_trades = (strategy_returns > 0).sum()
            total_trade_periods = (strategy_returns != 0).sum()
            win_rate = winning_trades / total_trade_periods if total_trade_periods > 0 else 0
            
            # 平均收益
            avg_return = strategy_returns.mean()
            avg_win = strategy_returns[strategy_returns > 0].mean() if winning_trades > 0 else 0
            avg_loss = strategy_returns[strategy_returns < 0].mean() if (strategy_returns < 0).sum() > 0 else 0
            
            return {
                'final_return': float(final_return),
                'annual_return': float(annual_return),
                'max_drawdown': float(max_drawdown),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'total_trades': total_trades,
                'win_rate': float(win_rate),
                'avg_return': float(avg_return),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'trading_days': trading_days
            }
            
        except Exception as e:
            logger.error(f"计算策略指标失败: {e}")
            return {'error': str(e)}
    
    def backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """执行完整回测"""
        try:
            # 计算信号
            data_with_signals = self.calculate_signals(data)
            
            # 计算收益
            data_with_returns = self.calculate_returns(data_with_signals)
            
            # 计算指标
            metrics = self.calculate_metrics(data_with_returns)
            
            # 添加策略参数信息
            metrics['short_period'] = self.short_period
            metrics['long_period'] = self.long_period
            metrics['strategy_type'] = 'ma_cross'
            
            return {
                'metrics': metrics,
                'data': data_with_returns,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            } 