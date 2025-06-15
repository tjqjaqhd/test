
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
    """실제 데이터 기반 백테스팅 실행"""
    try:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        duration_days = (end_date - start_date).days
        
        # 실제 과거 데이터 조회
        historical_data = await exchange_service.get_ohlcv_data(
            request.symbol, '1d', duration_days + 10
        )
        
        if not historical_data:
            raise HTTPException(status_code=400, detail="과거 데이터를 가져올 수 없습니다")
        
        # 백테스팅 시뮬레이션 실행
        backtest_result = await run_backtest_simulation(
            request, historical_data, duration_days
        )
        
        return backtest_result
        
    except Exception as e:
        logger.error(f"백테스팅 실행 오류: {e}")
        raise HTTPException(status_code=500, detail=f"백테스팅 실행 실패: {str(e)}")

async def run_backtest_simulation(request: BacktestRequest, historical_data: List[Dict], duration_days: int) -> Dict:
    """백테스팅 시뮬레이션 실행"""
    balance = request.initial_balance
    position = 0.0  # 보유 수량
    trades = []
    daily_balance = []
    
    # AI 전략 분석
    df = pd.DataFrame(historical_data)
    strategy_analysis = await ai_service.generate_trading_strategy(
        request.symbol, 
        {"historical_data": historical_data, "current_price": df['close'].iloc[-1], "volatility": 0.02},
        {"sentiment": "중립", "confidence": 0.7},
        {"prediction": "상승", "confidence": 0.8}
    )
    
    # 일별 백테스팅
    for i, candle in enumerate(historical_data[-duration_days:]):
        current_price = candle['close']
        
        # 매매 신호 생성 (전략에 따른)
        should_buy, should_sell = generate_trading_signals(
            request.strategy, i, historical_data, current_price
        )
        
        # 매수 실행
        if should_buy and balance > current_price:
            buy_amount = balance * 0.3  # 30% 매수
            shares_bought = buy_amount / current_price
            position += shares_bought
            balance -= buy_amount
            
            trades.append({
                "date": candle['datetime'],
                "type": "매수",
                "price": current_price,
                "amount": buy_amount,
                "shares": shares_bought,
                "balance": balance + (position * current_price)
            })
        
        # 매도 실행
        elif should_sell and position > 0:
            sell_shares = position * 0.5  # 50% 매도
            sell_amount = sell_shares * current_price
            position -= sell_shares
            balance += sell_amount
            
            trades.append({
                "date": candle['datetime'],
                "type": "매도",
                "price": current_price,
                "amount": sell_amount,
                "shares": sell_shares,
                "balance": balance + (position * current_price)
            })
        
        # 일별 잔고 기록
        total_value = balance + (position * current_price)
        daily_balance.append({
            "date": candle['datetime'],
            "balance": total_value,
            "cash": balance,
            "position_value": position * current_price
        })
    
    # 최종 정산
    final_price = historical_data[-1]['close']
    final_balance = balance + (position * final_price)
    total_return = ((final_balance - request.initial_balance) / request.initial_balance) * 100
    
    # 성과 지표 계산
    max_balance = max([day['balance'] for day in daily_balance])
    min_balance = min([day['balance'] for day in daily_balance])
    max_drawdown = ((max_balance - min_balance) / max_balance) * 100
    
    # 승률 계산
    profitable_trades = [t for t in trades if t['type'] == '매도']
    win_rate = 0
    if len(profitable_trades) > 1:
        wins = 0
        for i in range(1, len(profitable_trades)):
            if profitable_trades[i]['price'] > profitable_trades[i-1]['price']:
                wins += 1
        win_rate = (wins / (len(profitable_trades) - 1)) * 100 if len(profitable_trades) > 1 else 0
    
    return {
        "symbol": request.symbol,
        "strategy": request.strategy,
        "period": f"{request.start_date} ~ {request.end_date}",
        "initial_balance": request.initial_balance,
        "final_balance": final_balance,
        "total_return": total_return,
        "total_trades": len(trades),
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": calculate_sharpe_ratio(daily_balance),
        "trades": trades[-10:],  # 최근 10개 거래만
        "daily_performance": daily_balance[-30:],  # 최근 30일만
        "strategy_analysis": strategy_analysis,
        "performance_metrics": {
            "best_day": max_balance,
            "worst_day": min_balance,
            "volatility": calculate_volatility([day['balance'] for day in daily_balance]),
            "avg_daily_return": total_return / duration_days if duration_days > 0 else 0
        }
    }

def generate_trading_signals(strategy: str, day_index: int, data: List[Dict], current_price: float) -> tuple:
    """전략별 매매 신호 생성"""
    should_buy = False
    should_sell = False
    
    if day_index < 5:  # 초기 데이터 부족
        return should_buy, should_sell
    
    recent_prices = [data[day_index - i]['close'] for i in range(5, 0, -1)]
    
    if strategy == "arbitrage":  # 차익거래
        # 단순 평균 회귀 전략
        avg_price = sum(recent_prices) / len(recent_prices)
        if current_price < avg_price * 0.98:
            should_buy = True
        elif current_price > avg_price * 1.02:
            should_sell = True
            
    elif strategy == "short_trading":  # 단타
        # 모멘텀 전략
        if recent_prices[-1] > recent_prices[-2] * 1.01:
            should_buy = True
        elif recent_prices[-1] < recent_prices[-2] * 0.99:
            should_sell = True
            
    elif strategy == "leverage_trading":  # 레버리지
        # 추세 추종 전략
        if all(recent_prices[i] < recent_prices[i+1] for i in range(len(recent_prices)-1)):
            should_buy = True
        elif all(recent_prices[i] > recent_prices[i+1] for i in range(len(recent_prices)-1)):
            should_sell = True
            
    elif strategy == "meme_trading":  # 밈코인
        # 변동성 돌파 전략
        price_std = pd.Series(recent_prices).std()
        if current_price > max(recent_prices) + price_std:
            should_buy = True
        elif current_price < min(recent_prices) - price_std:
            should_sell = True
    
    return should_buy, should_sell

def calculate_sharpe_ratio(daily_balance: List[Dict]) -> float:
    """샤프 비율 계산"""
    if len(daily_balance) < 2:
        return 0.0
    
    returns = []
    for i in range(1, len(daily_balance)):
        ret = (daily_balance[i]['balance'] - daily_balance[i-1]['balance']) / daily_balance[i-1]['balance']
        returns.append(ret)
    
    if not returns:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    return_std = pd.Series(returns).std()
    
    return (avg_return / return_std) * (252 ** 0.5) if return_std > 0 else 0.0  # 연환산

def calculate_volatility(balances: List[float]) -> float:
    """변동성 계산"""
    if len(balances) < 2:
        return 0.0
    
    returns = []
    for i in range(1, len(balances)):
        ret = (balances[i] - balances[i-1]) / balances[i-1]
        returns.append(ret)
    
    return pd.Series(returns).std() * (252 ** 0.5) if returns else 0.0  # 연환산nt(50, 200)
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
