"""pytest 공통 설정.

프로젝트 루트를 sys.path에 추가해 `import src.*` 가 어떤 실행 위치에서도 동작하게 한다.
(pyproject.toml의 [tool.pytest.ini_options] pythonpath 설정 대안 — pyproject 읽기전용 대응)
"""

import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트가 실제 SMTP로 메일을 보내지 않도록 강제(콘솔 백엔드).

    .env에 SMTP_HOST가 설정돼 있으면 get_email_sender()가 SmtpEmailSender를 반환해
    회원가입 테스트가 존재하지 않는 @example.com 주소로 실발송→반송을 유발한다.
    smtp_host를 None으로 눌러 전 테스트에서 ConsoleEmailSender(무발송)로 고정한다.
    """
    from src.core.config import settings

    monkeypatch.setattr(settings, "smtp_host", None)
