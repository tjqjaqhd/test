
"""
📋 API 스키마 정의
요청/응답 데이터 모델
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    """지원되는 거래 전략"""
    ARBITRAGE = "arbitrage"
    SHORT_TRADING = "short_trading"
    LEVERAGE_TRADING = "leverage_trading"
    MEME_TRADING = "meme_trading"

class TradingSymbol(str, Enum):
    """지원되는 거래쌍"""
    BTC_KRW = "BTC/KRW"
    ETH_KRW = "ETH/KRW"
    XRP_KRW = "XRP/KRW"
    ADA_KRW = "ADA/KRW"

class SimulationRequest(BaseModel):
    """시뮬레이션 시작 요청"""
    strategy: StrategyType = Field(..., description="거래 전략")
    symbol: TradingSymbol = Field(..., description="거래쌍")
    initial_balance: float = Field(1000000, description="초기 자본금 (원)")
    duration_hours: Optional[int] = Field(24, description="시뮬레이션 기간 (시간)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "short_trading",
                "symbol": "BTC/KRW",
                "initial_balance": 1000000,
                "duration_hours": 24
            }
        }

class SimulationResponse(BaseModel):
    """시뮬레이션 시작 응답"""
    simulation_id: str
    status: str
    message: str

class BacktestRequest(BaseModel):
    """백테스팅 요청"""
    strategy: StrategyType
    symbol: TradingSymbol
    start_date: datetime
    end_date: datetime
    initial_balance: float = 1000000
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "arbitrage",
                "symbol": "BTC/KRW",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-31T23:59:59",
                "initial_balance": 1000000
            }
        }

class BacktestResponse(BaseModel):
    """백테스팅 결과"""
    strategy: str
    symbol: str
    period: str
    initial_balance: float
    final_balance: float
    total_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    completed_at: datetime
    
    @property
    def profit_loss(self) -> float:
        return self.final_balance - self.initial_balance
    
    @property
    def return_rate(self) -> float:
        return ((self.final_balance / self.initial_balance) - 1) * 100

class TradeRecord(BaseModel):
    """거래 기록"""
    timestamp: datetime
    side: str  # "buy" or "sell"
    amount: float
    price: float
    profit_loss: float
