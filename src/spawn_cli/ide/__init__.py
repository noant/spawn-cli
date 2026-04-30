from __future__ import annotations

from . import registry  # noqa: F401
from . import _stub  # noqa: F401 — load stubs before concrete adapters
from . import cursor  # noqa: F401
from . import claude_code  # noqa: F401
from . import codex  # noqa: F401
from . import gemini_cli  # noqa: F401
from . import github_copilot  # noqa: F401
from . import windsurf  # noqa: F401
from ._stub import StubAdapter
from .claude_code import ClaudeCodeAdapter
from .codex import CodexAdapter
from .cursor import CursorAdapter
from .gemini_cli import GeminiCliAdapter
from .github_copilot import GitHubCopilotAdapter
from .windsurf import WindsurfAdapter
from .registry import (
    ALIASES,
    IGNORE_BLOCK_END,
    IGNORE_BLOCK_START,
    SPAWN_BLOCK_END,
    SPAWN_BLOCK_START,
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    detect_supported_ides,
    get,
    normalize_skill_name,
    register,
    remove_ignore_block,
    render_skill_md,
    rewrite_ignore_block,
    rewrite_managed_block,
    supported_ide_keys,
)

__all__ = [
    "ALIASES",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "CursorAdapter",
    "GeminiCliAdapter",
    "GitHubCopilotAdapter",
    "DetectResult",
    "IGNORE_BLOCK_END",
    "IGNORE_BLOCK_START",
    "IdeAdapter",
    "IdeCapabilities",
    "SPAWN_BLOCK_END",
    "SPAWN_BLOCK_START",
    "StubAdapter",
    "WindsurfAdapter",
    "detect_supported_ides",
    "get",
    "normalize_skill_name",
    "register",
    "remove_ignore_block",
    "render_skill_md",
    "rewrite_ignore_block",
    "rewrite_managed_block",
    "supported_ide_keys",
]
