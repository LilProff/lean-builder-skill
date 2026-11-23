# lean-builder-skill

Eleven free Claude Code skills that build a website, SaaS, internal tool or AI agent at the lowest cost, for
personal projects, client work and startups. Paystack-ready. Free, MIT.

## What it does

- **Picks the cheapest stack** for your build type and context with a small script, so the same answers always
  give the same stack and picking costs no extra Claude usage.
- **Writes the plan and the cost sheet** (`plan.md`, `cost.md`) with every free-tier limit, the date it was
  checked and a link to the provider's page.
- **Scaffolds from official starters** (Astro, Next.js, Cloudflare, FastAPI) plus small add-on files: security
  headers, a contact form, a Paystack webhook, WhatsApp and Telegram bots, an OpenRouter client that uses free
  models first, n8n flows, an audit log and row level security.
- **Deploys behind a preflight check**: the build passes, no secrets in the repo, env vars listed, headers set.
- **Hands client work over properly**: the client owns every account, rotates every key, and gets a run guide.

## Install

In Claude Code:

```
/plugin marketplace add LilProff/lean-builder-skill
/plugin install lean-builder-skill@lean-builder-skill
```

Then run the `profile` skill once to record which accounts you have (names of keys only, never the keys).

## 60-second demo

Brief: *"A one-page portfolio for a freelance developer, with a contact form. It should cost nothing to host."*
(`examples/website-personal`). `/kit` asks five quick questions, runs the picker and shows:

```
Stack `website-personal` (website, personal, not earning), on your accounts.

| Role  | Choice             | Free-tier limits                                          | Checked on |
|-------|--------------------|-----------------------------------------------------------|------------|
| app   | Astro              | none listed                                               | 2026-11-23 |
| host  | Cloudflare Pages   | builds: 500 per month; files_per_site: 20000 per site ... | 2026-11-23 |
| forms | Cloudflare Workers | requests_per_day: 100000 per day; cpu_ms: 10 ms ...       | 2026-11-23 |
| email | Resend             | emails_per_month: 3000; emails_per_day: 100 ...           | 2026-11-23 |

Upgrade triggers: `resend:emails_per_month>2400`, `resend:emails_per_day>80`
```

It then writes `plan.md` and `cost.md`, waits for your yes, and hands over to `build-website`.

## The 11 skills

| Skill | What it does |
|---|---|
| `kit` | Front door: intake, stack choice, plan and cost sheet, hand-off to a build skill. |
| `profile` | Saves your private profile: accounts, currency, region, default context, key names. |
| `lean-claude` | Keeps Claude Code usage low: short CLAUDE.md, STATUS.md, model choice, one feature per session. |
| `build-website` | Astro on Cloudflare Pages with a contact form; Keystatic for client editing. |
| `build-saas` | Next.js with Neon and Better Auth or Supabase, plus Paystack. |
| `build-internal` | Internal tools and ERPs: roles, row level security, audit log, optional FastAPI on Cloud Run. |
| `build-agent` | WhatsApp or Telegram agents on a Cloudflare Worker with OpenRouter and n8n. |
| `pay` | Paystack done safely: server start, signed webhook, verify call, update once. |
| `deploy` | Preflight check, exact host and DNS steps for you to do, live URL check. |
| `cost-guard` | Checks usage against free-tier limits and warns before a bill arrives. |
| `handoff` | Client handover: account ownership, run guide, credential rotation checklist, support terms. |

## How stacks are chosen

Four build types (website, SaaS, internal tool, agent) times three contexts (personal, client, startup), in
`shared/stacks.json`. In short:

- **Websites:** Astro on Cloudflare Pages. GitHub Pages only as a fallback for personal sites, because GitHub
  does not allow it for business sites.
- **SaaS:** Next.js. Vercel Hobby only while the product earns nothing; Cloudflare Workers once it charges.
  Neon for personal builds (never paused), Supabase for client and startup builds.
- **Internal tools:** Next.js and Supabase on the client's own account, FastAPI on Cloud Run for heavy jobs.
- **Agents:** a Cloudflare Worker for webhooks, OpenRouter free models first, n8n for glue, D1 or Neon for memory.

Not every build needs every part. `/kit` can leave roles out of v1 (for example `--skip-roles forms,email` for a
one-page site with no contact form), and their add-on files and upgrade triggers go with them.

Every limit lives in `shared/free-tiers.json` with its source page and the date it was checked (2026-11-23 for
this release). `cost-guard` warns when a figure is more than 90 days old. Where a provider's page could not be
read (Paystack fees), the kit says so and links the page instead of guessing.

## Safety rules

- Claude never types passwords, card numbers or live keys and never buys anything. You do every account step.
- Secrets live only in your host's environment variables. A secret scan runs before every push.
- Client work starts on the client's own accounts and private repos.
- No invented users, numbers or testimonials in anything the kit writes.

## Develop

```
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test "tests/overlays/*.test.ts"
```

Tools in `shared/tools/` use the Python standard library only. Overlay logic is dependency-free TypeScript.

## Credits

The plugin format follows the public Claude skill packs at github.com/Jakeschincariol. Built by
[Samuel Sholarin](https://lilproff.github.io/sasdev/). MIT licence.
