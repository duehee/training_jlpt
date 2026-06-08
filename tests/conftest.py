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
