
"""
💱 거래소 연동 서비스
실제 거래소 API를 통한 데이터 수집 및 거래 기능
"""

import ccxt
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

from src.core.config import get_settings
from src.core.logging_config import get_logger
from src.core.exceptions import ExchangeConnectionError, DataNotFoundError

logger = get_logger(__name__)

class ExchangeService:
    """거래소 통합 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.exchanges = {}
        self.price_cache = {}
        self.cache_timeout = 10  # 10초 캐시
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """거래소 초기화"""
        try:
            if self.settings.simulation_mode:
                # 시뮬레이션 모드: API 키 없이 초기화
                logger.info("🎯 시뮬레이션 모드로 거래소 초기화")
                self.exchanges['upbit'] = ccxt.upbit({
                    'enableRateLimit': True,
                })
                self.exchanges['binance'] = ccxt.binance({
                    'enableRateLimit': True,
                })
            else:
                # 실제 거래 모드: API 키 사용
                self.exchanges['upbit'] = ccxt.upbit({
                    'apiKey': self.settings.upbit_access_key,
                    'secret': self.settings.upbit_secret_key,
                    'enableRateLimit': True,
                })
                
                # Binance는 sandbox 모드 지원
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': self.settings.binance_api_key,
                    'secret': self.settings.binance_secret_key,
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            
            logger.info("✅ 거래소 연결 초기화 완료")
            
        except Exception as e:
            logger.error(f"거래소 초기화 오류: {e}")
            # 기본 설정으로 계속 진행
            self.exchanges['upbit'] = ccxt.upbit({'enableRateLimit': True})
            self.exchanges['binance'] = ccxt.binance({'enableRateLimit': True})
            logger.info("⚠️ 기본 설정으로 거래소 초기화됨")
    
    async def get_current_price(self, symbol: str, exchange: str = 'upbit') -> Optional[float]:
        """현재 가격 조회 (캐시 포함)"""
        cache_key = f"{exchange}_{symbol}"
        current_time = time.time()
        
        # 캐시 확인
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_timeout:
                return cached_data['price']
        
        try:
            if exchange not in self.exchanges:
                raise ExchangeConnectionError(f"지원하지 않는 거래소: {exchange}")
            
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, self.exchanges[exchange].fetch_ticker, symbol
            )
            
            price = ticker['last'] if ticker and 'last' in ticker else None
            
            # 캐시 업데이트
            if price:
                self.price_cache[cache_key] = {
                    'price': price,
                    'timestamp': current_time
                }
            
            return price
            
        except Exception as e:
            logger.error(f"가격 조회 오류 ({exchange}, {symbol}): {e}")
            # 시뮬레이션용 더미 데이터
            if self.settings.simulation_mode:
                import random
                base_prices = {
                    'BTC/KRW': 80000000,
                    'ETH/KRW': 4000000,
                    'XRP/KRW': 1500,
                    'ADA/KRW': 800
                }
                base_price = base_prices.get(symbol, 100000)
                simulated_price = base_price * (1 + random.uniform(-0.05, 0.05))
                
                # 캐시에 저장
                self.price_cache[cache_key] = {
                    'price': simulated_price,
                    'timestamp': current_time
                }
                return simulated_price
            return None
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str = '1d', limit: int = 100, exchange: str = 'upbit') -> List[Dict]:
        """OHLCV 데이터 조회"""
        try:
            if exchange not in self.exchanges:
                raise ExchangeConnectionError(f"지원하지 않는 거래소: {exchange}")
            
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, self.exchanges[exchange].fetch_ohlcv, symbol, timeframe, None, limit
            )
            
            if not ohlcv:
                raise DataNotFoundError(f"OHLCV 데이터가 없습니다: {symbol}")
            
            # 데이터 포맷 변환
            formatted_data = []
            for candle in ohlcv:
                formatted_data.append({
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0] / 1000).isoformat(),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"OHLCV 조회 오류 ({exchange}, {symbol}): {e}")
            
            # 시뮬레이션용 더미 데이터 생성
            if self.settings.simulation_mode:
                return self._generate_dummy_ohlcv(symbol, limit)
            return []
    
    async def get_orderbook(self, symbol: str, exchange: str = 'upbit') -> Dict:
        """호가창 데이터 조회"""
        try:
            if exchange not in self.exchanges:
                raise ExchangeConnectionError(f"지원하지 않는 거래소: {exchange}")
            
            orderbook = await asyncio.get_event_loop().run_in_executor(
                None, self.exchanges[exchange].fetch_order_book, symbol
            )
            
            return {
                'bids': orderbook['bids'][:10],  # 상위 10개
                'asks': orderbook['asks'][:10],  # 상위 10개
                'timestamp': orderbook['timestamp'],
                'datetime': orderbook['datetime']
            }
            
        except Exception as e:
            logger.error(f"호가창 조회 오류 ({exchange}, {symbol}): {e}")
            
            # 시뮬레이션용 더미 데이터
            if self.settings.simulation_mode:
                current_price = await self.get_current_price(symbol, exchange)
                if current_price:
                    return self._generate_dummy_orderbook(current_price)
            return {}
    
    async def get_real_trading_data(self, symbol: str, hours: int = 24, exchange: str = 'upbit') -> Dict:
        """실제 거래 데이터 종합 조회"""
        try:
            # 현재 가격
            current_price = await self.get_current_price(symbol, exchange)
            
            # OHLCV 데이터 (시간별)
            historical_data = await self.get_ohlcv_data(symbol, '1h', hours, exchange)
            
            # 변동성 계산
            volatility = self._calculate_volatility(historical_data)
            
            # 가격 트렌드 분석
            price_trend = self._analyze_price_trend(historical_data)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'historical_data': historical_data,
                'volatility': volatility,
                'price_trend': price_trend,
                'data_points': len(historical_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"거래 데이터 조회 오류: {e}")
            return {}
    
    def _generate_dummy_ohlcv(self, symbol: str, limit: int) -> List[Dict]:
        """시뮬레이션용 더미 OHLCV 데이터 생성"""
        import random
        
        base_prices = {
            'BTC/KRW': 80000000,
            'ETH/KRW': 4000000,
            'XRP/KRW': 1500,
            'ADA/KRW': 800
        }
        
        base_price = base_prices.get(symbol, 100000)
        data = []
        current_time = datetime.now()
        
        for i in range(limit):
            timestamp = current_time - timedelta(hours=limit-i)
            
            # 랜덤한 가격 변동
            variation = random.uniform(-0.05, 0.05)
            open_price = base_price * (1 + variation)
            
            high_price = open_price * (1 + random.uniform(0, 0.03))
            low_price = open_price * (1 - random.uniform(0, 0.03))
            close_price = open_price * (1 + random.uniform(-0.02, 0.02))
            volume = random.uniform(100, 10000)
            
            data.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'datetime': timestamp.isoformat(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        return data
    
    def _generate_dummy_orderbook(self, current_price: float) -> Dict:
        """시뮬레이션용 더미 호가창 생성"""
        import random
        
        bids = []
        asks = []
        
        for i in range(10):
            bid_price = current_price * (1 - (i + 1) * 0.001)
            ask_price = current_price * (1 + (i + 1) * 0.001)
            
            bids.append([bid_price, random.uniform(0.1, 10.0)])
            asks.append([ask_price, random.uniform(0.1, 10.0)])
        
        return {
            'bids': bids,
            'asks': asks,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'datetime': datetime.now().isoformat()
        }
    
    def _calculate_volatility(self, historical_data: List[Dict]) -> float:
        """변동성 계산"""
        if len(historical_data) < 2:
            return 0.02  # 기본 변동성
        
        prices = [float(candle['close']) for candle in historical_data]
        returns = []
        
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        if not returns:
            return 0.02
        
        # 표준편차 계산
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        return min(max(volatility, 0.01), 0.1)  # 1% ~ 10% 범위로 제한
    
    def _analyze_price_trend(self, historical_data: List[Dict]) -> str:
        """가격 트렌드 분석"""
        if len(historical_data) < 5:
            return "중립"
        
        recent_prices = [float(candle['close']) for candle in historical_data[-5:]]
        
        # 단순 추세 분석
        if recent_prices[-1] > recent_prices[0] * 1.02:
            return "상승"
        elif recent_prices[-1] < recent_prices[0] * 0.98:
            return "하락"
        else:
            return "중립"

# 전역 서비스 인스턴스
exchange_service = ExchangeService()
