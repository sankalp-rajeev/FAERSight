"""Cross-platform entry points for the first engineering milestone."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from faersight.config import load_experiment
from faersight.integration import ingest_experiment, prepare_sources, validate_mart
from faersight.mining import run_experiment
from faersight.pipeline import build_fixture, reproduce_fixture
from faersight.spotcheck import spotcheck_sources
from faersight.weka import run_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="faersight")
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("validate-config")
    config.add_argument("path", type=Path)
    config.add_argument("--require-frozen", action="store_true")
    mining = commands.add_parser("mine")
    mining.add_argument("database", type=Path)
    mining.add_argument("--output", type=Path, required=True)
    mining.add_argument("--config", type=Path, default=Path("config/mining.yaml"))
    mining.add_argument("--jar", type=Path, default=os.environ.get("WEKA_JAR"))
    mining.add_argument("--java")
    sensitivity = commands.add_parser("sensitivity")
    sensitivity.add_argument("database", type=Path)
    sensitivity.add_argument("--primary-run", type=Path, required=True)
    sensitivity.add_argument("--output", type=Path, required=True)
    sensitivity.add_argument("--config", type=Path, default=Path("config/sensitivity.yaml"))
    sensitivity.add_argument("--jar", type=Path, default=os.environ.get("WEKA_JAR"))
    sensitivity.add_argument("--java")
    for name in ("acquire", "ingest", "validate-mart", "spotcheck"):
        command = commands.add_parser(name)
        if name in ("validate-mart", "spotcheck"):
            command.add_argument("path", type=Path)
        if name != "validate-mart":
            command.add_argument("--config", type=Path, default=Path("config/experiment.yaml"))
            command.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
        if name == "ingest":
            command.add_argument(
                "--output", type=Path, default=Path("data/processed/2025Q4-statins")
            )
        if name == "spotcheck":
            command.add_argument("--per-stratum", type=int, default=5)
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
        elif args.command == "sensitivity":
            from faersight.sensitivity import run_sensitivity

            if args.jar is None:
                raise ValueError("Set WEKA_JAR or supply --jar PATH to WEKA 3.8.6")
            result = run_sensitivity(
                args.database,
                args.primary_run,
                args.output,
                config_path=args.config,
                jar=args.jar,
                java=args.java,
            )
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in result.items()
                        if k not in {"artifacts", "source_code_hashes"}
                    },
                    indent=2,
                )
            )
        elif args.command == "mine":
            if args.jar is None:
                raise ValueError("Set WEKA_JAR or supply --jar PATH to WEKA 3.8.6")
            result = run_experiment(
                args.database, args.output, config_path=args.config, jar=args.jar, java=args.java
            )
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in result.items()
                        if k not in {"artifacts", "source_code_hashes"}
                    },
                    indent=2,
                )
            )
        elif args.command == "acquire":
            sources = prepare_sources(args.config, args.raw_dir, download=True)
            for source in sources:
                print(f"Verified {source['quarter']}: {source['download']['sha256']}")
        elif args.command == "ingest":
            quality = ingest_experiment(args.config, args.raw_dir, args.output)
            print(json.dumps(quality, indent=2))
        elif args.command == "spotcheck":
            sources = prepare_sources(args.config, args.raw_dir)
            print(
                json.dumps(
                    spotcheck_sources(
                        args.path, sources, args.path.parent, per_stratum=args.per_stratum
                    ),
                    indent=2,
                )
            )
        elif args.command == "validate-mart":
            quality = validate_mart(args.path)
            print(json.dumps(quality, indent=2))
            if quality["status"] != "passed":
                return 1
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
