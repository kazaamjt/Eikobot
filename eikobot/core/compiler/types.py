from typing import Union


class EikoBaseType:
    def __init__(self, eiko_type: str) -> None:
        self.type = eiko_type


class EikoInt(EikoBaseType):
    def __init__(self, value: int) -> None:
        super().__init__("int")
        self.value = value


class EikoFloat(EikoBaseType):
    def __init__(self, value: float) -> None:
        super().__init__("float")
        self.value = value


EikoNumber = Union[EikoInt, EikoFloat]


class EikoBool(EikoBaseType):
    def __init__(self, value: bool) -> None:
        super().__init__("bool")
        self.value = value


class EikoStr(EikoBaseType):
    def __init__(self, value: str) -> None:
        super().__init__("str")
        self.value = value
