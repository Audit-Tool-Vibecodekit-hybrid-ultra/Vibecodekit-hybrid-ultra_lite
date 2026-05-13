# VibecodeKit — Devin-Native Setup Guide

Build projects from scratch using VibecodeKit's 6-step methodology,
directly from a Devin session — no Claude Code, Cursor, or other IDE required.

## Quick Start (30 seconds)

```bash
# 1. Clone VibecodeKit
git clone https://github.com/Audit-Tool-Vibecodekit-hybrid-ultra/Vibecodekit-hybrid-ultra_lite.git ~/vibecodekit-tool

# 2. Set up environment
export PYTHONPATH=~/vibecodekit-tool/scripts

# 3. Generate a build plan
python -m vibecodekit.cli build plan "Build a todo app with user auth" --target ./my-app

# 4. Run scaffold to create project files
python -m vibecodekit.cli scaffold apply api-todo ./my-app --stack fastapi --force

# 5. Start building!
```

---

## Full Pipeline Guide

VibecodeKit uses a 6-step methodology called **VIBECODE Master**:

```
1.SCAN → 2.RRI → 3.VISION → 4.BLUEPRINT → 5.SCAFFOLD+BUILD → 6.VERIFY
```

### Step 1: SCAN — Understand the Landscape

Read-only exploration of what already exists.

```bash
python -m vibecodekit.cli build step scan --target ./my-app --description "Todo app with auth"
```

For existing repos, also run:
```bash
python -m vibecodekit.cli build step scan --target /path/to/existing/repo
```

**Output:** `scan-report.md` with tech stack, modules, patterns, gaps.

### Step 2: RRI — Requirements Interview

Answer 16 structured questions covering functional, non-functional, technical, and UX requirements.

```bash
python -m vibecodekit.cli build step rri --description "Todo app with user authentication"
```

**Output:** `rri-matrix.md` with all requirements documented.

### Step 3: VISION — Goals & Stack

Define the project's purpose, KPIs, and technology choices.

```bash
python -m vibecodekit.cli build step vision \
    --description "Todo app with auth" \
    --preset api-todo \
    --stack fastapi
```

**Output:** `vision.md` with 1-line goal, 3 KPIs, non-goals, stack decision.

### Step 4: BLUEPRINT — Architecture Design

Design the data model, API interfaces, and file structure.

```bash
python -m vibecodekit.cli build step blueprint \
    --description "Todo app with auth" \
    --preset api-todo \
    --stack fastapi
```

**Output:** `blueprint.md` with ASCII architecture diagram, data model, API spec.

### Step 5: SCAFFOLD + BUILD — Generate & Implement

Generate starter project files, then implement features:

```bash
# List available presets
python -m vibecodekit.cli scaffold list

# Generate starter files
python -m vibecodekit.cli scaffold apply api-todo ./my-app --stack fastapi --force

# Preview what will be created
python -m vibecodekit.cli scaffold preview api-todo --stack fastapi --target-dir ./my-app
```

Then implement features based on your blueprint.

### Step 6: VERIFY — Quality Gate

Run all verification checks:

```bash
# Check command safety
python -m vibecodekit.cli permission "npm install express" --mode default

# Run conformance audit
python -m vibecodekit.cli audit --threshold 1.0

# Run external benchmarks
python -m vibecodekit.cli benchmark
```

---

## Available Presets (11)

| Preset | Stack | What it builds |
|--------|-------|---------------|
| `api-todo` | fastapi | REST API + SQLite + pytest |
| `blog` | nextjs | MDX blog with listing |
| `crm` | nextjs/fastapi | Contacts CRUD |
| `dashboard` | nextjs | KPI cards + Recharts |
| `docs` | nextjs | Documentation site |
| `landing-page` | nextjs | Marketing landing + email capture |
| `mobile-app` | expo | React Native starter |
| `osint-terminal` | nextjs | Intelligence terminal UI |
| `portfolio` | nextjs | Hero + Work + Contact |
| `saas` | nextjs | NextAuth + Prisma + auth/dashboard |
| `shop-online` | nextjs | Product catalog + cart |

---

## All-in-One Command

Generate plan + run scaffold in one shot:

```bash
python -m vibecodekit.cli build run "Build a SaaS dashboard" --target ./my-saas --preset saas --stack nextjs
```

---

## Permission Engine

Before running any shell command, check its safety:

```bash
# Safe command
python -m vibecodekit.cli permission "git status" --mode default
# → allow

# Dangerous command
python -m vibecodekit.cli permission "rm -rf /" --mode default
# → deny

# Package install
python -m vibecodekit.cli permission "npm install express" --mode default
# → mutation (requires confirmation)
```

The permission engine uses 70+ regex patterns across 18 attack categories with F1=100%.

---

## Intent Classification

Route natural language to the right pipeline step:

```bash
python -m vibecodekit.cli intent classify "I want to build a blog"
# → {"intent": "BUILD", "confidence": 0.85, ...}

python -m vibecodekit.cli intent classify "scan the codebase"
# → {"intent": "SCAN", "confidence": 0.90, ...}
```

---

## Devin Session Auto-Setup

Add this to your Devin environment config to auto-install VibecodeKit:

```yaml
initialize:
  - git clone https://github.com/Audit-Tool-Vibecodekit-hybrid-ultra/Vibecodekit-hybrid-ultra_lite.git ~/vibecodekit-tool 2>/dev/null || (cd ~/vibecodekit-tool && git pull origin main --quiet)
  - export PYTHONPATH=~/vibecodekit-tool/scripts:${PYTHONPATH:-}
```

Or run the setup script:
```bash
bash ~/vibecodekit-tool/.devin/setup.sh
```

---

## CLI Reference

```
vibe build plan <description>       Generate 6-step pipeline plan
vibe build step <name>              Get instructions for one step
vibe build run <description>        Run full pipeline (plan + scaffold)
vibe scaffold list                  List all 11 presets
vibe scaffold apply <preset> <dir>  Generate project files
vibe scaffold preview <preset>      Preview file tree
vibe permission <cmd>               Check command safety
vibe intent classify <text>         Route text to pipeline step
vibe audit                          Run 100-probe conformance test
vibe benchmark                      Run external validation benchmarks
vibe doctor                         Health check
vibe demo                           Self-contained demo (no network)
```

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'vibecodekit'"**
```bash
export PYTHONPATH=~/vibecodekit-tool/scripts
```

**"Unknown preset"**
```bash
python -m vibecodekit.cli scaffold list  # See all valid presets
```

**"Permission denied" on a safe command**
```bash
python -m vibecodekit.cli permission "<command>" --mode default --unsafe  # Override (use carefully!)
```
