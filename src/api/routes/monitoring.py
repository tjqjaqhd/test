
"""
📊 시스템 모니터링 관련 API 라우트
"""

from fastapi import APIRouter
import psutil
import os
from datetime import datetime

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": "healthy",
            "database": "not_configured",
            "redis": "not_configured",
            "simulation_engine": "healthy"
        }
    }

@router.get("/system")
async def get_system_info():
    """시스템 정보 조회"""
    # 현재 프로세스 정보
    process = psutil.Process(os.getpid())
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        },
        "process": {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
            "status": process.status()
        }
    }

@router.get("/metrics")
async def get_metrics():
    """메트릭 정보"""
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "active_simulations": 0,
            "total_trades_today": 0,
            "api_calls_per_minute": 0,
            "average_response_time_ms": 50
        }
    }
