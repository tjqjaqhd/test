
"""
📊 시스템 모니터링 관련 API 라우트
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

from src.core.logging_config import get_logger
from src.core.config import get_settings

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])
logger = get_logger(__name__)
settings = get_settings()

@router.get("/system")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "application": {
                "simulation_mode": settings.simulation_mode,
                "debug": settings.debug,
                "log_level": settings.log_level
            }
        }
    except Exception as e:
        logger.error(f"시스템 상태 조회 오류: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        }

@router.get("/logs")
async def get_recent_logs():
    """최근 로그 조회"""
    try:
        log_file = "logs/app.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-50:]  # 최근 50줄
                return {
                    "timestamp": datetime.now().isoformat(),
                    "log_count": len(recent_lines),
                    "logs": [line.strip() for line in recent_lines]
                }
        else:
            return {
                "timestamp": datetime.now().isoformat(),
                "log_count": 0,
                "logs": [],
                "message": "로그 파일이 존재하지 않습니다"
            }
    except Exception as e:
        logger.error(f"로그 조회 오류: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/performance")
async def get_performance_metrics():
    """성능 지표 조회"""
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "uptime": "실행 중",
                "requests_per_minute": "N/A",
                "avg_response_time": "N/A",
                "error_rate": "N/A"
            },
            "services": {
                "exchange_service": "연결됨",
                "ai_service": "활성화",
                "database": "N/A (메모리 사용)"
            }
        }
    except Exception as e:
        logger.error(f"성능 지표 조회 오류: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
