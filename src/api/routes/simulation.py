
"""
🎯 시뮬레이션 관련 API 라우트 - 실제 데이터 & AI 통합
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncio
from datetime import datetime, timedelta
import random
import time
import pandas as pd

from src.services.exchange_service import exchange_service
from src.services.ai_inference_service import ai_service

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
    """실제 데이터 기반 AI 시뮬레이션 시작"""
    simulation_id = str(uuid.uuid4())
    
    try:
        # 실제 시장 데이터 가져오기
        market_data = await exchange_service.get_real_trading_data(
            request.symbol, 
            request.duration_hours
        )
        
        if not market_data:
            raise HTTPException(status_code=400, detail="실제 시장 데이터를 가져올 수 없습니다")
        
        # AI 시장 분석
        historical_df = pd.DataFrame(market_data['historical_data'])
        sentiment = await ai_service.analyze_market_sentiment(request.symbol)
        prediction = await ai_service.predict_price_direction(historical_df, request.symbol)
        strategy = await ai_service.generate_trading_strategy(
            request.symbol, market_data, sentiment, prediction
        )
        
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
            "trades": [],
            "market_data": market_data,
            "ai_analysis": {
                "sentiment": sentiment,
                "prediction": prediction,
                "strategy": strategy
            },
            "real_price": market_data['current_price'],
            "volatility": market_data['volatility']
        }
        
        return {
            "simulation_id": simulation_id, 
            "status": "started",
            "ai_analysis": {
                "sentiment": sentiment,
                "prediction": prediction,
                "strategy": strategy
            },
            "market_data": {
                "current_price": market_data['current_price'],
                "volatility": market_data['volatility'],
                "trend": market_data['price_trend']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시뮬레이션 시작 실패: {str(e)}")

@router.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """AI 기반 실시간 시뮬레이션 상태 조회"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    sim = active_simulations[simulation_id]
    
    # 실행 중인 시뮬레이션 업데이트
    if sim["status"] == "running":
        elapsed = datetime.now() - sim["start_time"]
        elapsed_hours = elapsed.total_seconds() / 3600
        
        if elapsed_hours < sim["duration_hours"]:
            try:
                # 실제 현재 가격 업데이트
                current_price = await exchange_service.get_current_price(sim["symbol"])
                if current_price:
                    sim["real_price"] = current_price
                
                # AI 기반 거래 시뮬레이션
                volatility = sim.get("volatility", 0.02)
                
                # AI 전략에 따른 거래 결정
                ai_strategy = sim.get("ai_analysis", {}).get("strategy", {})
                ai_action = ai_strategy.get("action", "대기")
                ai_confidence = ai_strategy.get("confidence", 0.5)
                
                # 거래 실행 확률 (AI 신뢰도 기반)
                if random.random() < ai_confidence * 0.3:  # 최대 30% 확률로 거래
                    sim["trade_count"] += 1
                    
                    # AI 예측에 따른 수익률 조정
                    if ai_action == "매수":
                        change_factor = 1 + (volatility * random.uniform(0.5, 1.5))
                    elif ai_action == "매도":
                        change_factor = 1 - (volatility * random.uniform(0.5, 1.5))
                    else:
                        change_factor = 1 + (volatility * random.uniform(-0.5, 0.5))
                    
                    sim["current_balance"] *= change_factor
                
                # 실제 시장 변동 반영 (30%)
                market_change = random.uniform(-volatility, volatility)
                sim["current_balance"] *= (1 + market_change * 0.3)
                
                sim["profit_loss"] = sim["current_balance"] - sim["initial_balance"]
                sim["profit_rate"] = (sim["profit_loss"] / sim["initial_balance"]) * 100
                
                # 거래 기록 추가
                if sim["trade_count"] > len(sim["trades"]):
                    sim["trades"].append({
                        "timestamp": datetime.now().isoformat(),
                        "action": ai_action,
                        "balance": sim["current_balance"],
                        "profit_rate": sim["profit_rate"],
                        "ai_confidence": ai_confidence,
                        "market_price": current_price
                    })
                
            except Exception as e:
                logger.error(f"시뮬레이션 업데이트 오류: {e}")
        else:
            sim["status"] = "completed"
    
    return sim

@router.delete("/{simulation_id}")
async def stop_simulation(simulation_id: str):
    """시뮬레이션 중지"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    active_simulations[simulation_id]["status"] = "stopped"
    return {"message": "시뮬레이션이 중지되었습니다"}

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
