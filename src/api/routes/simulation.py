
"""
📊 시뮬레이션 API 라우트
백테스팅 및 실시간 시뮬레이션 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from src.core.logging_config import get_logger
from src.api.models.schemas import (
    SimulationRequest,
    SimulationResponse,
    BacktestRequest,
    BacktestResponse
)

router = APIRouter()
logger = get_logger(__name__)

# 임시 시뮬레이션 결과 저장소 (실제로는 데이터베이스 사용)
simulation_results = {}

@router.post("/start", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """새로운 시뮬레이션 시작"""
    simulation_id = str(uuid.uuid4())
    
    logger.info(f"🚀 시뮬레이션 시작: {simulation_id}")
    logger.info(f"전략: {request.strategy}, 자산: {request.symbol}, 초기자본: {request.initial_balance:,}원")
    
    # 시뮬레이션 결과 초기화
    simulation_results[simulation_id] = {
        "id": simulation_id,
        "status": "running",
        "strategy": request.strategy,
        "symbol": request.symbol,
        "initial_balance": request.initial_balance,
        "current_balance": request.initial_balance,
        "trades": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # 백그라운드에서 시뮬레이션 실행
    background_tasks.add_task(run_simulation_background, simulation_id, request)
    
    return SimulationResponse(
        simulation_id=simulation_id,
        status="started",
        message="시뮬레이션이 시작되었습니다."
    )

@router.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """시뮬레이션 상태 조회"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다.")
    
    result = simulation_results[simulation_id]
    return {
        "simulation_id": simulation_id,
        "status": result["status"],
        "current_balance": result["current_balance"],
        "profit_loss": result["current_balance"] - result["initial_balance"],
        "profit_rate": ((result["current_balance"] / result["initial_balance"]) - 1) * 100,
        "trade_count": len(result["trades"]),
        "updated_at": result["updated_at"]
    }

@router.get("/results/{simulation_id}")
async def get_simulation_results(simulation_id: str):
    """시뮬레이션 전체 결과 조회"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다.")
    
    return simulation_results[simulation_id]

@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """백테스팅 실행"""
    logger.info(f"📈 백테스팅 시작: {request.strategy} - {request.symbol}")
    logger.info(f"기간: {request.start_date} ~ {request.end_date}")
    
    # 임시 백테스팅 결과 (실제로는 백테스팅 엔진에서 계산)
    mock_result = {
        "strategy": request.strategy,
        "symbol": request.symbol,
        "period": f"{request.start_date} ~ {request.end_date}",
        "initial_balance": request.initial_balance,
        "final_balance": request.initial_balance * 1.15,  # 15% 수익률 가정
        "total_trades": 45,
        "win_rate": 67.5,
        "max_drawdown": 8.2,
        "sharpe_ratio": 1.34,
        "completed_at": datetime.now()
    }
    
    return BacktestResponse(**mock_result)

@router.delete("/stop/{simulation_id}")
async def stop_simulation(simulation_id: str):
    """시뮬레이션 중지"""
    if simulation_id not in simulation_results:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다.")
    
    simulation_results[simulation_id]["status"] = "stopped"
    simulation_results[simulation_id]["updated_at"] = datetime.now()
    
    logger.info(f"⏹️ 시뮬레이션 중지: {simulation_id}")
    
    return {"message": "시뮬레이션이 중지되었습니다."}

async def run_simulation_background(simulation_id: str, request: SimulationRequest):
    """백그라운드에서 실행되는 시뮬레이션 로직"""
    import asyncio
    import random
    
    # 실제로는 여기서 거래 전략을 실행하고 결과를 업데이트
    for i in range(50):  # 50회 거래 시뮬레이션
        await asyncio.sleep(1)  # 1초 대기
        
        if simulation_results[simulation_id]["status"] == "stopped":
            break
        
        # 랜덤 거래 결과 생성 (실제로는 전략 로직 실행)
        profit_loss = random.uniform(-10000, 15000)
        simulation_results[simulation_id]["current_balance"] += profit_loss
        
        # 거래 기록 추가
        trade = {
            "timestamp": datetime.now(),
            "side": "buy" if profit_loss > 0 else "sell",
            "amount": abs(profit_loss),
            "profit_loss": profit_loss
        }
        simulation_results[simulation_id]["trades"].append(trade)
        simulation_results[simulation_id]["updated_at"] = datetime.now()
    
    # 시뮬레이션 완료
    simulation_results[simulation_id]["status"] = "completed"
    logger.info(f"✅ 시뮬레이션 완료: {simulation_id}")
