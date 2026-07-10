import pytest
from hsi_engine.models import Peripheral, Register, BitField
from hsi_engine.validator import validate
from hsi_engine.errors import ValidationError


def make_valid_peripheral():
    return Peripheral(
        name="UART0",
        base_address=0x40011000,
        register_width=32,
        registers=[
            Register(name="CTRL", offset=0x00, access="RW", size_bytes=4, bit_fields=[
                BitField(name="ENABLE", bit_start=0, bit_width=1),
                BitField(name="PARITY", bit_start=1, bit_width=2),
            ]),
            Register(name="STATUS", offset=0x04, access="RO", size_bytes=4, bit_fields=[
                BitField(name="TX_EMPTY", bit_start=0, bit_width=1),
            ]),
            Register(name="DATA", offset=0x08, access="RW", size_bytes=4, bit_fields=[]),
        ],
    )


def test_valid_peripheral_passes():
    validate(make_valid_peripheral())  # should not raise


def test_register_overlap_detected():
    peripheral = make_valid_peripheral()
    peripheral.registers[1].offset = 0x02  # STATUS now overlaps CTRL (0x00-0x03)
    with pytest.raises(ValidationError, match="overlap"):
        validate(peripheral)


def test_bitfield_boundary_violation_detected():
    peripheral = make_valid_peripheral()
    peripheral.registers[0].bit_fields.append(
        BitField(name="BAD_FIELD", bit_start=30, bit_width=4)  # exceeds 32-bit width
    )
    with pytest.raises(ValidationError, match="exceeds register width"):
        validate(peripheral)


def test_duplicate_register_name_detected():
    peripheral = make_valid_peripheral()
    peripheral.registers.append(Register(name="CTRL", offset=0x0C, access="RW", size_bytes=4))
    with pytest.raises(ValidationError, match="Duplicate register name"):
        validate(peripheral)


def test_duplicate_bitfield_name_detected():
    peripheral = make_valid_peripheral()
    peripheral.registers[0].bit_fields.append(
        BitField(name="ENABLE", bit_start=5, bit_width=1)  # duplicate of existing ENABLE
    )
    with pytest.raises(ValidationError, match="Duplicate bit-field"):
        validate(peripheral)


def test_bitfield_overlap_detected():
    peripheral = make_valid_peripheral()
    peripheral.registers[0].bit_fields.append(
        BitField(name="OVERLAP_FIELD", bit_start=0, bit_width=2)  # overlaps ENABLE (bit 0)
    )
    with pytest.raises(ValidationError, match="Bit-field overlap"):
        validate(peripheral)