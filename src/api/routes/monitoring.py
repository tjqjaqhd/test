
"""
📊 모니터링 API 라우터
시스템 상태 및 헬스체크
"""

from fastapi import APIRouter, HTTPException
import psutil
import os
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check():
    """전체 시스템 헬스체크"""
    try:
        checks = {}
        
        # API 서버 상태
        checks["api_server"] = "healthy"
        
        # 데이터베이스 연결 체크 (현재는 사용하지 않음)
        checks["database"] = "not_configured"
        
        # 거래소 연결 체크
        try:
            from src.services.exchange_service import exchange_service
            # 업비트 연결 테스트
            price = await exchange_service.get_current_price("BTC/KRW", "upbit")
            checks["exchange_upbit"] = "healthy" if price else "unhealthy"
        except Exception as e:
            checks["exchange_upbit"] = f"error: {str(e)[:50]}"
        
        # 메모리 사용량 체크
        memory = psutil.virtual_memory()
        checks["memory"] = "healthy" if memory.percent < 90 else "warning"
        
        # 디스크 사용량 체크
        disk = psutil.disk_usage('/')
        checks["disk"] = "healthy" if disk.percent < 90 else "warning"
        
        # 전체 상태 결정
        overall_status = "healthy"
        if any("error" in str(status) or status == "unhealthy" for status in checks.values()):
            overall_status = "unhealthy"
        elif any(status == "warning" for status in checks.values()):
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "uptime_seconds": get_uptime_seconds()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/system")
async def get_system_info():
    """시스템 리소스 정보"""
    try:
        # CPU 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        
        # 디스크 정보
        disk = psutil.disk_usage('/')
        
        # 프로세스 정보
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory": {
                    "total_gb": round(memory.total / 1024**3, 2),
                    "available_gb": round(memory.available / 1024**3, 2),
                    "used_gb": round(memory.used / 1024**3, 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1024**3, 2),
                    "free_gb": round(disk.free / 1024**3, 2),
                    "used_gb": round(disk.used / 1024**3, 2),
                    "percent": disk.percent
                }
            },
            "process": process_info,
            "uptime_seconds": get_uptime_seconds()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 정보 조회 실패: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """상세 메트릭 정보"""
    try:
        # 네트워크 통계
        net_io = psutil.net_io_counters()
        
        # 부팅 시간
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # 로드 평균 (Linux/Unix만)
        load_avg = None
        try:
            load_avg = os.getloadavg()
        except (OSError, AttributeError):
            load_avg = None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "system": {
                "boot_time": boot_time.isoformat(),
                "load_average": load_avg
            },
            "python": {
                "version": os.sys.version,
                "executable": os.sys.executable
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메트릭 조회 실패: {str(e)}")

@router.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """최근 로그 조회"""
    try:
        # 로그 파일 경로 (실제 구현 시 설정에서 가져와야 함)
        log_files = [
            "logs/app.log",
            "logs/error.log"
        ]
        
        logs = []
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        file_lines = f.readlines()
                        recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                        for line in recent_lines:
                            logs.append({
                                "file": log_file,
                                "content": line.strip(),
                                "timestamp": datetime.now().isoformat()  # 실제로는 로그에서 파싱해야 함
                            })
                except Exception as e:
                    logs.append({
                        "file": log_file,
                        "content": f"로그 파일 읽기 오류: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {str(e)}")

def get_uptime_seconds() -> float:
    """서버 업타임 계산"""
    try:
        # 프로세스 시작 시간 기준
        process = psutil.Process()
        start_time = process.create_time()
        return datetime.now().timestamp() - start_time
    except:
        return 0.0
