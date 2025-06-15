
"""
🌐 FastAPI 메인 애플리케이션
REST API 서버 및 라우팅 설정
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from src.core.config import get_settings
from src.core.logging_config import get_logger
from src.api.routes.simulation import router as simulation_router
from src.api.routes.monitoring import router as monitoring_router

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="암호화폐 트레이딩 시뮬레이터 API",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 요청 로깅 미들웨어
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
        return response
    
    # 라우터 등록
    app.include_router(simulation_router)
    app.include_router(monitoring_router)
    
    # 기본 엔드포인트
    @app.get("/")
    async def root():
        return {
            "message": f"🚀 {settings.app_name} API 서버",
            "version": settings.app_version,
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs",
            "health": "/api/v1/monitoring/health"
        }
    
    # 헬스체크 (간단한 버전)
    @app.get("/health")
    async def simple_health():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    logger.info("✅ FastAPI 애플리케이션 생성 완료")
    return app
