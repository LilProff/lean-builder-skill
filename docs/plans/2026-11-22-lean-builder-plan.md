# lean-builder-skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public Claude Code plugin of 11 skills that picks the cheapest stack for a build (website, SaaS, internal tool, AI agent) in a personal, client or startup context, writes the plan and cost sheet, scaffolds from official starters plus small overlays, deploys behind a preflight gate and hands off.

**Architecture:** Skills are Markdown (`skills/<name>/SKILL.md`). Every decision a test can pin lives in data (`shared/stacks.json`, `shared/free-tiers.json`) and small stdlib Python tools (`shared/tools/*.py`), so picking a stack costs no model calls and is deterministic. Overlays are small file sets copied onto official starters by `apply_overlays.py`; their testable logic is dependency-free TypeScript run with `node --test`.

**Tech Stack:** Python 3.12 stdlib (tools), pytest + jsonschema (tests only), TypeScript with Node 24 built-in type stripping and `node:test` (overlay logic), GitHub Actions (CI).

**Spec:** `docs/specs/2026-11-22-lean-builder-design.md` (approved 22 Nov 2026). Read it before any task.

## Global Constraints

- Repo root is `lean-builder-skill/` (workspace folder). All commands run from the repo root.
- `shared/tools/*.py`: Python 3 standard library only. Test deps live only in `requirements-dev.txt`: `pytest>=8`, `jsonschema>=4.23`.
- Overlay TypeScript logic files import nothing outside the Web platform (`crypto.subtle`, `fetch`, `TextEncoder`). Framework glue files (Hono routers, Next.js routes) are thin and untested. Relative imports use explicit `.ts` extensions (Node type stripping needs them).
- Node used for tests: 24.x (local is v24.14.0). Python: 3.12.
- Every CLI calls `sys.stdout.reconfigure(encoding="utf-8")` first and writes files as UTF-8 (Windows consoles default to cp1252; output contains `₦`).
- Plugin identity: name `lean-builder-skill`, version `0.1.0`, license MIT, author `Samuel Sholarin` (`https://lilproff.github.io/sasdev/`), repo `https://github.com/LilProff/lean-builder-skill`.
- Private profile path: `~/.claude/lean-builder/profile.md`. Secret VALUES never appear in it, in any repo file, or in any output.
- Skills find shared files from the "Base directory for this skill" line Claude Code prints when a skill loads: `<base>/../../shared/`.
- Copy rules (all user-facing text, skills included): plain English, short sentences, no em dashes (U+2014) or en dashes (U+2013), no invented users, results or testimonials.
- Free-tier figures come only from official provider pages, each with `source_url` and `checked_on` (YYYY-MM-DD). If a figure cannot be found, omit it and add a `notes` line. Never guess.
- Staleness threshold: 90 days.
- **Commits:** Samuel's rule is "commit and push only when he asks". Each "Commit" step runs only if he has authorised commits for this repo; otherwise stage with `git add` and move on. Never push.
- **Spec refinement (needed for account matching):** in `free-tiers.json` the field `account` is an account id string (or `null` for frameworks with no account), not a boolean. Account ids: `vercel`, `cloudflare`, `github`, `gcp`, `render`, `supabase`, `neon`, `resend`, `openrouter`, `paystack`, `grey`, `n8n-selfhosted`, `meta`, `telegram`. The profile's `accounts` list uses these ids.

## Review Focus

1. **No profile, or a hand-edited profile with a typo**: picking must still work (defaults kept, a note says no profile was read) and a malformed front matter line gives an error naming the line, not a stack trace. Tests in Task 4 and Task 5.
2. **Windows console (cp1252) printing `₦`**: tools must not crash with `UnicodeEncodeError`. Test in Task 5.
3. **Overlays applied onto a project that already has `CLAUDE.md`, `.gitignore` or `.env.example`**: never overwrite the user's file without `--force`; append mode adds only missing lines. Tests in Task 9.
4. **Secret scan on a real project** (node_modules, lockfiles, large binaries, a committed `.env`): must skip vendored and binary files without crashing, and must flag a real `.env`. Tests in Task 7.
5. **A personal SaaS that starts charging**: picking with `--commercial yes` must move off Vercel Hobby, and the `vercel-hobby:commercial_use` trigger must fire when usage says commercial. Tests in Task 5 and Task 6.

---

### Task 1: Repo skeleton and plugin manifests

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `LICENSE`, `.gitignore`, `requirements-dev.txt`, `README.md` (stub), `tests/conftest.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Produces: `tests/conftest.py` fixtures `repo_root() -> Path` and `shared_dir() -> Path` (repo_root / "shared"), used by every later Python test; also puts `shared/tools` on `sys.path`.

- [ ] **Step 1: Create the folder as a git repo (local only)**

Run: `git init` inside `lean-builder-skill/` (skip if `.git` exists). Set repo-local author: `git config user.name Lilproff` and `git config user.email ayomidesholarin13@gmail.com`.

- [ ] **Step 2: Install test deps**

Create `requirements-dev.txt` with `pytest>=8` and `jsonschema>=4.23`. Run: `python -m pip install --user -r requirements-dev.txt`. Expected: `python -c "import jsonschema"` succeeds.

- [ ] **Step 3: Write the failing tests**

```python
def test_plugin_json_fields(repo_root):
    p = json.loads((repo_root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert p["name"] == "lean-builder-skill"
    assert p["version"] == "0.1.0"
    assert p["license"] == "MIT"
    assert p["repository"] == "https://github.com/LilProff/lean-builder-skill"

def test_marketplace_points_to_root(repo_root):
    m = json.loads((repo_root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert m["plugins"][0]["name"] == "lean-builder-skill"
    assert m["plugins"][0]["source"] == "./"

def test_gitignore_blocks_secrets(repo_root):
    lines = (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
    for needed in (".env", ".env.*", "!.env.example", "node_modules/", "__pycache__/"):
        assert needed in lines
```

- [ ] **Step 4: Run to verify they fail** — `python -m pytest tests/test_manifest.py -v` → FAIL (files missing).

- [ ] **Step 5: Create the files**

`plugin.json` follows the format of github.com/Jakeschincariol/founder-skill (`name`, `description`, `version`, `author{name,url}`, `homepage`, `repository`, `license`, `keywords`). Description: "Eleven free Claude skills that build a website, SaaS, internal tool or AI agent at the lowest cost: pick the stack, write the plan and cost sheet, scaffold, deploy and hand off. Paystack-ready. Free, MIT." Keywords: `claude-code`, `claude-skills`, `free-tier`, `low-cost`, `paystack`, `cloudflare`, `nextjs`, `ai-agents`. `marketplace.json`: `$schema` `https://anthropic.com/claude-code/marketplace.schema.json`, `name` and `owner` as plugin, one plugin with `source: "./"`, `category: "development"`. `LICENSE`: MIT, "Copyright (c) 2026 Samuel Ayomide Sholarin". README stub: title and one line (full README in Task 17).

- [ ] **Step 6: Run to verify they pass** — same command → 3 passed.

- [ ] **Step 7: Commit (if authorised)** — `git add -A && git commit -m "chore: plugin skeleton and manifests"`

---

### Task 2: Provider catalogue (`free-tiers.json`)

**Files:**
- Create: `shared/free-tiers.json`, `shared/free-tiers.schema.json`
- Test: `tests/test_free_tiers.py`

**Interfaces:**
- Produces: provider ids used by every later task. Exact id list (the test pins it):
  frameworks (`account: null`): `astro`, `nextjs`, `hono`, `fastapi`, `better-auth`, `keystatic`;
  services: `cloudflare-pages`, `cloudflare-workers`, `cloudflare-d1`, `cloudflare-r2`, `cloudflare-cron` (account `cloudflare`), `github-pages` (`github`), `vercel-hobby`, `vercel-pro` (`vercel`), `render` (`render`), `gcp-cloud-run` (`gcp`), `supabase` (`supabase`), `neon` (`neon`), `resend` (`resend`), `openrouter` (`openrouter`), `paystack` (`paystack`), `grey` (`grey`), `n8n-selfhosted` (`n8n-selfhosted`), `whatsapp-cloud-api` (`meta`), `telegram-bot` (`telegram`).

- [ ] **Step 1: Write the schema and the failing tests**

Schema (draft 2020-12): object of entries; each entry requires `name` (string), `account` (string or null), `plan` (string), `limits` (array of `{metric: string, value: number|boolean|string, unit?: string, period: string}`), `commercial_use` (boolean or `"conditional"`), `idle_behaviour` (string or null), `source_url` (string, `^https://`), `checked_on` (`^\d{4}-\d{2}-\d{2}$`); optional `notes` (string). No extra keys.

```python
EXPECTED_IDS = {...}  # the 25 ids above

def test_schema_valid(): jsonschema.validate(tiers, schema)
def test_exact_provider_ids(): assert set(tiers) == EXPECTED_IDS
def test_services_have_limits(): assert all(e["limits"] for e in tiers.values() if e["account"])
def test_checked_on_not_future(): assert all(date.fromisoformat(e["checked_on"]) <= date.today() for e in tiers.values())
def test_vercel_hobby_not_commercial(): assert tiers["vercel-hobby"]["commercial_use"] is False
```

- [ ] **Step 2: Run to verify they fail** — `python -m pytest tests/test_free_tiers.py -v` → FAIL.

- [ ] **Step 3: Research and fill each entry from official pages, today's date as `checked_on`**

Start from these pages (follow redirects to the current official page; record the final URL):
Cloudflare Pages limits `https://developers.cloudflare.com/pages/platform/limits/`; Workers `https://developers.cloudflare.com/workers/platform/pricing/`; D1 `https://developers.cloudflare.com/d1/platform/pricing/`; R2 `https://developers.cloudflare.com/r2/pricing/`; Cron Triggers `https://developers.cloudflare.com/workers/configuration/cron-triggers/`; GitHub Pages `https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits`; Vercel `https://vercel.com/docs/limits/fair-use-guidelines` and `https://vercel.com/pricing`; Render `https://render.com/docs/free`; Cloud Run `https://cloud.google.com/run/pricing`; Supabase `https://supabase.com/pricing`; Neon `https://neon.com/pricing`; Resend `https://resend.com/pricing`; OpenRouter `https://openrouter.ai/docs/api-reference/limits`; Paystack `https://paystack.com/ng/pricing`; Grey `https://grey.co`; n8n licence `https://docs.n8n.io/sustainable-use-license/`; WhatsApp `https://developers.facebook.com/docs/whatsapp/pricing`; Telegram `https://core.telegram.org/bots/faq`. Framework entries: `plan: "open source"`, `limits: []`, docs URL as `source_url`, `commercial_use: true`.

Pin these facts where the page confirms them: Vercel Hobby non-commercial; Supabase free pauses idle projects (record the idle period); Render free sleeps when idle; n8n self-hosting for a client: record the licence's exact condition in `notes` and set `commercial_use: "conditional"`; Paystack local fee, cap and international fee as `string` values with units.

- [ ] **Step 4: Run to verify they pass** — 5 passed.

- [ ] **Step 5: Commit (if authorised)** — `git commit -m "data: provider catalogue with official free-tier limits"`

---

### Task 3: Decision table (`stacks.json`)

**Files:**
- Create: `shared/stacks.json`, `shared/stacks.schema.json`
- Test: `tests/test_stacks.py`

**Interfaces:**
- Consumes: provider ids from Task 2.
- Produces: rows with keys `id, type, context, commercial, accounts_owner, stack{role: provider_id}, fallbacks{role: [provider_id]}, why{role: string}, overlays[overlay_id], upgrade_triggers[string]` (schema per spec §6.1). Overlay ids used: `claude-md-lean`, `status-md`, `env-example`, `gitignore-secrets`, `security-headers` (resolved per host in Task 5), `contact-form-worker`, `paystack-webhook`, `whatsapp-webhook-worker`, `telegram-webhook-worker`, `openrouter-client`, `n8n-skeletons`, `audit-log-table`, `rls-policies`, `cloud-run-fastapi`.

- [ ] **Step 1: Write the schema and failing tests**

```python
def test_schema_valid(): jsonschema.validate(stacks, schema)
def test_every_combination_has_exactly_one_row():
    for t in ("website", "saas", "internal", "agent"):
        for c in ("personal", "client", "startup"):
            for commercial in (True, False):
                assert len(matching(stacks, t, c, commercial)) == 1, (t, c, commercial)
def test_all_providers_exist(): every provider in every stack and fallback list is a key of free-tiers.json
def test_client_rows_owned_by_client(): all(r["accounts_owner"] == ("client" if r["context"] == "client" else "builder") for r in rows)
def test_every_role_has_a_why(): set(r["why"]) == set(r["stack"]) for every row
def test_base_overlays_on_every_row(): {"claude-md-lean", "status-md", "env-example", "gitignore-secrets"} <= set(r["overlays"])
```

`matching` treats `commercial: "any"` as matching both values.

- [ ] **Step 2: Run to verify they fail.**

- [ ] **Step 3: Write the 13 rows** (every row also gets the four base overlays; `why` gets one plain sentence per role):

| id | commercial | stack | fallbacks | extra overlays | triggers |
|---|---|---|---|---|---|
| website-personal | any | app astro, host cloudflare-pages, forms cloudflare-workers, email resend | host [github-pages] | security-headers, contact-form-worker | resend:emails_per_month>2400 |
| website-client | any | as website-personal + cms keystatic | none | same | same |
| website-startup | any | as website-personal | host [github-pages] | same | same |
| saas-personal-free | false | app nextjs, host vercel-hobby, data neon, auth better-auth, payments paystack, email resend, jobs cloudflare-cron, files cloudflare-r2 | host [cloudflare-workers], data [supabase] | security-headers, paystack-webhook | vercel-hobby:commercial_use, neon:storage_gb>0.4 |
| saas-personal-commercial | true | as above but host cloudflare-workers | data [supabase] | same | neon:storage_gb>0.4, cloudflare-workers:requests_per_day>80000 |
| saas-client | any | app nextjs, host cloudflare-workers, data supabase, auth supabase, payments paystack, email resend, jobs cloudflare-cron, files supabase | host [vercel-pro] | security-headers, paystack-webhook, rls-policies | supabase:idle_pause, supabase:db_size_mb>400 |
| saas-startup | any | as saas-client but files cloudflare-r2 | host [render] | same as saas-client | supabase:idle_pause, supabase:db_size_mb>400, cloudflare-workers:requests_per_day>80000 |
| internal-personal | any | app nextjs, host cloudflare-workers, data neon, auth better-auth | data [supabase] | security-headers | neon:storage_gb>0.4 |
| internal-client | any | app nextjs, host cloudflare-workers, data supabase, auth supabase, backend gcp-cloud-run, api fastapi, sync n8n-selfhosted | host [vercel-pro] | security-headers, rls-policies, audit-log-table, cloud-run-fastapi, n8n-skeletons | supabase:idle_pause, supabase:db_size_mb>400 |
| internal-startup | any | app nextjs, host cloudflare-workers, data supabase, auth supabase | data [neon] | security-headers, rls-policies, audit-log-table | supabase:idle_pause |
| agent-personal | any | glue n8n-selfhosted, webhooks cloudflare-workers, router hono, ai openrouter, data cloudflare-d1, messaging telegram-bot | data [neon], glue [render] | telegram-webhook-worker, openrouter-client, n8n-skeletons | cloudflare-workers:requests_per_day>80000, openrouter:free_requests_per_day>40 |
| agent-client | any | glue n8n-selfhosted, webhooks cloudflare-workers, router hono, ai openrouter, data neon, messaging whatsapp-cloud-api | none | whatsapp-webhook-worker, openrouter-client, n8n-skeletons | n8n-selfhosted:client_hosting_licence |
| agent-startup | any | glue n8n-selfhosted, webhooks cloudflare-workers, router hono, ai openrouter, data neon, messaging whatsapp-cloud-api | messaging [telegram-bot] | whatsapp-webhook-worker, openrouter-client, n8n-skeletons | cloudflare-workers:requests_per_day>80000 |

Trigger thresholds must sit below the matching limit recorded in Task 2. If a Task 2 limit differs, set the threshold to 80% of the recorded limit and say so in that role's `why`.

- [ ] **Step 4: Run to verify they pass** — 6 passed.
- [ ] **Step 5: Commit (if authorised)** — `git commit -m "data: decision table for 4 build types x 3 contexts"`

---

### Task 4: Profile reading and writing, shared secret patterns

**Files:**
- Create: `shared/tools/secret_patterns.py`, `shared/tools/profile_io.py`
- Test: `tests/test_profile_io.py`

**Interfaces:**
- Produces:
  - `secret_patterns.PATTERNS: dict[str, re.Pattern]` and `looks_like_secret(text: str) -> str | None` (returns the pattern name).
  - `profile_io.DEFAULT_PATH = Path.home() / ".claude/lean-builder/profile.md"`
  - `profile_io.load_profile(path: Path) -> dict | None` returning `{"accounts": set[str], "currency": str, "region": str, "default_context": str, "client_rule": str, "secret_names": list[str], "notes": str}`; `None` if the file does not exist.
  - `profile_io.write_profile(path: Path, data: dict) -> None`
  - `profile_io.ProfileError(ValueError)` with message containing `line <n>`.

Patterns (names → regex): `paystack` `sk_(live|test)_[A-Za-z0-9]{20,}`; `openrouter` `sk-or-v1-[A-Fa-f0-9]{32,}`; `anthropic` `sk-ant-[A-Za-z0-9_-]{20,}`; `openai` `sk-(proj-)?[A-Za-z0-9_-]{32,}` (checked after the two above); `resend` `re_[A-Za-z0-9_]{20,}`; `github` `gh[pousr]_[A-Za-z0-9]{36,}`; `aws` `AKIA[0-9A-Z]{16}`; `google` `AIza[0-9A-Za-z_-]{35}`; `private-key` `-----BEGIN [A-Z ]*PRIVATE KEY-----`.

- [ ] **Step 1: Write failing tests**

```python
def test_load_missing_returns_none(tmp_path): assert load_profile(tmp_path / "nope.md") is None
def test_load_parses_lists_and_scalars(tmp_path):
    p = write(tmp_path, "---\naccounts: [cloudflare, neon]\ncurrency: NGN\n---\nnotes here\n")
    prof = load_profile(p)
    assert prof["accounts"] == {"cloudflare", "neon"} and prof["currency"] == "NGN" and prof["notes"] == "notes here"
def test_malformed_line_names_line(tmp_path):  # Review Focus 1
    p = write(tmp_path, "---\naccounts [cloudflare]\n---\n")
    with pytest.raises(ProfileError, match="line 2"): load_profile(p)
def test_write_refuses_secret_values(tmp_path):
    with pytest.raises(ValueError, match="paystack"):
        write_profile(tmp_path / "p.md", {"accounts": ["paystack"], "secret_names": ["sk_live_" + "a" * 24]})
def test_roundtrip(tmp_path): write then load returns the same accounts and secret_names
def test_patterns_detect_fakes(): looks_like_secret("sk-or-v1-" + "ab" * 20) == "openrouter"; looks_like_secret("PAYSTACK_SECRET_KEY") is None
```

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.** Front matter is the block between the first two `---` lines; each non-empty line must be `key: value` or `key: [a, b]`; anything else raises `ProfileError` with its 1-based file line number. Unknown keys are kept as strings. `write_profile` checks every value with `looks_like_secret` first, creates parent folders and writes UTF-8.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit (if authorised)** — `git commit -m "feat: profile io and secret patterns"`

---

### Task 5: Stack picker (`pick_stack.py`)

**Files:**
- Create: `shared/tools/pick_stack.py`
- Test: `tests/test_pick_stack.py`

**Interfaces:**
- Consumes: `profile_io.load_profile`, `profile_io.DEFAULT_PATH`, `profile_io.ProfileError` (Task 4); `stacks.json`, `free-tiers.json` (Tasks 2 and 3).
- Produces:
  - `NoMatchError(ValueError)`, `AmbiguousMatchError(ValueError)`
  - `pick(build_type: str, context: str, commercial: bool, accounts: set[str] | None, stacks: dict, tiers: dict, today: date) -> dict`
  - result dict: `{"row_id", "type", "context", "commercial", "accounts_owner", "components": {role: {"provider", "name", "account", "limits", "source_url", "checked_on", "stale": bool, "account_needed": bool, "note": str | None}}, "overlays": list[str], "upgrade_triggers": list[str], "notes": list[str]}`
  - `render_md(result: dict) -> str` (a Markdown table: Role | Choice | Free-tier limits | Checked on | Note, then the notes as bullets)
  - `main(argv: list[str] | None = None) -> int`; CLI flags `--type`, `--context`, `--commercial {yes,no}`, `--profile PATH` (default `DEFAULT_PATH`), `--data-dir PATH` (default the `shared/` folder next to `tools/`), `--md`, `--out PATH` (also write the JSON result there as UTF-8, creating parent folders). Exit 2 on `NoMatchError`, `AmbiguousMatchError` or `ProfileError`, with the message on stderr.

Algorithm (beyond spec §7):
- Account swap applies only when `accounts is not None`, the row is not `client`, and the provider has a non-null `account` not in `accounts`. Take the first fallback whose account is null or in `accounts`; note: `"No <account> account in your profile: using <fallback name> instead."`. If none fits, keep the default, `account_needed: True`, note `"Needs a new <account> account."`.
- `accounts is None` adds the top-level note `"No profile found: using default choices. Run the profile skill to personalise."`.
- `stale` when `today - checked_on > 90 days`; note `"Limits last checked <date>: re-check before relying on them."`.
- Overlay `security-headers` is replaced after swaps by `security-headers-vercel` (final host starts with `vercel-`), `security-headers-cloudflare` (starts with `cloudflare-` or is `github-pages`), or dropped with note `"Set security headers in the app for <host name>."`.
- `NoMatchError` message lists the valid types and contexts: `website, saas, internal, agent` and `personal, client, startup`.

- [ ] **Step 1: Write failing tests** (fixture data in `tmp_path` for unit tests, `real` fixture loads the real `shared/` data and today's date)

```python
def test_saas_personal_free_picks_vercel_hobby(real): r = pick("saas", "personal", False, {"vercel","neon","resend","cloudflare","paystack"}, *real); assert r["components"]["host"]["provider"] == "vercel-hobby"
def test_saas_personal_commercial_moves_off_hobby(real): pick(..., True, ...)["components"]["host"]["provider"] == "cloudflare-workers"  # Review Focus 5
def test_missing_account_uses_fallback(real): accounts without "vercel" → host "cloudflare-workers", note contains "No vercel account"
def test_no_fallback_marks_account_needed(fx): account_needed is True and note starts "Needs a new"
def test_client_rows_skip_account_checks(real): pick("saas", "client", True, set(), ...) has no swaps, accounts_owner "client"
def test_no_profile_keeps_defaults_with_note(real): accounts=None → defaults, notes[0] starts "No profile found"  # Review Focus 1
def test_unknown_type_raises(real): with pytest.raises(NoMatchError): pick("mobile", ...)
def test_stale_limits_flagged(fx): today = checked_on + 91 days → stale True
def test_headers_overlay_resolved(real): personal free → "security-headers-vercel" in overlays; commercial → "security-headers-cloudflare"
def test_deterministic(real): two identical calls return equal dicts
def test_main_bad_type_returns_2(capsys): main(["--type","mobile","--context","personal","--commercial","no"]) == 2 and "website, saas, internal, agent" in capsys.readouterr().err
def test_md_output_on_cp1252_stdout(monkeypatch): sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252"); main([...valid..., "--md"]) == 0  # Review Focus 2
def test_out_writes_json(tmp_path): main([...valid..., "--out", str(tmp_path / "kit/stack.json")]) == 0 and the file parses to the same dict as pick()
```

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement** per the interface and algorithm above. Iterate roles in the row's key order so output is stable.
- [ ] **Step 4: Run to verify they pass** — `python -m pytest tests/test_pick_stack.py -v`.
- [ ] **Step 5: Commit (if authorised)** — `git commit -m "feat: deterministic stack picker"`

---

### Task 6: Free-tier and trigger check (`freetier_check.py`)

**Files:**
- Create: `shared/tools/freetier_check.py`
- Test: `tests/test_freetier_check.py`

**Interfaces:**
- Produces:
  - `stale_entries(tiers: dict, today: date, max_age_days: int = 90) -> list[str]` (provider ids, sorted)
  - `evaluate_triggers(triggers: list[str], usage: dict[str, float | bool]) -> list[str]` (fired triggers, input order)
  - `main(argv: list[str] | None = None) -> int`; flags `--plan-json PATH` (a `pick()` result), `--usage PATH` (JSON object), `--data-dir`, `--strict` (exit 1 if anything is stale or fired; otherwise exit 0 and print).

Trigger grammar: `provider:metric>number` fires when `usage["provider:metric"] > number`; `provider:condition` fires when `usage["provider:condition"] is True`. Missing usage keys never fire. A malformed trigger raises `ValueError` naming it.

- [ ] **Step 1: Failing tests**

```python
def test_threshold_fires(): evaluate_triggers(["neon:storage_gb>0.4"], {"neon:storage_gb": 0.45}) == ["neon:storage_gb>0.4"]
def test_threshold_quiet_below(): evaluate_triggers(["neon:storage_gb>0.4"], {"neon:storage_gb": 0.3}) == []
def test_condition_fires_on_true(): evaluate_triggers(["vercel-hobby:commercial_use"], {"vercel-hobby:commercial_use": True}) == ["vercel-hobby:commercial_use"]  # Review Focus 5
def test_missing_usage_never_fires(): evaluate_triggers(["supabase:idle_pause"], {}) == []
def test_malformed_trigger_raises(): with pytest.raises(ValueError, match="neon>>1"): evaluate_triggers(["neon>>1"], {})
def test_stale_entries(): one entry 100 days old, one 10 days → only the old id
def test_strict_exit_code(tmp_path): fired trigger + --strict → 1; without --strict → 0
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: free-tier and trigger check`.

---

### Task 7: Secret scan (`secret_scan.py`)

**Files:**
- Create: `shared/tools/secret_scan.py`
- Test: `tests/test_secret_scan.py`

**Interfaces:**
- Consumes: `secret_patterns.PATTERNS` (Task 4).
- Produces: `Hit = NamedTuple("Hit", [("path", Path), ("line", int), ("kind", str)])`; `scan(root: Path) -> list[Hit]` (sorted by path, line); `main(argv: list[str] | None = None) -> int` (exit 1 on any hit, prints `path:line kind`, never prints the matched text).

Rules: skip dirs `.git`, `node_modules`, `.next`, `dist`, `build`, `.venv`, `__pycache__`, `.wrangler`; skip files over 2 MB and files with a null byte in the first 8 KB; any file named `.env` or `.env.*` other than `.env.example` is a hit of kind `env-file` at line 0.

- [ ] **Step 1: Failing tests** (fake keys built at runtime, never literal in the repo, e.g. `"sk_live_" + "x" * 24`)

```python
def test_finds_key_in_source(tmp_path): one fake paystack key on line 3 → [Hit(path, 3, "paystack")]
def test_flags_env_file(tmp_path): .env → kind "env-file"; .env.example → no hit
def test_skips_node_modules(tmp_path): fake key under node_modules/ → []
def test_skips_large_and_binary(tmp_path): 3 MB file with a key and a binary file with b"\x00" → []  # Review Focus 4
def test_output_hides_secret(tmp_path, capsys): main([str(tmp_path)]) == 1 and the fake key text not in captured output
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: secret scan`.

---

### Task 8: Preflight gate (`preflight.py`)

**Files:**
- Create: `shared/tools/preflight.py`
- Test: `tests/test_preflight.py`

**Interfaces:**
- Consumes: `secret_scan.scan` (Task 7), `freetier_check.stale_entries` (Task 6).
- Produces: `Check = NamedTuple("Check", [("name", str), ("status", str), ("detail", str)])` with status in `{"pass", "fail", "warn"}`; `run_preflight(project: Path, host: str, build_cmd: str | None, tiers: dict, today: date) -> list[Check]`; `main(argv) -> int` (flags `--project`, `--host`, `--build-cmd`, `--data-dir`; prints a table; exit 1 if any `fail`).

Checks in order: `build` (`warn` "no build command given" when `build_cmd` is None; else run via `subprocess.run(build_cmd, shell=True, cwd=project)`, fail on non-zero), `secrets` (fail on any hit), `env-example` (fail if `.env.example` missing), `gitignore-env` (fail unless `.gitignore` has a line `.env` or `.env*`), `headers` (cloudflare-* or github-pages: pass if `_headers` or `public/_headers` contains `X-Content-Type-Options`; vercel-*: pass if `vercel.json` has a `headers` key or a `next.config.*` contains `headers(`; any other host: `warn` "set headers in the app"), `limits` (`warn` listing stale provider ids, else pass).

- [ ] **Step 1: Failing tests**

```python
def test_clean_cloudflare_project_passes(tmp_path): files .env.example, .gitignore(".env"), public/_headers(X-Content-Type-Options) → no "fail"
def test_failing_build_fails(tmp_path): build_cmd 'python -c "import sys; sys.exit(1)"' → build is "fail"
def test_missing_env_example_fails(tmp_path)
def test_vercel_headers_from_vercel_json(tmp_path): vercel.json {"headers": []} → headers "pass"
def test_render_headers_warn(tmp_path): host "render" → headers "warn"
def test_main_exit_code(tmp_path): any fail → 1, all pass/warn → 0
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: preflight gate`.

---

### Task 9: Overlay mechanism and base overlays

**Files:**
- Create: `shared/tools/apply_overlays.py`; overlays `shared/overlays/<id>/overlay.json` + `files/...` for `claude-md-lean`, `status-md`, `env-example`, `gitignore-secrets`, `security-headers-cloudflare`, `security-headers-vercel`
- Test: `tests/test_overlays.py`

**Interfaces:**
- Produces:
  - `overlay.json`: `{"id": str, "description": str, "files": [{"src": str, "dest": str, "mode": "copy" | "append"}]}` (`src` relative to the overlay's `files/`, `dest` relative to the project).
  - `ApplyReport = NamedTuple("ApplyReport", [("created", list[str]), ("appended", list[str]), ("skipped", list[str])])`
  - `apply(ids: list[str], project: Path, overlays_dir: Path, values: dict[str, str], force: bool = False) -> ApplyReport`
  - `main(argv) -> int` (flags `--ids a,b`, `--project`, `--values values.json`, `--force`)
  - Placeholders `{{KEY}}` in text files are replaced from `values`; any placeholder with no value raises `KeyError` listing every missing key before anything is written.

Template content decisions:
- `claude-md-lean/files/CLAUDE.md` (max 60 lines): placeholders `{{PROJECT_NAME}}`, `{{STACK_SUMMARY}}`, `{{CONTEXT}}`; sections: what this is, stack, commands, rules (no secrets in repo, small verified steps, update STATUS.md after each step, strongest model for planning only, helper agents for broad search), where things are.
- `status-md/files/STATUS.md`: "Resume here", "In progress" (checklist template with "Stopped at" and "Next step"), "Done"; same shape as the workspace work log.
- `env-example/files/.env.example`: a comment saying "names only, never values" and `{{ENV_VARS}}` (newline-separated names, each `NAME=`).
- `gitignore-secrets/files/.gitignore` with mode `append`: lines `.env`, `.env.*`, `!.env.example`, `.wrangler/`, `.vercel/`.
- `security-headers-cloudflare/files/public/_headers`: `/*` block with `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- `security-headers-vercel/files/vercel.json`: the same four headers under `headers` for source `/(.*)`.

- [ ] **Step 1: Failing tests**

```python
def test_every_overlay_manifest_valid(shared_dir): each overlay.json has id == folder name and every src exists
def test_stack_overlay_ids_exist(shared_dir): every overlay id in stacks.json ("security-headers" expanded to both variants) has a folder  # runs green only after Tasks 10 to 12; mark xfail(strict=True) until Task 12 removes the mark
def test_apply_creates_files(tmp_path)
def test_apply_skips_existing_without_force(tmp_path): existing CLAUDE.md unchanged and listed in skipped  # Review Focus 3
def test_force_overwrites(tmp_path)
def test_append_adds_missing_lines_once(tmp_path): .gitignore with ".env" → after two applies each line appears once
def test_missing_value_raises_before_writing(tmp_path): KeyError lists "PROJECT_NAME"; project dir unchanged
def test_claude_md_template_max_60_lines(shared_dir)
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: overlay mechanism and base overlays`.

---

### Task 10: Website and payment overlays

**Files:**
- Create: `shared/overlays/contact-form-worker/` (`overlay.json`, `files/functions/contact.ts`, `files/src/lib/contact.ts`), `shared/overlays/paystack-webhook/` (`overlay.json`, `files/src/lib/paystack.ts`, `files/src/app/api/paystack/webhook/route.ts`)
- Test: `tests/overlays/contact.test.ts`, `tests/overlays/paystack.test.ts`

**Interfaces:**
- Produces (dependency-free logic files):
  - `contact.ts`: `validateContact(body: unknown): { ok: boolean; errors: string[]; data?: { name: string; email: string; message: string } }` (rejects a non-empty honeypot field `website`, empty fields, invalid email, message over 5000 chars).
  - `paystack.ts`: `verifyPaystackSignature(rawBody: string, signature: string | null, secret: string): Promise<boolean>` (HMAC SHA-512 hex via `crypto.subtle`, constant-time compare); `verifyTransaction(reference: string, secretKey: string, fetchFn: typeof fetch): Promise<{ status: string; amountKobo: number; reference: string }>` (GET `https://api.paystack.co/transaction/verify/<reference>` with `Authorization: Bearer <secretKey>`).
- The Cloudflare Pages Function `functions/contact.ts` posts to `https://api.resend.com/emails` using env vars `RESEND_API_KEY`, `CONTACT_TO_EMAIL`, `CONTACT_FROM_EMAIL`. The Next.js route reads the raw body, verifies the signature, calls `verifyTransaction`, and leaves one clearly marked spot for an idempotent order update keyed by `reference`.

- [ ] **Step 1: Failing tests** (`node --test tests/overlays/`)

```ts
test("valid signature passes", async () => { const sig = createHmac("sha512", "s").update(body).digest("hex"); assert.equal(await verifyPaystackSignature(body, sig, "s"), true); });
test("tampered body fails", ...); test("missing signature fails", ...);
test("verifyTransaction maps the response", async () => { const fake = async () => new Response(JSON.stringify({ status: true, data: { status: "success", amount: 500000, reference: "r1" } })); assert.deepEqual(await verifyTransaction("r1", "k", fake), { status: "success", amountKobo: 500000, reference: "r1" }); });
test("honeypot rejects", ...); test("bad email rejects", ...); test("valid contact passes", ...);
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: contact form and Paystack overlays`.

---

### Task 11: Agent overlays

**Files:**
- Create: `shared/overlays/whatsapp-webhook-worker/` (`overlay.json`, `files/src/whatsapp.ts`, `files/src/index.ts`), `telegram-webhook-worker/` (`overlay.json`, `files/src/telegram.ts`, `files/src/index.ts`), `openrouter-client/` (`overlay.json`, `files/src/openrouter.ts`), `n8n-skeletons/` (`overlay.json`, `files/n8n/sheet-sync.json`, `lead-capture.json`, `daily-report.json`)
- Test: `tests/overlays/whatsapp.test.ts`, `tests/overlays/telegram.test.ts`, `tests/overlays/openrouter.test.ts`, `tests/test_n8n_skeletons.py`

**Interfaces:**
- Produces:
  - `whatsapp.ts`: `verifyMetaChallenge(params: URLSearchParams, verifyToken: string): string | null`; `verifyMetaSignature(rawBody: string, header: string | null, appSecret: string): Promise<boolean>` (`sha256=<hex>` HMAC SHA-256); `extractTextMessages(payload: unknown): { from: string; text: string; id: string }[]`.
  - `telegram.ts`: `checkSecretToken(headerValue: string | null, expected: string): boolean`; `extractTelegramText(update: unknown): { chatId: number; text: string } | null`.
  - `openrouter.ts`: `complete(messages: { role: string; content: string }[], opts: { apiKey: string; models: string[]; fetchFn: typeof fetch; cache?: Map<string, string> }): Promise<{ model: string; text: string; fromCache: boolean }>`; tries `models` in order, moves on after HTTP 429 or 5xx, throws `Error("all models failed: <statuses>")`; cache key is the JSON of `[models, messages]`.
  - `index.ts` files: thin Hono routers using the functions above (untested; `hono` is installed by the build skill).
  - n8n JSON: each has `name`, `nodes` (array, first node is a trigger), `connections` (object), and no stored credential values.

- [ ] **Step 1: Failing tests**

```ts
test("challenge echoes when token matches", ...); test("challenge null on wrong token", ...);
test("meta signature valid", ...); test("meta signature invalid", ...); test("extracts text messages, ignores statuses", ...);
test("telegram secret mismatch false", ...); test("extracts chat id and text", ...); test("non-text update null", ...);
test("falls back after 429", async () => { /* fake fetch: model A → 429, model B → 200 */ assert.equal(r.model, "B"); });
test("cache hit skips fetch", ...); test("all fail throws with statuses", ...);
```
```python
def test_n8n_skeletons_shape(shared_dir): each file parses, has name/nodes/connections; no node has a "credentials" object with values
```

- [ ] **Steps 2 to 5:** run fail, implement, run pass, commit (if authorised) `feat: agent overlays`.

---

### Task 12: Internal-tool overlays

**Files:**
- Create: `shared/overlays/audit-log-table/` (`overlay.json`, `files/db/audit_log.sql`), `shared/overlays/rls-policies/` (`overlay.json`, `files/db/rls_template.sql`), `shared/overlays/cloud-run-fastapi/` (`overlay.json`, `files/api/main.py`, `files/api/requirements.txt`, `files/api/Dockerfile`)
- Modify: `tests/test_overlays.py` (remove the `xfail` mark from `test_stack_overlay_ids_exist`)
- Test: `tests/test_internal_overlays.py`

**Interfaces:**
- Produces:
  - `audit_log` table: `id uuid primary key default gen_random_uuid()`, `actor_id uuid`, `action text not null`, `entity text not null`, `entity_id text`, `before jsonb`, `after jsonb`, `created_at timestamptz not null default now()`; row level security enabled; insert and select policies only (no update or delete policy).
  - RLS template: `org_id uuid` ownership pattern with a commented example table and select/insert/update/delete policies using `auth.uid()`-based membership (Supabase).
  - FastAPI: `GET /health` returns `{"status": "ok"}`; Dockerfile serves with uvicorn on `${PORT:-8080}`; `requirements.txt` has `fastapi` and `uvicorn[standard]` with minimum versions only.

- [ ] **Step 1: Failing tests**

```python
def test_audit_log_has_rls_and_no_update_delete(shared_dir): "enable row level security" in sql.lower(); no "for update" or "for delete" on audit_log
def test_rls_template_uses_org_id(shared_dir)
def test_dockerfile_uses_port_env(shared_dir): "${PORT" in dockerfile
def test_health_route_declared(shared_dir): '@app.get("/health")' in main_py
```

- [ ] **Steps 2 to 5:** run fail, implement, remove the xfail mark, run the whole suite `python -m pytest -q` pass, commit (if authorised) `feat: internal-tool overlays`.

---

### Task 13: Core skills: `profile`, `kit`, `lean-claude`

**Files:**
- Create: `skills/profile/SKILL.md`, `skills/kit/SKILL.md`, `skills/lean-claude/SKILL.md`
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: tool CLIs from Tasks 4 to 9 (`pick_stack.py`, `freetier_check.py`, `apply_overlays.py`, `profile_io.py`), overlay ids.
- Produces: skill names exactly `profile`, `kit`, `lean-claude`; `kit` hands off by telling Claude to load `build-website`, `build-saas`, `build-internal` or `build-agent` (Task 14 names).

Required content:
- `profile`: six questions with defaults (accounts from the id list in Global Constraints, currency, region, default context, client rule, secret names); writes via `profile_io.write_profile`; refuses pasted key values and says why; shows the saved file path.
- `kit`: (1) load the profile or run `profile`; (2) one intake round of at most 5 questions with defaults (what it does, who for, context, earns money yes/no, who owns accounts, deadline); (3) run `python <shared>/tools/pick_stack.py --type .. --context .. --commercial .. --md --out kit/stack.json` and show the table; (4) write `plan.md` (spec §9 contents with a "Not in v1" list) and `cost.md` (monthly cost at zero, small and growing usage, upgrade triggers, every figure with its checked-on date and link); (5) apply `claude-md-lean` and `status-md` via `apply_overlays.py`; (6) stop and ask for a yes; (7) hand to the build skill.
- `lean-claude`: the rules from spec §5 and §9; how to keep CLAUDE.md under 60 lines; model choice (strongest for planning and hard debugging, lighter for search and simple edits); helper agents for broad exploration; one feature per session; update STATUS.md before any compact.

- [ ] **Step 1: Failing tests** (parametrised over every folder in `skills/`, so later tasks are covered automatically)

```python
def test_frontmatter(skill_dir): name == folder name; 50 <= len(description) <= 1024
def test_referenced_tools_exist(skill_dir): every "tools/<x>.py" mentioned exists in shared/tools
def test_referenced_overlays_exist(skill_dir): every backticked token equal to one of the overlay ids listed in Task 3 (plus the two security-headers variants) exists as a folder in shared/overlays; every backticked token ending in "-worker", "-webhook", "-skeletons", "-table", "-policies" or "-fastapi" is one of those ids
def test_no_dashes(skill_dir): "—" not in text and "–" not in text
def test_core_skills_present(repo_root): {"profile", "kit", "lean-claude"} <= set(names)
```

- [ ] **Steps 2 to 5:** run fail, write the three skills, run pass, commit (if authorised) `feat: kit, profile and lean-claude skills`.

---

### Task 14: Build skills

**Files:**
- Create: `skills/build-website/SKILL.md`, `skills/build-saas/SKILL.md`, `skills/build-internal/SKILL.md`, `skills/build-agent/SKILL.md`
- Test: `tests/test_skills.py` (add `test_build_skills_present`)

Required content (every build skill): read `plan.md` and `kit/stack.json`; run the official starter (`npm create astro@latest`, `npx create-next-app@latest`, `npm create cloudflare@latest` for Workers, FastAPI layout from `cloud-run-fastapi`); apply the row's overlays with `apply_overlays.py` (values from the plan); build one thin vertical slice first; after each step run the build and tests and check the browser at 375 and 1440 px; update `STATUS.md` after each step; never type keys or passwords (write env var names into `.env.example` and tell the human where to paste values).
- `build-website`: Astro static, `contact-form-worker`, Keystatic only for client rows, page checks (title, description, alt text, one H1).
- `build-saas`: data and auth per stack (Neon + Better Auth or Supabase), `paystack-webhook` plus the `pay` skill for checkout, an owner column on every user-owned table.
- `build-internal`: roles, `audit-log-table`, `rls-policies`, optional `cloud-run-fastapi`, client-owned accounts from day one, sheet sync from `n8n-skeletons`.
- `build-agent`: messaging channel per stack (`telegram-webhook-worker` or `whatsapp-webhook-worker`), `openrouter-client` with free models first and a paid fallback, cache, D1 or Neon memory, n8n flows; for client rows, the n8n licence note recorded in Task 2 and the client's own Meta Business number.

- [ ] **Steps:** add `test_build_skills_present` asserting the four names; run fail; write skills; run `python -m pytest tests/test_skills.py -v` pass; commit (if authorised) `feat: build skills`.

---

### Task 15: Support skills: `pay`, `deploy`, `cost-guard`, `handoff`

**Files:**
- Create: `skills/pay/SKILL.md`, `skills/deploy/SKILL.md`, `skills/cost-guard/SKILL.md`, `skills/handoff/SKILL.md`
- Test: `tests/test_skills.py` (add `test_exactly_eleven_skills`)

Required content:
- `pay`: Paystack checkout flow (initialise on the server, redirect or inline, webhook, verify, idempotent update by `reference`); amounts in kobo; test keys during build; Grey explained as receiving foreign payouts only.
- `deploy`: per-host steps for Cloudflare (Pages and Workers via `wrangler`), Vercel, Render, Cloud Run; run `preflight.py` and stop on any fail; write exact env var names, DNS records and settings to `deploy.md`; the human does every account, billing and DNS step; check the live URL returns 200 afterwards.
- `cost-guard`: run `freetier_check.py --plan-json kit/stack.json` with a usage file the human fills, or one the skill estimates and labels as an estimate; explain each fired trigger and the move it implies; refresh `cost.md`.
- `handoff`: create `handoff/` with an account ownership table, run guide, credential transfer checklist (the client rotates every key and password after handover), and a support terms section left for Samuel to fill.

- [ ] **Steps:** add `test_exactly_eleven_skills` (set equals the 11 names in spec §5); run fail; write skills; run pass; commit (if authorised) `feat: pay, deploy, cost-guard and handoff skills`.

---

### Task 16: Worked examples

**Files:**
- Create: `examples/README.md` (states `EXAMPLES_DATE`, the fixed date used to generate the expected files), and `examples/website-personal/`, `examples/saas-startup/`, `examples/internal-client/`, `examples/agent-personal/`, each with `brief.md` (3 to 6 lines plus a front matter block `type`, `context`, `commercial`, `accounts`) and `expected.json` (the full `pick()` result)
- Test: `tests/test_examples.py`

- [ ] **Step 1: Failing test**

```python
@pytest.mark.parametrize("ex", ["website-personal", "saas-startup", "internal-client", "agent-personal"])
def test_example_matches_picker(ex, repo_root, shared_dir):
    meta = front_matter(repo_root / "examples" / ex / "brief.md")
    result = pick(meta["type"], meta["context"], meta["commercial"], set(meta["accounts"]), stacks, tiers, EXAMPLES_DATE)
    assert result == json.loads((repo_root / "examples" / ex / "expected.json").read_text(encoding="utf-8"))
```

- [ ] **Step 2:** run fail. **Step 3:** write the briefs (generic, no client names) and generate each `expected.json` by running `pick_stack.py`; read each one and confirm it matches the Task 3 table. **Step 4:** run pass. **Step 5:** commit (if authorised) `docs: worked examples`.

---

### Task 17: README and CI

**Files:**
- Create/replace: `README.md`, `.github/workflows/ci.yml`

README sections: one-line pitch; what it does in 5 bullets; install (`/plugin marketplace add LilProff/lean-builder-skill` then `/plugin install lean-builder-skill@lean-builder-skill`); a 60-second demo transcript built from `examples/website-personal`; the 11 skills table; the decision table summary with "limits checked on <date>"; safety rules; credits (plugin format inspired by the public packs at github.com/Jakeschincariol); MIT. No invented usage numbers or testimonials.

CI (`ubuntu-latest`): `actions/checkout@v4`; `actions/setup-python@v5` (3.12) then `pip install -r requirements-dev.txt` and `python -m pytest -q`; `actions/setup-node@v4` (24) then `node --test tests/overlays/`; `lycheeverse/lychee-action@v2` with `--no-progress --exclude-mail` over `README.md`, `skills/**/*.md`, `docs/**/*.md`.

- [ ] **Step 1:** run locally: `python -m pytest -q` and `node --test tests/overlays/` → all pass.
- [ ] **Step 2:** write README and workflow; open every README link once to confirm it resolves.
- [ ] **Step 3:** commit (if authorised) `docs: README and CI`.

---

### Task 18: Install locally and dogfood with Samuel

**Files:**
- Create: `STATUS.md` (from the `status-md` overlay, for the repo itself)
- Modify: workspace `WORK_LOG.md` (project 6)

- [ ] **Step 1:** Samuel runs in Claude Code: `/plugin marketplace add "<absolute path to lean-builder-skill>"` then `/plugin install lean-builder-skill@lean-builder-skill`. Expected: the 11 skills are listed.
- [ ] **Step 2:** Samuel runs the `profile` skill and answers its six questions (accounts: vercel, cloudflare, gcp, render, supabase, neon, n8n-selfhosted, openrouter, paystack, grey). Expected: `~/.claude/lean-builder/profile.md` exists and contains no key values.
- [ ] **Step 3:** In a scratch folder, Samuel runs `/kit` for a personal website. Expected: `plan.md`, `cost.md`, `kit/stack.json`, `CLAUDE.md`, `STATUS.md` created; stack is Astro on Cloudflare Pages; every limit shows its checked-on date.
- [ ] **Step 4:** Samuel says yes to the plan; `build-website` builds the one-page site and `deploy` takes it live on Cloudflare Pages (Samuel does the account steps). Expected: `preflight.py` passes, the live URL returns 200, and `cost.md` shows ₦0 hosting (spec success criterion).
- [ ] **Step 5:** Record what was confusing or wrong in `STATUS.md` as v0.1.1 items. Update `WORK_LOG.md` project 6, and note in project 5 that its first build should start from `/kit` (the remaining spec success criterion).
- [ ] **Step 6:** Ask Samuel to confirm the final repo name and whether to create the public GitHub repo `LilProff/<name>` and push. Do nothing on GitHub without his yes.
