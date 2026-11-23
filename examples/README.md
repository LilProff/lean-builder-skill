# Worked examples

Each folder has a short `brief.md` (with the build type, context, whether it earns money, and the accounts the
builder has) and `expected.json`: exactly what `shared/tools/pick_stack.py` returns for that brief.

The expected files were generated with the picker's date fixed at **2026-11-23**, the date the free-tier limits
were last checked. Tests use the same date, so they do not start failing as time passes.

| Example | What it shows |
|---|---|
| `website-personal` | A free portfolio on Astro and Cloudflare Pages with a working contact form. |
| `saas-startup` | A paid booking app on Next.js, Supabase and Paystack, hosted where business use is allowed. |
| `internal-client` | A client's operations dashboard, built on the client's own accounts, with roles and an audit log. |
| `agent-personal` | A Telegram bot on a Cloudflare Worker using free OpenRouter models first. |

To regenerate after changing `shared/stacks.json` or `shared/free-tiers.json`, call `pick()` for each brief
with `date(2026, 11, 23)`, exactly as `tests/test_examples.py` does (the command line has no date flag), then read each `expected.json` before committing it.
