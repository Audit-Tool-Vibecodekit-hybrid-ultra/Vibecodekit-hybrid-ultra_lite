"""Decorator-based probe registry.

Source of truth for the conformance probes since cycle 14 PR β-6.
Each ``probes_*.py`` module decorates its functions with ``@probe(id,
group=...)``; the decorator appends them to the module-global
``_REGISTRY`` list at import time.  ``conformance_audit.PROBES``
exposes a sorted snapshot for back-compat.

Public API
==========

``@probe(id, *, group=..., since=..., standalone=...)``
    Decorator that appends ``(id, fn)`` to the global registry.  Use
    on a top-level function ``def fn(tmp: Path) -> tuple[bool, str]:``.

``collect_registered(*, skip_standalone=False, groups=None) -> list[(id, fn)]``
    Snapshot the registry in registration order.  Used by the runner
    via ``conformance_audit.PROBES`` (which sorts the snapshot by
    probe-id so the audit output preserves v0.22.x ordering).

Adding a new probe
==================

1. Pick the probes_*.py module that matches the probe's behavioural
   group (runtime / methodology / assets / governance).
2. Define ``def _probe_<canonical_name>(tmp: Path) -> tuple[bool, str]``
   and decorate with ``@probe("<NN>_<canonical_name>", group="<group>")``.
3. That's it — the runner picks it up automatically; no manual
   ``PROBES`` list edit is required.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, FrozenSet, List, Optional, Sequence, Tuple

ProbeFn = Callable[[Path], Tuple[bool, "str"]]
ProbeEntry = Tuple[str, ProbeFn]


@dataclass(frozen=True)
class ProbeMetadata:
    """Metadata attached to a registered probe."""
    id: str
    group: str
    since: Optional[str]
    standalone: bool


_REGISTRY: List[ProbeEntry] = []
_METADATA: List[ProbeMetadata] = []


def probe(id: str, *, group: str = "uncategorised",
          since: Optional[str] = None,
          standalone: bool = False) -> Callable[[ProbeFn], ProbeFn]:
    """Register a probe function in the global registry.

    Parameters
    ----------
    id:
        Stable probe identifier (e.g. ``"01_async_generator_loop"``).
        Becomes the row key in audit output.  Must be unique across
        the registry.
    group:
        Logical bucket (``runtime``/``methodology``/``assets``/
        ``governance``) — used for filtering and reporting.
    since:
        Tool version that introduced the probe (e.g. ``"v0.22.0"``).
        Optional, currently informational only.
    standalone:
        If ``True``, this probe exercises standalone/demo-only code
        (query_loop, recovery_engine).  It can be skipped with
        ``--skip-standalone`` in production contexts.

    Returns
    -------
    A decorator that returns the probe function unchanged after
    appending it to ``_REGISTRY``.
    """
    def deco(fn: ProbeFn) -> ProbeFn:
        for existing_id, _ in _REGISTRY:
            if existing_id == id:
                raise ValueError(
                    f"probe id collision: {id!r} already registered"
                )
        _REGISTRY.append((id, fn))
        _METADATA.append(ProbeMetadata(id=id, group=group, since=since, standalone=standalone))
        return fn

    return deco


def collect_registered(*, skip_standalone: bool = False,
                       groups: Optional[Sequence[str]] = None) -> List[ProbeEntry]:
    """Return the registered probes, optionally filtering.

    Parameters
    ----------
    skip_standalone:
        If ``True``, exclude probes marked ``standalone=True``.
    groups:
        If provided, only return probes whose ``group`` is in this set.
    """
    allowed_groups: Optional[FrozenSet[str]] = frozenset(groups) if groups else None
    result: List[ProbeEntry] = []
    for entry, meta in zip(_REGISTRY, _METADATA):
        if skip_standalone and meta.standalone:
            continue
        if allowed_groups is not None and meta.group not in allowed_groups:
            continue
        result.append(entry)
    return result


def get_metadata(probe_id: str) -> Optional[ProbeMetadata]:
    """Return metadata for a given probe id, or None."""
    for meta in _METADATA:
        if meta.id == probe_id:
            return meta
    return None


def _reset_for_tests() -> None:
    """Drop all registry entries.  Test-only helper."""
    _REGISTRY.clear()
    _METADATA.clear()
