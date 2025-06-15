
"""
📝 로깅 설정
구조화된 로그 및 다양한 출력 형식 지원
"""

import logging
import sys
from pathlib import Path
from loguru import logger
from src.core.config import get_settings

def setup_logging():
    """로깅 시스템 초기화"""
    settings = get_settings()
    
    # 기본 로깅 제거
    logger.remove()
    
    # 콘솔 로그 설정 (개발용)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # 파일 로그 설정
    logs_dir = settings.logs_dir
    logs_dir.mkdir(exist_ok=True)
    
    # 일반 로그
    logger.add(
        logs_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 에러 로그
    logger.add(
        logs_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 트레이딩 전용 로그
    logger.add(
        logs_dir / "trading.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[strategy]} | {message}",
        level="INFO",
        filter=lambda record: "strategy" in record["extra"],
        rotation="1 day",
        retention="90 days"
    )
    
    logger.info("🚀 로깅 시스템 초기화 완료")
    return logger

def get_logger(name: str):
    """특정 모듈용 로거 반환"""
    return logger.bind(module=name)
