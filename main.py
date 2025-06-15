
#!/usr/bin/env python3
"""
🚀 트레이딩 시뮬레이터 메인 애플리케이션
암호화폐 거래 전략 백테스팅 및 시뮬레이션 플랫폼
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import streamlit.web.cli as stcli
import sys
import threading
import time
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import get_settings
from src.core.logging_config import setup_logging
from src.api.main import create_app

def run_streamlit():
    """Streamlit 대시보드 실행"""
    sys.argv = ["streamlit", "run", "src/ui/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
    stcli.main()

def run_fastapi():
    """FastAPI 서버 실행"""
    settings = get_settings()
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower()
    )

def main():
    """메인 애플리케이션 시작점"""
    # 로깅 설정
    setup_logging()
    
    print("🚀 트레이딩 시뮬레이터 시작 중...")
    print("📊 FastAPI 서버: http://0.0.0.0:8000")
    print("📈 Streamlit 대시보드: http://0.0.0.0:8501")
    
    # Streamlit을 별도 스레드에서 실행
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # 잠시 대기 후 FastAPI 실행
    time.sleep(2)
    run_fastapi()

if __name__ == "__main__":
    main()
