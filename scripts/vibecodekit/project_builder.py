"""``vibe build`` — Devin-native project builder pipeline.

Orchestrates the 6-step VIBECODE methodology (scan → rri → vision →
blueprint → scaffold → verify) so Devin or any CLI-only agent can
build projects without Claude Code or another IDE.

Usage::

    vibe build plan "Build a todo app with user auth"
    vibe build step scan --target ./my-app
    vibe build step rri --description "todo app with auth"
    vibe build step vision --description "todo app with auth"
    vibe build step blueprint --description "todo app with auth"
    vibe build step scaffold --preset api-todo --stack fastapi --target ./my-app
    vibe build step verify --target ./my-app
    vibe build run "Build a todo app" --target ./my-app --preset api-todo
"""
from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineStep:
    """One step in the build pipeline."""
    number: int
    name: str
    status: str  # pending | running | done | skipped
    output: str  # path or inline content
    instructions: str  # what the agent should do


@dataclass
class BuildPlan:
    """Full pipeline plan for building a project."""
    description: str
    preset: Optional[str]
    stack: Optional[str]
    target_dir: str
    steps: list[PipelineStep] = field(default_factory=list)
    recommended_preset: Optional[str] = None
    recommended_stack: Optional[str] = None


# ---------------------------------------------------------------------------
# Preset recommender
# ---------------------------------------------------------------------------

_PRESET_KEYWORDS: dict[str, list[str]] = {
    "api-todo": ["api", "todo", "rest", "backend", "fastapi", "task"],
    "blog": ["blog", "article", "post", "writing", "cms", "content"],
    "crm": ["crm", "customer", "contact", "client", "relationship", "lead"],
    "dashboard": ["dashboard", "admin", "analytics", "kpi", "metrics", "chart"],
    "docs": ["docs", "documentation", "wiki", "knowledge", "guide", "manual"],
    "landing-page": ["landing", "marketing", "homepage", "launch", "startup"],
    "mobile-app": ["mobile", "app", "ios", "android", "expo", "react native"],
    "osint-terminal": ["osint", "terminal", "intelligence", "cyber", "security"],
    "portfolio": ["portfolio", "personal", "resume", "cv", "showcase"],
    "saas": ["saas", "subscription", "auth", "login", "payment", "tenant"],
    "shop-online": ["shop", "store", "ecommerce", "product", "cart", "checkout"],
}

_STACK_FOR_PRESET: dict[str, str] = {
    "api-todo": "fastapi",
    "blog": "nextjs",
    "crm": "nextjs",
    "dashboard": "nextjs",
    "docs": "nextjs",
    "landing-page": "nextjs",
    "mobile-app": "expo",
    "osint-terminal": "nextjs",
    "portfolio": "nextjs",
    "saas": "nextjs",
    "shop-online": "nextjs",
}


def recommend_preset(description: str) -> tuple[str, str, float]:
    """Return (preset, stack, confidence) based on description keywords."""
    desc_lower = description.lower()
    scores: dict[str, float] = {}
    for preset, keywords in _PRESET_KEYWORDS.items():
        score = sum(1.0 for kw in keywords if kw in desc_lower)
        if score > 0:
            scores[preset] = score

    if not scores:
        return "api-todo", "fastapi", 0.1  # safe default

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    confidence = min(scores[best] / 3.0, 1.0)
    return best, _STACK_FOR_PRESET[best], confidence


# ---------------------------------------------------------------------------
# Step generators — produce instruction text for each pipeline step
# ---------------------------------------------------------------------------

def _step_scan(target_dir: str) -> str:
    """Generate SCAN step instructions."""
    return textwrap.dedent(f"""\
    # Step 1: SCAN — Read-only repo exploration

    Scan the target directory to understand what already exists.

    ## Actions:
    1. List directory structure (2 levels deep):
       ```bash
       find {target_dir} -maxdepth 2 -type f | head -50
       ```
    2. Identify tech stack (package.json, pyproject.toml, Cargo.toml, etc.)
    3. Check for existing patterns, tests, docs
    4. Note any gaps or TODOs

    ## Output:
    Write a `scan-report.md` in the project root with:
    - Tech stack detected
    - Key modules and responsibilities
    - Dependencies (prod/dev)
    - Patterns already in use
    - Gaps: missing tests, missing docs, TODO clusters

    If the directory is empty or doesn't exist, note "greenfield project"
    and proceed to RRI.
    """)


def _step_rri(description: str) -> str:
    """Generate RRI step instructions."""
    return textwrap.dedent(f"""\
    # Step 2: RRI — Reverse Requirements Interview

    Project: {description}

    ## 16 Key Questions (answer based on the project description):

    ### Functional Requirements
    1. What is the primary user action? (e.g., "create tasks", "browse products")
    2. What are the core entities? (e.g., User, Task, Product)
    3. What CRUD operations are needed for each entity?
    4. What are the business rules / validation constraints?

    ### Non-Functional Requirements
    5. Expected scale? (users, requests/sec, data volume)
    6. Authentication method? (email/password, OAuth, API key)
    7. Performance targets? (page load < 2s, API response < 200ms)
    8. Offline support needed?

    ### Technical Constraints
    9. Preferred stack? (if not specified, use scaffold recommendation)
    10. Deployment target? (Vercel, Docker, VPS, Fly.io)
    11. Database? (SQLite for MVP, PostgreSQL for prod)
    12. External APIs or services needed?

    ### UX Requirements
    13. Who is the target user? (developer, non-tech, enterprise)
    14. Mobile-first or desktop-first?
    15. Accessibility requirements? (WCAG level)
    16. Internationalization needed?

    ## Output:
    Write `rri-matrix.md` with answers to all 16 questions.
    Mark uncertain answers with ⚠️ for human review.
    """)


def _step_vision(description: str, preset: str, stack: str) -> str:
    """Generate VISION step instructions."""
    return textwrap.dedent(f"""\
    # Step 3: VISION — Project Goals & Stack

    Project: {description}
    Recommended preset: {preset}
    Recommended stack: {stack}

    ## Define:

    ### 1-Line Goal
    Write a single sentence describing what this project does.

    ### 3 KPIs (Key Performance Indicators)
    - KPI 1: [measurable metric, e.g., "page load < 2s"]
    - KPI 2: [measurable metric, e.g., "test coverage > 80%"]
    - KPI 3: [measurable metric, e.g., "0 critical security issues"]

    ### Non-Goals (what this project does NOT do)
    List 3-5 things explicitly out of scope for this phase.

    ### Stack Decision
    - Frontend: {stack if stack == 'nextjs' else 'N/A (API-only)'}
    - Backend: {'FastAPI + SQLite' if stack == 'fastapi' else 'Next.js API routes'}
    - Styling: {'Tailwind CSS' if stack in ('nextjs', 'expo') else 'N/A'}
    - Testing: {'pytest' if stack == 'fastapi' else 'Jest + React Testing Library'}

    ## Output:
    Write `vision.md` with all sections above.
    """)


def _step_blueprint(description: str, preset: str, stack: str) -> str:
    """Generate BLUEPRINT step instructions."""
    return textwrap.dedent(f"""\
    # Step 4: BLUEPRINT — Architecture & Data Model

    Project: {description}
    Preset: {preset} | Stack: {stack}

    ## Design:

    ### Architecture Diagram (ASCII)
    Draw a simple ASCII diagram showing:
    - Client → API → Database flow
    - Key components and their relationships

    ### Data Model
    For each entity from RRI:
    - Fields with types
    - Relationships (1:1, 1:N, N:M)
    - Indexes needed

    ### API Interface
    For each endpoint:
    - Method + Path
    - Request/Response shape
    - Auth requirements

    ### File Structure
    ```
    {preset}/
    ├── src/           # application code
    ├── tests/         # test suite
    ├── docs/          # documentation
    └── ...
    ```

    ## Output:
    Write `blueprint.md` with architecture, data model, and API design.
    Mark as `APPROVED` when ready to proceed to scaffold.
    """)


def _step_scaffold(preset: str, stack: str, target_dir: str) -> str:
    """Generate SCAFFOLD step instructions."""
    return textwrap.dedent(f"""\
    # Step 5: SCAFFOLD — Generate Starter Project

    ## Run scaffold command:
    ```bash
    PYTHONPATH=./scripts python -m vibecodekit.cli scaffold apply \\
        {preset} {target_dir} --stack {stack} --force
    ```

    This will generate:
    - File structure for {preset} preset
    - Stack: {stack}
    - Design tokens and base components
    - Configuration files

    ## After scaffold:
    1. Verify generated files:
       ```bash
       PYTHONPATH=./scripts python -m vibecodekit.cli scaffold preview \\
           {preset} --stack {stack} {target_dir}
       ```
    2. Install dependencies:
       ```bash
       cd {target_dir}
       {'pip install -e ".[dev]"' if stack == 'fastapi' else 'npm install'}
       ```
    3. Run initial build/test:
       ```bash
       {'pytest' if stack == 'fastapi' else 'npm run build'}
       ```

    ## Then BUILD:
    Implement the features defined in blueprint.md.
    Follow the data model and API interface exactly.
    Write tests for each feature.
    """)


def _step_verify(target_dir: str) -> str:
    """Generate VERIFY step instructions."""
    return textwrap.dedent(f"""\
    # Step 6: VERIFY — Quality Gate

    ## Run verification:

    ### 1. Run tests
    ```bash
    cd {target_dir}
    # Python projects:
    pytest -q
    # Node.js projects:
    npm test
    ```

    ### 2. Run permission check on any shell commands used
    ```bash
    PYTHONPATH=./scripts python -m vibecodekit.cli permission "npm install" --mode default
    ```

    ### 3. Run conformance audit
    ```bash
    PYTHONPATH=./scripts python -m vibecodekit.conformance_audit --threshold 1.0
    ```

    ### 4. Check for security issues
    ```bash
    PYTHONPATH=./scripts python -m vibecodekit.cli permission "rm -rf /" --mode default
    # Should return: deny
    ```

    ## Verification checklist:
    - [ ] All tests pass
    - [ ] No security vulnerabilities
    - [ ] API endpoints return correct responses
    - [ ] Error handling covers edge cases
    - [ ] Code follows project conventions
    - [ ] Documentation is up to date

    ## Output:
    Write `verify-report.md` with pass/fail for each check.
    """)


# ---------------------------------------------------------------------------
# Plan generator
# ---------------------------------------------------------------------------

def generate_plan(
    description: str,
    target_dir: str = "./project",
    preset: Optional[str] = None,
    stack: Optional[str] = None,
) -> BuildPlan:
    """Generate a full build plan from a project description."""
    rec_preset, rec_stack, confidence = recommend_preset(description)
    use_preset = preset or rec_preset
    use_stack = stack or rec_stack

    steps = [
        PipelineStep(1, "scan", "pending",
                     f"{target_dir}/scan-report.md",
                     _step_scan(target_dir)),
        PipelineStep(2, "rri", "pending",
                     f"{target_dir}/rri-matrix.md",
                     _step_rri(description)),
        PipelineStep(3, "vision", "pending",
                     f"{target_dir}/vision.md",
                     _step_vision(description, use_preset, use_stack)),
        PipelineStep(4, "blueprint", "pending",
                     f"{target_dir}/blueprint.md",
                     _step_blueprint(description, use_preset, use_stack)),
        PipelineStep(5, "scaffold", "pending",
                     target_dir,
                     _step_scaffold(use_preset, use_stack, target_dir)),
        PipelineStep(6, "verify", "pending",
                     f"{target_dir}/verify-report.md",
                     _step_verify(target_dir)),
    ]

    return BuildPlan(
        description=description,
        preset=use_preset,
        stack=use_stack,
        target_dir=target_dir,
        steps=steps,
        recommended_preset=rec_preset,
        recommended_stack=rec_stack,
    )


def plan_to_dict(plan: BuildPlan) -> dict:
    """Serialize a BuildPlan to a JSON-safe dict."""
    return {
        "description": plan.description,
        "preset": plan.preset,
        "stack": plan.stack,
        "target_dir": plan.target_dir,
        "recommended_preset": plan.recommended_preset,
        "recommended_stack": plan.recommended_stack,
        "steps": [
            {
                "number": s.number,
                "name": s.name,
                "status": s.status,
                "output": s.output,
                "instructions": s.instructions,
            }
            for s in plan.steps
        ],
    }


def step_instructions(
    step_name: str,
    description: str = "",
    preset: str = "api-todo",
    stack: str = "fastapi",
    target_dir: str = "./project",
) -> str:
    """Return the instruction text for a single pipeline step."""
    generators = {
        "scan": lambda: _step_scan(target_dir),
        "rri": lambda: _step_rri(description),
        "vision": lambda: _step_vision(description, preset, stack),
        "blueprint": lambda: _step_blueprint(description, preset, stack),
        "scaffold": lambda: _step_scaffold(preset, stack, target_dir),
        "verify": lambda: _step_verify(target_dir),
    }
    gen = generators.get(step_name)
    if gen is None:
        valid = ", ".join(generators)
        raise ValueError(f"Unknown step '{step_name}'. Valid: {valid}")
    return gen()


# ---------------------------------------------------------------------------
# Full pipeline runner (generates all artifacts as markdown)
# ---------------------------------------------------------------------------

def run_full_pipeline(
    description: str,
    target_dir: str = "./project",
    preset: Optional[str] = None,
    stack: Optional[str] = None,
    vck_root: Optional[str] = None,
) -> dict:
    """Run the full pipeline and return structured output.

    This does NOT build the actual project — it generates the methodology
    artifacts (scan template, RRI matrix template, vision, blueprint) and
    then runs scaffold + verify via the existing engines.

    The agent (Devin) is expected to:
    1. Read each step's instructions
    2. Execute them (fill templates, write code, run commands)
    3. Move to the next step
    """
    plan = generate_plan(description, target_dir, preset, stack)

    # Try to run scaffold if engine is available
    scaffold_result = None
    verify_result = None
    if vck_root:
        try:
            from . import scaffold_engine as se
            engine = se.ScaffoldEngine()
            scaffold_result = engine.apply(
                plan.preset or "api-todo",
                target_dir,
                stack=plan.stack,
                force=True,
                seed_vibecode=True,
            )
            verify_issues = engine.verify(scaffold_result)
            verify_result = {
                "files_written": list(scaffold_result.files_written),
                "bytes_written": scaffold_result.bytes_written,
                "verify_issues": [i.message for i in verify_issues],
            }
        except Exception as e:
            scaffold_result = None
            verify_result = {"error": str(e)}

    return {
        "plan": plan_to_dict(plan),
        "scaffold_result": verify_result,
        "devin_instructions": textwrap.dedent("""\
            ## How to use this plan:

            1. Read each step's `instructions` field
            2. Execute the actions described
            3. Write the output artifacts (scan-report.md, rri-matrix.md, etc.)
            4. After scaffold, implement the features from your blueprint
            5. Run verify to ensure quality

            Each step builds on the previous one. Do not skip steps.
        """),
    }
