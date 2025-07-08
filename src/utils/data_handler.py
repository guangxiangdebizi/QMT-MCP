"""
数据处理模块
负责数据的预处理、格式化和验证
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataHandler:
    """数据处理器"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """验证股票代码格式"""
        if not symbol:
            return False
        
        # 检查是否包含市场后缀
        if '.' not in symbol:
            return False
        
        code, market = symbol.split('.')
        
        # 检查市场代码
        if market not in ['SZ', 'SH']:
            return False
        
        # 检查股票代码长度
        if len(code) != 6:
            return False
        
        # 检查是否为数字
        if not code.isdigit():
            return False
        
        return True
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """验证日期格式 YYYYMMDD"""
        if not date_str or len(date_str) != 8:
            return False
        
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            # 简单的日期验证
            if year < 2000 or year > 2030:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_market_data(data: pd.DataFrame) -> bool:
        """验证市场数据格式"""
        if data is None or data.empty:
            return False
        
        # 检查必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"缺少必要的列: {col}")
                return False
        
        # 检查是否有有效数据
        if data['close'].isna().all():
            logger.error("所有收盘价都是NaN")
            return False
        
        return True
    
    @staticmethod
    def clean_market_data(data: pd.DataFrame) -> pd.DataFrame:
        """清洗市场数据"""
        if data is None or data.empty:
            return data
        
        # 移除价格为0或负数的记录
        data = data[(data['close'] > 0) & (data['open'] > 0) & 
                   (data['high'] > 0) & (data['low'] > 0)]
        
        # 移除异常的价格数据（high < low）
        data = data[data['high'] >= data['low']]
        
        # 移除成交量为负数的记录
        data = data[data['volume'] >= 0]
        
        # 按日期排序
        if 'time' in data.columns:
            data = data.sort_values('time')
        
        return data
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """格式化百分比"""
        if pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}%}"
    
    @staticmethod
    def format_number(value: float, decimals: int = 3) -> str:
        """格式化数字"""
        if pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}f}"
    
    @staticmethod
    def calculate_returns(data: pd.DataFrame) -> pd.DataFrame:
        """计算收益率"""
        if data is None or data.empty:
            return data
        
        data = data.copy()
        data['returns'] = data['close'].pct_change()
        data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
        
        return data
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
        """计算波动率"""
        return returns.rolling(window=window).std() * np.sqrt(252)
    
    @staticmethod
    def parse_date_range(date_range: str) -> tuple[str, str]:
        """解析日期范围"""
        if '-' in date_range:
            start_date, end_date = date_range.split('-')
            return start_date.strip(), end_date.strip()
        else:
            # 如果没有分隔符，返回默认范围
            return "20241101", "20241201" 