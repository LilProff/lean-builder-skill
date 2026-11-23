---
name: build-agent
description: Builds an AI agent or automation on WhatsApp or Telegram with a small Cloudflare Worker, OpenRouter models (free first, paid fallback, cached answers), memory in D1 or Neon, and n8n flows for the glue. Use after /kit picks an agent stack, or when the user says "build a WhatsApp bot", "Telegram bot", "AI assistant", "automate this" or "AI agent".
---

# build-agent

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## Before you start

Read `plan.md`, `kit/stack.json` and `STATUS.md`. Write down in `plan.md`: what the agent may do, what it must never do, and when it hands over to a person.

## Steps (update STATUS.md after each one)

1. **Starter.** `npm create cloudflare@latest` (Hello World Worker, TypeScript), then `npm install hono`.
   If the folder is not empty (kit already wrote `plan.md`, `cost.md` and `kit/`), run the starter in a `_starter` subfolder instead, move its contents up without overwriting `plan.md`, `cost.md`, `kit/`, `CLAUDE.md` or `STATUS.md`, then delete `_starter`.
2. **Overlays.** Write `kit/values.json` with `ENV_VARS`, then:
   `python <base>/../../shared/tools/apply_overlays.py --ids <overlays from kit/stack.json> --project . --values kit/values.json`
   The starter already wrote `src/index.ts`, so the worker overlay is skipped. Apply it alone a second time with `--force` to replace the Hello World file: `python <base>/../../shared/tools/apply_overlays.py --ids <whatsapp-webhook-worker or telegram-webhook-worker> --project . --values kit/values.json --force`. Never use `--force` on the other overlays.
   - Telegram rows get `telegram-webhook-worker`; WhatsApp rows get `whatsapp-webhook-worker`.
   - Every agent gets `openrouter-client` and `n8n-skeletons`.
3. **Models.** Set `OPENROUTER_MODELS` to free models first and one paid model last. Free models are rate limited (check `kit/stack.json` for today's figures), so cache answers and keep prompts short.
4. **Thin slice.** One message in, one sensible answer out, on a test number or test bot.
5. **Memory.** Store each conversation in D1 or Neon (per `kit/stack.json`), keyed by the sender. Keep only what the agent needs.
6. **Tools and flows.** Add actions one at a time (look up an order, log a sale). Use n8n for anything that touches spreadsheets or other apps.
7. **Hand-over.** When the agent is unsure, it says so and alerts a person. Never let it promise prices, refunds or delivery dates it cannot check.

## Check after every step

- `npm test` (or `node --test`) passes for the logic files.
- A tampered webhook signature is rejected.
- The free model limit is not hit in a normal day (`cost-guard` skill).

## Client rows

- The client's own Meta Business account and phone number, and the client's own OpenRouter key.
- n8n runs on the client's server: its licence allows their own internal business use only.
- WhatsApp: replies are only allowed inside the 24-hour window after the customer writes; each number gets 1,000 free service messages a month, then they are charged. Template messages are charged per message.

When it works, load `deploy`, then `handoff` for client work.
