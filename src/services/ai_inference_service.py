
"""
🤖 AI 추론 서비스
머신러닝 기반 시장 분석, 가격 예측, 전략 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import ta

from src.core.logging_config import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)

class AIInferenceService:
    """AI 추론 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.models = {}
        self.scalers = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """AI 모델 초기화"""
        try:
            # 가격 예측 모델
            self.models['price_prediction'] = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            
            # 변동성 예측 모델
            self.models['volatility_prediction'] = RandomForestRegressor(
                n_estimators=50,
                random_state=42,
                max_depth=8
            )
            
            # 스케일러
            self.scalers['price'] = StandardScaler()
            self.scalers['features'] = StandardScaler()
            
            logger.info("✅ AI 모델 초기화 완료")
            
        except Exception as e:
            logger.error(f"AI 모델 초기화 오류: {e}")
    
    async def analyze_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """시장 심리 분석"""
        try:
            # 시뮬레이션용 심리 분석
            sentiments = ["매우_낙관적", "낙관적", "중립", "비관적", "매우_비관적"]
            weights = [0.15, 0.25, 0.3, 0.2, 0.1]  # 가중치
            
            sentiment = np.random.choice(sentiments, p=weights)
            confidence = random.uniform(0.6, 0.95)
            
            # 추가 분석 지표
            fear_greed_index = random.uniform(0, 100)
            social_volume = random.uniform(1000, 50000)
            news_sentiment = random.uniform(-1, 1)
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "fear_greed_index": fear_greed_index,
                "social_volume": social_volume,
                "news_sentiment": news_sentiment,
                "analysis_time": datetime.now().isoformat(),
                "factors": {
                    "technical": random.uniform(0.3, 0.7),
                    "fundamental": random.uniform(0.2, 0.8),
                    "social": random.uniform(0.1, 0.9)
                }
            }
            
        except Exception as e:
            logger.error(f"심리 분석 오류: {e}")
            return {
                "sentiment": "중립",
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def predict_price_direction(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """가격 방향 예측"""
        try:
            if df.empty or len(df) < 10:
                raise ValueError("충분한 데이터가 없습니다")
            
            # 기술적 지표 계산
            features = self._calculate_features(df)
            
            if features is None or len(features) < 5:
                raise ValueError("기술적 지표 계산 실패")
            
            # 예측 (시뮬레이션)
            directions = ["강한_상승", "상승", "중립", "하락", "강한_하락"]
            probabilities = [0.15, 0.25, 0.3, 0.25, 0.05]
            
            predicted_direction = np.random.choice(directions, p=probabilities)
            confidence = random.uniform(0.6, 0.9)
            
            # 예상 변동률
            expected_change = self._calculate_expected_change(predicted_direction)
            
            # 시간대별 예측
            hourly_predictions = []
            for i in range(24):
                hourly_predictions.append({
                    "hour": i + 1,
                    "direction": np.random.choice(["상승", "중립", "하락"], p=[0.4, 0.3, 0.3]),
                    "change_percent": random.uniform(-5, 5)
                })
            
            return {
                "symbol": symbol,
                "prediction": predicted_direction,
                "confidence": confidence,
                "expected_change_percent": expected_change,
                "time_horizon": "24시간",
                "technical_score": random.uniform(0.3, 0.8),
                "hourly_predictions": hourly_predictions[:6],  # 첫 6시간만
                "key_levels": {
                    "support": float(df['low'].min() * 0.98),
                    "resistance": float(df['high'].max() * 1.02)
                },
                "prediction_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"가격 예측 오류: {e}")
            return {
                "prediction": "중립",
                "confidence": 0.5,
                "expected_change_percent": 0.0,
                "error": str(e)
            }
    
    async def generate_trading_strategy(self, symbol: str, market_data: Dict, 
                                       sentiment: Dict, prediction: Dict) -> Dict[str, Any]:
        """거래 전략 생성"""
        try:
            # 전략 결정 로직
            sentiment_score = self._convert_sentiment_to_score(sentiment.get('sentiment', '중립'))
            prediction_score = self._convert_prediction_to_score(prediction.get('prediction', '중립'))
            
            # 종합 점수 계산
            combined_score = (sentiment_score * 0.4) + (prediction_score * 0.6)
            
            # 전략 결정
            if combined_score > 0.6:
                action = "매수"
                strategy_type = "적극매수"
                position_size = 0.7
            elif combined_score > 0.3:
                action = "매수"
                strategy_type = "부분매수"
                position_size = 0.4
            elif combined_score < -0.6:
                action = "매도"
                strategy_type = "적극매도"
                position_size = 0.8
            elif combined_score < -0.3:
                action = "매도"
                strategy_type = "부분매도"
                position_size = 0.3
            else:
                action = "대기"
                strategy_type = "관망"
                position_size = 0.0
            
            # 리스크 관리
            stop_loss = self._calculate_stop_loss(action, market_data)
            take_profit = self._calculate_take_profit(action, market_data)
            
            return {
                "action": action,
                "strategy_type": strategy_type,
                "confidence": min(abs(sentiment.get('confidence', 0.5)) + abs(prediction.get('confidence', 0.5)), 1.0),
                "position_size": position_size,
                "entry_conditions": self._generate_entry_conditions(action, market_data),
                "exit_conditions": {
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "time_limit": "24시간"
                },
                "risk_level": self._assess_risk_level(combined_score, market_data),
                "expected_return": self._calculate_expected_return(action, prediction),
                "reasoning": self._generate_strategy_reasoning(sentiment, prediction, combined_score),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"전략 생성 오류: {e}")
            return {
                "action": "대기",
                "strategy_type": "관망",
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def calculate_technical_indicators(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """기술적 지표 계산"""
        try:
            df = pd.DataFrame(ohlcv_data)
            if df.empty:
                return {}
            
            # 가격 컬럼 확인 및 변환
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            indicators = {}
            
            # 이동평균
            if len(df) >= 20:
                indicators['sma_20'] = float(ta.trend.sma_indicator(df['close'], window=20).iloc[-1])
                indicators['ema_20'] = float(ta.trend.ema_indicator(df['close'], window=20).iloc[-1])
            
            # RSI
            if len(df) >= 14:
                indicators['rsi'] = float(ta.momentum.rsi(df['close'], window=14).iloc[-1])
            
            # MACD
            if len(df) >= 26:
                macd_line = ta.trend.macd(df['close'])
                macd_signal = ta.trend.macd_signal(df['close'])
                indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0
                indicators['macd_signal'] = float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0
            
            # 볼린저 밴드
            if len(df) >= 20:
                bb_high = ta.volatility.bollinger_hband(df['close'])
                bb_low = ta.volatility.bollinger_lband(df['close'])
                bb_mid = ta.volatility.bollinger_mavg(df['close'])
                
                indicators['bollinger'] = {
                    'upper': float(bb_high.iloc[-1]) if not pd.isna(bb_high.iloc[-1]) else 0,
                    'middle': float(bb_mid.iloc[-1]) if not pd.isna(bb_mid.iloc[-1]) else 0,
                    'lower': float(bb_low.iloc[-1]) if not pd.isna(bb_low.iloc[-1]) else 0
                }
            
            # 거래량 지표
            if 'volume' in df.columns and len(df) >= 10:
                indicators['volume_sma'] = float(df['volume'].rolling(10).mean().iloc[-1])
                indicators['volume_ratio'] = float(df['volume'].iloc[-1] / indicators['volume_sma'])
            
            return indicators
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 오류: {e}")
            return {}
    
    async def assess_trading_risk(self, symbol: str, investment_amount: float) -> Dict[str, Any]:
        """거래 리스크 평가"""
        try:
            # 심볼별 기본 리스크
            symbol_risk = {
                'BTC/KRW': 0.6,  # 중간 리스크
                'ETH/KRW': 0.7,  # 중상 리스크
                'XRP/KRW': 0.8,  # 높은 리스크
                'ADA/KRW': 0.9   # 매우 높은 리스크
            }
            
            base_risk = symbol_risk.get(symbol, 0.75)
            
            # 투자금액에 따른 리스크 조정
            amount_risk_multiplier = min(investment_amount / 10000000, 2.0)  # 1천만원 기준
            
            # 종합 리스크 점수
            total_risk_score = min(base_risk * amount_risk_multiplier, 1.0)
            
            # 리스크 등급
            if total_risk_score < 0.3:
                risk_level = "낮음"
            elif total_risk_score < 0.6:
                risk_level = "보통"
            elif total_risk_score < 0.8:
                risk_level = "높음"
            else:
                risk_level = "매우높음"
            
            # 추천 포지션 크기
            recommended_position = max(0.1, 1.0 - total_risk_score)
            
            return {
                "symbol": symbol,
                "investment_amount": investment_amount,
                "risk_score": total_risk_score,
                "risk_level": risk_level,
                "recommended_position_size": recommended_position,
                "max_loss_estimate": investment_amount * total_risk_score * 0.5,
                "risk_factors": {
                    "market_volatility": random.uniform(0.3, 0.9),
                    "liquidity_risk": random.uniform(0.1, 0.7),
                    "correlation_risk": random.uniform(0.2, 0.8)
                },
                "recommendations": self._generate_risk_recommendations(risk_level),
                "assessment_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"리스크 평가 오류: {e}")
            return {
                "risk_level": "높음",
                "risk_score": 0.8,
                "error": str(e)
            }
    
    # 헬퍼 메서드들
    def _calculate_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """기술적 지표 기반 특성 계산"""
        try:
            if len(df) < 20:
                return None
            
            features = []
            
            # 가격 관련 특성
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
            features.append(price_change)
            
            # 거래량 특성
            volume_ratio = df['volume'].iloc[-1] / df['volume'].mean()
            features.append(volume_ratio)
            
            # 변동성
            volatility = df['close'].pct_change().std()
            features.append(volatility)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"특성 계산 오류: {e}")
            return None
    
    def _convert_sentiment_to_score(self, sentiment: str) -> float:
        """심리를 점수로 변환"""
        sentiment_map = {
            "매우_낙관적": 0.9,
            "낙관적": 0.6,
            "중립": 0.0,
            "비관적": -0.6,
            "매우_비관적": -0.9
        }
        return sentiment_map.get(sentiment, 0.0)
    
    def _convert_prediction_to_score(self, prediction: str) -> float:
        """예측을 점수로 변환"""
        prediction_map = {
            "강한_상승": 0.9,
            "상승": 0.6,
            "중립": 0.0,
            "하락": -0.6,
            "강한_하락": -0.9
        }
        return prediction_map.get(prediction, 0.0)
    
    def _calculate_expected_change(self, direction: str) -> float:
        """예상 변동률 계산"""
        change_map = {
            "강한_상승": random.uniform(5, 15),
            "상승": random.uniform(1, 5),
            "중립": random.uniform(-1, 1),
            "하락": random.uniform(-5, -1),
            "강한_하락": random.uniform(-15, -5)
        }
        return change_map.get(direction, 0.0)
    
    def _calculate_stop_loss(self, action: str, market_data: Dict) -> float:
        """손절매 계산"""
        current_price = market_data.get('current_price', 0)
        volatility = market_data.get('volatility', 0.02)
        
        if action == "매수":
            return current_price * (1 - volatility * 2)
        elif action == "매도":
            return current_price * (1 + volatility * 2)
        return current_price
    
    def _calculate_take_profit(self, action: str, market_data: Dict) -> float:
        """익절매 계산"""
        current_price = market_data.get('current_price', 0)
        volatility = market_data.get('volatility', 0.02)
        
        if action == "매수":
            return current_price * (1 + volatility * 3)
        elif action == "매도":
            return current_price * (1 - volatility * 3)
        return current_price
    
    def _generate_entry_conditions(self, action: str, market_data: Dict) -> List[str]:
        """진입 조건 생성"""
        conditions = []
        
        if action == "매수":
            conditions.extend([
                "RSI < 70",
                "거래량 증가 확인",
                "지지선 근처 진입"
            ])
        elif action == "매도":
            conditions.extend([
                "RSI > 30",
                "저항선 근처 진입",
                "하락 모멘텀 확인"
            ])
        else:
            conditions.append("명확한 신호 대기")
        
        return conditions
    
    def _assess_risk_level(self, score: float, market_data: Dict) -> str:
        """리스크 레벨 평가"""
        volatility = market_data.get('volatility', 0.02)
        
        if abs(score) > 0.7 and volatility > 0.05:
            return "높음"
        elif abs(score) > 0.5 or volatility > 0.03:
            return "보통"
        else:
            return "낮음"
    
    def _calculate_expected_return(self, action: str, prediction: Dict) -> float:
        """예상 수익률 계산"""
        expected_change = prediction.get('expected_change_percent', 0)
        confidence = prediction.get('confidence', 0.5)
        
        if action in ["매수", "매도"]:
            return abs(expected_change) * confidence
        return 0.0
    
    def _generate_strategy_reasoning(self, sentiment: Dict, prediction: Dict, score: float) -> str:
        """전략 근거 생성"""
        reasoning_parts = []
        
        sentiment_text = sentiment.get('sentiment', '중립')
        prediction_text = prediction.get('prediction', '중립')
        
        reasoning_parts.append(f"시장 심리: {sentiment_text}")
        reasoning_parts.append(f"가격 예측: {prediction_text}")
        
        if score > 0.5:
            reasoning_parts.append("강한 상승 신호로 적극 매수 권장")
        elif score > 0:
            reasoning_parts.append("상승 신호로 부분 매수 고려")
        elif score < -0.5:
            reasoning_parts.append("강한 하락 신호로 매도 권장")
        elif score < 0:
            reasoning_parts.append("하락 위험으로 신중한 접근 필요")
        else:
            reasoning_parts.append("불분명한 신호로 관망 권장")
        
        return " | ".join(reasoning_parts)
    
    def _generate_risk_recommendations(self, risk_level: str) -> List[str]:
        """리스크별 추천사항 생성"""
        recommendations = {
            "낮음": [
                "안정적인 투자 환경",
                "큰 포지션도 고려 가능",
                "장기 보유 적합"
            ],
            "보통": [
                "적절한 포지션 크기 유지",
                "손절매 라인 설정 필수",
                "정기적인 포트폴리오 점검"
            ],
            "높음": [
                "소액 투자 권장",
                "엄격한 리스크 관리 필요",
                "단기간 모니터링 필수"
            ],
            "매우높음": [
                "투자 재고 권장",
                "전문가 상담 필요",
                "최소 금액만 투자"
            ]
        }
        return recommendations.get(risk_level, ["신중한 접근 필요"])

# 전역 서비스 인스턴스
ai_service = AIInferenceService()
