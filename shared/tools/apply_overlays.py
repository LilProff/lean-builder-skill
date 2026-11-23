"""Copy small overlay files onto a project made by an official starter.

Usage: python apply_overlays.py --ids claude-md-lean,status-md --project . --values values.json [--force]

Each overlay lives in shared/overlays/<id>/ with overlay.json and a files/ folder.
{{KEY}} placeholders are filled from the values. Existing files are never overwritten without --force.
Append-mode files only add lines that are missing.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

OVERLAYS_DIR = Path(__file__).resolve().parent.parent / "overlays"
PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class ApplyReport(NamedTuple):
    created: list[str]
    appended: list[str]
    skipped: list[str]


def _load(ids: list[str], overlays_dir: Path) -> list[tuple[Path, dict]]:
    loaded = []
    for overlay_id in ids:
        manifest = overlays_dir / overlay_id / "overlay.json"
        if not manifest.exists():
            raise KeyError(f"Unknown overlay: {overlay_id}")
        loaded.append((manifest.parent, json.loads(manifest.read_text(encoding="utf-8"))))
    return loaded


def _render(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], text)


def apply(ids: list[str], project: Path, overlays_dir: Path, values: dict[str, str],
          force: bool = False) -> ApplyReport:
    project = Path(project)
    loaded = _load(ids, Path(overlays_dir))

    sources = []
    missing: set[str] = set()
    for folder, manifest in loaded:
        for entry in manifest["files"]:
            text = (folder / "files" / entry["src"]).read_text(encoding="utf-8")
            missing |= {key for key in PLACEHOLDER.findall(text) if key not in values}
            sources.append((entry, text))
    if missing:
        raise KeyError(f"Missing values for: {', '.join(sorted(missing))}")

    report = ApplyReport([], [], [])
    for entry, text in sources:
        dest = project / entry["dest"]
        content = _render(text, values)
        if entry["mode"] == "append" and dest.exists():
            existing = dest.read_text(encoding="utf-8")
            have = {line.strip() for line in existing.splitlines()}
            new = [line for line in content.splitlines() if line.strip() and line.strip() not in have]
            if new:
                sep = "" if existing.endswith("\n") or not existing else "\n"
                dest.write_text(existing + sep + "\n".join(new) + "\n", encoding="utf-8")
                report.appended.append(entry["dest"])
            else:
                report.skipped.append(entry["dest"])
            continue
        if dest.exists() and not force:
            report.skipped.append(entry["dest"])
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        report.created.append(entry["dest"])
    return report


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Apply lean-builder overlays to a project.")
    parser.add_argument("--ids", required=True, help="comma-separated overlay ids")
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--values", type=Path, help="JSON object of placeholder values")
    parser.add_argument("--overlays-dir", type=Path, default=OVERLAYS_DIR)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    values = json.loads(args.values.read_text(encoding="utf-8")) if args.values else {}
    try:
        report = apply([i.strip() for i in args.ids.split(",") if i.strip()], args.project,
                       args.overlays_dir, values, args.force)
    except KeyError as err:
        print(str(err).strip("'\""), file=sys.stderr)
        return 2
    for label, items in (("Created", report.created), ("Appended to", report.appended),
                         ("Skipped (already there)", report.skipped)):
        if items:
            print(f"{label}: {', '.join(items)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
