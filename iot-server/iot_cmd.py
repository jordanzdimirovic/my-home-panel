import enum
from typing import Tuple

SUPPORTED_COMMAND_TYPES = {
    "kasaplug": [
        "switch"
    ]
}

REQUIRED_PARAMS = {
    "switch": ["state"]
}

def ensure_params_satisfy(cmd, params):
    for param in params:
        if param not in REQUIRED_PARAMS[cmd]:
            return False

    return True

class IOTCommand: pass

class SwitchCommand(IOTCommand):
    """Represents a command that can turn on / off a device"""
    def __init__(self, state: bool):
        self.state = state

class ColourCommand(IOTCommand):
    """Represents a command that can change a colour"""
    def __init__(self, rgb: Tuple[int, int, int]):
        self.rgb = rgb
