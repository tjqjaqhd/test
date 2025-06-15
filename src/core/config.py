
"""
⚙️ 설정 관리 모듈
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 애플리케이션 설정
    app_name: str = "Trading Simulator"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 5000
    
    # 데이터베이스 설정
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "trading_simulator"
    db_user: str = "user"
    db_password: str = "password"
    
    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # 보안 설정
    secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # 거래소 API 키
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    binance_testnet: bool = True
    
    upbit_access_key: Optional[str] = None
    upbit_secret_key: Optional[str] = None
    
    bithumb_api_key: Optional[str] = None
    bithumb_secret_key: Optional[str] = None
    
    # AI/ML 설정
    huggingface_api_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # 로깅 설정
    log_level: str = "INFO"
    log_file_path: str = "logs/trading_simulator.log"
    
    # 모니터링 설정
    prometheus_port: int = 9090
    grafana_port: int = 3000
    grafana_admin_user: str = "admin"
    grafana_admin_password: str = "admin"
    
    # 성능 설정
    max_websocket_connections: int = 100
    rate_limit_per_minute: int = 60
    price_cache_ttl: int = 10
    analysis_cache_ttl: int = 300
    
    # 알림 설정
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_url_complete(self) -> str:
        """완전한 데이터베이스 URL 생성"""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url_complete(self) -> str:
        """완전한 Redis URL 생성"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return not self.debug
    
    def get_exchange_config(self, exchange: str) -> dict:
        """거래소별 설정 반환"""
        configs = {
            "binance": {
                "apiKey": self.binance_api_key,
                "secret": self.binance_secret_key,
                "sandbox": self.binance_testnet,
                "enableRateLimit": True,
            },
            "upbit": {
                "apiKey": self.upbit_access_key,
                "secret": self.upbit_secret_key,
                "enableRateLimit": True,
            },
            "bithumb": {
                "apiKey": self.bithumb_api_key,
                "secret": self.bithumb_secret_key,
                "enableRateLimit": True,
            }
        }
        return configs.get(exchange, {})


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
