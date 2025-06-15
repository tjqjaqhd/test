
#!/usr/bin/env python3
"""
🚀 트레이딩 시뮬레이터 메인 애플리케이션
암호화폐 거래 전략 백테스팅 및 시뮬레이션 플랫폼
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import threading
import time
from pathlib import Path
import os
import signal

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import get_settings
from src.core.logging_config import setup_logging
from src.api.main import create_app

# 전역 변수로 프로세스 관리
streamlit_process = None

def run_streamlit():
    """Streamlit 대시보드 실행"""
    global streamlit_process
    try:
        print("🚀 Streamlit 대시보드를 시작합니다... (포트: 5000)")
        streamlit_process = subprocess.Popen([
            "streamlit", "run", "src/ui/dashboard.py",
            "--server.port=5000",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--theme.base=dark"
        ])
        streamlit_process.wait()
    except Exception as e:
        print(f"❌ Streamlit 실행 오류: {e}")

def run_fastapi():
    """FastAPI 서버 실행"""
    settings = get_settings()
    app = create_app()
    
    print("🚀 FastAPI 서버를 시작합니다... (포트: 8000)")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        access_log=True
    )

def signal_handler(signum, frame):
    """시그널 핸들러 - 깔끔한 종료"""
    print("\n🛑 애플리케이션을 종료합니다...")
    global streamlit_process
    if streamlit_process:
        streamlit_process.terminate()
        streamlit_process.wait()
    sys.exit(0)

def main():
    """메인 애플리케이션 시작점"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 로깅 설정
    setup_logging()
    
    print("=" * 60)
    print("🚀 트레이딩 시뮬레이터 시작 중...")
    print("=" * 60)
    print("📊 FastAPI 서버: http://0.0.0.0:8000")
    print("📈 Streamlit 대시보드: http://0.0.0.0:5000")
    print("📚 API 문서: http://0.0.0.0:8000/docs")
    print("=" * 60)
    
    # Streamlit을 별도 스레드에서 실행
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # 잠시 대기 후 FastAPI 실행
    print("⏳ Streamlit 초기화 대기 중...")
    time.sleep(5)
    
    try:
        run_fastapi()
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")
    finally:
        # 정리 작업
        global streamlit_process
        if streamlit_process:
            streamlit_process.terminate()

if __name__ == "__main__":
    main()
