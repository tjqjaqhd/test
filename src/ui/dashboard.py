
"""
📱 트레이딩 시뮬레이터 대시보드
Streamlit 기반 웹 인터페이스
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import time

# 페이지 설정
st.set_page_config(
    page_title="🔥 암호화폐 트레이딩 시뮬레이터",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4ECDC4;
    }
</style>
""", unsafe_allow_html=True)

# API 베이스 URL
API_BASE_URL = "http://0.0.0.0:8000/api/v1"

def main():
    """메인 대시보드"""
    
    # 헤더
    st.markdown('<h1 class="main-header">🔥 암호화폐 트레이딩 시뮬레이터</h1>', unsafe_allow_html=True)
    
    # 사이드바 - 설정
    with st.sidebar:
        st.header("⚙️ 시뮬레이션 설정")
        
        strategy = st.selectbox(
            "거래 전략",
            ["arbitrage", "short_trading", "leverage_trading", "meme_trading"],
            format_func=lambda x: {
                "arbitrage": "🔄 차익거래",
                "short_trading": "⚡ 단타매매",
                "leverage_trading": "📈 레버리지",
                "meme_trading": "🐕 밈코인"
            }[x]
        )
        
        symbol = st.selectbox(
            "거래쌍",
            ["BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW"],
            format_func=lambda x: f"💰 {x}"
        )
        
        initial_balance = st.number_input(
            "초기 자본금 (원)",
            min_value=100000,
            max_value=100000000,
            value=1000000,
            step=100000,
            format="%d"
        )
        
        duration_hours = st.slider("시뮬레이션 기간 (시간)", 1, 72, 24)
        
        # 시뮬레이션 시작 버튼
        if st.button("🚀 시뮬레이션 시작", type="primary", use_container_width=True):
            start_simulation(strategy, symbol, initial_balance, duration_hours)
    
    # 메인 컨텐츠
    tab1, tab2, tab3, tab4 = st.tabs(["📊 실시간 모니터링", "📈 백테스팅", "📋 거래 기록", "⚙️ 시스템 상태"])
    
    with tab1:
        show_realtime_monitoring()
    
    with tab2:
        show_backtesting()
    
    with tab3:
        show_trade_history()
    
    with tab4:
        show_system_status()

def start_simulation(strategy, symbol, initial_balance, duration_hours):
    """시뮬레이션 시작"""
    try:
        response = requests.post(f"{API_BASE_URL}/simulation/start", json={
            "strategy": strategy,
            "symbol": symbol,
            "initial_balance": initial_balance,
            "duration_hours": duration_hours
        })
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.simulation_id = result["simulation_id"]
            st.success(f"✅ 시뮬레이션이 시작되었습니다! ID: {result['simulation_id'][:8]}...")
        else:
            st.error("❌ 시뮬레이션 시작에 실패했습니다.")
    except Exception as e:
        st.error(f"❌ 연결 오류: {str(e)}")

def show_realtime_monitoring():
    """실시간 모니터링 화면"""
    st.subheader("📊 실시간 시뮬레이션 모니터링")
    
    if "simulation_id" not in st.session_state:
        st.info("👈 사이드바에서 시뮬레이션을 시작해주세요.")
        return
    
    # 시뮬레이션 상태 조회
    try:
        response = requests.get(f"{API_BASE_URL}/simulation/status/{st.session_state.simulation_id}")
        if response.status_code == 200:
            status = response.json()
            
            # 메트릭 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "현재 잔고",
                    f"{status['current_balance']:,.0f}원",
                    f"{status['profit_loss']:+,.0f}원"
                )
            
            with col2:
                st.metric(
                    "수익률",
                    f"{status['profit_rate']:+.2f}%",
                    f"{status['profit_rate']:+.2f}%"
                )
            
            with col3:
                st.metric("거래 횟수", f"{status['trade_count']}회")
            
            with col4:
                status_color = {
                    "running": "🟢",
                    "completed": "🔵",
                    "stopped": "🔴"
                }.get(status["status"], "⚪")
                st.metric("상태", f"{status_color} {status['status']}")
            
            # 실시간 차트 (모의 데이터)
            if status['trade_count'] > 0:
                chart_data = generate_mock_chart_data(status['trade_count'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_data['time'],
                    y=chart_data['balance'],
                    mode='lines',
                    name='잔고 변화',
                    line=dict(color='#4ECDC4', width=3)
                ))
                
                fig.update_layout(
                    title="💰 실시간 잔고 변화",
                    xaxis_title="시간",
                    yaxis_title="잔고 (원)",
                    template="plotly_white",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # 자동 새로고침
            time.sleep(2)
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 데이터 조회 실패: {str(e)}")

def show_backtesting():
    """백테스팅 화면"""
    st.subheader("📈 백테스팅")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bt_strategy = st.selectbox("전략", ["arbitrage", "short_trading", "leverage_trading"])
        bt_symbol = st.selectbox("거래쌍", ["BTC/KRW", "ETH/KRW", "XRP/KRW"])
    
    with col2:
        bt_start_date = st.date_input("시작 날짜", datetime.now() - timedelta(days=30))
        bt_end_date = st.date_input("종료 날짜", datetime.now())
    
    bt_initial_balance = st.number_input("초기 자본금", value=1000000, step=100000)
    
    if st.button("🔍 백테스팅 실행", type="secondary"):
        with st.spinner("백테스팅 실행 중..."):
            try:
                response = requests.post(f"{API_BASE_URL}/simulation/backtest", json={
                    "strategy": bt_strategy,
                    "symbol": bt_symbol,
                    "start_date": bt_start_date.isoformat() + "T00:00:00",
                    "end_date": bt_end_date.isoformat() + "T23:59:59",
                    "initial_balance": bt_initial_balance
                })
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 결과 표시
                    st.success("✅ 백테스팅 완료!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("최종 잔고", f"{result['final_balance']:,.0f}원")
                    
                    with col2:
                        profit_loss = result['final_balance'] - result['initial_balance']
                        return_rate = (profit_loss / result['initial_balance']) * 100
                        st.metric("수익률", f"{return_rate:+.2f}%", f"{profit_loss:+,.0f}원")
                    
                    with col3:
                        st.metric("총 거래 수", f"{result['total_trades']}회")
                    
                    with col4:
                        st.metric("승률", f"{result['win_rate']:.1f}%")
                    
                    # 추가 지표
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("최대 낙폭", f"{result['max_drawdown']:.2f}%")
                    with col2:
                        st.metric("샤프 비율", f"{result['sharpe_ratio']:.2f}")
                        
            except Exception as e:
                st.error(f"❌ 백테스팅 실패: {str(e)}")

def show_trade_history():
    """거래 기록 화면"""
    st.subheader("📋 거래 기록")
    
    # 모의 거래 데이터
    mock_trades = pd.DataFrame({
        '시간': pd.date_range(start='2024-01-01', periods=20, freq='H'),
        '거래쌍': ['BTC/KRW'] * 20,
        '매수/매도': ['매수', '매도'] * 10,
        '수량': [0.001, 0.0015, 0.002] * 7 + [0.001],
        '가격': [50000000 + i*100000 for i in range(20)],
        '손익': [5000, -3000, 8000, -2000, 12000] * 4
    })
    
    st.dataframe(mock_trades, use_container_width=True)
    
    # 거래 통계
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 거래 수", "20회")
    
    with col2:
        st.metric("수익 거래", "12회")
    
    with col3:
        st.metric("손실 거래", "8회")

def show_system_status():
    """시스템 상태 화면"""
    st.subheader("⚙️ 시스템 상태")
    
    try:
        response = requests.get(f"{API_BASE_URL}/monitoring/system")
        if response.status_code == 200:
            system_info = response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💻 시스템 리소스")
                st.metric("CPU 사용률", f"{system_info['system']['cpu_percent']:.1f}%")
                st.metric("메모리 사용률", f"{system_info['system']['memory']['percent']:.1f}%")
                st.metric("디스크 사용률", f"{system_info['system']['disk']['percent']:.1f}%")
            
            with col2:
                st.subheader("🔧 프로세스 정보")
                st.metric("프로세스 ID", system_info['process']['pid'])
                st.metric("프로세스 CPU", f"{system_info['process']['cpu_percent']:.1f}%")
                st.metric("프로세스 메모리", f"{system_info['process']['memory_mb']:.1f}MB")
                
        # 헬스체크
        response = requests.get(f"{API_BASE_URL}/monitoring/health")
        if response.status_code == 200:
            health = response.json()
            
            st.subheader("🏥 서비스 상태")
            for service, status in health['checks'].items():
                status_icon = "✅" if status == "healthy" else "⚠️" if status == "not_configured" else "❌"
                st.write(f"{status_icon} {service}: {status}")
                
    except Exception as e:
        st.error(f"❌ 시스템 정보 조회 실패: {str(e)}")

def generate_mock_chart_data(trade_count):
    """모의 차트 데이터 생성"""
    import numpy as np
    
    times = pd.date_range(start=datetime.now() - timedelta(hours=1), periods=trade_count, freq='2min')
    base_balance = 1000000
    changes = np.random.randn(trade_count).cumsum() * 5000
    balances = base_balance + changes
    
    return pd.DataFrame({
        'time': times,
        'balance': balances
    })

if __name__ == "__main__":
    main()
