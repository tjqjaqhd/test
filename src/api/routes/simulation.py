
"""
🎯 시뮬레이션 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncio
from datetime import datetime, timedelta
import random
import time

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

# 메모리에 시뮬레이션 상태 저장 (실제 운영에서는 DB 사용)
active_simulations: Dict[str, Dict] = {}

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

def generate_mock_trading_data(duration_hours: int, initial_balance: float):
    """모의 거래 데이터 생성"""
    trades_per_hour = random.randint(2, 5)
    total_trades = duration_hours * trades_per_hour
    
    balance = initial_balance
    trades = []
    
    for i in range(total_trades):
        # 랜덤한 수익/손실 (-5% ~ +5%)
        change_percent = random.uniform(-0.05, 0.05)
        change_amount = balance * change_percent
        balance += change_amount
        
        trades.append({
            "timestamp": datetime.now() - timedelta(hours=duration_hours-i/trades_per_hour),
            "balance": balance,
            "change": change_amount,
            "profit_rate": ((balance - initial_balance) / initial_balance) * 100
        })
    
    return trades

@router.post("/start")
async def start_simulation(request: SimulationRequest):
    """시뮬레이션 시작"""
    simulation_id = str(uuid.uuid4())
    
    # 시뮬레이션 상태 초기화
    active_simulations[simulation_id] = {
        "id": simulation_id,
        "strategy": request.strategy,
        "symbol": request.symbol,
        "initial_balance": request.initial_balance,
        "current_balance": request.initial_balance,
        "duration_hours": request.duration_hours,
        "status": "running",
        "start_time": datetime.now(),
        "trade_count": 0,
        "profit_loss": 0.0,
        "profit_rate": 0.0,
        "trades": []
    }
    
    return {
        "simulation_id": simulation_id,
        "status": "started",
        "message": "시뮬레이션이 시작되었습니다"
    }

@router.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """시뮬레이션 상태 조회"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    sim = active_simulations[simulation_id]
    
    # 시간 경과에 따른 모의 거래 데이터 업데이트
    elapsed_time = (datetime.now() - sim["start_time"]).total_seconds() / 3600
    if elapsed_time < sim["duration_hours"]:
        # 진행 중인 시뮬레이션 - 랜덤 업데이트
        if random.random() < 0.3:  # 30% 확률로 새 거래 발생
            change_percent = random.uniform(-0.02, 0.02)
            change_amount = sim["current_balance"] * change_percent
            sim["current_balance"] += change_amount
            sim["trade_count"] += 1
            
            sim["profit_loss"] = sim["current_balance"] - sim["initial_balance"]
            sim["profit_rate"] = (sim["profit_loss"] / sim["initial_balance"]) * 100
    else:
        sim["status"] = "completed"
    
    return sim

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """백테스팅 실행"""
    # 모의 백테스팅 결과 생성
    start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    duration_days = (end_date - start_date).days
    
    # 랜덤한 결과 생성
    final_balance = request.initial_balance * random.uniform(0.8, 1.3)  # -20% ~ +30%
    total_trades = random.randint(50, 200)
    winning_trades = random.randint(int(total_trades * 0.4), int(total_trades * 0.7))
    
    return {
        "initial_balance": request.initial_balance,
        "final_balance": final_balance,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "win_rate": (winning_trades / total_trades) * 100,
        "max_drawdown": random.uniform(5, 20),
        "sharpe_ratio": random.uniform(0.5, 2.0),
        "duration_days": duration_days
    }

@router.get("/list")
async def list_simulations():
    """시뮬레이션 목록 조회"""
    return list(active_simulations.values())

@router.delete("/{simulation_id}")
async def stop_simulation(simulation_id: str):
    """시뮬레이션 중지"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    active_simulations[simulation_id]["status"] = "stopped"
    return {"message": "시뮬레이션이 중지되었습니다"}
