from typing import List
from .models import Peripheral, Register
from .errors import ValidationError


def check_duplicate_registers(peripheral: Peripheral) -> List[str]:
    errors = []
    seen = set()
    for reg in peripheral.registers:
        if reg.name in seen:
            errors.append(f"Duplicate register name: '{reg.name}'")
        seen.add(reg.name)
    return errors


def check_duplicate_bitfields(register: Register) -> List[str]:
    errors = []
    seen = set()
    for bf in register.bit_fields:
        if bf.name in seen:
            errors.append(f"Duplicate bit-field name '{bf.name}' in register '{register.name}'")
        seen.add(bf.name)
    return errors


def check_bitfield_boundary(register: Register, register_width: int) -> List[str]:
    errors = []
    for bf in register.bit_fields:
        if bf.bit_start < 0 or bf.bit_width <= 0:
            errors.append(
                f"Invalid bit-field '{bf.name}' in '{register.name}': "
                f"bit_start={bf.bit_start}, bit_width={bf.bit_width} must be >= 0 and > 0"
            )
            continue
        end_bit = bf.bit_start + bf.bit_width - 1
        if end_bit >= register_width:
            errors.append(
                f"Bit-field '{bf.name}' in '{register.name}' exceeds register width: "
                f"occupies bits {bf.bit_start}-{end_bit}, but register is only {register_width} bits wide"
            )
    return errors


def check_register_overlap(peripheral: Peripheral) -> List[str]:
    errors = []
    sorted_regs = sorted(peripheral.registers, key=lambda r: r.offset)
    for a, b in zip(sorted_regs, sorted_regs[1:]):
        a_end = a.offset + a.size_bytes
        if a_end > b.offset:
            errors.append(
                f"Register overlap: '{a.name}' (0x{a.offset:02X}-0x{a_end - 1:02X}) "
                f"overlaps '{b.name}' (starts 0x{b.offset:02X})"
            )
    return errors


def check_bitfield_overlap(register: Register) -> List[str]:
    errors = []
    sorted_fields = sorted(register.bit_fields, key=lambda f: f.bit_start)
    for a, b in zip(sorted_fields, sorted_fields[1:]):
        a_end = a.bit_start + a.bit_width
        if a_end > b.bit_start:
            errors.append(
                f"Bit-field overlap in '{register.name}': '{a.name}' "
                f"(bits {a.bit_start}-{a_end - 1}) overlaps '{b.name}' (starts bit {b.bit_start})"
            )
    return errors


def validate(peripheral: Peripheral) -> None:
    """Runs every static check and raises one ValidationError listing ALL problems found,
    rather than stopping at the first one."""
    errors: List[str] = []
    errors.extend(check_duplicate_registers(peripheral))
    errors.extend(check_register_overlap(peripheral))

    for register in peripheral.registers:
        errors.extend(check_duplicate_bitfields(register))
        errors.extend(check_bitfield_boundary(register, peripheral.register_width))
        errors.extend(check_bitfield_overlap(register))

    if errors:
        message = f"Validation failed for peripheral '{peripheral.name}' with {len(errors)} error(s):\n"
        message += "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(message)