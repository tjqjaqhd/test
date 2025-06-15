
"""
🤖 AI 분석 관련 API 라우트
시장 분석, 가격 예측, 전략 추천 제공
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.services.ai_inference_service import ai_service
from src.services.exchange_service import exchange_service
from src.core.logging_config import get_logger

router = APIRouter(prefix="/api/v1/ai", tags=["ai_analysis"])
logger = get_logger(__name__)

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    days: int = 30

@router.post("/sentiment/{symbol}")
async def analyze_market_sentiment(symbol: str):
    """시장 심리 분석"""
    try:
        sentiment = await ai_service.analyze_market_sentiment(symbol)
        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"심리 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-price")
async def predict_price_direction(request: AnalysisRequest):
    """가격 방향 예측"""
    try:
        # 과거 데이터 조회
        ohlcv_data = await exchange_service.get_ohlcv_data(
            request.symbol, request.timeframe, request.days
        )
        
        if not ohlcv_data:
            raise HTTPException(status_code=400, detail="시장 데이터를 가져올 수 없습니다")
        
        df = pd.DataFrame(ohlcv_data)
        prediction = await ai_service.predict_price_direction(df, request.symbol)
        
        return {
            "symbol": request.symbol,
            "prediction": prediction,
            "timeframe": request.timeframe,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"가격 예측 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy-recommendation")
async def recommend_trading_strategy(request: AnalysisRequest):
    """거래 전략 추천"""
    try:
        # 시장 데이터 수집
        market_data = await exchange_service.get_real_trading_data(
            request.symbol, request.days * 24
        )
        
        if not market_data:
            raise HTTPException(status_code=400, detail="시장 데이터를 가져올 수 없습니다")
        
        # AI 분석
        sentiment = await ai_service.analyze_market_sentiment(request.symbol)
        df = pd.DataFrame(market_data['historical_data'])
        prediction = await ai_service.predict_price_direction(df, request.symbol)
        
        # 전략 생성
        strategy = await ai_service.generate_trading_strategy(
            request.symbol, market_data, sentiment, prediction
        )
        
        return {
            "symbol": request.symbol,
            "strategy": strategy,
            "market_analysis": {
                "sentiment": sentiment,
                "prediction": prediction
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"전략 추천 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/technical-indicators/{symbol}")
async def get_technical_indicators(symbol: str, timeframe: str = "1d", limit: int = 100):
    """기술적 지표 분석"""
    try:
        ohlcv_data = await exchange_service.get_ohlcv_data(symbol, timeframe, limit)
        
        if not ohlcv_data:
            raise HTTPException(status_code=400, detail="시장 데이터를 가져올 수 없습니다")
        
        indicators = await ai_service.calculate_technical_indicators(ohlcv_data)
        
        return {
            "symbol": symbol,
            "indicators": indicators,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"기술적 지표 계산 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-assessment/{symbol}")
async def assess_trading_risk(symbol: str, investment_amount: float = 1000000):
    """리스크 평가"""
    try:
        risk_assessment = await ai_service.assess_trading_risk(symbol, investment_amount)
        
        return {
            "symbol": symbol,
            "investment_amount": investment_amount,
            "risk_assessment": risk_assessment,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"리스크 평가 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
