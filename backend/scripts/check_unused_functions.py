"""Report unused module-level functions in the backend package."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

SOURCE_PACKAGE = "learning_engine"
USAGE_PATHS = (Path(SOURCE_PACKAGE), Path("tests"))
MIN_ATTRIBUTE_PARTS = 2
ENTRY_POINT_FUNCTIONS = frozenset({("learning_engine.presentation.app", "run")})


@dataclass(frozen=True)
class FunctionDef:
    module: str
    name: str
    path: Path
    line: int


@dataclass(frozen=True)
class ImportAlias:
    module: str
    name: str | None


def _python_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.rglob("*.py")) if path.is_dir() else [path]


def _module_name(path: Path) -> str | None:
    if not path.is_relative_to(SOURCE_PACKAGE):
        return None

    relative = path.with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_module_function(
    node: ast.AST,
) -> TypeGuard[ast.FunctionDef | ast.AsyncFunctionDef]:
    return isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)


def _find_module_functions(path: Path) -> list[FunctionDef]:
    module = _module_name(path)
    if module is None:
        return []

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        FunctionDef(module=module, name=node.name, path=path, line=node.lineno)
        for node in tree.body
        if _is_module_function(node)
    ]


def _import_aliases(tree: ast.AST) -> dict[str, ImportAlias]:
    aliases: dict[str, ImportAlias] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == SOURCE_PACKAGE or alias.name.startswith(f"{SOURCE_PACKAGE}."):
                    aliases[alias.asname or alias.name] = ImportAlias(module=alias.name, name=None)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (node.module == SOURCE_PACKAGE or node.module.startswith(f"{SOURCE_PACKAGE}."))
        ):
            for alias in node.names:
                aliases[alias.asname or alias.name] = ImportAlias(module=node.module, name=alias.name)
    return aliases


def _used_imported_name(
    node: ast.Name,
    imports: dict[str, ImportAlias],
    definitions: set[tuple[str, str]],
) -> tuple[str, str] | None:
    imported = imports.get(node.id)
    if imported is None or imported.name is None:
        return None

    candidate = (imported.module, imported.name)
    return candidate if candidate in definitions else None


def _used_local_name(
    node: ast.Name,
    module: str | None,
    definitions: set[tuple[str, str]],
) -> tuple[str, str] | None:
    if module is None:
        return None

    candidate = (module, node.id)
    return candidate if candidate in definitions else None


def _attribute_path(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (*_attribute_path(node.value), node.attr)
    return ()


def _used_attribute(
    node: ast.Attribute,
    imports: dict[str, ImportAlias],
    definitions: set[tuple[str, str]],
) -> tuple[str, str] | None:
    parts = _attribute_path(node)
    if len(parts) < MIN_ATTRIBUTE_PARTS:
        return None

    imported = imports.get(parts[0])
    if imported is not None and imported.name is None:
        candidate = (".".join((imported.module, *parts[1:-1])), parts[-1])
        return candidate if candidate in definitions else None

    if parts[0] == SOURCE_PACKAGE:
        candidate = (".".join(parts[:-1]), parts[-1])
        return candidate if candidate in definitions else None

    return None


def _used_functions_in_file(path: Path, definitions: set[tuple[str, str]]) -> set[tuple[str, str]]:
    module = _module_name(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = _import_aliases(tree)
    used: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_name = _used_imported_name(node, imports, definitions) or _used_local_name(node, module, definitions)
            if used_name is not None:
                used.add(used_name)
        elif isinstance(node, ast.Attribute):
            used_attribute = _used_attribute(node, imports, definitions)
            if used_attribute is not None:
                used.add(used_attribute)

    return used


def main() -> int:
    source_files = _python_files(Path(SOURCE_PACKAGE))
    usage_files = [file for path in USAGE_PATHS for file in _python_files(path)]
    functions = [function for file in source_files for function in _find_module_functions(file)]
    definitions = {(function.module, function.name) for function in functions}
    used = set[tuple[str, str]]()

    for file in usage_files:
        used.update(_used_functions_in_file(file, definitions))

    unused = [
        function
        for function in functions
        if (function.module, function.name) not in used
        and (function.module, function.name) not in ENTRY_POINT_FUNCTIONS
    ]
    for function in unused:
        sys.stdout.write(f"{function.path}:{function.line}: unused module-level function '{function.name}'\n")

    return 1 if unused else 0


if __name__ == "__main__":
    sys.exit(main())
