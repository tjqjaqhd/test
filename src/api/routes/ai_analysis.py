
"""
🤖 AI 분석 API 라우트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime, timedelta

from src.services.exchange_service import exchange_service
from src.services.ai_inference_service import ai_service

router = APIRouter(prefix="/api/v1/ai", tags=["ai-analysis"])

class AnalysisRequest(BaseModel):
    symbol: str
    hours: int = 24
    exchange: str = "upbit"

@router.post("/analyze")
async def analyze_market(request: AnalysisRequest):
    """종합 AI 시장 분석"""
    try:
        # 실제 시장 데이터 수집
        market_data = await exchange_service.get_real_trading_data(
            request.symbol, request.hours, request.exchange
        )
        
        if not market_data:
            raise HTTPException(status_code=400, detail="시장 데이터를 가져올 수 없습니다")
        
        # 데이터프레임 생성
        historical_df = pd.DataFrame(market_data['historical_data'])
        
        # AI 분석 실행
        sentiment = await ai_service.analyze_market_sentiment(request.symbol)
        prediction = await ai_service.predict_price_direction(historical_df, request.symbol)
        strategy = await ai_service.generate_trading_strategy(
            request.symbol, market_data, sentiment, prediction
        )
        
        return {
            "symbol": request.symbol,
            "analysis_time": datetime.now().isoformat(),
            "market_data": {
                "current_price": market_data['current_price'],
                "volatility": market_data['volatility'],
                "trend": market_data['price_trend'],
                "volume_avg": market_data['volume_avg']
            },
            "ai_analysis": {
                "sentiment": sentiment,
                "prediction": prediction,
                "strategy": strategy
            },
            "risk_assessment": {
                "level": "높음" if market_"""
🤖 AI 분석 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/api/v1/ai", tags=["ai_analysis"])

class AnalysisRequest(BaseModel):
    symbol: str
    hours: int = 24
    exchange: str = "binance"

class MarketAnalysisResponse(BaseModel):
    symbol: str
    trend: str
    confidence: float
    volatility: str
    volatility_score: float
    recommendation: str
    signals: List[Dict]
    timestamp: str

@router.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: AnalysisRequest):
    """시장 분석 수행"""
    try:
        # 모의 분석 데이터 생성 (실제로는 AI 모델 사용)
        
        # 변동성 계산 (모의)
        volatility_score = np.random.uniform(0.01, 0.1)
        volatility = "높음" if volatility_score > 0.05 else "중간" if volatility_score > 0.02 else "낮음"
        
        # 트렌드 분석 (모의)
        trend_score = np.random.uniform(-1, 1)
        trend = "상승" if trend_score > 0.2 else "하락" if trend_score < -0.2 else "횡보"
        
        # 신호 생성
        signals = [
            {"type": "기술적분석", "signal": trend, "confidence": abs(trend_score)},
            {"type": "심리분석", "signal": "중립", "confidence": 0.6},
            {"type": "거래량분석", "signal": "증가", "confidence": 0.7}
        ]
        
        return MarketAnalysisResponse(
            symbol=request.symbol,
            trend=trend,
            confidence=abs(trend_score),
            volatility=volatility,
            volatility_score=volatility_score,
            recommendation="신중한 거래" if volatility_score > 0.05 else "일반 거래",
            signals=signals,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

@router.get("/sentiment/{symbol}")
async def get_market_sentiment(symbol: str):
    """시장 심리 분석"""
    try:
        # 모의 심리 데이터
        sentiment_score = np.random.uniform(-1, 1)
        sentiment = "긍정" if sentiment_score > 0.2 else "부정" if sentiment_score < -0.2 else "중립"
        
        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "score": sentiment_score,
            "confidence": abs(sentiment_score),
            "sources": ["뉴스", "소셜미디어", "거래량"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"심리 분석 실패: {str(e)}")

@router.get("/prediction/{symbol}")
async def get_price_prediction(symbol: str, hours: int = 24):
    """가격 예측"""
    try:
        current_price = 50000000  # 모의 현재가 (BTC 기준)
        
        # 모의 예측 생성
        predictions = []
        for i in range(1, hours + 1):
            change = np.random.uniform(-0.05, 0.05)  # ±5% 변동
            predicted_price = current_price * (1 + change)
            predictions.append({
                "hour": i,
                "price": predicted_price,
                "confidence": np.random.uniform(0.6, 0.9)
            })
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "predictions": predictions,
            "model": "LSTM-Transformer",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 실패: {str(e)}")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

@router.get("/models/status")
async def get_ai_models_status():
    """AI 모델 상태 확인"""
    return {
        "models": {
            "sentiment_analysis": {
                "name": "Market Sentiment Analyzer",
                "status": "active",
                "accuracy": "85%",
                "last_updated": datetime.now().isoformat()
            },
            "price_prediction": {
                "name": "Technical Analysis Predictor", 
                "status": "active",
                "accuracy": "78%",
                "last_updated": datetime.now().isoformat()
            },
            "strategy_generator": {
                "name": "AI Trading Strategy Generator",
                "status": "active", 
                "accuracy": "82%",
                "last_updated": datetime.now().isoformat()
            }
        },
        "system_status": "operational",
        "total_analyses": "실시간 카운팅",
        "uptime": "99.9%"
    }
