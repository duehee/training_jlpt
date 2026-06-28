"""Jinja2 템플릿 단일 인스턴스.

템플릿 디렉터리는 `src/web/templates/`(하린 트랙 산출물). 본 모듈은 라우터에서
공유하는 `templates` 객체만 제공한다.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates: Jinja2Templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))
