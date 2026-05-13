# Build Project with VibecodeKit

Build a new project from scratch using the VibecodeKit 6-step VIBECODE methodology pipeline.

## Prerequisites

```bash
# Clone the VibecodeKit tool repo (if not already present)
git clone https://github.com/Audit-Tool-Vibecodekit-hybrid-ultra/Vibecodekit-hybrid-ultra_lite.git ~/vibecodekit-tool

# Set PYTHONPATH to the scripts directory
export PYTHONPATH=~/vibecodekit-tool/scripts
export VCK_ROOT=~/vibecodekit-tool
```

## Step 1: Generate Build Plan

Describe what you want to build. The tool will recommend a preset and stack:

```bash
python -m vibecodekit.cli build plan "<project description>" --target ./my-project
```

Example:
```bash
python -m vibecodekit.cli build plan "Build a SaaS dashboard with user auth and payment" --target ./saas-app
```

This outputs:
- Recommended **preset** (one of 11: api-todo, blog, crm, dashboard, docs, landing-page, mobile-app, osint-terminal, portfolio, saas, shop-online)
- Recommended **stack** (nextjs, fastapi, or expo)
- 6-step pipeline with output file paths

## Step 2: Follow the Pipeline

For each step, get detailed instructions:

```bash
# Step 1: SCAN — understand what exists
python -m vibecodekit.cli build step scan --target ./my-project --description "<description>"

# Step 2: RRI — requirements gathering (16 questions)
python -m vibecodekit.cli build step rri --description "<description>"

# Step 3: VISION — goals, KPIs, non-goals, stack decision
python -m vibecodekit.cli build step vision --description "<description>" --preset <preset> --stack <stack>

# Step 4: BLUEPRINT — architecture, data model, API design
python -m vibecodekit.cli build step blueprint --description "<description>" --preset <preset> --stack <stack>

# Step 5: SCAFFOLD — generate starter project files
python -m vibecodekit.cli build step scaffold --preset <preset> --stack <stack> --target ./my-project

# Step 6: VERIFY — quality gate
python -m vibecodekit.cli build step verify --target ./my-project
```

## Step 3: Run Scaffold

After completing the planning steps (scan → rri → vision → blueprint), scaffold the project:

```bash
python -m vibecodekit.cli scaffold apply <preset> ./my-project --stack <stack> --force
```

Verify the scaffold:
```bash
python -m vibecodekit.cli scaffold preview <preset> --stack <stack> --target-dir ./my-project
```

## Step 4: Build Features

After scaffolding, implement features based on the blueprint:
1. Follow the data model from `blueprint.md`
2. Implement API endpoints as specified
3. Write tests for each feature
4. Check commands through the permission engine:
   ```bash
   python -m vibecodekit.cli permission "npm install express" --mode default
   ```

## Step 5: Verify & Ship

```bash
# Run the conformance audit
python -m vibecodekit.cli audit --threshold 1.0

# Run external benchmarks
python -m vibecodekit.cli benchmark

# Run project tests
cd ./my-project && npm test  # or: pytest
```

## Quick Run (All-in-One)

For a quick start that generates plan + scaffolds in one command:

```bash
python -m vibecodekit.cli build run "<description>" --target ./my-project
```

## Available Presets

| Preset | Stack | Description |
|--------|-------|-------------|
| api-todo | fastapi | REST API with SQLite + pytest |
| blog | nextjs | Blog with markdown posts |
| crm | nextjs/fastapi | Customer CRM — contacts CRUD |
| dashboard | nextjs | Admin dashboard with KPI cards |
| docs | nextjs | Documentation site (Nextra-style) |
| landing-page | nextjs | Marketing landing page |
| mobile-app | expo | React Native starter with tabs |
| osint-terminal | nextjs | Intelligence terminal UI |
| portfolio | nextjs | Personal portfolio |
| saas | nextjs | SaaS starter with NextAuth + Prisma |
| shop-online | nextjs | E-commerce with product catalog |

## Useful CLI Commands

```bash
# List all available presets
python -m vibecodekit.cli scaffold list

# Classify user intent
python -m vibecodekit.cli intent classify "build a todo app"

# Check a command's safety
python -m vibecodekit.cli permission "rm -rf /" --mode default

# Run health check
python -m vibecodekit.cli doctor

# Run demo (no network needed)
python -m vibecodekit.cli demo
```
