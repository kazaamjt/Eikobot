# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions._resource import EikoResourceDefinition
from eikobot.core.compiler.definitions.base_types import EikoResource
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.compiler.definitions.function import PluginDefinition
from eikobot.core.compiler.importlib import resolve_import


def test_import_std() -> None:
    context = CompilerContext("__main__", {})
    resolve_import(["std"], context)
    std_context = context.get("std")
    assert isinstance(std_context, CompilerContext)


def test_std(eiko_std_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_file)

    test_resource = compiler.context.get("test_resource")
    assert isinstance(test_resource, EikoResource)
    assert test_resource.type.name == "CompileTestResource"

    test_2 = compiler.context.get("test_2")
    assert isinstance(test_2, EikoResource)
    assert test_2.type.name == "Test_2"
    assert test_2.properties.get("test") == test_resource


def test_from_import(eiko_from_import_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_from_import_file)

    test_resource = compiler.context.get("test_resource")
    assert isinstance(test_resource, EikoResource)
    assert test_resource.type.name == "CompileTestResource"

    test_2 = compiler.context.get("test_2")
    assert isinstance(test_2, EikoResource)
    assert test_2.type.name == "Test_2"
    assert test_2.properties.get("test") == test_resource


def test_multi_import(eiko_multi_import_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_multi_import_file)

    std = compiler.context.get("std")
    assert isinstance(std, CompilerContext)

    inspect = compiler.context.get("inspect")
    assert isinstance(inspect, PluginDefinition)

    file = compiler.context.get("file")
    assert isinstance(file, CompilerContext)

    file_definition = compiler.context.get("File")
    assert isinstance(file_definition, EikoResourceDefinition)

    read_file = compiler.context.get("read_file")
    assert isinstance(read_file, PluginDefinition)
