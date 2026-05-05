"""Audit runner — orchestrates probes, collects results, prints/JSON output.

Extracted from ``conformance_audit.py`` in cycle 14 PR β-1.  This module
is the engine that:

  1) Iterates over a list of probes (manual or registry-collected).
  2) Hands each probe a fresh ``tmp/<probe-id>`` working directory.
  3) Records ``pass / fail`` plus the probe's free-text detail string.
  4) Computes parity = passed / total and compares to threshold.
  5) Returns a JSON-serialisable report and (in CLI mode) prints it.

The runner is **agnostic** to where probes come from.  Callers may pass
their own ``probes`` list (used by the back-compat shim in
``conformance_audit.py``) or omit it, in which case the runner pulls
from ``vibecodekit.conformance_audit.PROBES`` for full back-compat.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

ProbeFn = Callable[[Path], Tuple[bool, str]]
ProbeEntry = Tuple[str, ProbeFn]

# Essential probes for lite-mode installations (~15 probes).
# Covers: permission engine, context defense, recovery, session,
# security classifier, config, install reconciliation, and health.
LITE_PROBES = frozenset({
    "05_streaming_tool_execution",
    "06_context_modifier_chain",
    "09_five_layer_context_defense",
    "10_permission_classification",
    "19_background_tasks",
    "24_denial_concurrency_safe",
    "38_config_persistence",
    "51_command_context_wiring",
    "52_command_agent_binding",
    "68_classifier_ensemble_contract",
    "69_classifier_regex_rule_bank",
    "70_classifier_blocks_prompt_injection",
    "71_classifier_blocks_secret_leak",
    "80_session_ledger_module",
    "85_no_orphan_module",
})


def audit(threshold: float = 0.85, *,
          probes: Optional[Sequence[ProbeEntry]] = None,
          skip_standalone: bool = False,
          skip_legacy: bool = False,
          lite: bool = False) -> Dict[str, Any]:
    """Run all probes against fresh temp dirs, return parity report.

    Parameters
    ----------
    threshold:
        Minimum parity (passed / total) for the audit to be considered
        "met".  Default ``0.85``.
    probes:
        Optional list of ``(id, fn)`` pairs.  If ``None`` (default)
        the runner pulls ``PROBES`` from ``vibecodekit.conformance_audit``
        — preserving v0.22.x behaviour exactly.
    skip_standalone:
        If ``True``, exclude probes marked ``standalone=True`` in the
        registry.  Only effective when ``probes`` is ``None`` (i.e. the
        runner collects from the registry).  Standalone probes exercise
        demo-only code (query_loop, recovery_engine) that does not run
        in production Claude Code context.
    skip_legacy:
        If ``True``, exclude probes marked ``legacy=True`` (tautological
        file-existence checks from Category B).  Default since v0.26.0.
    lite:
        If ``True``, run only the ``LITE_PROBES`` essential subset
        (~15 probes) suitable for lite mode installations.

    Returns
    -------
    Dict with keys ``threshold``, ``passed``, ``total``, ``parity``,
    ``met``, and ``probes`` (a list of per-probe rows).
    """
    if probes is None:
        needs_filtering = skip_standalone or skip_legacy or lite
        if needs_filtering:
            from ._registry import collect_registered
            probes = sorted(
                collect_registered(
                    skip_standalone=skip_standalone,
                    skip_legacy=skip_legacy,
                ),
                key=lambda row: row[0],
            )
            if lite:
                probes = [(pid, fn) for pid, fn in probes
                          if pid in LITE_PROBES]
        else:
            from vibecodekit.conformance_audit import PROBES as _DEFAULT_PROBES
            probes = _DEFAULT_PROBES

    rows: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as td:
        for name, probe in probes:
            sub = Path(td) / name
            sub.mkdir(parents=True, exist_ok=True)
            try:
                ok, detail = probe(sub)
                rows.append({"pattern": name, "pass": bool(ok), "detail": detail})
            except Exception as e:  # pragma: no cover - exception path
                rows.append({
                    "pattern": name,
                    "pass": False,
                    "detail": f"exception: {type(e).__name__}: {e}",
                })
    passed = sum(1 for r in rows if r["pass"])
    total = len(rows)
    parity = (passed / total) if total else 0.0
    return {
        "threshold": threshold,
        "passed": passed,
        "total": total,
        "parity": round(parity, 4),
        "met": parity >= threshold,
        "skip_standalone": skip_standalone,
        "skip_legacy": skip_legacy,
        "lite": lite,
        "probes": rows,
    }


def main() -> None:
    """CLI entry — prints parity report and exits 0 iff met."""
    ap = argparse.ArgumentParser(
        description="Run behaviour-based conformance audit.",
    )
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-standalone", action="store_true",
                    help="Skip probes that exercise standalone/demo-only code "
                         "(query_loop, recovery_engine).")
    ap.add_argument("--skip-legacy", action="store_true",
                    help="Skip legacy tautological probes (Category B file-exists "
                         "checks).  Recommended for external-validation workflows.")
    ap.add_argument("--legacy", action="store_true",
                    help="Include legacy probes (overrides --skip-legacy).")
    ap.add_argument("--lite", action="store_true",
                    help="Run only the essential lite-mode probe subset (~15 probes).")
    args = ap.parse_args()
    do_skip_legacy = args.skip_legacy and not args.legacy
    out = audit(args.threshold, skip_standalone=args.skip_standalone,
                skip_legacy=do_skip_legacy, lite=args.lite)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(
            f"parity: {out['parity']:.2%}   "
            f"({out['passed']}/{out['total']}, "
            f"threshold {out['threshold']:.0%})"
        )
        for r in out["probes"]:
            mark = "PASS" if r["pass"] else "FAIL"
            print(f"  [{mark}] {r['pattern']:<36} {r['detail']}")
    sys.exit(0 if out["met"] else 1)
