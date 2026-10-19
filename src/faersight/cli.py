"""Cross-platform entry points for the first engineering milestone."""

import argparse
import os
import subprocess
from pathlib import Path

from faersight.config import load_experiment
from faersight.pipeline import build_fixture, reproduce_fixture
from faersight.weka import run_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="faersight")
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("validate-config")
    config.add_argument("path", type=Path)
    config.add_argument("--require-frozen", action="store_true")
    for name in ("build-fixture-arff", "reproduce-fixture", "weka-smoke"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path, default=Path("artifacts/generated/fixture"))
        if name != "weka-smoke":
            command.add_argument("--fixtures", type=Path, default=Path("tests/fixtures"))
        if name != "build-fixture-arff":
            command.add_argument("--jar", type=Path, default=os.environ.get("WEKA_JAR"))
            command.add_argument("--java")
        if name == "weka-smoke":
            command.add_argument(
                "--arff", type=Path, default=Path("tests/fixtures/toy_presence.arff")
            )
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-config":
            _, pending = load_experiment(args.path, require_frozen=args.require_frozen)
            print(
                "Configuration valid. "
                + ("Pending: " + ", ".join(pending) if pending else "No pending scope values.")
            )
        elif args.command == "build-fixture-arff":
            result = build_fixture(args.fixtures, args.output)
            print(f"Synthetic fixture: N={result['eligible_n']}; output: {args.output}")
        else:
            if args.jar is None:
                raise ValueError("Set WEKA_JAR or supply --jar PATH to WEKA 3.8.6")
            if args.command == "weka-smoke":
                rules = run_smoke(args.arff, args.output / "weka", jar=args.jar, java=args.java)
                print(f"WEKA presence-only smoke passed: {len(rules)} accepted rule(s)")
            else:
                result = reproduce_fixture(args.fixtures, args.output, jar=args.jar, java=args.java)
                print(
                    f"Synthetic end-to-end pipeline passed: N={result['eligible_n']}; "
                    f"output: {args.output}"
                )
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
