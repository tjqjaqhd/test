
"""
🏪 거래소 데이터 서비스
CCXT를 사용한 실제 거래소 데이터 연동
"""

import ccxt
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
import time

class ExchangeService:
    """거래소 데이터 서비스"""
    
    def __init__(self):
        self.exchanges = {
            'upbit': ccxt.upbit({
                'sandbox': False,
                'rateLimit': 1000,
                'enableRateLimit': True,
            }),
            'binance': ccxt.binance({
                'sandbox': False,
                'rateLimit': 1000,
                'enableRateLimit': True,
            })
        }
        self._cache = {}
        self._cache_ttl = 60  # 1분 캐시
    
    async def get_current_price(self, symbol: str, exchange_name: str = 'upbit') -> Optional[float]:
        """현재 시세 조회 (캐시 적용)"""
        cache_key = f"price_{exchange_name}_{symbol}"
        
        # 캐시 확인
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_data
        
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
            
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            # 캐시 저장
            self._cache[cache_key] = (price, time.time())
            return price
        except Exception as e:
            logger.error(f"시세 조회 오류 ({exchange_name}, {symbol}): {e}")
            return None
    
    async def get_real_trading_data(self, symbol: str, hours: int = 24, exchange_name: str = 'upbit') -> Dict:
        """실제 거래 데이터 기반 시뮬레이션 데이터 생성"""
        try:
            # 실제 OHLCV 데이터 가져오기
            df = await self.get_ohlcv_data(symbol, '1h', 
                                         datetime.now() - timedelta(hours=hours), 
                                         hours, exchange_name)
            
            if df is None or df.empty:
                return None
            
            # 실제 가격 변동성 분석
            price_changes = df['close'].pct_change().dropna()
            volatility = price_changes.std()
            
            return {
                'current_price': float(df['close'].iloc[-1]),
                'volatility': float(volatility),
                'volume_avg': float(df['volume'].mean()),
                'price_trend': 'up' if df['close'].iloc[-1] > df['close'].iloc[0] else 'down',
                'historical_data': df.to_dict('records')
            }
        except Exception as e:
            logger.error(f"실제 거래 데이터 조회 오류: {e}")
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
