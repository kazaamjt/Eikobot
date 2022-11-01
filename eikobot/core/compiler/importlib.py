"""
The importlib allows for importing
of both Eiko and Python code.
"""
import importlib.util
from dataclasses import dataclass
from inspect import getfullargspec, getmembers, isclass, isfunction
from pathlib import Path
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, List, Optional

from .. import logger
from ..backend.handlers import CRUDHandler
from .definitions.base_types import EikoBaseType
from .definitions.function import PluginArg, PluginDefinition
from .errors import EikoCompilationError

if TYPE_CHECKING:
    from .definitions.context import CompilerContext

INTERNAL_LIB_PATH = Path(__file__).parent.parent.resolve() / "lib"
PATHS: List[Path] = [INTERNAL_LIB_PATH, Path(".")]


@dataclass
class Module:
    """A resolved module that can be imported by being compiled."""

    name: str
    path: Path
    context: "CompilerContext"

    def __post_init__(self) -> None:
        self.submodules: List["Module"] = []
        self.context.set_path(self.path)


def resolve_import(
    import_path: List[str], main_context: "CompilerContext"
) -> Optional[Module]:
    """
    Tries to import a given path.
    """
    for _path in PATHS:
        result = _resolve_import(import_path.copy(), _path, main_context)
        if result is not None:
            return result

    return None


def _resolve_import(
    import_path: List[str], parent: Path, context: "CompilerContext"
) -> Optional[Module]:
    current = import_path[0]
    import_path.remove(current)

    current_dir = parent / current
    if current_dir.exists() and current_dir.is_dir():
        init_file = current_dir / "__init__.eiko"
        if init_file.exists():
            if len(import_path) == 0:
                new_context = context.get_or_set_context(current)
                module = Module(current_dir.stem, init_file, new_context)
                _get_submodules(module)
                return module

            new_context = context.get_or_set_context(current)
            return _resolve_import(import_path, current_dir, new_context)

        return None

    if len(import_path) == 0:
        file_path = parent / (current + ".eiko")
        if file_path.exists():
            new_context = context.get_or_set_context(current)
            return Module(file_path.stem, file_path, new_context)

    return None


def resolve_from_import(
    import_path: List[str], context: "CompilerContext"
) -> Optional[Module]:
    """
    Tries to from import a given path list.
    """
    for _path in PATHS:
        module = _resolve_from_import(import_path.copy(), _path, context)
        if module is not None:
            return module

    return None


def _resolve_from_import(
    import_path: List[str], parent: Path, context: "CompilerContext"
) -> Optional[Module]:
    current = import_path[0]
    import_path.remove(current)

    current_dir = parent / current
    if current_dir.exists() and current_dir.is_dir():
        init_file = current_dir / "__init__.eiko"
        if init_file.exists():
            new_context = context.get_or_set_context(current)
            new_context.set_path(init_file)
            if len(import_path) == 0:
                module = Module(current_dir.stem, init_file, new_context)
                _get_submodules(module)
                return module

            return _resolve_import(import_path, current_dir, new_context)

        return None

    if len(import_path) == 0:
        file_path = parent / (current + ".eiko")
        if file_path.exists():
            new_context = context.get_or_set_context(current)
            return Module(file_path.stem, file_path, new_context)

    return None


def import_python_code(
    module_path: List[str], eiko_file_path: Path, context: "CompilerContext"
) -> None:
    """
    Resolves and exposes python code that is tagged as eiko-plugins.
    """
    file_path = eiko_file_path.with_suffix(".py")
    if file_path.exists():
        logger.debug(f"Found python plugins file for eiko file: {eiko_file_path}")
        module_name = ".".join(module_path)
        py_module = load_python_code(module_name, file_path)
        for member in getmembers(py_module):
            _obj = member[1]
            if isfunction(_obj) and hasattr(_obj, "eiko_plugin"):
                plugin_name = _obj.__name__
                if hasattr(_obj, "alias"):
                    if _obj.alias is not None:
                        plugin_name = _obj.alias
                logger.debug(f"Importing plugin '{plugin_name}' from {file_path}")
                if context.shallow_get(plugin_name) is None:
                    context.set(
                        plugin_name, _load_plugin(module_name, plugin_name, _obj)
                    )

            elif (
                isclass(_obj)
                and issubclass(_obj, CRUDHandler)
                and _obj is not CRUDHandler
            ):
                logger.debug(f"Importing handler '{_obj.__name__}' from {file_path}")
    else:
        logger.debug(f"Found no python plugins for eiko file: {eiko_file_path}")


def load_python_code(module_name: str, file_path: Path) -> ModuleType:
    """
    Loads Python code from a given path.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is not None:
        py_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_module)  # type: ignore
        return py_module

    raise EikoCompilationError(f"Failed to import python module {module_name} ")


def _load_plugin(module: str, name: str, function: FunctionType) -> PluginDefinition:
    fullargspec = getfullargspec(function)
    annotations = fullargspec.annotations
    return_type = annotations.get("return", "")
    if return_type == "":
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
        if not issubclass(arg_annotation, (EikoBaseType, bool, float, int, str, Path)):
            print(type(arg_annotation))
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


def _get_submodules(module: Module) -> None:
    for path in module.path.parent.glob("*"):
        if path.is_dir():
            init_file = path / "__init__.eiko"
            if init_file.exists():
                new_context = module.context.get_or_set_context(path.stem)
                new_module = Module(path.stem, init_file, new_context)
                module.submodules.append(new_module)
                _get_submodules(new_module)

        # Assume this has already been imported
        elif path.name == "__init__.eiko":
            pass

        elif path.suffix == ".eiko":
            module.submodules.append(
                Module(path.stem, path, module.context.get_or_set_context(path.stem))
            )
