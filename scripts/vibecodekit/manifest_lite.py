"""Lite-mode command manifest — 10 core commands for personal users.

The full VibecodeKit ships 42 slash commands.  For personal / solo
projects this is cognitive overload.  Lite mode exposes only the 10
commands that cover the core 6-step workflow:

    scan → rri → vision → blueprint → scaffold → verify

Plus essential runtime utilities (permission, doctor, install, master
router).

Activate lite mode:
    export VIBECODEKIT_MODE=lite

Or pass ``--lite`` to ``vibe install``.

The ``is_lite()`` helper reads ``VIBECODEKIT_MODE`` from the environment
and returns ``True`` when the value is ``"lite"``.
"""
from __future__ import annotations

import os
from typing import FrozenSet

# The 10 commands that cover the core workflow + essential utilities.
LITE_COMMANDS: FrozenSet[str] = frozenset({
    "vibe",             # master router — dispatches to the right command
    "vibe-scan",        # step 1: read-only repo exploration
    "vibe-rri",         # step 2: reverse requirements interview
    "vibe-vision",      # step 3: goals + KPIs + non-goals
    "vibe-blueprint",   # step 4: architecture + data model
    "vibe-scaffold",    # step 5: scaffold a runnable starter
    "vibe-verify",      # step 6: adversarial QA gate (absorbs complete + refine)
    "vibe-permission",  # essential: dry-run permission pipeline
    "vibe-doctor",      # essential: health check
    "vibe-install",     # essential: install overlay into project
})

# Full command set — all 42 commands.
FULL_COMMANDS: FrozenSet[str] = frozenset({
    # /vibe-* commands (25 + 1 master)
    "vibe", "vibe-scan", "vibe-rri", "vibe-rri-t", "vibe-rri-ux",
    "vibe-rri-ui", "vibe-vision", "vibe-blueprint", "vibe-scaffold",
    "vibe-verify", "vibe-complete", "vibe-refine", "vibe-permission",
    "vibe-doctor", "vibe-install", "vibe-run", "vibe-compact",
    "vibe-dashboard", "vibe-audit", "vibe-memory", "vibe-approval",
    "vibe-tip", "vibe-task", "vibe-subagent", "vibe-module",
    "vibe-ship",
    # /vck-* commands (16)
    "vck-cso", "vck-review", "vck-qa", "vck-qa-only", "vck-ship",
    "vck-investigate", "vck-canary", "vck-pipeline", "vck-eng-review",
    "vck-ceo-review", "vck-second-opinion", "vck-design-consultation",
    "vck-design-review", "vck-office-hours", "vck-learn", "vck-retro",
})


def is_lite() -> bool:
    """Return True if VIBECODEKIT_MODE is set to 'lite'."""
    return os.environ.get("VIBECODEKIT_MODE", "").lower() == "lite"


def active_commands() -> FrozenSet[str]:
    """Return the set of commands for the current mode."""
    return LITE_COMMANDS if is_lite() else FULL_COMMANDS
