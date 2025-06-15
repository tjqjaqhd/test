
"""
📝 로깅 설정
구조화된 로깅 시스템
"""

import sys
import logging
from pathlib import Path
from loguru import logger
from datetime import datetime

from src.core.config import get_settings

def setup_logging():
    """로깅 시스템 설정"""
    settings = get_settings()
    
    # 기본 로깅 제거
    logger.remove()
    
    # 로그 디렉토리 생성
    log_dir = settings.logs_dir
    log_dir.mkdir(exist_ok=True)
    
    # 콘솔 로깅
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # 파일 로깅 - 일반 로그
    logger.add(
        log_dir / "trading_simulator.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # 파일 로깅 - 에러 로그
    logger.add(
        log_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="90 days",
        compression="zip"
    )
    
    # 파일 로깅 - 거래 로그
    logger.add(
        log_dir / "trading.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[trade_type]} | {extra[symbol]} | {message}",
        level="INFO",
        rotation="1 day",
        retention="1 year",
        filter=lambda record: "trade_type" in record["extra"]
    )
    
    logger.info("✅ 로깅 시스템 초기화 완료")

def get_logger(name: str):
    """로거 인스턴스 반환"""
    return logger.bind(name=name)

def log_trade(trade_type: str, symbol: str, message: str):
    """거래 전용 로깅"""
    logger.bind(trade_type=trade_type, symbol=symbol).info(message)

# 성능 모니터링 데코레이터
def log_performance(func):
    """함수 실행 시간 로깅 데코레이터"""
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"⚡ {func.__name__} 실행 완료 - {execution_time:.2f}초")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} 실행 실패 - {execution_time:.2f}초 - 오류: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"⚡ {func.__name__} 실행 완료 - {execution_time:.2f}초")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} 실행 실패 - {execution_time:.2f}초 - 오류: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

import asyncio
