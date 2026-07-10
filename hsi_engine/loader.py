import json, yaml
from .models import Peripheral, Register, BitField
from .errors import ConfigLoadError

def load_config(path: str) -> Peripheral:
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) if path.endswith((".yml", ".yaml")) else json.load(f)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ConfigLoadError(f"Could not parse '{path}': {e}")

    try:
        registers = []
        for r in raw["registers"]:
            bit_fields = [BitField(**bf) for bf in r.get("bit_fields", [])]
            registers.append(Register(
                name=r["name"],
                offset=int(r["offset"], 16),
                access=r["access"],
                bit_fields=bit_fields,
                size_bytes=raw.get("register_width", 32) // 8,
            ))
        return Peripheral(
            name=raw["peripheral_name"],
            base_address=int(raw["base_address"], 16),
            register_width=raw.get("register_width", 32),
            registers=registers,
        )
    except KeyError as e:
        raise ConfigLoadError(f"Missing required field {e} in '{path}'")