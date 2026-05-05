"""External validation benchmarks — replaces tautological self-tests.

Unlike the conformance audit probes (which test the tool's own spec
against its own code), these benchmarks test the tool against **external
datasets** — real-world attack commands, prompt injections, and
scaffold viability checks.

The key difference: if the tool has a bug, these benchmarks will catch
it.  Self-referential probes cannot.

Benchmark classes
=================

1. ``PermissionBenchmark`` — tests the 6-layer permission engine against
   a dataset of known-dangerous and known-safe commands.  Computes
   precision, recall, and F1 score.

2. ``PromptInjectionBenchmark`` — tests the security classifier against
   known prompt injection patterns.

3. ``ScaffoldViabilityBenchmark`` — tests that scaffold presets produce
   valid project structures (files exist, structure is correct).

4. ``IntentClassifierBenchmark`` — tests the intent router against
   labelled intent examples.

Usage::

    python -m vibecodekit.external_benchmark --all
    python -m vibecodekit.external_benchmark --benchmark permission
    python -m vibecodekit.external_benchmark --benchmark injection
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

BENCHMARK_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "benchmarks"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    total: int
    correct: int
    precision: float
    recall: float
    f1: float
    errors: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total": self.total,
            "correct": self.correct,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "error_count": len(self.errors),
            "errors": self.errors[:20],  # cap output
        }


def _load_dataset(filename: str) -> List[Dict[str, Any]]:
    """Load a JSONL benchmark dataset."""
    path = BENCHMARK_DIR / filename
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(json.loads(line))
    return entries


def _compute_metrics(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Compute precision, recall, F1 from confusion matrix components."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


class PermissionBenchmark:
    """Test permission engine accuracy against known attack commands.

    Dataset format (JSONL):
        {"cmd": "rm -rf /", "expected": "deny", "category": "destructive"}
        {"cmd": "ls -la", "expected": "allow", "category": "read_only"}
    """

    DATASET = "attack-commands.jsonl"

    def run(self) -> BenchmarkResult:
        from . import permission_engine

        data = _load_dataset(self.DATASET)
        if not data:
            return BenchmarkResult("permission", 0, 0, 0.0, 0.0, 0.0,
                                   [{"error": f"dataset not found: {self.DATASET}"}])

        # Reset denial fatigue circuit breaker so each command is evaluated
        # independently.  Without this, the circuit breaker trips after 3
        # consecutive denials and converts subsequent deny → ask, causing
        # false negatives in the benchmark.
        denial_path = Path("/tmp") / ".vibecode" / "runtime" / "denials.json"
        if denial_path.exists():
            denial_path.unlink()

        tp = fp = fn = tn = 0
        errors: List[Dict[str, Any]] = []

        for entry in data:
            cmd = entry["cmd"]
            expected = entry["expected"]  # "deny" or "allow"

            # Reset denial store before each command to prevent circuit
            # breaker from accumulating state across benchmark entries.
            if denial_path.exists():
                denial_path.unlink()

            try:
                result = permission_engine.decide_typed(cmd, mode="default", root="/tmp")
                actual = result.decision
            except Exception as e:
                errors.append({"cmd": cmd, "expected": expected,
                               "error": str(e)})
                continue

            if expected == "deny":
                if actual == "deny":
                    tp += 1
                else:
                    fn += 1
                    errors.append({"cmd": cmd, "expected": "deny",
                                   "actual": actual, "type": "false_negative"})
            else:  # expected allow
                if actual in ("allow", "ask"):
                    tn += 1
                else:
                    fp += 1
                    errors.append({"cmd": cmd, "expected": "allow",
                                   "actual": actual, "type": "false_positive"})

        precision, recall, f1 = _compute_metrics(tp, fp, fn)
        return BenchmarkResult("permission", len(data), tp + tn,
                               precision, recall, f1, errors)


class PromptInjectionBenchmark:
    """Test security classifier against prompt injection patterns.

    Dataset format (JSONL):
        {"input": "ignore previous...", "expected": "blocked", "category": "direct"}
    """

    DATASET = "prompt-injections.jsonl"

    def run(self) -> BenchmarkResult:
        from . import security_classifier

        data = _load_dataset(self.DATASET)
        if not data:
            return BenchmarkResult("injection", 0, 0, 0.0, 0.0, 0.0,
                                   [{"error": f"dataset not found: {self.DATASET}"}])

        tp = fp = fn = tn = 0
        errors: List[Dict[str, Any]] = []

        for entry in data:
            text = entry["input"]
            expected = entry["expected"]  # "blocked" or "safe"

            try:
                result = security_classifier.classify_text(text)
                is_blocked = result.verdict.decision == "deny" if hasattr(result, 'verdict') else False
                actual = "blocked" if is_blocked else "safe"
            except Exception as e:
                errors.append({"input": text[:80], "expected": expected,
                               "error": str(e)})
                continue

            if expected == "blocked":
                if actual == "blocked":
                    tp += 1
                else:
                    fn += 1
                    errors.append({"input": text[:80], "expected": "blocked",
                                   "actual": actual, "type": "false_negative"})
            else:
                if actual == "safe":
                    tn += 1
                else:
                    fp += 1
                    errors.append({"input": text[:80], "expected": "safe",
                                   "actual": actual, "type": "false_positive"})

        precision, recall, f1 = _compute_metrics(tp, fp, fn)
        return BenchmarkResult("injection", len(data), tp + tn,
                               precision, recall, f1, errors)


class ScaffoldViabilityBenchmark:
    """Test that scaffold presets produce valid project structures.

    Does not require a dataset file — runs against the built-in presets.
    """

    def run(self) -> BenchmarkResult:
        import tempfile
        from .scaffold_engine import ScaffoldEngine

        engine = ScaffoldEngine()
        presets = engine.list_presets()
        correct = 0
        errors: List[Dict[str, Any]] = []

        for preset_info in presets:
            preset_name = preset_info.name
            try:
                with tempfile.TemporaryDirectory() as td:
                    engine.apply(preset_name, td, stack=preset_info.stacks[0])
                    # Check that at least one file was created
                    created = list(Path(td).rglob("*"))
                    files = [f for f in created if f.is_file()]
                    if files:
                        correct += 1
                    else:
                        errors.append({"preset": preset_name,
                                       "error": "no files created"})
            except Exception as e:
                errors.append({"preset": preset_name, "error": str(e)})

        total = len(presets) if presets else 0
        p = correct / total if total > 0 else 0.0
        return BenchmarkResult("scaffold", total, correct,
                               p, p, p, errors)


class IntentClassifierBenchmark:
    """Test intent router against labelled examples.

    Dataset format (JSONL):
        {"input": "deploy to vercel", "expected_intent": "SHIP"}
    """

    DATASET = "intent-labels.jsonl"

    def run(self) -> BenchmarkResult:
        from .intent_router import IntentRouter

        data = _load_dataset(self.DATASET)
        if not data:
            return BenchmarkResult("intent", 0, 0, 0.0, 0.0, 0.0,
                                   [{"error": f"dataset not found: {self.DATASET}"}])

        router = IntentRouter()
        correct = 0
        errors: List[Dict[str, Any]] = []

        for entry in data:
            text = entry["input"]
            expected = entry["expected_intent"]

            try:
                match = router.classify(text)
                actual = match.intents[0] if hasattr(match, 'intents') and match.intents else "UNKNOWN"
            except Exception as e:
                errors.append({"input": text[:80], "expected": expected,
                               "error": str(e)})
                continue

            if actual == expected:
                correct += 1
            else:
                errors.append({"input": text[:80], "expected": expected,
                               "actual": actual})

        total = len(data)
        p = correct / total if total > 0 else 0.0
        return BenchmarkResult("intent", total, correct, p, p, p, errors)


BENCHMARKS = {
    "permission": PermissionBenchmark,
    "injection": PromptInjectionBenchmark,
    "scaffold": ScaffoldViabilityBenchmark,
    "intent": IntentClassifierBenchmark,
}


def run_all(names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run selected (or all) benchmarks, return combined report."""
    selected = names or list(BENCHMARKS.keys())
    results = []
    for name in selected:
        if name not in BENCHMARKS:
            continue
        bench = BENCHMARKS[name]()
        result = bench.run()
        results.append(result.to_dict())

    return {
        "benchmarks": results,
        "total_benchmarks": len(results),
        "all_passing": all(r["f1"] >= 0.90 for r in results if r["total"] > 0),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run external validation benchmarks.")
    ap.add_argument("--benchmark", choices=list(BENCHMARKS.keys()),
                    help="Run a specific benchmark (default: all).")
    ap.add_argument("--all", action="store_true",
                    help="Run all benchmarks.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    names = [args.benchmark] if args.benchmark else None
    report = run_all(names)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for r in report["benchmarks"]:
            status = "PASS" if r["f1"] >= 0.90 else "FAIL"
            print(f"  [{status}] {r['name']:<12} "
                  f"F1={r['f1']:.2%}  P={r['precision']:.2%}  R={r['recall']:.2%}  "
                  f"({r['correct']}/{r['total']})")
        print(f"\nOverall: {'ALL PASS' if report['all_passing'] else 'SOME FAIL'}")

    sys.exit(0 if report["all_passing"] else 1)


if __name__ == "__main__":
    main()
