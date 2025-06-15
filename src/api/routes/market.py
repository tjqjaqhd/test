
"""
📈 시장 데이터 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
import sys
import os

# 서비스 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.services.exchange_service import exchange_service

router = APIRouter(prefix="/api/v1/market", tags=["market"])

@router.get("/price/{symbol}")
async def get_current_price(symbol: str, exchange: str = "upbit"):
    """현재 시세 조회"""
    try:
        price = await exchange_service.get_current_price(symbol, exchange)
        if price is None:
            raise HTTPException(status_code=404, detail="시세 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "price": price,
            "exchange": exchange,
            "timestamp": exchange_service.exchanges[exchange].milliseconds()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시세 조회 오류: {str(e)}")

@router.get("/stats/{symbol}")
async def get_24h_stats(symbol: str, exchange: str = "upbit"):
    """24시간 통계 조회"""
    try:
        stats = await exchange_service.get_24h_stats(symbol, exchange)
        if stats is None:
            raise HTTPException(status_code=404, detail="통계 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            **stats,
            "timestamp": exchange_service.exchanges[exchange].milliseconds()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@router.get("/ohlcv/{symbol}")
async def get_ohlcv_data(symbol: str, timeframe: str = "1h", limit: int = 100, exchange: str = "upbit"):
    """OHLCV 캔들 데이터 조회"""
    try:
        df = await exchange_service.get_ohlcv_data(symbol, timeframe, limit=limit, exchange_name=exchange)
        if df is None:
            raise HTTPException(status_code=404, detail="OHLCV 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OHLCV 조회 오류: {str(e)}")

@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, exchange: str = "upbit"):
    """호가 정보 조회"""
    try:
        orderbook = await exchange_service.get_orderbook(symbol, exchange)
        if orderbook is None:
            raise HTTPException(status_code=404, detail="호가 데이터를 찾을 수 없습니다")
        
        return {
            "symbol": symbol,
            "exchange": exchange,
            **orderbook
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"호가 조회 오류: {str(e)}")
