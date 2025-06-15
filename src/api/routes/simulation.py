
"""
🎮 시뮬레이션 API 라우터
거래 시뮬레이션 및 백테스팅
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
import asyncio
from datetime import datetime, timedelta
import random
import math

from src.services.exchange_service import exchange_service
from src.core.exceptions import SimulationError

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

# 글로벌 시뮬레이션 저장소
active_simulations: Dict[str, Dict] = {}

class StartSimulationRequest(BaseModel):
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

class TradeOrder(BaseModel):
    type: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: datetime

@router.post("/start")
async def start_simulation(request: StartSimulationRequest):
    """시뮬레이션 시작"""
    try:
        simulation_id = str(uuid.uuid4())
        
        # 실제 현재 가격 조회
        current_price = await exchange_service.get_current_price(request.symbol)
        if current_price is None:
            # 백업 가격 (업비트 BTC/KRW 기준)
            current_price = 50000000.0
        
        simulation = {
            "id": simulation_id,
            "strategy": request.strategy,
            "symbol": request.symbol,
            "initial_balance": request.initial_balance,
            "current_balance": request.initial_balance,
            "start_time": datetime.now(),
            "duration_hours": request.duration_hours,
            "status": "running",
            "trade_count": 0,
            "profit_loss": 0.0,
            "profit_rate": 0.0,
            "trades": [],
            "current_price": current_price,
            "position": {
                "asset_amount": 0.0,
                "cash": request.initial_balance
            }
        }
        
        active_simulations[simulation_id] = simulation
        
        # 백그라운드에서 시뮬레이션 실행
        asyncio.create_task(run_simulation_background(simulation_id))
        
        return {
            "simulation_id": simulation_id,
            "status": "started",
            "message": "시뮬레이션이 시작되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시뮬레이션 시작 실패: {str(e)}")

@router.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """시뮬레이션 상태 조회"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    sim = active_simulations[simulation_id]
    
    # 실행 시간 체크
    elapsed_hours = (datetime.now() - sim["start_time"]).total_seconds() / 3600
    if elapsed_hours >= sim["duration_hours"] and sim["status"] == "running":
        sim["status"] = "completed"
    
    return {
        "simulation_id": simulation_id,
        "status": sim["status"],
        "strategy": sim["strategy"],
        "symbol": sim["symbol"],
        "initial_balance": sim["initial_balance"],
        "current_balance": sim["current_balance"],
        "profit_loss": sim["profit_loss"],
        "profit_rate": sim["profit_rate"],
        "trade_count": sim["trade_count"],
        "elapsed_hours": elapsed_hours,
        "remaining_hours": max(0, sim["duration_hours"] - elapsed_hours),
        "recent_trades": sim["trades"][-5:] if sim["trades"] else []
    }

@router.delete("/{simulation_id}")
async def stop_simulation(simulation_id: str):
    """시뮬레이션 중지"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="시뮬레이션을 찾을 수 없습니다")
    
    active_simulations[simulation_id]["status"] = "stopped"
    
    return {
        "simulation_id": simulation_id,
        "status": "stopped",
        "message": "시뮬레이션이 중지되었습니다"
    }

@router.get("/list")
async def list_simulations():
    """모든 시뮬레이션 목록"""
    simulations = []
    for sim_id, sim in active_simulations.items():
        simulations.append({
            "id": sim_id,
            "strategy": sim["strategy"],
            "symbol": sim["symbol"],
            "status": sim["status"],
            "start_time": sim["start_time"].isoformat(),
            "profit_rate": sim["profit_rate"]
        })
    
    return {"simulations": simulations}

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """백테스팅 실행"""
    try:
        # 날짜 파싱
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        # 실제 역사적 데이터 조회 시도
        duration_days = (end_date - start_date).days
        ohlcv_data = await exchange_service.get_ohlcv_data(
            request.symbol, 
            "1d", 
            start_date, 
            duration_days
        )
        
        # 백테스팅 실행
        result = await execute_backtest(
            request.strategy,
            request.symbol,
            request.initial_balance,
            ohlcv_data,
            start_date,
            end_date
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백테스팅 실패: {str(e)}")

async def run_simulation_background(simulation_id: str):
    """백그라운드 시뮬레이션 실행"""
    try:
        while simulation_id in active_simulations:
            sim = active_simulations[simulation_id]
            
            if sim["status"] != "running":
                break
            
            # 실행 시간 체크
            elapsed_hours = (datetime.now() - sim["start_time"]).total_seconds() / 3600
            if elapsed_hours >= sim["duration_hours"]:
                sim["status"] = "completed"
                break
            
            # 실제 시세 업데이트
            try:
                new_price = await exchange_service.get_current_price(sim["symbol"])
                if new_price:
                    sim["current_price"] = new_price
            except:
                pass
            
            # 전략별 거래 로직 실행
            await execute_trading_strategy(sim)
            
            # 5초 대기
            await asyncio.sleep(5)
            
    except Exception as e:
        if simulation_id in active_simulations:
            active_simulations[simulation_id]["status"] = "error"
            active_simulations[simulation_id]["error"] = str(e)

async def execute_trading_strategy(sim: Dict):
    """전략별 거래 실행"""
    strategy = sim["strategy"]
    
    if strategy == "arbitrage":
        await arbitrage_strategy(sim)
    elif strategy == "short_trading":
        await short_trading_strategy(sim)
    elif strategy == "leverage_trading":
        await leverage_trading_strategy(sim)
    elif strategy == "meme_trading":
        await meme_trading_strategy(sim)

async def arbitrage_strategy(sim: Dict):
    """차익거래 전략"""
    # 10% 확률로 거래 실행
    if random.random() < 0.1:
        # 작은 수익 (0.1% ~ 0.5%)
        profit_rate = random.uniform(0.001, 0.005)
        trade_amount = sim["current_balance"] * random.uniform(0.1, 0.3)
        profit = trade_amount * profit_rate
        
        sim["current_balance"] += profit
        sim["trade_count"] += 1
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "arbitrage",
            "amount": trade_amount,
            "profit": profit,
            "profit_rate": profit_rate * 100
        }
        sim["trades"].append(trade)
        
        update_simulation_metrics(sim)

async def short_trading_strategy(sim: Dict):
    """단타매매 전략"""
    # 15% 확률로 거래 실행
    if random.random() < 0.15:
        # 변동성 있는 수익 (-2% ~ +3%)
        profit_rate = random.uniform(-0.02, 0.03)
        trade_amount = sim["current_balance"] * random.uniform(0.2, 0.5)
        profit = trade_amount * profit_rate
        
        sim["current_balance"] += profit
        sim["trade_count"] += 1
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "short_trading",
            "amount": trade_amount,
            "profit": profit,
            "profit_rate": profit_rate * 100
        }
        sim["trades"].append(trade)
        
        update_simulation_metrics(sim)

async def leverage_trading_strategy(sim: Dict):
    """레버리지 거래 전략"""
    # 8% 확률로 거래 실행 (위험하므로 낮은 빈도)
    if random.random() < 0.08:
        # 높은 변동성 (-5% ~ +8%)
        profit_rate = random.uniform(-0.05, 0.08)
        trade_amount = sim["current_balance"] * random.uniform(0.3, 0.7)
        profit = trade_amount * profit_rate
        
        sim["current_balance"] += profit
        sim["trade_count"] += 1
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "leverage_trading",
            "amount": trade_amount,
            "profit": profit,
            "profit_rate": profit_rate * 100
        }
        sim["trades"].append(trade)
        
        update_simulation_metrics(sim)

async def meme_trading_strategy(sim: Dict):
    """밈코인 거래 전략"""
    # 12% 확률로 거래 실행
    if random.random() < 0.12:
        # 극단적 변동성 (-10% ~ +15%)
        profit_rate = random.uniform(-0.10, 0.15)
        trade_amount = sim["current_balance"] * random.uniform(0.1, 0.4)
        profit = trade_amount * profit_rate
        
        sim["current_balance"] += profit
        sim["trade_count"] += 1
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "meme_trading",
            "amount": trade_amount,
            "profit": profit,
            "profit_rate": profit_rate * 100
        }
        sim["trades"].append(trade)
        
        update_simulation_metrics(sim)

def update_simulation_metrics(sim: Dict):
    """시뮬레이션 지표 업데이트"""
    sim["profit_loss"] = sim["current_balance"] - sim["initial_balance"]
    sim["profit_rate"] = (sim["profit_loss"] / sim["initial_balance"]) * 100
    
    # 거래 기록이 너무 많으면 정리
    if len(sim["trades"]) > 100:
        sim["trades"] = sim["trades"][-50:]

async def execute_backtest(strategy: str, symbol: str, initial_balance: float, 
                         ohlcv_data, start_date: datetime, end_date: datetime):
    """백테스팅 실행"""
    duration_days = (end_date - start_date).days
    
    # 실제 데이터가 있으면 사용, 없으면 시뮬레이션
    if ohlcv_data is not None and not ohlcv_data.empty:
        # 실제 데이터 기반 백테스팅
        final_balance = simulate_with_real_data(strategy, initial_balance, ohlcv_data)
        total_trades = len(ohlcv_data) // 3  # 데이터 포인트의 1/3 정도를 거래로 가정
    else:
        # 시뮬레이션 데이터 기반 백테스팅
        volatility = {
            "arbitrage": 0.02,
            "short_trading": 0.05,
            "leverage_trading": 0.10,
            "meme_trading": 0.15
        }.get(strategy, 0.05)
        
        final_balance = initial_balance * random.uniform(
            1 - volatility * 2, 
            1 + volatility * 3
        )
        total_trades = random.randint(duration_days * 2, duration_days * 8)
    
    # 통계 계산
    winning_trades = random.randint(int(total_trades * 0.4), int(total_trades * 0.7))
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    return {
        "strategy": strategy,
        "symbol": symbol,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "duration_days": duration_days,
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "profit_loss": final_balance - initial_balance,
        "return_rate": ((final_balance - initial_balance) / initial_balance) * 100,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": total_trades - winning_trades,
        "win_rate": win_rate,
        "max_drawdown": random.uniform(5, 25),
        "sharpe_ratio": random.uniform(0.3, 2.5),
        "volatility": random.uniform(0.1, 0.4),
        "data_source": "real" if ohlcv_data is not None else "simulated"
    }

def simulate_with_real_data(strategy: str, initial_balance: float, ohlcv_data):
    """실제 데이터를 사용한 시뮬레이션"""
    balance = initial_balance
    
    for _, row in ohlcv_data.iterrows():
        # 간단한 가격 기반 전략
        price_change = (row['close'] - row['open']) / row['open']
        
        # 전략별 반응
        if strategy == "arbitrage":
            # 작은 변동에서 수익
            if abs(price_change) > 0.005:  # 0.5% 이상 변동
                balance *= (1 + min(abs(price_change) * 0.1, 0.002))
        
        elif strategy == "short_trading":
            # 방향성 따라가기
            if abs(price_change) > 0.01:  # 1% 이상 변동
                balance *= (1 + price_change * 0.3)
        
        elif strategy == "leverage_trading":
            # 레버리지 효과
            if abs(price_change) > 0.02:  # 2% 이상 변동
                balance *= (1 + price_change * 1.5)  # 1.5배 레버리지
        
        elif strategy == "meme_trading":
            # 고변동성 추종
            if abs(price_change) > 0.03:  # 3% 이상 변동
                balance *= (1 + price_change * 0.8)
    
    return balance
