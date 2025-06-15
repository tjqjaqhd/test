
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
import atexit

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
        
        # Streamlit 실행 명령어 수정
        cmd = [
            "python", "-m", "streamlit", "run", "src/ui/dashboard.py",
            "--server.port=5000",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.enableCORS=true",
            "--server.enableXsrfProtection=false",
            "--server.enableWebsocketCompression=false",
            "--server.allowRunOnSave=false",
            "--server.runOnSave=false",
            "--client.showErrorDetails=false"
        ]
        
        streamlit_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Streamlit 출력 모니터링
        for line in iter(streamlit_process.stdout.readline, ''):
            if line:
                print(f"[Streamlit] {line.strip()}")
                if "You can now view your Streamlit app" in line:
                    print("✅ Streamlit 대시보드가 성공적으로 시작되었습니다!")
                    
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
        access_log=True,
        reload=False
    )

def cleanup():
    """정리 작업"""
    global streamlit_process
    if streamlit_process:
        print("🧹 Streamlit 프로세스를 정리합니다...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()

def signal_handler(signum, frame):
    """시그널 핸들러 - 깔끔한 종료"""
    print("\n🛑 애플리케이션을 종료합니다...")
    cleanup()
    sys.exit(0)

def check_port_availability(port):
    """포트 사용 가능 여부 확인"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except:
        return False

def main():
    """메인 애플리케이션 시작점"""
    # 포트 사용 가능 여부 확인
    if not check_port_availability(5000):
        print("⚠️ 포트 5000이 사용 중입니다. 기존 프로세스를 종료합니다...")
        os.system("pkill -f streamlit")
        time.sleep(2)
    
    if not check_port_availability(8000):
        print("⚠️ 포트 8000이 사용 중입니다. 기존 프로세스를 종료합니다...")
        os.system("pkill -f uvicorn")
        time.sleep(2)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # 로깅 설정
    setup_logging()
    
    print("=" * 60)
    print("🚀 트레이딩 시뮬레이터 시작 중...")
    print("=" * 60)
    print("📊 FastAPI 서버: http://0.0.0.0:8000")
    print("📈 Streamlit 대시보드: http://0.0.0.0:5000")
    print("📚 API 문서: http://0.0.0.0:8000/docs")
    print("🌐 웹뷰에서 접근: 오른쪽 상단의 'Open in new tab' 클릭")
    print("=" * 60)
    
    # Streamlit을 별도 스레드에서 실행
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # 충분한 대기 시간과 상태 확인
    print("⏳ Streamlit 초기화를 기다리는 중...")
    time.sleep(5)
    
    # Streamlit 서버 준비 확인
    streamlit_ready = False
    for i in range(10):
        try:
            import requests
            response = requests.get("http://127.0.0.1:5000", timeout=2)
            if response.status_code == 200:
                streamlit_ready = True
                print("✅ Streamlit 서버 준비 완료!")
                break
        except:
            pass
        time.sleep(1)
    
    if not streamlit_ready:
        print("⚠️ Streamlit 서버 확인 실패 - 계속 진행합니다...")
    
    try:
        run_fastapi()
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
