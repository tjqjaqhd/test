"""
📝 API 스키마 모델 정의
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SimulationRequest(BaseModel):
    strategy: str
    symbol: str
    initial_balance: float
    duration_hours: int

class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_balance: float

class SimulationStatus(BaseModel):
    id: str
    strategy: str
    symbol: str
    initial_balance: float
    current_balance: float
    duration_hours: int
    status: str
    start_time: datetime
    trade_count: int
    profit_loss: float
    profit_rate: float

class BacktestResult(BaseModel):
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    duration_days: int

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    checks: dict

class SystemStatus(BaseModel):
    system: dict
    process: dict
    timestamp: str