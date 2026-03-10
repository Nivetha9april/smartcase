"""
smartcase/cli.py
----------------
Command-line interface for SmartCase.

Usage examples:
    smartcase "Hello world, apple is a company."
    smartcase "some text" --model en_core_web_trf
    smartcase --file input.txt
    smartcase --file input.txt --output cleaned.txt
    smartcase --file input.txt --explain
    echo "pipe text here" | smartcase
"""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartcase",
        description=(
            "SmartCase — NER-aware text cleaner that preserves important "
            "capitalization (named entities, acronyms, brands) during NLP preprocessing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  smartcase "apple bought beats. NASA launched a rocket."
  smartcase --file input.txt --output cleaned.txt
  smartcase --file input.txt --explain
  cat raw.txt | smartcase
        """,
    )

    # ── Input (mutually exclusive: inline text OR --file OR stdin pipe) ────
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "text",
        nargs="?",
        metavar="TEXT",
        help="Inline text to clean (wrap in quotes).",
    )
    input_group.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to a plain-text file to clean.",
    )

    # ── Output ─────────────────────────────────────────────────────────────
    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="Write cleaned text to this file instead of printing to terminal.",
    )

    # ── Options ────────────────────────────────────────────────────────────
    parser.add_argument(
        "--explain", "-e",
        action="store_true",
        help="Show which tokens were preserved as named entities or acronyms.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress info messages — only output the cleaned text.",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Print SmartCase version and exit.",
    )

    return parser


def read_input(args) -> str:
    """Return raw input text from inline arg, --file, or stdin pipe."""
    if args.text:
        return args.text
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                return fh.read()
        except FileNotFoundError:
            print(f"[smartcase] Error: file not found — {args.file}", file=sys.stderr)
            sys.exit(1)
        except OSError as exc:
            print(f"[smartcase] Error reading file: {exc}", file=sys.stderr)
            sys.exit(1)
    # Fallback: read from stdin (pipe mode)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def write_output(text: str, path: str) -> None:
    """Write cleaned text to a file or print to stdout."""
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"[smartcase] Saved to {path}", file=sys.stderr)
    else:
        print(text)


def explain_cleaning(original: str, cleaned: str) -> None:
    """
    Compare original vs cleaned text and print which tokens were preserved.
    Sends output to stderr so it doesn't pollute stdout when piping.
    """
    import re

    original_tokens = original.split()

    print("\n── SmartCase Explain Report ──", file=sys.stderr)
    print(f"  Original tokens : {len(original_tokens)}", file=sys.stderr)

    preserved = []
    for token in original_tokens:
        # A token was "preserved" if it appears as-is (not lowercased) in cleaned output
        clean_word = re.sub(r'[^A-Za-z0-9]', '', token)
        if clean_word and clean_word in cleaned and clean_word != clean_word.lower():
            reason = "ACRONYM" if clean_word.isupper() and len(clean_word) <= 5 else "NAMED ENTITY"
            preserved.append((clean_word, reason))

    if preserved:
        print(f"\n  Preserved ({len(preserved)} tokens):", file=sys.stderr)
        for token, reason in preserved:
            print(f"    • {token:<25} [{reason}]", file=sys.stderr)
    else:
        print("\n  No tokens preserved (all text was lowercased).", file=sys.stderr)

    print(file=sys.stderr)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Version flag ───────────────────────────────────────────────────────
    if args.version:
        try:
            from smartcase import __version__
            print(f"SmartCase {__version__}")
        except ImportError:
            print("SmartCase (version unknown)")
        sys.exit(0)

    # ── Read input ─────────────────────────────────────────────────────────
    raw_text = read_input(args)

    if raw_text is None:
        parser.print_help()
        sys.exit(0)

    raw_text = raw_text.strip()
    if not raw_text:
        print("[smartcase] Warning: input is empty.", file=sys.stderr)
        sys.exit(0)

    # ── Import your clean_text function ────────────────────────────────────
    try:
        from smartcase.cleaner import clean_text
    except ImportError:
        try:
            from smartcase import clean_text
        except ImportError:
            print(
                "[smartcase] Error: Could not import clean_text.\n"
                "  Make sure SmartCase is installed: pip install smartcase",
                file=sys.stderr,
            )
            sys.exit(1)

    # ── Info header (only shown in terminal, not when piping) ──────────────
    if not args.quiet and not args.output and sys.stderr.isatty():
        print("[smartcase] Running NER-aware text cleaning...\n", file=sys.stderr)

    # ── Run clean_text ─────────────────────────────────────────────────────
    try:
        cleaned = clean_text(raw_text)
    except OSError:
        print(
            "[smartcase] Error: spaCy model 'en_core_web_sm' not found.\n"
            "  Run: python -m spacy download en_core_web_sm",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Explain report ─────────────────────────────────────────────────────
    if args.explain:
        explain_cleaning(raw_text, cleaned)

    # ── Output ─────────────────────────────────────────────────────────────
    write_output(cleaned, args.output)


if __name__ == "__main__":
    main()
