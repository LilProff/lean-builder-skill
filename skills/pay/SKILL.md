---
name: pay
description: Adds Paystack payments the safe way, with checkout started on the server, a signed webhook, a server-side verify call and an order update that cannot run twice, and explains Grey for receiving foreign payouts. Use when the user says "add payments", "Paystack checkout", "take card payments", "subscriptions in naira" or "get paid in dollars".
---

# pay

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).
The webhook route and helpers come from the `paystack-webhook` overlay (`src/lib/paystack.ts`, `src/app/api/paystack/webhook/route.ts`).

## The flow

1. **Start on the server.** Your server calls Paystack's initialize endpoint with the amount, email and your own order reference. Never let the browser set the amount.
2. **Pay.** Send the customer to the returned checkout link (or use Paystack's inline popup).
3. **Webhook.** Paystack calls `/api/paystack/webhook`. The route checks the `x-paystack-signature` header against your secret key and rejects anything that fails.
4. **Verify.** The route calls `verifyTransaction(reference)` and trusts only that answer, not the webhook body.
5. **Update once.** Mark the order paid only if it is not paid already, looked up by `reference`. Paystack can send the same event more than once.
6. **Answer 200 fast.** Do slow work after replying, or Paystack retries.

## Money rules

- Amounts are in kobo (₦1 = 100 kobo). Store integers, never floats.
- Use test keys while building. The owner switches to live keys in the host's settings at launch.
- If the host in `kit/stack.json` is `vercel-hobby`, Vercel Hobby is for non-commercial use: before switching to live keys, re-run kit with `--commercial yes` and move to the host it picks.
- Fees: Paystack's pricing page blocks automated reads, so `cost.md` must say "copy the current fee from https://paystack.com/ng/pricing". Never guess a fee.

## Client work

The client creates the Paystack account in their business name, so payouts go straight to them. You never hold the client's money or keys.

## Getting paid from abroad

Grey gives foreign bank account details (USD, GBP, EUR) to receive payouts, for example from international clients or digital product sales. It is not a checkout gateway: customers do not pay you through Grey on your site.

## Rules

- Never type card numbers, keys or passwords for the user.
- Never log full webhook bodies with customer details in production.
