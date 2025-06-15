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
import numpy as np
import random

# 페이지 설정
st.set_page_config(
    page_title="🔥 암호화폐 트레이딩 시뮬레이터",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.api_retries = 0

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
        box_shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4ECDC4;
    }

    .status-running { color: #28a745; }
    .status-completed { color: #007bff; }
    .status-stopped { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# API 베이스 URL - 실제 서버 주소 사용
API_BASE_URL = "http://0.0.0.0:8000/api/v1"

def check_api_connection():
    """API 서버 연결 확인"""
    try:
        # 여러 방법으로 연결 시도
        urls_to_try = [
            "http://0.0.0.0:8000/health",
            "http://localhost:8000/health",
            "http://127.0.0.1:8000/health"
        ]

        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    global API_BASE_URL
                    API_BASE_URL = url.replace("/health", "/api/v1")
                    return True
            except:
                continue
        return False
    except:
        return False

def main():
    """메인 대시보드"""

    # 헤더
    st.markdown('<h1 class="main-header">🔥 암호화폐 트레이딩 시뮬레이터</h1>', unsafe_allow_html=True)

    # API 연결 상태 확인
    api_connected = check_api_connection()
    if not api_connected:
        st.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        st.info("💡 메인 터미널에서 'python main.py'가 실행 중인지 확인하세요.")
        return

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

        # 현재 시뮬레이션 상태 표시
        if "simulation_id" in st.session_state:
            st.divider()
            st.subheader("현재 시뮬레이션")
            st.code(f"ID: {st.session_state.simulation_id[:8]}...")
            if st.button("🛑 시뮬레이션 중지", type="secondary"):
                stop_simulation()

    # 메인 컨텐츠
    tab1, tab2, tab3, tab4 = st.tabs(["📊 실시간 모니터링", "📈 백테스팅", "📋 거래 기록", "⚙️ 시스템 상태"])

    with tab1:
        try:
            show_realtime_monitoring()
        except Exception as e:
            st.error(f"실시간 모니터링 오류: {str(e)}")

    with tab2:
        try:
            show_backtesting()
        except Exception as e:
            st.error(f"백테스팅 오류: {str(e)}")

    with tab3:
        try:
            show_trade_history()
        except Exception as e:
            st.error(f"거래 기록 오류: {str(e)}")

    with tab4:
        try:
            show_system_status()
        except Exception as e:
            st.error(f"시스템 상태 오류: {str(e)}")

def start_simulation(strategy, symbol, initial_balance, duration_hours):
    """시뮬레이션 시작"""
    try:
        with st.spinner("시뮬레이션을 시작하는 중..."):
            response = requests.post(f"{API_BASE_URL}/simulation/start", json={
                "strategy": strategy,
                "symbol": symbol,
                "initial_balance": initial_balance,
                "duration_hours": duration_hours
            }, timeout=10)

        if response.status_code == 200:
            result = response.json()
            st.session_state.simulation_id = result["simulation_id"]
            st.success(f"✅ 시뮬레이션이 시작되었습니다! ID: {result['simulation_id'][:8]}...")
            st.rerun()
        else:
            st.error(f"❌ 시뮬레이션 시작 실패: {response.text}")
    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과: 서버 응답이 느립니다.")
    except Exception as e:
        st.error(f"❌ 시뮬레이션 시작 오류: {str(e)}")

def stop_simulation():
    """시뮬레이션 중지"""
    try:
        response = requests.delete(f"{API_BASE_URL}/simulation/{st.session_state.simulation_id}")
        if response.status_code == 200:
            st.success("✅ 시뮬레이션이 중지되었습니다.")
            del st.session_state.simulation_id
            st.rerun()
    except Exception as e:
        st.error(f"❌ 시뮬레이션 중지 오류: {str(e)}")

def show_realtime_monitoring():
    """실시간 모니터링 화면"""
    st.subheader("📊 실시간 시뮬레이션 모니터링")

    if "simulation_id" not in st.session_state:
        st.info("👈 사이드바에서 시뮬레이션을 시작해주세요.")

        # 실시간 시장 데이터 표시
        st.subheader("📈 실시간 시장 데이터")
        selected_symbol = st.selectbox(
            "거래쌍 선택",
            ["BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW"],
            key="market_symbol"
        )
        
        market_data = fetch_real_market_data(selected_symbol)
        
        # 현재 가격 및 통계 표시
        if market_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                price = market_data.get('current_price', 0)
                st.metric("현재 가격", f"{price:,.0f}원" if price > 1000 else f"{price:.2f}원")
            
            with col2:
                stats = market_data.get('stats', {})
                change = stats.get('change', 0)
                st.metric("전일 대비", f"{change:+,.0f}원" if abs(change) > 1 else f"{change:+.4f}원")
            
            with col3:
                percentage = stats.get('percentage', 0)
                st.metric("변동률", f"{percentage:+.2f}%")
            
            with col4:
                data_source = market_data.get('data_source', 'unknown')
                source_icon = "🔴" if data_source == 'real' else "🟡"
                st.metric("데이터", f"{source_icon} {data_source.upper()}")
            
            # 차트 표시
            chart_data = market_data.get('chart_data', [])
            if chart_data:
                df = pd.DataFrame(chart_data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df['price'],
                    mode='lines+markers',
                    name=f'{selected_symbol} 가격',
                    line=dict(color='#4ECDC4', width=3),
                    marker=dict(size=4)
                ))

                fig.update_layout(
                    title=f"💰 {selected_symbol} 가격 차트",
                    xaxis_title="시간",
                    yaxis_title="가격 (원)" if "KRW" in selected_symbol else "가격",
                    template="plotly_white",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", key="refresh_market"):
            st.rerun()
        return

    # 시뮬레이션 상태 조회
    try:
        response = requests.get(f"{API_BASE_URL}/simulation/status/{st.session_state.simulation_id}", timeout=5)
        if response.status_code == 200:
            status = response.json()

            # 메트릭 표시
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                profit_loss = status.get('profit_loss', 0)
                st.metric(
                    "현재 잔고",
                    f"{status.get('current_balance', 0):,.0f}원",
                    f"{profit_loss:+,.0f}원"
                )

            with col2:
                profit_rate = status.get('profit_rate', 0)
                st.metric(
                    "수익률",
                    f"{profit_rate:+.2f}%",
                    f"{profit_rate:+.2f}%"
                )

            with col3:
                st.metric("거래 횟수", f"{status.get('trade_count', 0)}회")

            with col4:
                status_text = status.get('status', 'unknown')
                status_color = {
                    "running": "🟢",
                    "completed": "🔵",
                    "stopped": "🔴"
                }.get(status_text, "⚪")
                st.metric("상태", f"{status_color} {status_text}")

            # 실시간 차트
            if status.get('trade_count', 0) > 0:
                chart_data = generate_mock_chart_data(status['trade_count'], status['initial_balance'])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=chart_data['time'],
                    y=chart_data['balance'],
                    mode='lines+markers',
                    name='잔고 변화',
                    line=dict(color='#4ECDC4', width=3),
                    marker=dict(size=4)
                ))

                fig.update_layout(
                    title="💰 실시간 잔고 변화",
                    xaxis_title="시간",
                    yaxis_title="잔고 (원)",
                    template="plotly_white",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

            # 자동 새로고침 (5초마다)
            if status.get('status') == 'running':
                time.sleep(5)
                st.rerun()

    except requests.exceptions.Timeout:
        st.error("❌ 서버 응답 시간 초과")
    except Exception as e:
        st.error(f"❌ 데이터 조회 실패: {str(e)}")

def show_backtesting():
    """백테스팅 화면"""
    st.subheader("📈 백테스팅")

    col1, col2 = st.columns(2)

    with col1:
        bt_strategy = st.selectbox("전략", ["arbitrage", "short_trading", "leverage_trading"], key="bt_strategy")
        bt_symbol = st.selectbox("거래쌍", ["BTC/KRW", "ETH/KRW", "XRP/KRW"], key="bt_symbol")

    with col2:
        bt_start_date = st.date_input("시작 날짜", datetime.now() - timedelta(days=30))
        bt_end_date = st.date_input("종료 날짜", datetime.now())

    bt_initial_balance = st.number_input("초기 자본금", value=1000000, step=100000, key="bt_balance")

    if st.button("🔍 백테스팅 실행", type="secondary"):
        with st.spinner("백테스팅 실행 중..."):
            try:
                response = requests.post(f"{API_BASE_URL}/simulation/backtest", json={
                    "strategy": bt_strategy,
                    "symbol": bt_symbol,
                    "start_date": bt_start_date.isoformat() + "T00:00:00",
                    "end_date": bt_end_date.isoformat() + "T23:59:59",
                    "initial_balance": bt_initial_balance
                }, timeout=15)

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

                else:
                    st.error(f"❌ 백테스팅 실패: {response.text}")

            except Exception as e:
                st.error(f"❌ 백테스팅 실패: {str(e)}")

def show_trade_history():
    """거래 기록 화면"""
    st.subheader("📋 거래 기록")

    # 모의 거래 데이터
    mock_trades = pd.DataFrame({
        '시간': pd.date_range(start='2024-01-01', periods=20, freq='h'),
        '거래쌍': ['BTC/KRW'] * 20,
        '매수/매도': (['매수', '매도'] * 10)[:20],
        '수량': ([0.001, 0.0015, 0.002] * 7)[:20],
        '가격': [50000000 + i*100000 for i in range(20)],
        '손익': ([5000, -3000, 8000, -2000, 12000] * 4)[:20]
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
        # 시스템 정보 조회
        response = requests.get(f"{API_BASE_URL}/monitoring/system", timeout=5)
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
        response = requests.get(f"{API_BASE_URL}/monitoring/health", timeout=5)
        if response.status_code == 200:
            health = response.json()

            st.subheader("🏥 서비스 상태")
            for service, status in health['checks'].items():
                status_icon = "✅" if status == "healthy" else "⚠️" if status == "not_configured" else "❌"
                st.write(f"{status_icon} {service}: {status}")

    except Exception as e:
        st.error(f"❌ 시스템 정보 조회 실패: {str(e)}")

def fetch_real_market_data(symbol: str = "BTC/KRW"):
    """실제 시장 데이터 조회"""
    try:
        # 1. 현재 가격 조회
        price_response = requests.get(f"{API_BASE_URL}/market/price/{symbol}", timeout=5)
        if price_response.status_code == 200:
            price_data = price_response.json()
            
            # 2. 24시간 통계 조회
            stats_response = requests.get(f"{API_BASE_URL}/market/stats/{symbol}", timeout=5)
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                
                # 3. OHLCV 데이터 조회
                ohlcv_response = requests.get(f"{API_BASE_URL}/market/ohlcv/{symbol}?limit=24", timeout=5)
                if ohlcv_response.status_code == 200:
                    ohlcv_data = ohlcv_response.json()
                    
                    # 차트용 데이터 생성
                    chart_data = []
                    for item in ohlcv_data.get('data', []):
                        chart_data.append({
                            'time': pd.to_datetime(item['datetime']),
                            'price': item['close'],
                            'volume': item['volume']
                        })
                    
                    return {
                        'current_price': price_data.get('price'),
                        'stats': stats_data.get('stats', {}),
                        'chart_data': chart_data,
                        'symbol': symbol,
                        'data_source': 'real'
                    }
        
        # API 연결 실패 시 알림
        st.warning(f"⚠️ {symbol} 실시간 데이터 조회 실패 - 데모 데이터로 표시")
        
    except requests.exceptions.Timeout:
        st.warning("⏰ 데이터 조회 시간 초과 - 데모 데이터로 표시")
    except requests.exceptions.ConnectionError:
        st.warning("🔌 서버 연결 실패 - 데모 데이터로 표시")
    except Exception as e:
        st.warning(f"❌ 데이터 조회 오류: {str(e)[:50]} - 데모 데이터로 표시")

    # 실패시 데모 데이터 반환
    return generate_demo_data(symbol)

def generate_demo_data(symbol: str = "BTC/KRW"):
    """데모 차트 데이터 생성 (백업용)"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=1), periods=24, freq='h')
    
    # 심볼별 기본 가격 설정
    base_prices = {
        "BTC/KRW": 50000000,
        "ETH/KRW": 3000000,
        "XRP/KRW": 1000,
        "ADA/KRW": 500
    }
    
    base_price = base_prices.get(symbol, 1000000)
    prices = []
    volumes = []

    for i in range(len(dates)):
        # 현실적인 가격 변동 (-3% ~ +3%)
        change = random.uniform(-0.03, 0.03)
        base_price *= (1 + change)
        prices.append(base_price)
        
        # 거래량 생성
        volumes.append(random.uniform(100, 1000))

    chart_data = []
    for i, date in enumerate(dates):
        chart_data.append({
            'time': date,
            'price': prices[i],
            'volume': volumes[i]
        })

    return {
        'current_price': prices[-1],
        'stats': {
            'price': prices[-1],
            'change': prices[-1] - prices[0],
            'percentage': ((prices[-1] - prices[0]) / prices[0]) * 100,
            'high': max(prices),
            'low': min(prices),
            'volume': sum(volumes)
        },
        'chart_data': chart_data,
        'symbol': symbol,
        'data_source': 'demo'
    }

def generate_mock_chart_data(trade_count, initial_balance):
    """모의 차트 데이터 생성"""
    times = pd.date_range(start=datetime.now() - timedelta(hours=1), periods=trade_count, freq='2min')
    changes = np.random.randn(trade_count).cumsum() * 2000
    balances = initial_balance + changes

    return pd.DataFrame({
        'time': times,
        'balance': balances
    })

if __name__ == "__main__":
    main()