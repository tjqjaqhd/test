"""
📊 모니터링 관련 API 라우트
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
            "exchange_api": "not_configured"
        }
    }

@router.get("/system")
async def system_status():
    """시스템 상태 조회"""
    # 시스템 메모리 정보
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # 현재 프로세스 정보
    process = psutil.Process(os.getpid())

    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        },
        "process": {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "num_threads": process.num_threads()
        },
        "timestamp": datetime.now().isoformat()
    }