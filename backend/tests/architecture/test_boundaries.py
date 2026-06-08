from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "learning_engine"
LAYER_NAMES = frozenset({"common", "domain", "application", "infrastructure", "presentation"})
FORBIDDEN_IMPORTS = {
    "common": frozenset(
        {
            "learning_engine.application",
            "learning_engine.domain",
            "learning_engine.infrastructure",
            "learning_engine.presentation",
        }
    ),
    "domain": frozenset(
        {
            "learning_engine.application",
            "learning_engine.infrastructure",
            "learning_engine.presentation",
        }
    ),
    "application": frozenset(
        {
            "learning_engine.infrastructure",
            "learning_engine.presentation",
        }
    ),
    "infrastructure": frozenset({"learning_engine.presentation"}),
    "presentation": frozenset(),
}
def _layer_for(path: Path) -> str | None:
    relative = path.relative_to(PACKAGE_ROOT)
    first_part = relative.parts[0]
    return first_part if first_part in LAYER_NAMES else None


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def _is_forbidden(module: str, forbidden_roots: frozenset[str]) -> bool:
    return any(module == forbidden or module.startswith(f"{forbidden}.") for forbidden in forbidden_roots)


def test_backend_layer_imports_follow_dependency_direction() -> None:
    violations: list[str] = []

    for path in PACKAGE_ROOT.rglob("*.py"):
        layer = _layer_for(path)
        if layer is None:
            continue

        forbidden_roots = FORBIDDEN_IMPORTS[layer]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _imported_modules(tree):
            if _is_forbidden(module, forbidden_roots):
                violations.append(f"{path.relative_to(PACKAGE_ROOT)} imports {module}")

    assert violations == []
