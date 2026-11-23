"""Pre-deploy gate. Every check must not fail before anything goes live.

Usage: python preflight.py --project . --host cloudflare-pages [--build-cmd "npm run build"]
Exit 1 if any check fails. Warnings do not block.
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

from freetier_check import stale_entries
from secret_scan import scan

DATA_DIR = Path(__file__).resolve().parent.parent


class Check(NamedTuple):
    name: str
    status: str
    detail: str


def _build(project: Path, build_cmd: str | None) -> Check:
    if not build_cmd:
        return Check("build", "warn", "No build command given, so the build was not checked.")
    result = subprocess.run(build_cmd, shell=True, cwd=project, capture_output=True, text=True)
    if result.returncode != 0:
        return Check("build", "fail", f"'{build_cmd}' exited with {result.returncode}.")
    return Check("build", "pass", f"'{build_cmd}' succeeded.")


def _secrets(project: Path) -> Check:
    hits = scan(project)
    if hits:
        where = ", ".join(f"{h.path.name}:{h.line}" for h in hits[:5])
        return Check("secrets", "fail", f"{len(hits)} possible secret(s): {where}. Move them to host env vars.")
    return Check("secrets", "pass", "No secrets found.")


def _env_example(project: Path) -> Check:
    if (project / ".env.example").exists():
        return Check("env-example", "pass", ".env.example lists the env var names.")
    return Check("env-example", "fail", "Add .env.example listing every env var NAME (no values).")


def _gitignore(project: Path) -> Check:
    path = project / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if any(line.strip() in (".env", ".env*", ".env.*") for line in lines):
        return Check("gitignore-env", "pass", ".env files are ignored by git.")
    return Check("gitignore-env", "fail", "Add .env to .gitignore so secrets are never committed.")


def _headers(project: Path, host: str) -> Check:
    if host.startswith("cloudflare-") or host == "github-pages":
        for rel in ("_headers", "public/_headers"):
            path = project / rel
            if path.exists() and "X-Content-Type-Options" in path.read_text(encoding="utf-8"):
                return Check("headers", "pass", f"Security headers set in {rel}.")
        configs = list(project.glob("next.config.*"))
        for config in configs:
            if "headers(" in config.read_text(encoding="utf-8"):
                return Check("headers", "pass", f"Security headers set in {config.name}.")
        if host == "cloudflare-workers" and not (project / "public").is_dir() and not configs:
            return Check("headers", "warn", "API-only Worker (no public/ folder): set headers on responses that "
                                            "return HTML; JSON-only webhooks need none.")
        return Check("headers", "fail", "Add security headers in public/_headers (overlay security-headers-cloudflare).")
    if host.startswith("vercel-"):
        vercel_json = project / "vercel.json"
        if vercel_json.exists():
            try:
                if "headers" in json.loads(vercel_json.read_text(encoding="utf-8")):
                    return Check("headers", "pass", "Security headers set in vercel.json.")
            except json.JSONDecodeError:
                return Check("headers", "fail", "vercel.json is not valid JSON.")
        for config in project.glob("next.config.*"):
            if "headers(" in config.read_text(encoding="utf-8"):
                return Check("headers", "pass", f"Security headers set in {config.name}.")
        return Check("headers", "fail", "Add security headers in vercel.json (overlay security-headers-vercel).")
    return Check("headers", "warn", "Set security headers in the app for this host.")


def _limits(tiers: dict, today: date) -> Check:
    stale = stale_entries(tiers, today)
    if stale:
        return Check("limits", "warn", f"Free-tier data older than 90 days: {', '.join(stale)}.")
    return Check("limits", "pass", "Free-tier data is fresh.")


def run_preflight(project: Path, host: str, build_cmd: str | None, tiers: dict, today: date) -> list[Check]:
    project = Path(project)
    return [
        _build(project, build_cmd),
        _secrets(project),
        _env_example(project),
        _gitignore(project),
        _headers(project, host),
        _limits(tiers, today),
    ]


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Pre-deploy gate.")
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--host", required=True)
    parser.add_argument("--build-cmd")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    tiers = json.loads((args.data_dir / "free-tiers.json").read_text(encoding="utf-8"))
    checks = run_preflight(args.project, args.host, args.build_cmd, tiers, date.today())
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for check in checks:
        print(f"| {check.name} | {check.status.upper()} | {check.detail} |")
    failed = [c.name for c in checks if c.status == "fail"]
    print("Preflight FAILED: " + ", ".join(failed) if failed else "Preflight passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
