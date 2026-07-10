from dataclasses import dataclass, field
from typing import List

@dataclass
class BitField:
    name: str
    bit_start: int
    bit_width: int

@dataclass
class Register:
    name: str
    offset: int          # already converted from hex string
    access: str
    bit_fields: List[BitField] = field(default_factory=list)
    size_bytes: int = 4   # derived from register_width, set at load time

@dataclass
class Peripheral:
    name: str
    base_address: int
    register_width: int
    registers: List[Register] = field(default_factory=list)