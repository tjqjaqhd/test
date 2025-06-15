
"""
⚠️ 사용자 정의 예외 클래스
"""

class TradingSimulatorException(Exception):
    """트레이딩 시뮬레이터 기본 예외"""
    pass

class ExchangeConnectionError(TradingSimulatorException):
    """거래소 연결 오류"""
    pass

class DataNotFoundError(TradingSimulatorException):
    """데이터 없음 오류"""
    pass

class SimulationError(TradingSimulatorException):
    """시뮬레이션 실행 오류"""
    pass

class InvalidParameterError(TradingSimulatorException):
    """잘못된 파라미터 오류"""
    pass
