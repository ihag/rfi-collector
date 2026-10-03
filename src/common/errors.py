class RfiError(Exception):
    """사용자에게 메시지를 그대로 보여줄 수 있는, 예상된 오류."""


class ConfigError(RfiError):
    """설정(.env, API 키 등) 문제."""


class ApiError(RfiError):
    """API 호출 실패 또는 비정상 응답."""


class OutputError(RfiError):
    """결과 파일 저장 실패."""
