---
name: cost-guard
description: Checks a live or planned lean-builder project against its free-tier limits, flags limit data older than 90 days, fires upgrade triggers before a bill arrives and refreshes cost.md with what to move to and what it costs. Use when the user says "will this cost me money", "check my free tier", "are we near the limit", "cost check" or before and after launch.
---

# cost-guard

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## 1. Gather usage

Ask the owner for current numbers from each dashboard, or estimate them and label every estimate clearly as an estimate. Write them to `kit/usage.json`, keyed like the triggers in `kit/stack.json`:

```json
{ "neon:storage_gb": 0.3, "cloudflare-workers:requests_per_day": 12000, "vercel-hobby:commercial_use": false }
```

## 2. Run the check

```bash
python <base>/../../shared/tools/freetier_check.py --plan-json kit/stack.json --usage kit/usage.json
```

It lists free-tier data older than 90 days and every trigger that fired.

## 3. Explain each result in plain English

- **Stale data:** open the provider's page (link in `kit/stack.json`), re-check the limit, and update `shared/free-tiers.json` with the new figure and today's date.
- **Fired trigger:** say what it means and the cheapest move. Examples:
  - `vercel-hobby:commercial_use`: the product now earns money, so move to Cloudflare Workers (re-run `kit` with `--commercial yes`).
  - `supabase:idle_pause`: a live client system must be on Supabase Pro, paid by the client.
  - `neon:storage_gb>0.8`: clean old data or move to a paid plan before the 1 GB limit.
  - `openrouter:free_requests_per_day>40`: add credits or a paid fallback model before users hit the cap.

## 4. Refresh cost.md

Update the monthly cost now, at small use and at growing use, with each figure's checked-on date and source link. Never invent a price: if a page gives no figure, say so and link it.
