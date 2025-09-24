# src/cosmicanimator/application/narration/__init__.py
from .contracts import NarrationResult, WordTiming
from .tts import VoiceScene
from .orchestra import Orchestra, ensure_orchestra
from .subtitle import SubtitleOverlay
from .policy import SubtitlePolicy
from .scheduler import SubtitleScheduler

__all__ = [
    "VoiceScene",
    "Orchestra",
    "ensure_orchestra",
    "SubtitleOverlay",
    "SubtitleScheduler",
    "SubtitlePolicy",
    "NarrationResult",
    "WordTiming",
]
