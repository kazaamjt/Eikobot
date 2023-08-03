"""
The nuts and bolts of Eikobot.
"""


def human_readable(number: int) -> str:
    """
    Turns a large integer representing bytes
    in to a human readable string.
    """
    number = number // 8
    for unit in ["", "K", "M", "G", "T"]:
        if number < 10240:
            return f"{number}{unit}B"
        number = number // 1024
    return f"{number}PB"


def machine_readable(number: str) -> int:
    """
    Turns a human readable number of bytes in to an integer.
    """
    if number.isdigit():
        return int(number)

    if number.endswith("B"):
        return int(number[:-1])

    if number.endswith("KB"):
        return int(number[:-2]) * 1024

    if number.endswith("MB"):
        return int(number[:-2]) * 1024**2

    if number.endswith("GB"):
        return int(number[:-2]) * 1024**3

    if number.endswith("TB"):
        return int(number[:-2]) * 1024**4

    if number.endswith("PB"):
        return int(number[:-2]) * 1024**5

    raise ValueError(f"Cannot convert value of '{number}' to an integer.")
