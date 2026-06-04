from dataclasses import dataclass, field
from typing import Optional, Protocol


MAX_TEXT_LENGTH = 500


@dataclass
class EngineInfo:
    name: str
    label: str
    model_loaded: bool = False
    loading: bool = False
    load_error: Optional[str] = None
    device: Optional[str] = None
    voices: list[str] = field(default_factory=list)


class TTSEngine(Protocol):
    name: str
    label: str

    def load(self) -> None: ...

    def is_loaded(self) -> bool: ...

    def is_loading(self) -> bool: ...

    def get_load_error(self) -> Optional[str]: ...

    def get_info(self) -> EngineInfo: ...

    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes: ...
