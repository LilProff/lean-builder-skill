---
name: handoff
description: Hands a finished client build over properly, with an account ownership table, a plain-English run guide, a credential transfer checklist where the client rotates every key and password, and a support terms section. Use when the user says "hand over to the client", "handoff", "client handover", "transfer ownership" or after deploying client work.
---

# handoff

Create a `handoff/` folder in the project with four files. Write for a non-technical business owner.

## 1. `handoff/accounts.md`: who owns what

| Service | What it does | Account owner | Login email | Plan and monthly cost |
|---|---|---|---|---|

One row per service in `kit/stack.json` (hosting, database, email, payments, domain, n8n server, WhatsApp number). Every owner must be the client. If anything is still on the builder's account, list it at the top under "To move before handover" with the steps.

## 2. `handoff/run-guide.md`: keeping it running

- How to sign in to each tool.
- What to check weekly (for example, the daily report arrives, payments match the bank).
- What to do if the site or bot is down: the host's status page, then who to call.
- Where backups are and how to restore one.
- The upgrade triggers from `cost.md`, in plain words.

## 3. `handoff/credentials-checklist.md`: transfer, then rotate

For every key, password and token:

- [ ] The client has access in their own account.
- [ ] The client has created a NEW key or password (rotation) and pasted it into the host settings.
- [ ] The old key is deleted.
- [ ] The builder's access is removed, or reduced to what the support terms allow.

Never put any key or password in these files. Names only.

## 4. `handoff/support.md`: support terms

Leave headed sections for the owner to fill in: what is covered, response times, how to request changes, price for extra work, and the end date. Do not invent terms or prices.

## Finish

Walk the client through `accounts.md` and the checklist on a call. Tick each box together.
