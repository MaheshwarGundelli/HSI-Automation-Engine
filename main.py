import sys, argparse
from hsi_engine.loader import load_config
from hsi_engine.validator import validate
from hsi_engine.codegen import generate_header
from hsi_engine.errors import ConfigLoadError, ValidationError

def main():
    parser = argparse.ArgumentParser(description="Hardware-Software Interface Automation Engine")
    parser.add_argument("config", help="Path to peripheral config (JSON or YAML)")
    parser.add_argument("-o", "--output", default="output/peripheral.h")
    args = parser.parse_args()

    try:
        peripheral = load_config(args.config)
        validate(peripheral)                       # raises ValidationError with all issues
        generate_header(peripheral, args.output)
        print(f"[OK] Generated {args.output} from {args.config}")
    except (ConfigLoadError, ValidationError) as e:
        print(f"[FAILED] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()