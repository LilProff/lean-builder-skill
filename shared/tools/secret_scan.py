"""Scan a project for things that look like real secrets before a push.

Usage: python secret_scan.py <project folder>
Prints "path:line kind" for each hit and never prints the secret itself. Exit 1 on any hit.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from secret_patterns import PATTERNS

SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", ".venv", "__pycache__", ".wrangler"}
MAX_BYTES = 2 * 1024 * 1024


class Hit(NamedTuple):
    path: Path
    line: int
    kind: str


def _is_env_file(name: str) -> bool:
    return (name == ".env" or name.startswith(".env.")) and name != ".env.example"


def _env_file_is_safe(root: Path, path: Path) -> bool:
    """In a git repo, an env file that git ignores and does not track never reaches the remote.
    Without .git (or without git installed) every env file is reported, as before."""
    if not (root / ".git").exists():
        return False
    try:
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(path)],
                                 capture_output=True).returncode == 0
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(path)],
                                 capture_output=True).returncode == 0
    except OSError:
        return False
    return ignored and not tracked


def _is_binary(path: Path) -> bool:
    with open(path, "rb") as handle:
        return b"\x00" in handle.read(8192)


def _scan_file(path: Path) -> list[Hit]:
    hits = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in PATTERNS.items():
            if pattern.search(line):
                hits.append(Hit(path, number, kind))
                break
    return hits


def scan(root: Path) -> list[Hit]:
    root = Path(root)
    hits: list[Hit] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            path = Path(current) / name
            if _is_env_file(name):
                if not _env_file_is_safe(root, path):
                    hits.append(Hit(path, 0, "env-file"))
                continue
            try:
                if path.stat().st_size > MAX_BYTES or _is_binary(path):
                    continue
                hits.extend(_scan_file(path))
            except OSError:
                continue
    return sorted(hits, key=lambda h: (str(h.path), h.line))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path(".")
    hits = scan(root)
    for hit in hits:
        print(f"{hit.path}:{hit.line} {hit.kind}")
    if hits:
        print(f"{len(hits)} possible secret(s) found. Move them to the host's environment variables.")
        return 1
    print("No secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
