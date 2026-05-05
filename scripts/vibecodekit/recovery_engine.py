"""Back-compat shim — canonical code lives in ``_standalone.recovery_engine``.

**STANDALONE / DEMO MODE ONLY** — in production Claude Code / Cursor
context, the host agent provides its own recovery mechanism.  This module
is kept for backward compatibility; all functionality lives in
``vibecodekit._standalone.recovery_engine``.
"""
from __future__ import annotations

from ._standalone.recovery_engine import (  # noqa: F401
    LEVELS,
    RecoveryLedger,
    _main,
)
