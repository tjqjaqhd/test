
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

# 로거 초기화
logger = get_logger(__name__)
settings = get_settings()

def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    
    app = FastAPI(
        title="🚀 트레이딩 시뮬레이터 API",
        description="실시간 암호화폐 트레이딩 시뮬레이션 & 백테스팅 플랫폼",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
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
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        
        # 요청 로깅
        logger.info(f"📥 {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        return response
    
    # 라우터 등록
    app.include_router(simulation_router)
    app.include_router(monitoring_router)
    
    # 헬스체크 엔드포인트
    @app.get("/health")
    async def health_check():
        """서버 상태 확인"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "mode": "simulation" if settings.simulation_mode else "live"
        }
    
    # 루트 엔드포인트
    @app.get("/")
    async def root():
        """API 정보"""
        return {
            "message": "🚀 트레이딩 시뮬레이터 API",
            "docs": "/docs",
            "health": "/health",
            "simulation_mode": settings.simulation_mode
        }
    
    # 예외 핸들러
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"❌ Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    
    logger.info("✅ FastAPI 애플리케이션 초기화 완료")
    return app

# 애플리케이션 인스턴스
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 서버 시작: http://{settings.api_host}:{settings.api_port}")
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
