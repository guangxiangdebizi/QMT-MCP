"""
XTQuant客户端管理模块
负责与迅投量化客户端的连接和数据获取
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class XTQuantClient:
    """XTQuant客户端管理器"""
    
    def __init__(self):
        self._connected = False
        self._xt = None
        
    def connect(self) -> bool:
        """连接到XTQuant"""
        try:
            import xtquant.xtdata as xt
            self._xt = xt
            
            # 尝试连接
            result = xt.connect()
            logger.info(f"XTQuant连接结果类型: {type(result)}")
            
            # 测试连接是否真正可用
            if self._test_connection():
                self._connected = True
                logger.info("XTQuant连接成功")
                return True
            else:
                self._connected = False
                logger.warning("XTQuant连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"XTQuant连接失败: {e}")
            self._connected = False
            return False
    
    def _test_connection(self) -> bool:
        """测试连接是否可用"""
        try:
            # 尝试获取简单的股票列表来测试连接
            test_result = self._xt.get_stock_list_in_sector('沪深A股')
            if test_result is not None and len(test_result) > 0:
                logger.info(f"连接测试成功，获取到 {len(test_result)} 只股票")
                return True
            return False
        except Exception as e:
            logger.debug(f"连接测试失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def get_market_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票行情数据 - 修复数据结构处理"""
        if not self._connected:
            raise ConnectionError("XTQuant未连接，请先调用connect()方法")
        
        try:
            # 确保日期格式为YYYYMMDD（xtquant期望的格式）
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')
                
            # 确保日期不为空
            if not start_date or not end_date:
                logger.error(f"日期参数不能为空: start_date={start_date}, end_date={end_date}")
                return None
            
            logger.info(f"正在获取{symbol}从{start_date}到{end_date}的数据")
            
            # 获取日线数据
            data = self._xt.get_market_data(
                stock_list=[symbol],
                period='1d',
                start_time=start_date,  # 使用YYYYMMDD格式
                end_time=end_date,      # 使用YYYYMMDD格式
                fill_data=True
            )
            
            # 检查data是否为None或格式错误
            if data is None:
                logger.error(f"获取{symbol}数据返回None - 可能的原因：股票不存在、日期超出范围、网络连接问题")
                return None
            
            if not isinstance(data, dict):
                logger.error(f"获取{symbol}数据返回格式错误，期望dict，实际{type(data)}")
                logger.error(f"返回数据内容: {data}")
                return None
                
            logger.info(f"获取{symbol}数据成功，数据类型: {type(data)}, 数据大小: {len(data) if data else 0}")
            
            # xtquant返回的数据结构是 {field_name: DataFrame}
            # 检查是否有所需的基本字段
            required_fields = ['time', 'open', 'high', 'low', 'close', 'volume']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"获取{symbol}数据缺少必要字段: {missing_fields}")
                logger.error(f"实际可用字段: {list(data.keys())}")
                return None
            
            logger.info(f"数据字段检查通过，获取到字段: {list(data.keys())}")
            
            # 智能匹配股票代码
            time_df = data['time']
            available_symbols = list(time_df.index)
            matched_symbol = None
            
            # 尝试多种匹配方式
            if symbol in available_symbols:
                # 精确匹配
                matched_symbol = symbol
                logger.info(f"精确匹配到股票代码: {symbol}")
            else:
                # 尝试去掉市场后缀匹配（如 000001.SZ -> 000001）
                code_without_suffix = symbol.split('.')[0] if '.' in symbol else symbol
                for avail_symbol in available_symbols:
                    if avail_symbol == code_without_suffix:
                        matched_symbol = avail_symbol
                        logger.info(f"去后缀匹配成功: {symbol} -> {matched_symbol}")
                        break
                    elif avail_symbol.split('.')[0] == code_without_suffix:
                        matched_symbol = avail_symbol
                        logger.info(f"代码匹配成功: {symbol} -> {matched_symbol}")
                        break
            
            if matched_symbol is None:
                logger.error(f"股票代码 {symbol} 未找到匹配项。可用代码: {available_symbols[:10]}...")
                return None
            
            # 重构数据为标准格式 DataFrame
            try:
                dates = time_df.columns
                result_data = {
                    'time': [pd.to_datetime(str(date)) for date in dates],
                    'open': data['open'].loc[matched_symbol].values,
                    'high': data['high'].loc[matched_symbol].values,
                    'low': data['low'].loc[matched_symbol].values,
                    'close': data['close'].loc[matched_symbol].values,
                    'volume': data['volume'].loc[matched_symbol].values,
                }
                
                # 添加成交额（如果存在）
                if 'amount' in data:
                    result_data['amount'] = data['amount'].loc[matched_symbol].values
                
                # 添加前收盘价（如果存在）
                if 'preClose' in data:
                    result_data['preClose'] = data['preClose'].loc[matched_symbol].values
                
                # 创建DataFrame
                df = pd.DataFrame(result_data)
                df.set_index('time', inplace=True)
                
                if df.empty:
                    logger.warning(f"重构后的{symbol}数据为空 - 在指定日期范围内没有交易数据")
                    logger.info(f"建议检查：1) 股票是否在此期间停牌 2) 日期范围是否有效 3) 数据权限是否充足")
                    return None
                
                logger.info(f"成功获取{symbol}的{len(df)}条数据")
                return df
                
            except Exception as e:
                logger.error(f"重构{symbol}数据时出错: {e}")
                logger.error(f"matched_symbol: {matched_symbol}, 可用数据字段: {list(data.keys())}")
                logger.error(f"时间数据shape: {time_df.shape}, 收盘价数据shape: {data['close'].shape}")
                return None
                
        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {e}")
            return None
    
    def get_raw_market_data(self, symbols: list, start_date: str, end_date: str) -> Optional[Dict]:
        """获取原始格式的多股票数据"""
        if not self._connected:
            raise ConnectionError("XTQuant未连接")
        
        try:
            # 确保日期格式为YYYYMMDD
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')
                
            # 确保日期不为空
            if not start_date or not end_date:
                logger.error(f"日期参数不能为空: start_date={start_date}, end_date={end_date}")
                return None
            
            logger.info(f"正在获取{len(symbols)}只股票从{start_date}到{end_date}的原始数据")
            
            data = self._xt.get_market_data(
                stock_list=symbols,
                period='1d',
                start_time=start_date,
                end_time=end_date,
                fill_data=True
            )
            
            return data
            
        except Exception as e:
            logger.error(f"获取多股票原始数据失败: {e}")
            return None
    
    def get_stock_list(self, sector: str = '沪深A股') -> Optional[list]:
        """获取股票列表"""
        if not self._connected:
            raise ConnectionError("XTQuant未连接")
        
        try:
            return self._xt.get_stock_list_in_sector(sector)
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return None
    
    def disconnect(self):
        """断开连接"""
        if self._xt:
            try:
                self._xt.disconnect()
                logger.info("XTQuant连接已断开")
            except:
                pass
        self._connected = False

# 全局客户端实例
xt_client = XTQuantClient() 