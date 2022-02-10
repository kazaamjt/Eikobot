# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoResource
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.compiler.importer import resolve_import


def test_import_std() -> None:
    context = CompilerContext("__main__")
    resolve_import(["std"], context)
    std_context = context.get("std")
    assert isinstance(std_context, CompilerContext)


def test_std(eiko_std_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_file)

    test_resource = compiler.context.get("test_resource")
    assert isinstance(test_resource, EikoResource)
    assert test_resource.type == "CompileTestResource"

    test_2 = compiler.context.get("test_2")
    assert isinstance(test_2, EikoResource)
    assert test_2.type == "Test_2"
    assert test_2.properties.get("test") == test_resource


def test_from_import(tmp_path: Path) -> None:
    test_file_path = tmp_path / "test_from.eiko"
    with open(test_file_path, "w") as test_file:
        test_file.write("from std.test import CompileTestResource")

    compiler = Compiler()
    compiler.compile(test_file_path)
