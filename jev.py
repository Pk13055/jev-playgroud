#!/usr/bin/env -S uv run python
"""Ask Jev a typed TypeSafe question from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient, TypeSafeError

Mode = Literal["noul", "choice", "score"]


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def parse_choices(raw: str) -> list[str]:
    labels = [label.strip() for label in raw.split(",")]
    labels = [label for label in labels if label]
    if not labels:
        raise argparse.ArgumentTypeError("provide at least one non-empty choice")
    if len(labels) != len(set(labels)):
        raise argparse.ArgumentTypeError("choices must be unique")
    return labels


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask Jev a noul, choice, or score question.",
        epilog=(
            "Examples:\n"
            '  %(prog)s -m noul -q "Is the sky blue?" -s ""\n'
            '  %(prog)s -m noul -q "Does the customer request a refund?" -s ./ticket.txt\n'
            '  %(prog)s -m choice --choices calm,frustrated,angry -q "What is the tone?" -i ./ticket.txt\n'
            "\n"
            "-s/--state/-i is an empty string, or a path to a text file to read as state.\n"
            "Requires TYPESAFE_API_KEY."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-m",
        "--mode",
        required=True,
        choices=("noul", "choice", "choices", "score"),
        help="question type: noul, choice, or score",
    )
    parser.add_argument(
        "-q",
        "--query",
        required=True,
        help="the question to ask (TypeSafe instructions)",
    )
    parser.add_argument(
        "-i",
        "-s",
        "--state",
        dest="state",
        default="",
        help='empty string, or path to a text file to use as state',
    )
    parser.add_argument(
        "--choices",
        type=parse_choices,
        help="comma-separated options for choice mode, or ordered levels for score mode",
    )
    return parser.parse_args(argv)


def normalize_mode(mode: str) -> Mode:
    if mode == "choices":
        return "choice"
    return mode  # type: ignore[return-value]


def load_state(value: str) -> str:
    if value == "":
        return ""
    path = Path(value)
    try:
        return path.read_text()
    except OSError as error:
        raise SystemExit(f"error: cannot read state file {path}: {error}") from error


def build_question(mode: Mode, query: str, choices: list[str] | None) -> Noul | Choice | Score:
    if mode == "noul":
        if choices is not None:
            raise SystemExit("error: --choices is only used with -m choice or -m score")
        return Noul(instructions=query)
    if choices is None:
        kind = "options" if mode == "choice" else "ordered levels"
        raise SystemExit(f"error: --choices is required when -m {mode} ({kind})")
    if mode == "choice":
        return Choice(instructions=query, criteria={label: None for label in choices})
    return Score(instructions=query, criteria=choices)


def main(argv: list[str] | None = None) -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    args = parse_args(argv)
    mode = normalize_mode(args.mode)
    question = build_question(mode, args.query, args.choices)
    state = load_state(args.state)

    try:
        with TypeSafeClient() as client:
            response = client.system_one(state=state, questions={"query": question})
    except TypeSafeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    answer = response.answers["query"]
    print(json.dumps(answer.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
