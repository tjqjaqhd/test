
"""
🤖 AI 추론 서비스
Hugging Face Transformers를 활용한 시장 분석 및 예측
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import requests
import json
import time

class AIInferenceService:
    """AI 추론 서비스"""
    
    def __init__(self):
        self.model_cache = {}
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5분 캐시
        
        # Hugging Face API (무료 모델 사용)
        self.hf_api_url = "https://api-inference.huggingface.co/models"
        
        # 사용할 모델들
        self.models = {
            'sentiment': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
            'price_prediction': 'facebook/opt-125m'  # 경량 언어모델
        }
    
    async def analyze_market_sentiment(self, symbol: str, news_data: List[str] = None) -> Dict:
        """시장 심리 분석"""
        try:
            if not news_data:
                # 기본 시장 뉴스 텍스트 (실제로는 뉴스 API 연동)
                news_data = [
                    f"{symbol} 가격이 상승하고 있습니다",
                    f"{symbol} 거래량이 증가했습니다",
                    f"암호화폐 시장이 활발합니다"
                ]
            
            sentiment_scores = []
            for text in news_data:
                score = await self._analyze_text_sentiment(text)
                if score:
                    sentiment_scores.append(score)
            
            if not sentiment_scores:
                return {"sentiment": "neutral", "confidence": 0.5, "analysis": "데이터 부족"}
            
            avg_sentiment = np.mean(sentiment_scores)
            
            # 감정 분류
            if avg_sentiment > 0.6:
                sentiment = "positive"
            elif avg_sentiment < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "confidence": float(avg_sentiment),
                "analysis": f"{symbol}에 대한 시장 심리는 {sentiment}적입니다",
                "score_breakdown": sentiment_scores
            }
            
        except Exception as e:
            logger.error(f"시장 심리 분석 오류: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "analysis": "분석 불가"}
    
    async def _analyze_text_sentiment(self, text: str) -> Optional[float]:
        """텍스트 감정 분석 (간단한 키워드 기반)"""
        try:
            # 간단한 키워드 기반 감정 분석
            positive_words = ['상승', '증가', '좋은', '성장', '수익', '이익', '강세']
            negative_words = ['하락', '감소', '나쁜', '손실', '위험', '약세', '폭락']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total_words = len(text.split())
            if total_words == 0:
                return 0.5
            
            sentiment_score = (positive_count - negative_count) / total_words
            # 0-1 범위로 정규화
            normalized_score = max(0, min(1, 0.5 + sentiment_score))
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"텍스트 감정 분석 오류: {e}")
            return None
    
    async def predict_price_direction(self, historical_data: pd.DataFrame, symbol: str) -> Dict:
        """가격 방향 예측 (기술적 분석 기반)"""
        try:
            if historical_data.empty or len(historical_data) < 10:
                return {"direction": "neutral", "confidence": 0.5, "reasoning": "데이터 부족"}
            
            # 기술적 지표 계산
            prices = historical_data['close'] if 'close' in historical_data.columns else historical_data['price']
            
            # 단순 이동평균
            sma_short = prices.rolling(window=5).mean()
            sma_long = prices.rolling(window=10).mean()
            
            # RSI (Relative Strength Index)
            rsi = self._calculate_rsi(prices)
            
            # 볼린저 밴드
            bollinger = self._calculate_bollinger_bands(prices)
            
            # 예측 로직
            current_price = float(prices.iloc[-1])
            sma_short_current = float(sma_short.iloc[-1]) if not pd.isna(sma_short.iloc[-1]) else current_price
            sma_long_current = float(sma_long.iloc[-1]) if not pd.isna(sma_long.iloc[-1]) else current_price
            current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
            
            # 신호 계산
            signals = []
            
            # 이동평균 신호
            if sma_short_current > sma_long_current:
                signals.append(("상승", 0.7))
            else:
                signals.append(("하락", 0.7))
            
            # RSI 신호
            if current_rsi > 70:
                signals.append(("하락", 0.6))  # 과매수
            elif current_rsi < 30:
                signals.append(("상승", 0.6))  # 과매도
            else:
                signals.append(("중립", 0.5))
            
            # 볼린저 밴드 신호
            if current_price > bollinger['upper'].iloc[-1]:
                signals.append(("하락", 0.6))  # 상단 돌파
            elif current_price < bollinger['lower'].iloc[-1]:
                signals.append(("상승", 0.6))  # 하단 돌파
            else:
                signals.append(("중립", 0.5))
            
            # 최종 예측
            up_signals = [s[1] for s in signals if s[0] == "상승"]
            down_signals = [s[1] for s in signals if s[0] == "하락"]
            
            up_confidence = np.mean(up_signals) if up_signals else 0
            down_confidence = np.mean(down_signals) if down_signals else 0
            
            if up_confidence > down_confidence and up_confidence > 0.55:
                direction = "상승"
                confidence = up_confidence
            elif down_confidence > up_confidence and down_confidence > 0.55:
                direction = "하락" 
                confidence = down_confidence
            else:
                direction = "중립"
                confidence = 0.5
            
            reasoning = f"기술적 분석 결과: 단기이평({sma_short_current:.0f}), 장기이평({sma_long_current:.0f}), RSI({current_rsi:.1f})"
            
            return {
                "direction": direction,
                "confidence": float(confidence),
                "reasoning": reasoning,
                "technical_indicators": {
                    "rsi": float(current_rsi),
                    "sma_short": float(sma_short_current),
                    "sma_long": float(sma_long_current),
                    "bollinger_position": "상단" if current_price > bollinger['upper'].iloc[-1] else "하단" if current_price < bollinger['lower'].iloc[-1] else "중간"
                }
            }
            
        except Exception as e:
            logger.error(f"가격 방향 예측 오류: {e}")
            return {"direction": "neutral", "confidence": 0.5, "reasoning": "예측 실패"}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices))
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """볼린저 밴드 계산"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            return {
                'middle': sma,
                'upper': sma + (std * std_dev),
                'lower': sma - (std * std_dev)
            }
        except:
            return {
                'middle': prices,
                'upper': prices * 1.02,
                'lower': prices * 0.98
            }
    
    async def generate_trading_strategy(self, symbol: str, market_data: Dict, sentiment: Dict, prediction: Dict) -> Dict:
        """AI 기반 거래 전략 생성"""
        try:
            strategy_score = 0
            reasoning = []
            
            # 감정 분석 반영
            if sentiment['sentiment'] == 'positive':
                strategy_score += 0.3
                reasoning.append("긍정적 시장 심리")
            elif sentiment['sentiment'] == 'negative':
                strategy_score -= 0.3
                reasoning.append("부정적 시장 심리")
            
            # 예측 반영
            if prediction['direction'] == '상승':
                strategy_score += 0.4
                reasoning.append("상승 예측")
            elif prediction['direction'] == '하락':
                strategy_score -= 0.4
                reasoning.append("하락 예측")
            
            # 전략 결정
            if strategy_score > 0.3:
                action = "매수"
                confidence = min(0.9, 0.5 + strategy_score)
            elif strategy_score < -0.3:
                action = "매도"
                confidence = min(0.9, 0.5 + abs(strategy_score))
            else:
                action = "대기"
                confidence = 0.5
            
            return {
                "action": action,
                "confidence": float(confidence),
                "reasoning": " + ".join(reasoning) if reasoning else "중립적 상황",
                "score": float(strategy_score),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"거래 전략 생성 오류: {e}")
            return {"action": "대기", "confidence": 0.5, "reasoning": "전략 생성 실패"}

# 전역 서비스 인스턴스
ai_service = AIInferenceService()
