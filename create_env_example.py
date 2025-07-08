#!/usr/bin/env python3
# 临时脚本：创建.env.example文件

content = """# QuantMCP 环境配置示例
# 复制此文件为 .env 并根据你的环境修改相应配置

# 服务器配置
QUANTMCP_HOST=127.0.0.1
QUANTMCP_PORT=8000
QUANTMCP_TRANSPORT=sse

# XTQuant/QMT 配置
QMT_PATH=D:\\\\国金QMT交易端模拟\\\\userdata_mini
QMT_SESSION_ID=13579
QMT_ACCOUNT_ID=55012417

# QMT策略保存目录
QMT_STRATEGY_DIR=D:\\\\国金QMT交易端模拟\\\\mpython

# 交易风控配置
MAX_ORDER_VALUE=100000.0
MAX_POSITION_VALUE=500000.0
MIN_ORDER_QUANTITY=100
MARKET_ORDER_SPREAD=0.1

# 策略默认配置
DEFAULT_SYMBOL=000001.SZ
DEFAULT_START_DATE=20240101
DEFAULT_END_DATE=20241201
DEFAULT_SHORT_PERIOD=5
DEFAULT_LONG_PERIOD=20

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/quantmcp.log"""

with open('.env.example', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 创建 .env.example 文件成功')