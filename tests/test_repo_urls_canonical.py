"""CI guard: every github.com/<org>/ URL in the repo must reference an
allowed organisation.  Prevents stale fork / personal-account URLs from
leaking into releases.

Lý do tồn tại của từng org trong ``ALLOWED_ORGS``:

- ``Audit-Tool-Vibecodekit-hybrid-ultra`` — **canonical** GitHub org
  của lite fork hiện tại.  Đây là repo chính của bản Lite đã
  audit và fix toàn bộ classifiers (F1=100%).
- ``VibecodekitPJ7`` — **upstream** GitHub org của project gốc.
  Vẫn còn references trong CHANGELOG.md, RELEASE_NOTES, và các
  file lịch sử.
- ``VagabondKingsman`` — upstream attribution cho
  `taw-kit <https://github.com/VagabondKingsman/taw-kit>`_, layer
  được tích hợp vào VibecodeKit Hybrid Ultra ở giai đoạn BIG-UPDATE.
- ``garrytan`` — upstream MIT attribution cho
  `gstack <https://github.com/garrytan/gstack>`_, từ đó VCK port
  Python browser daemon + 16 ``/vck-*`` slash command (clean-room
  reimplementation).
"""
from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Orgs that are legitimate references in this codebase.  Đọc comment
# block ở đầu file cho lý do chi tiết.  Nếu cần thêm/bớt entry, đồng
# thời cập nhật ``tests/test_no_further_rebrands.py`` để giữ size cap.
ALLOWED_ORGS = {"Audit-Tool-Vibecodekit-hybrid-ultra", "VibecodekitPJ7", "VagabondKingsman", "garrytan"}

# Placeholder orgs used in examples (e.g. "github.com/.../pull/42").
_PLACEHOLDER_ORGS = {"...", "OWNER", "owner", "example", "your-org"}

_ORG_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/")

# Only scan text-ish files; skip binary and vendored content.
_SCAN_SUFFIXES = {".md", ".toml", ".json", ".py", ".yml", ".yaml", ".cfg", ".txt"}
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}


def _scan_files():
    bad: list[str] = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in _SCAN_SUFFIXES:
            continue
        if any(skip in p.parts for skip in _SKIP_DIRS):
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for m in _ORG_RE.finditer(text):
            org = m.group(1)
            if org in _PLACEHOLDER_ORGS:
                continue
            if org not in ALLOWED_ORGS:
                rel = p.relative_to(REPO_ROOT)
                bad.append(f"{rel}: found org {org!r} in {m.group(0)!r}")
    return bad


def test_no_stale_org_in_repo():
    bad = _scan_files()
    assert not bad, (
        "Stale / non-canonical GitHub org references found:\n"
        + "\n".join(f"  - {b}" for b in bad)
    )


def test_allowed_orgs_have_documented_rationale():
    """Mọi org trong ``ALLOWED_ORGS`` phải được nhắc trong module
    docstring (``__doc__``) — tức là có lý do tồn tại được ghi rõ
    bằng tiếng Việt cho người review sau này.  Nếu thêm org mới mà
    quên cập nhật comment block, test này fail."""
    import sys
    mod = sys.modules[__name__]
    doc = mod.__doc__ or ""
    missing = [org for org in ALLOWED_ORGS if org not in doc]
    assert not missing, (
        "Các org sau có trong ALLOWED_ORGS nhưng không được giải thích "
        "trong module docstring (vi phạm guideline PR2): "
        f"{sorted(missing)}.  Hãy thêm bullet giải thích trong "
        "module-level docstring của tests/test_repo_urls_canonical.py."
    )
