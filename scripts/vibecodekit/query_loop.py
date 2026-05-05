"""Back-compat shim — canonical code lives in ``_standalone.query_loop``.

**STANDALONE / DEMO MODE ONLY** — in production Claude Code / Cursor
context, the host agent provides its own query loop.  This module is
kept for backward compatibility; all functionality lives in
``vibecodekit._standalone.query_loop``.

The ``run_plan`` function and related constants are re-exported so
existing callers (conformance probes, CLI ``demo-run``, tests) keep
working without import changes.
"""
from __future__ import annotations

from ._standalone.query_loop import (  # noqa: F401
    DEFAULT_MAX_FOLLOW_UPS,
    DEFAULT_MAX_TURNS,
    run_plan,
)
