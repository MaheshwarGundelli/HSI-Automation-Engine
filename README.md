# HSI Automation Engine

**Hardware-Software Interface Automation Engine** — a Python tool that reads a hardware peripheral configuration (JSON/YAML) and automatically generates a production-grade, safety-validated embedded C header file.

Manually transcribing register maps from microcontroller datasheets into C structs and bitmask macros is slow and error-prone — a single wrong bit position or overlapping offset doesn't throw a compiler error, it silently breaks hardware behavior. This tool treats the register map as **data**: describe a peripheral once in a config file, run it through a static validation engine, and generate a correct, well-formatted C header every time.

---

## Features

- **Config-driven** — define peripherals, registers, and bit-fields in JSON or YAML instead of hand-writing C.
- **Static validation before code generation:**
  - Register overlap detection (no two registers may share overlapping memory offsets)
  - Bit-field boundary checking (a field can't exceed its register's bit width)
  - Duplicate name detection (registers and bit-fields within a peripheral)
  - All errors are collected and reported together, not one-at-a-time
- **Production-style C output:**
  - Fixed-width types (`uint32_t`, etc.) via `<stdint.h>`
  - `volatile`-qualified struct fields to prevent compiler optimization of hardware reads/writes
  - Automatic padding (`RESERVED` fields) when register offsets have gaps
  - Auto-generated `_Pos` / `_Msk` / shift-mask macros for every bit-field
  - Header guards, base-address pointer macro, and a generated-file warning comment
- **Modular architecture** — separate loader, validator, and code generator, each independently testable.

---

## Project Structure

```
hsi-engine/
├── hsi_engine/
│   ├── __init__.py
│   ├── models.py       # Peripheral / Register / BitField data classes
│   ├── loader.py        # Reads JSON/YAML into model objects
│   ├── validator.py     # Overlap, boundary, and duplicate checks
│   ├── codegen.py       # Generates the .h file
│   └── errors.py        # Custom exception types
├── configs/
│   ├── uart_valid.json
│   ├── uart_overlap_error.json      # deliberately broken, demonstrates validation
│   └── uart_boundary_error.json     # deliberately broken, demonstrates validation
├── output/               # Generated headers land here
├── tests/
│   └── test_validator.py
├── main.py               # CLI entry point
└── README.md
```

---

## Installation

```bash
git clone https://github.com/<your-username>/hsi-engine.git
cd hsi-engine

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install pyyaml pytest
```

---

## Usage

Generate a header from a config file:

```bash
python main.py configs/uart_valid.json -o output/uart0.h
```

On success:
```
[OK] Generated output/uart0.h from configs/uart_valid.json
```

On a validation failure (see the deliberately broken example configs), the tool exits with a non-zero status and prints every problem found, without generating any output:
```
[FAILED] Validation failed for peripheral 'UART0' with 1 error(s):
  - Register overlap: 'CTRL' (0x00-0x03) overlaps 'STATUS' (starts 0x02)
```

Run the test suite:
```bash
python -m pytest tests/
```

---

## Config Schema

```json
{
  "peripheral_name": "UART0",
  "base_address": "0x40011000",
  "register_width": 32,
  "registers": [
    {
      "name": "CTRL",
      "offset": "0x00",
      "access": "RW",
      "bit_fields": [
        {"name": "ENABLE", "bit_start": 0, "bit_width": 1},
        {"name": "PARITY", "bit_start": 1, "bit_width": 2}
      ]
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `peripheral_name` | string | Name used for the struct type, header guard, and macro prefixes |
| `base_address` | hex string | Base memory address of the peripheral |
| `register_width` | int | Bit width of each register (8/16/32/64) |
| `registers[].name` | string | Register name |
| `registers[].offset` | hex string | Byte offset from `base_address` |
| `registers[].access` | string | `RO`, `WO`, or `RW` |
| `registers[].bit_fields[].name` | string | Bit-field name |
| `registers[].bit_fields[].bit_start` | int | Starting bit position |
| `registers[].bit_fields[].bit_width` | int | Number of bits the field occupies |

---

## Example Output

```c
typedef struct {
    volatile uint32_t CTRL;              /* Offset: 0x00  (Read-Write) */
    volatile uint32_t STATUS;            /* Offset: 0x04  (Read-Only) */
    volatile uint32_t DATA;              /* Offset: 0x08  (Read-Write) */
} UART0_Type;

#define UART0   ((UART0_Type *) 0x40011000UL)

#define UART0_CTRL_PARITY_Pos          (1U)
#define UART0_CTRL_PARITY_Msk          (0x6U)
#define UART0_CTRL_PARITY(x)           (((x) << UART0_CTRL_PARITY_Pos) & UART0_CTRL_PARITY_Msk)
```

Usage in firmware:
```c
UART0->CTRL |= UART0_CTRL_PARITY(2);
```

---

## Design Notes

- **Struct layout over pointer-casting** — a single base pointer with a struct lets the compiler compute member offsets, matching how vendor HALs (e.g. CMSIS) expose peripherals, instead of hand-deriving `BASE + OFFSET` at every register access.
- **`volatile` on every field** — hardware can change a register's value independently of program flow (e.g. a status flag on receive-complete); `volatile` prevents the compiler from caching a stale value.
- **Fail with all errors, not the first one** — the validator collects every violation across every register before raising, so a user fixes all their config mistakes in one pass.

---

## Possible Extensions

- Enforce `access` permissions at codegen time (`const volatile` for read-only registers)
- Explicit reserved/undocumented-bit checking within a register, not just gaps between registers
- SVD file import, to ingest real vendor-published register specs directly

---
