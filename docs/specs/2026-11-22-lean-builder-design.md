# lean-builder-skill: design spec

- Date: 22 Nov 2026. Status: written, awaiting Samuel's review. Owner: Samuel Sholarin (GitHub `LilProff`).
- Working name: `lean-builder-skill` (can be renamed before the repo goes public).
- Decisions behind this spec are logged in the workspace `WORK_LOG.md`, project 6.

## 1. Purpose

Samuel builds in three contexts: **personal** (brand, open source, micro-SaaS, reproductions of big-company
research), **client** (apps, ERPs, AI systems, automations), and **startup** (co-founded, he is the sole
builder). He wants every build to cost as little as possible in money and time while having maximum effect,
using Claude Code and the free or cheap services he already has.

`lean-builder-skill` is a **public Claude Code plugin** (MIT) that, for a given build:
1. picks the cheapest stack that fits the build type and context, deterministically;
2. writes a one-page plan and a cost sheet with free-tier limits and upgrade triggers;
3. scaffolds the project from official starters plus small overlay files;
4. builds in small verified steps, deploys behind a preflight gate, and hands off.

It doubles as a personal-brand asset (the format is proven: comparable public skill packs by
github.com/Jakeschincariol reach 4k to 10k stars). Its edge over those packs: cost and free-tier awareness,
African payments (Paystack, Grey), a personal/client/startup split, and Claude-usage discipline.

### Success criteria (v1)
- From `/kit` to an approved `plan.md` in under 10 minutes of Samuel's time.
- A personal website goes live at ₦0 hosting cost using only the kit.
- All four example briefs produce their expected stack in tests.
- The first brand-pipeline build (WORK_LOG project 5) ships using the kit.

## 2. Scope

**In v1:** four build types (website, SaaS, internal tool/ERP, AI agent/automation), three contexts, 11 skills,
shared data files, small Python tools, examples, tests, CI.

**Not in v1:** mobile apps, Stripe, Firebase, languages other than English, any paid feature of the pack itself.

## 3. Public and private parts

| Part | Where | Pushed? |
|---|---|---|
| The plugin (skills, shared data, tools, examples, tests) | `lean-builder-skill/` repo | Yes, public, MIT |
| Samuel's profile (accounts, defaults, key NAMES) | `~/.claude/lean-builder/profile.md` | Never (outside every repo) |
| Per-project outputs (`plan.md`, `cost.md`, `STATUS.md`, `CLAUDE.md`) | inside each project | Up to that project |

Anyone else who installs the pack gets a first-run setup (the `profile` skill) that creates their own profile.

## 4. Repo layout

```
lean-builder-skill/
  .claude-plugin/plugin.json        plugin manifest
  .claude-plugin/marketplace.json   one-step install
  README.md                         pitch, install, 60-second demo, credits
  LICENSE                           MIT
  skills/
    kit/SKILL.md                    front door (router)
    build-website/SKILL.md
    build-saas/SKILL.md
    build-internal/SKILL.md
    build-agent/SKILL.md
    pay/SKILL.md
    deploy/SKILL.md
    cost-guard/SKILL.md
    lean-claude/SKILL.md
    handoff/SKILL.md
    profile/SKILL.md
  shared/
    stacks.json                     decision table (single source of truth)
    stacks.schema.json              JSON Schema for stacks.json
    free-tiers.json                 provider limits, source URL, checked_on date
    free-tiers.schema.json
    overlays/<overlay-id>/...       small files added on top of official starters
    tools/pick_stack.py             deterministic stack picker
    tools/freetier_check.py         flags stale limit data and crossed triggers
    tools/preflight.py              pre-deploy gate
    tools/secret_scan.py            pre-push secret scan
  examples/
    website-personal/brief.md, expected.json
    saas-startup/brief.md, expected.json
    internal-client/brief.md, expected.json
    agent-personal/brief.md, expected.json
  tests/                            pytest for every tool + schema checks + example checks
  .github/workflows/ci.yml          pytest, schema validation, markdown link check
  docs/specs/                       this file
```

Tools use the Python 3 standard library only (no installs), except tests (pytest) and schema validation in CI.

## 5. Skills

Each skill is one `SKILL.md` with a description that names the phrases that trigger it. Skills read shared
files by relative path from the plugin root.

| Skill | Purpose | Reads | Writes |
|---|---|---|---|
| `kit` | Front door. Profile check, intake (3 to 5 questions with defaults), runs `pick_stack.py`, writes the plan, asks for a yes, hands to the right `build-*` skill. | profile, stacks.json, free-tiers.json | `plan.md`, `cost.md`, `CLAUDE.md`, `STATUS.md` in the project |
| `build-website` | Astro on Cloudflare Pages; contact form via Worker to Resend; optional Keystatic CMS for clients. | plan.md, overlays | project code |
| `build-saas` | Next.js + data/auth per plan (Neon + Better Auth, or Supabase) + Paystack; thin vertical slice first. | plan.md, overlays | project code |
| `build-internal` | Next.js with roles, audit log, row-level security; optional FastAPI on Cloud Run; client-owned accounts. | plan.md, overlays | project code |
| `build-agent` | n8n flows + Cloudflare Worker (Hono) webhooks for WhatsApp Cloud API and Telegram; OpenRouter free-first with paid fallback and caching; D1 or Neon for memory. | plan.md, overlays | project code, n8n workflow JSON |
| `pay` | Paystack checkout, webhook signature verification, transaction verify call, idempotent order updates; explains Grey for receiving foreign payouts. | plan.md | payment module |
| `deploy` | Host setup for Cloudflare, Vercel, Render or Cloud Run; runs `preflight.py`; writes exact env var names, DNS records and settings; the human does every account step; checks the live URL. | plan.md, project | `deploy.md` |
| `cost-guard` | Runs `freetier_check.py`; compares known usage with triggers; warns before money is spent; refreshes `cost.md`. | free-tiers.json, cost.md | `cost.md` |
| `lean-claude` | Claude-usage rules: CLAUDE.md template under 60 lines, model choice per task, subagents for exploration, one feature per session, log before compact. | profile | `CLAUDE.md`, `STATUS.md` |
| `handoff` | Client handover: account ownership table, run guide, credential transfer checklist (the client changes passwords and keys), support terms. | project | `handoff/` folder |
| `profile` | Creates or updates the private profile through 6 questions; never stores secret values. | profile | `~/.claude/lean-builder/profile.md` |

## 6. Data formats

### 6.1 `shared/stacks.json`

```json
{
  "version": 1,
  "rows": [
    {
      "id": "saas-personal",
      "type": "saas",
      "context": "personal",
      "commercial": false,
      "accounts_owner": "builder",
      "stack": {
        "app": "nextjs",
        "host": "vercel-hobby",
        "data": "neon",
        "auth": "better-auth",
        "payments": "paystack",
        "email": "resend",
        "jobs": "cloudflare-cron",
        "files": "cloudflare-r2"
      },
      "fallbacks": { "host": ["cloudflare-workers"], "data": ["supabase"] },
      "why": { "host": "Free while the product earns nothing; Hobby forbids commercial use." },
      "overlays": ["claude-md-lean", "env-example", "security-headers", "paystack-webhook"],
      "upgrade_triggers": ["vercel-hobby:commercial_use", "neon:storage_gb>0.4"]
    }
  ]
}
```

Rules:
- `type` is one of `website`, `saas`, `internal`, `agent`. `context` is one of `personal`, `client`, `startup`.
- `commercial` is `true`, `false` or `"any"`. A row with `commercial: false` must not be picked for a build
  that earns money.
- Every component value must exist as a provider id in `free-tiers.json` (checked by tests). Framework-only
  components with no account (e.g. `nextjs`, `astro`, `better-auth`) are listed there with `"account": false`.
- `accounts_owner` is `client` for every `client` row.
- `upgrade_triggers` use `provider:metric>threshold` or `provider:condition`.

### 6.2 `shared/free-tiers.json`

```json
{
  "neon": {
    "name": "Neon",
    "account": true,
    "plan": "Free",
    "limits": [{ "metric": "storage_gb", "value": 0.5, "period": "per project" }],
    "commercial_use": true,
    "idle_behaviour": "scales to zero, resumes on request",
    "source_url": "https://neon.com/pricing",
    "checked_on": "YYYY-MM-DD"
  }
}
```

Every limit is copied from the provider's official pricing or limits page on the `checked_on` date. Values
quoted in conversation before this spec are provisional and must be re-verified when the file is written.

### 6.3 Private profile `~/.claude/lean-builder/profile.md`

```markdown
---
accounts: [vercel-hobby, cloudflare, gcp, render, supabase, neon, n8n-selfhosted, openrouter, paystack, grey]
currency: NGN
region: lagos
default_context: personal
client_rule: client-owned-accounts
secret_names: [PAYSTACK_SECRET_KEY, OPENROUTER_API_KEY, RESEND_API_KEY]
---
Free notes for Claude (preferences, habits).
```

Secret values never appear in the profile. `profile` refuses to write a value that looks like a key.

## 7. Stack picking (`pick_stack.py`)

Input: `--type`, `--context`, `--commercial yes|no`, optional `--profile` path. Output: JSON (and a Markdown
table with `--md`).

1. Select the rows matching `type` and `context`, and `commercial` (or `"any"`). Exactly one row must match;
   otherwise exit with a clear error (tested).
2. For each component that needs an account, if its provider is not in the profile's `accounts`, take the
   first fallback that is; record a note ("you have no Vercel account, using Cloudflare Workers"). If none
   fits, keep the default and mark it "new account needed".
3. For `client` rows, account checks are skipped: the client opens the accounts (listed in the plan).
4. Attach the provider limits from `free-tiers.json` and flag any `checked_on` older than 90 days.
5. Print the result. `kit` turns it into `plan.md` and `cost.md`.

Same inputs always give the same output. No network access, no model calls.

### v1 decision table (content of `stacks.json`, limits to be verified)

| Type | Personal | Client | Startup |
|---|---|---|---|
| Website | Astro, Cloudflare Pages, Worker + Resend form | same on client's Cloudflare account, optional Keystatic | Astro (Next.js only if app-like), Cloudflare Pages |
| SaaS | Next.js, Neon + Better Auth, Vercel Hobby while non-commercial; Cloudflare Workers once commercial; Paystack | Next.js, Supabase, Cloudflare or client's paid Vercel, client's Paystack | Next.js, Supabase, Cloudflare Workers, Paystack |
| Internal tool | Next.js, Supabase or Neon (same as startup) | Next.js, Supabase on client account (Pro when live), FastAPI on Cloud Run if heavy, n8n sheet sync | Next.js, Supabase or Neon |
| Agent | n8n self-hosted, Cloudflare Worker (Hono) webhooks, OpenRouter free-first, D1 or Neon | n8n on client's server (licence check), client's Meta Business number, client's model key | n8n, Worker webhooks, OpenRouter, Neon |

The SaaS personal cell is two rows (`commercial: false` on Vercel Hobby, `commercial: true` on Cloudflare
Workers). Shared services where relevant: Resend (email), Cloudflare cron (jobs), Cloudflare R2 (files), Grey
(receiving foreign payouts, not checkout).

## 8. Overlays (`shared/overlays/`)

Small, version-light files applied after the official starter runs:
`claude-md-lean`, `status-md`, `env-example`, `gitignore-secrets`, `security-headers` (per host),
`contact-form-worker`, `paystack-webhook` (signature check + verify call), `whatsapp-webhook-worker`,
`telegram-webhook-worker`, `openrouter-client` (free-first with fallback and cache), `n8n-skeletons`
(sheet sync, lead capture, daily report), `audit-log-table`, `rls-policies`, `cloud-run-fastapi`.

Starters are always the official ones (`create-next-app`, `npm create cloudflare`, `npm create astro`,
FastAPI layout). The kit never vendors a framework.

## 9. End-to-end flow

1. `kit` reads the profile (runs `profile` first if missing).
2. Intake: what it does, who it is for, context, commercial or not, who owns accounts, deadline. Defaults offered.
3. `pick_stack.py` chooses; `kit` writes `plan.md` (one-page spec, stack with one reason per part, "not in v1")
   and `cost.md` (monthly cost at zero, small and growing usage; upgrade triggers), plus `CLAUDE.md` and
   `STATUS.md` from `lean-claude`.
4. Samuel says yes. The `build-*` skill runs the starter, applies overlays, builds one thin vertical slice, then
   features in small steps, verifying each (build, tests, browser at 375 and 1440 px). `STATUS.md` is updated
   after each step (same resume protocol as the workspace work log).
5. `deploy`: `preflight.py` must pass (build, no secrets, env vars listed, headers, cost-guard green); the human
   does account steps; Claude writes settings and checks the live URL.
6. Client builds: `handoff`. Personal builds: a content packet for the brand pipeline.

## 10. Safety rules

- Claude never types passwords, card numbers or live keys and never buys anything. The human does every
  account, billing and DNS step; the kit writes exact instructions.
- Secrets live only in host env vars. Every project gitignores `.env*`; `secret_scan.py` runs before every push.
- Client work: client-owned accounts and private repos from day one. Personal work: public by default.
- Licence flags: n8n Sustainable Use License when hosting for clients; OpenRouter model terms; credit any blog
  post or repo a build is based on.
- Every free-tier figure shown to the user carries its `checked_on` date and source link.
- No invented claims (users, results, testimonials) in any README, plan or page.

## 11. Testing

- `pytest` for `pick_stack.py` (each row, fallbacks, client rows skip account checks, no-match error,
  commercial rule, staleness flag), `freetier_check.py`, `preflight.py`, `secret_scan.py` (fake key patterns).
- Schema validation of `stacks.json` and `free-tiers.json`; cross-check that every provider id exists.
- Example checks: each `examples/*/expected.json` equals `pick_stack.py` output for that brief's inputs.
- CI on GitHub Actions (free for public repos): tests, schema checks, markdown link check.
- Real-world check: the first brand-pipeline build ships with the kit; findings feed v1.1.

## 12. Open items

- Final repo name (default `lean-builder-skill`).
- Re-verify every free-tier limit from official pages when writing `free-tiers.json`.
- Confirm n8n licence wording for client-hosted instances before shipping `build-agent` client guidance.
- GitHub push only when Samuel says so (public repo under `LilProff`).
