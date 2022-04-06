import importlib.util
from inspect import getfullargspec, getmembers, isfunction
from pathlib import Path
from types import FunctionType, ModuleType
from typing import List, Optional, Tuple

from .. import logger
from .definitions.base_types import EikoBaseType
from .definitions.context import CompilerContext
from .definitions.function import PluginArg, PluginDefinition
from .errors import EikoCompilationError

INTERNAL_LIB_PATH = Path(__file__).parent.resolve() / "lib"
PATHS: List[Path] = [INTERNAL_LIB_PATH, Path(".")]


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
                new_context = context.get_or_set_context(current)
                return init_file, new_context

            new_context = context.get_or_set_context(current)
            return _resolve_import(import_path, current_dir, new_context)

        return None

    if len(import_path) == 0:
        file_path = parent / (current + ".eiko")
        if file_path.exists():
            new_context = context.get_or_set_context(current)
            return file_path, new_context

    return None


def resolve_from_import(
    import_path: List[str],
) -> Optional[Tuple[Path, CompilerContext]]:
    for _path in PATHS:
        file_path = _resolve_from_import(import_path.copy(), _path)
        if file_path is not None:
            return file_path

    return None


def _resolve_from_import(
    import_path: List[str], parent: Path
) -> Optional[Tuple[Path, CompilerContext]]:
    current = import_path[0]
    import_path.remove(current)

    current_dir = parent / current
    if current_dir.exists() and current_dir.is_dir():
        init_file = current_dir / "__init__.eiko"
        if init_file.exists():
            if len(import_path) == 0:
                new_context = CompilerContext(current)
                return init_file, new_context

            new_context = CompilerContext(current)
            return _resolve_import(import_path, current_dir, new_context)

        return None

    if len(import_path) == 0:
        file_path = parent / (current + ".eiko")
        if file_path.exists():
            new_context = CompilerContext(current)
            return file_path, new_context

    return None


def import_python_code(
    module_path: List[str], eiko_file_path: Path, context: CompilerContext
) -> None:
    file_path = eiko_file_path.with_suffix(".py")
    if file_path.exists():
        logger.debug(f"Found python plugins for eiko file: {eiko_file_path}")
        module_name = ".".join(module_path)
        py_module = load_python_code(module_name, file_path)
        for member in getmembers(py_module):
            name = member[0]
            _obj = member[1]
            if isfunction(_obj) and hasattr(_obj, "eiko_plugin"):
                logger.debug(f"Importing plugin {_obj.__name__} from {file_path}")
                context.set(name, _load_plugin(module_name, name, _obj))
    else:
        logger.debug(f"Found no python plugins for eiko file: {eiko_file_path}")


def load_python_code(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is not None:
        py_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_module)  # type: ignore
        return py_module

    raise EikoCompilationError(f"Failed to import python module {module_name} ")


def _load_plugin(module: str, name: str, function: FunctionType) -> PluginDefinition:
    fullargspec = getfullargspec(function)
    annotations = fullargspec.annotations
    return_type = annotations.get("return", None)
    if return_type is None:
        raise EikoCompilationError(
            f"Plugin {module}.{name} return type annotation is missing."
        )
    plugin_definition = PluginDefinition(function, annotations["return"], name, module)

    for arg_name in fullargspec.args:
        arg_annotation = annotations.get(arg_name)
        if arg_annotation is None:
            raise EikoCompilationError(
                f"Plugin '{module}.{name}' has no type annotation for argument '{arg_name}'."
            )
        if not issubclass(arg_annotation, (EikoBaseType, bool, float, int, str)):
            raise EikoCompilationError(
                f"Plugin '{module}.{name}' type annotation for argument '{arg_name}' must be "
                "'bool', 'float', 'int', 'str' or an eiko type.",
            )

        plugin_definition.add_arg(
            PluginArg(
                arg_name,
                arg_annotation,
            )
        )

    return plugin_definition
