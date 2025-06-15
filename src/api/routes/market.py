
"""
📊 마켓 데이터 API 라우터
실제 거래소 데이터 제공
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import asyncio
from datetime import datetime, timedelta

from src.services.exchange_service import exchange_service
from src.core.exceptions import ExchangeConnectionError, DataNotFoundError

router = APIRouter(prefix="/api/v1/market", tags=["market"])

@router.get("/price/{symbol}")
async def get_current_price(
    symbol: str,
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """현재 시세 조회"""
    try:
        price = await exchange_service.get_current_price(symbol, exchange)
        if price is None:
            raise HTTPException(status_code=404, detail="시세 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{symbol}")
async def get_24h_stats(
    symbol: str,
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """24시간 통계 조회"""
    try:
        stats = await exchange_service.get_24h_stats(symbol, exchange)
        if stats is None:
            raise HTTPException(status_code=404, detail="통계 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ohlcv/{symbol}")
async def get_ohlcv_data(
    symbol: str,
    timeframe: str = Query(default="1h", description="시간 프레임"),
    limit: int = Query(default=100, description="데이터 개수"),
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """OHLCV 캔들 데이터 조회"""
    try:
        since = datetime.now() - timedelta(hours=limit)
        df = await exchange_service.get_ohlcv_data(symbol, timeframe, since, limit, exchange)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="OHLCV 데이터를 찾을 수 없습니다")
        
        # DataFrame을 JSON으로 변환
        data = []
        for _, row in df.iterrows():
            data.append({
                "timestamp": int(row['timestamp']),
                "datetime": row['datetime'].isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "timeframe": timeframe,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orderbook/{symbol}")
async def get_orderbook(
    symbol: str,
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """호가 정보 조회"""
    try:
        orderbook = await exchange_service.get_orderbook(symbol, exchange)
        if orderbook is None:
            raise HTTPException(status_code=404, detail="호가 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            "orderbook": orderbook,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_available_symbols(
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """사용 가능한 거래쌍 목록"""
    try:
        # 주요 거래쌍 하드코딩 (실제로는 거래소 API에서 가져와야 함)
        symbols = {
            "upbit": [
                "BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW",
                "DOT/KRW", "LINK/KRW", "LTC/KRW", "BCH/KRW",
                "EOS/KRW", "TRX/KRW", "ATOM/KRW", "NEO/KRW"
            ],
            "binance": [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT",
                "ADA/USDT", "DOT/USDT", "LINK/USDT", "LTC/USDT"
            ]
        }
        
        return {
            "exchange": exchange,
            "symbols": symbols.get(exchange, []),
            "count": len(symbols.get(exchange, []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/multi-price")
async def get_multi_price(
    symbols: str = Query(description="쉼표로 구분된 심볼 목록"),
    exchange: str = Query(default="upbit", description="거래소 선택")
):
    """여러 심볼 동시 시세 조회"""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        results = {}
        
        tasks = []
        for symbol in symbol_list:
            tasks.append(exchange_service.get_current_price(symbol, exchange))
        
        prices = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, price in zip(symbol_list, prices):
            if isinstance(price, Exception):
                results[symbol] = {"error": str(price)}
            else:
                results[symbol] = {"price": price}
        
        return {
            "exchange": exchange,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
📊 시장 데이터 관련 API 라우트
실시간 가격, 차트 데이터, 시장 분석 제공
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

from src.services.exchange_service import exchange_service
from src.core.logging_config import get_logger

router = APIRouter(prefix="/api/v1/market", tags=["market"])
logger = get_logger(__name__)

@router.get("/price/{symbol}")
async def get_current_price(symbol: str):
    """현재 가격 조회"""
    try:
        price = await exchange_service.get_current_price(symbol)
        if not price:
            raise HTTPException(status_code=404, detail="가격 정보를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"가격 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ohlcv/{symbol}")
async def get_ohlcv_data(symbol: str, timeframe: str = "1d", limit: int = 100):
    """OHLCV 차트 데이터 조회"""
    try:
        data = await exchange_service.get_ohlcv_data(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data,
            "count": len(data) if data else 0
        }
    except Exception as e:
        logger.error(f"OHLCV 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str):
    """호가창 데이터 조회"""
    try:
        orderbook = await exchange_service.get_orderbook(symbol)
        return {
            "symbol": symbol,
            "orderbook": orderbook,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"호가창 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_supported_symbols():
    """지원하는 거래쌍 목록"""
    return {
        "symbols": [
            "BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW",
            "DOT/KRW", "LINK/KRW", "LTC/KRW", "BCH/KRW"
        ],
        "exchanges": ["upbit", "binance"]
    }

@router.get("/market-summary")
async def get_market_summary():
    """시장 전체 요약"""
    try:
        symbols = ["BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW"]
        summary = []
        
        for symbol in symbols:
            try:
                price = await exchange_service.get_current_price(symbol)
                if price:
                    summary.append({
                        "symbol": symbol,
                        "price": price,
                        "change_24h": 0.0  # 실제 구현 시 24시간 변화율 계산
                    })
            except:
                continue
        
        return {
            "market_summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"시장 요약 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
