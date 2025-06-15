
"""
⚙️ 애플리케이션 설정 관리
환경별 설정 및 전역 상수 정의
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "트레이딩 시뮬레이터"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API 설정
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # 데이터베이스 설정
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # 거래소 API 키 (환경변수에서 읽음)
    binance_api_key: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    binance_secret_key: Optional[str] = Field(default=None, env="BINANCE_SECRET_KEY")
    upbit_access_key: Optional[str] = Field(default=None, env="UPBIT_ACCESS_KEY")
    upbit_secret_key: Optional[str] = Field(default=None, env="UPBIT_SECRET_KEY")
    
    # 시뮬레이션 설정
    simulation_mode: bool = Field(default=True, env="SIMULATION_MODE")
    initial_balance: float = Field(default=1000000.0, env="INITIAL_BALANCE")  # 초기 자본금 (원)
    
    # 파일 경로 설정
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent
    
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"
    
    @property
    def config_dir(self) -> Path:
        return self.project_root / "config"
    
    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 전역 설정 인스턴스
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# 상수 정의
class TradingConstants:
    """트레이딩 관련 상수"""
    
    # 수수료율
    BINANCE_MAKER_FEE = 0.001  # 0.1%
    BINANCE_TAKER_FEE = 0.001  # 0.1%
    UPBIT_FEE = 0.0005  # 0.05%
    
    # 최소 거래 금액
    MIN_TRADE_AMOUNT = 5000  # 5천원
    
    # 백테스팅 기본 기간
    DEFAULT_BACKTEST_DAYS = 30
    
    # 지원 거래쌍
    SUPPORTED_PAIRS = [
        "BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW",
        "DOT/KRW", "LINK/KRW", "LTC/KRW", "BCH/KRW"
    ]
