"""Standalone-mode modules — NOT used in Claude Code / Cursor production context.

These modules provide a self-contained query loop, recovery engine, and
tool executor for demo / CLI / conformance-audit purposes.  In production,
the host agent (Claude Code, Cursor, Codex) provides its own query loop,
tool executor, and recovery mechanism — these standalone versions are
NOT invoked.

Moved here from the top-level ``vibecodekit`` package in v0.26.0 to
make the production vs demo boundary explicit.  Back-compat shims in
``vibecodekit/query_loop.py`` and ``vibecodekit/recovery_engine.py``
re-export everything so existing import paths keep working.
"""
