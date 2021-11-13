from pathlib import Path
from typing import List, Optional, Tuple

from .definitions.context import CompilerContext

INTERNAL_LIB_PATH = Path(__file__).parent.resolve() / "lib"

PATHS: List[Path] = [INTERNAL_LIB_PATH]


def resolve_import(
    import_path: List[str], main_context: CompilerContext
) -> Optional[Tuple[Path, CompilerContext]]:
    for _path in PATHS:
        file_path = _resolve_import(import_path.copy(), _path, main_context)
        if file_path is not None:
            return file_path

    return None


def _resolve_import(
    import_path: List[str], parent: Path, context: CompilerContext
) -> Optional[Tuple[Path, CompilerContext]]:
    current = import_path[0]
    import_path.remove(current)

    current_dir = parent / current
    if current_dir.exists() and current_dir.is_dir():
        init_file = current_dir / "__init__.eiko"
        if init_file.exists():
            if len(import_path) == 0:
                new_context = CompilerContext(current)
                context.set(current, new_context)
                return init_file, new_context

            new_context = CompilerContext(current)
            context.set(current, new_context)
            return _resolve_import(import_path, current_dir, new_context)

        return None

    if len(import_path) == 0:
        file_path = parent / (current + ".eiko")
        if file_path.exists():
            new_context = CompilerContext(current)
            context.set(current, new_context)
            return file_path, new_context

    return None
