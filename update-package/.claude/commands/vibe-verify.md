---
description: "Adversarial QA gate — verify + completion report + refine boundary classifier (lite: absorbs /vibe-complete + /vibe-refine)"
version: 0.26.0
allowed-tools: [Bash, Read]
wired_refs: [ref-25, ref-26, ref-30, ref-36]
agent: qa
---

# /vibe-verify

Adversarial QA gate — the single quality checkpoint in lite mode.  In
full mode, `/vibe-complete` and `/vibe-refine` are separate commands;
in lite mode, `/vibe-verify` absorbs their functionality:

1. **Verify** — open verify-report template, adversarial QA
2. **Complete** — completion report + quality gate
3. **Refine** — boundary classifier (in_scope vs requires_vision)

## Usage

```bash
# 1) Open the verify-report template
cat ai-rules/vibecodekit/templates/verify-report.md

# 2) Open the completion-report template
cat ai-rules/vibecodekit/templates/completion-report.md

# 3) Classify a candidate diff (refine boundary)
git diff main... | vibecodekit refine classify -
```

## Boundary rules (from /vibe-refine)

- **In scope:** copy / text / VN localisation, minor CSS-token /
  colour / spacing tweaks, content edits inside existing sections,
  localised verify-report fixes.
- **Out of scope (cần VISION):** new routes / pages / API endpoints,
  new top-level components, dependency bumps, schema migrations,
  config file edits, file renames, new module folders, CI/CD edits.

Exit codes for `vibecodekit refine classify`:
- `0` → `in_scope` (refine allowed)
- `1` → `requires_vision` (re-run BƯỚC 3 first)

## References

- `ai-rules/vibecodekit/references/25-verify-coverage.md`
- `ai-rules/vibecodekit/references/26-anti-patterns.md`
- `ai-rules/vibecodekit/references/30-vibecode-master.md` §8 (REFINE envelope)
- `ai-rules/vibecodekit/references/36-refine-boundary.md`

See `ai-rules/vibecodekit/SKILL.md` for the full documentation.

<!-- v0.11.3-runtime-wiring-begin -->
## Runtime wiring (v0.11.3)

Compose the LLM context block for this command from wired references + dynamic data:

```bash
PYTHONPATH=ai-rules/vibecodekit/scripts python -m vibecodekit.cli context \
  --command vibe-verify
```

**Wired references:** ref-25, ref-26, ref-30, ref-36 — loaded verbatim by `methodology.render_command_context`.

**Default agent:** `qa` (auto-spawned via `subagent_runtime.spawn_for_command`).  Override per command by editing the `agent:` frontmatter field.

<!-- v0.11.3-runtime-wiring-end -->
