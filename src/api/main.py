
"""
🌐 FastAPI 메인 애플리케이션
REST API 서버 및 라우팅 설정
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
from pathlib import Path

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
        description="암호화폐 트레이딩 시뮬레이션 및 백테스팅 플랫폼",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용, 운영시에는 특정 도메인만 허용
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
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s"
        )
        return response
    
    # 라우터 등록
    app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["시뮬레이션"])
    app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["모니터링"])
    
    # 헬스체크 엔드포인트
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version
        }
    
    # 루트 엔드포인트
    @app.get("/")
    async def root():
        return {
            "message": f"🚀 {settings.app_name} API 서버",
            "version": settings.app_version,
            "docs": "/docs",
            "dashboard": "http://0.0.0.0:8501"
        }
    
    logger.info("✅ FastAPI 애플리케이션 생성 완료")
    return app
