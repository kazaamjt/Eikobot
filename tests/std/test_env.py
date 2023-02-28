# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.helpers import EikoDict, EikoProtectedStr


def test_secrets_file(tmp_eiko_file: Path) -> None:
    secrets = tmp_eiko_file.parent / "secrets"
    secrets.write_text("secret_1=hehe\nsecret_2=hehe 2")
    model = """
from std import env

secrets = env.secrets_file(__file__.parent / "secrets")
"""
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write(model)

    compiler = Compiler()
    compiler.compile(tmp_eiko_file)

    eiko_secrets = compiler.context.get("secrets")
    assert isinstance(eiko_secrets, EikoDict)

    secret_1 = eiko_secrets.elements.get("secret_1")
    assert isinstance(secret_1, EikoProtectedStr)
    assert secret_1.value == "hehe"

    secret_2 = eiko_secrets.elements.get("secret_2")
    assert isinstance(secret_2, EikoProtectedStr)
    assert secret_2.value == "hehe 2"
