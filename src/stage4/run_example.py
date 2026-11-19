"""Run the E-value calculator on a JSON input table and print its results.

Usage: python run_example.py TABLE.json

TABLE.json holds a list of entries in the same format the calibration prompt asks
the model to produce (see src/prompts/evalue_calibration_v11.md, "Part A format").
`example_table.json` has two worked examples from VanderWeele & Ding (2017).

This wrapper exists so that evalue_calc.py itself stays byte-for-byte identical to
the copy embedded in the prompt.
"""
import json
import sys
from pathlib import Path

from evalue_calc import run_table


def main(path: str) -> int:
    """Load the table at `path`, run the calculator on it, and return an exit code."""
    try:
        table = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"{path} is not valid JSON: {e}", file=sys.stderr)
        return 2
    run_table(table)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[2])
    sys.exit(main(sys.argv[1]))
