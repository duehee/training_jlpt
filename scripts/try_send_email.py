"""일회성 이메일 발송 검증 스크립트 (세션 9).

`.env`에 SMTP 설정(SMTP_HOST 등)을 채운 뒤 실행해 실제 발송을 확인한다.
회원가입 흐름을 타지 않고 발송만 딱 검증한다.

사용법:
    poetry run python scripts/try_send_email.py                 # EMAIL_FROM 주소로
    poetry run python scripts/try_send_email.py you@example.com # 지정 주소로

동작:
- SMTP_HOST 미설정 → ConsoleEmailSender(콘솔 출력, 실발송 X).
- SMTP_HOST 설정 → SmtpEmailSender(aiosmtplib 실발송). 코드 변경 없이 .env로 전환.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings  # noqa: E402
from src.shared.auth.email import (  # noqa: E402
    ConsoleEmailSender,
    get_email_sender,
)


async def main() -> None:
    to = sys.argv[1] if len(sys.argv) > 1 else settings.email_from
    sender = get_email_sender()
    backend = type(sender).__name__

    print(f"backend      = {backend}")
    print(f"smtp_host    = {settings.smtp_host!r}")
    print(f"email_from   = {settings.email_from!r}")
    print(f"to           = {to!r}")

    if isinstance(sender, ConsoleEmailSender):
        print(
            "\n⚠️  SMTP_HOST 미설정 → 콘솔 백엔드입니다(실발송 안 함).\n"
            "    .env에 SMTP_HOST/USERNAME/PASSWORD를 채우면 실발송으로 전환됩니다."
        )

    await sender.send(
        to=to,
        subject="[JLPT] SMTP 발송 테스트",
        body="이 메일이 보이면 SMTP 설정이 정상입니다. 🎉",
    )
    print(f"\n✅ send() 완료 — {to} 확인해 보세요.")


if __name__ == "__main__":
    asyncio.run(main())
