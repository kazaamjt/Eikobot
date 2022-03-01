from eikobot.core.plugin import eiko_plugin


@eiko_plugin
def add_string(string_1: str, string_2: str) -> str:
    return string_1 + string_2
