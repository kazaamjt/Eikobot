# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.decorator import index_decorator
from eikobot.core.compiler.definitions.base_types import EikoResource


def test_decorator(eiko_decorator_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_decorator_file)

    _index_decorator = compiler.context.get("index")
    assert _index_decorator is index_decorator

    _command_res = compiler.context.get("cmd")
    assert isinstance(_command_res, EikoResource)
    assert _command_res.index() == "TCommand-127.0.0.1-echo test"
