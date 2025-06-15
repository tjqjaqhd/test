
"""
📊 모니터링 API 라우트
시스템 상태 및 성능 모니터링 엔드포인트
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

from src.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/system")
async def get_system_info():
    """시스템 정보 조회"""
    return {
        "timestamp": datetime.now(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        },
        "process": {
            "pid": os.getpid(),
            "cpu_percent": psutil.Process().cpu_percent(),
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }
    }

@router.get("/health")
async def detailed_health_check():
    """상세 헬스체크"""
    checks = {
        "api_server": "healthy",
        "database": "not_configured",
        "redis": "not_configured",
        "external_apis": "not_tested"
    }
    
    overall_status = "healthy" if all(
        status in ["healthy", "not_configured"] for status in checks.values()
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(),
        "checks": checks
    }

@router.get("/metrics")
async def get_metrics():
    """애플리케이션 메트릭"""
    return {
        "timestamp": datetime.now(),
        "uptime_seconds": 0,  # 실제로는 애플리케이션 시작 시간으로부터 계산
        "total_requests": 0,  # 실제로는 요청 카운터 사용
        "active_simulations": 0,  # 실제로는 활성 시뮬레이션 수
        "total_trades": 0,  # 실제로는 총 거래 수
        "error_count": 0  # 실제로는 에러 카운터 사용
    }
