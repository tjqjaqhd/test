
"""
🏪 거래소 데이터 서비스
CCXT를 사용한 실제 거래소 데이터 연동
"""

import ccxt
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

class ExchangeService:
    """거래소 데이터 서비스"""
    
    def __init__(self):
        self.exchanges = {
            'upbit': ccxt.upbit({
                'sandbox': False,
                'rateLimit': 1000,
            }),
            'binance': ccxt.binance({
                'sandbox': False,
                'rateLimit': 1000,
            })
        }
    
    async def get_current_price(self, symbol: str, exchange_name: str = 'upbit') -> Optional[float]:
        """현재 시세 조회"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
            
            ticker = exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"시세 조회 오류 ({exchange_name}, {symbol}): {e}")
            return None
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', 
                           since: Optional[datetime] = None, limit: int = 100,
                           exchange_name: str = 'upbit') -> Optional[pd.DataFrame]:
        """OHLCV 데이터 조회"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
            
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)
            
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since_timestamp, limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"OHLCV 데이터 조회 오류 ({exchange_name}, {symbol}): {e}")
            return None
    
    async def get_orderbook(self, symbol: str, exchange_name: str = 'upbit') -> Optional[Dict]:
        """호가 정보 조회"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
            
            orderbook = exchange.fetch_order_book(symbol)
            return orderbook
        except Exception as e:
            logger.error(f"호가 정보 조회 오류 ({exchange_name}, {symbol}): {e}")
            return None
    
    async def get_24h_stats(self, symbol: str, exchange_name: str = 'upbit') -> Optional[Dict]:
        """24시간 통계 조회"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
            
            ticker = exchange.fetch_ticker(symbol)
            return {
                'price': ticker['last'],
                'change': ticker['change'],
                'percentage': ticker['percentage'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'quoteVolume': ticker['quoteVolume']
            }
        except Exception as e:
            logger.error(f"24시간 통계 조회 오류 ({exchange_name}, {symbol}): {e}")
            return None

# 전역 서비스 인스턴스
exchange_service = ExchangeService()
