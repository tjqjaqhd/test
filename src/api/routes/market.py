"""
📊 시장 데이터 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import ccxt
import asyncio
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/market", tags=["market"])

# 지원 거래소 설정
EXCHANGES = {
    'binance': ccxt.binance(),
    'upbit': ccxt.upbit(),
    'bithumb': ccxt.bithumb()
}

@router.get("/exchanges")
async def get_supported_exchanges():
    """지원 거래소 목록"""
    return {
        "exchanges": list(EXCHANGES.keys()),
        "total_count": len(EXCHANGES)
    }

@router.get("/price/{symbol}")
async def get_current_price(symbol: str, exchange: str = "binance"):
    """현재 가격 조회"""
    try:
        if exchange not in EXCHANGES:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 거래소: {exchange}")

        exchange_client = EXCHANGES[exchange]

        # 심볼 형식 통일
        if exchange == "upbit":
            symbol = f"KRW-{symbol.split('/')[0]}" if '/' in symbol else f"KRW-{symbol}"

        ticker = exchange_client.fetch_ticker(symbol)

        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": ticker['last'],
            "change_24h": ticker['percentage'],
            "volume_24h": ticker['baseVolume'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 조회 실패: {str(e)}")

@router.get("/ohlcv/{symbol}")
async def get_ohlcv_data(symbol: str, timeframe: str = "1h", limit: int = 100, exchange: str = "binance"):
    """OHLCV 데이터 조회"""
    try:
        if exchange not in EXCHANGES:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 거래소: {exchange}")

        exchange_client = EXCHANGES[exchange]

        # 심볼 형식 통일
        if exchange == "upbit":
            symbol = f"KRW-{symbol.split('/')[0]}" if '/' in symbol else f"KRW-{symbol}"

        ohlcv = exchange_client.fetch_ohlcv(symbol, timeframe, limit=limit)

        data = []
        for candle in ohlcv:
            data.append({
                "timestamp": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5]
            })

        return {
            "symbol": symbol,
            "exchange": exchange,
            "timeframe": timeframe,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OHLCV 데이터 조회 실패: {str(e)}")

@router.get("/symbols/{exchange}")
async def get_exchange_symbols(exchange: str):
    """거래소별 거래 가능 심볼 목록"""
    try:
        if exchange not in EXCHANGES:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 거래소: {exchange}")

        exchange_client = EXCHANGES[exchange]
        markets = exchange_client.load_markets()

        symbols = []
        for symbol, market in markets.items():
            if market['active']:
                symbols.append({
                    "symbol": symbol,
                    "base": market['base'],
                    "quote": market['quote'],
                    "type": market['type']
                })

        return {
            "exchange": exchange,
            "symbols": symbols[:50],  # 처음 50개만 반환
            "total_count": len(symbols)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"심볼 목록 조회 실패: {str(e)}")

@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, exchange: str = "binance", limit: int = 20):
    """호가창 데이터 조회"""
    try:
        if exchange not in EXCHANGES:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 거래소: {exchange}")

        exchange_client = EXCHANGES[exchange]

        # 심볼 형식 통일
        if exchange == "upbit":
            symbol = f"KRW-{symbol.split('/')[0]}" if '/' in symbol else f"KRW-{symbol}"

        orderbook = exchange_client.fetch_order_book(symbol, limit)

        return {
            "symbol": symbol,
            "exchange": exchange,
            "bids": orderbook['bids'][:limit],
            "asks": orderbook['asks'][:limit],
            "timestamp": orderbook['timestamp']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"호가창 조회 실패: {str(e)}")