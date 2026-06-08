"""모든 ORM 모델을 여기서 import해 Base.metadata에 등록한다.

⚠️ Alembic autogenerate가 모델을 감지하려면 새 모델 파일 추가 시
반드시 이 파일에 import를 추가해야 한다.
"""

from src.db.models.base import Base
from src.db.models.cache import LlmResponseCache
from src.db.models.content import Chunk, ComparisonPair
from src.db.models.diagnostic import (
    AnonymousSession,
    DiagnosticAnswer,
    DiagnosticQuestion,
    DiagnosticSession,
)
from src.db.models.learning import (
    LastSession,
    LearningRecord,
    LearningSession,
    User,
    WeakPoint,
)

__all__ = [
    "Base",
    "Chunk",
    "ComparisonPair",
    "AnonymousSession",
    "DiagnosticSession",
    "DiagnosticQuestion",
    "DiagnosticAnswer",
    "User",
    "LearningSession",
    "LearningRecord",
    "WeakPoint",
    "LastSession",
    "LlmResponseCache",
]
