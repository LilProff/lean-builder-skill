---
name: build-saas
description: Builds a SaaS or micro-SaaS on Next.js with sign-in, a Postgres database (Neon with Better Auth, or Supabase) and Paystack payments, starting with one thin working slice and staying inside free tiers. Use after /kit picks a SaaS stack, or when the user says "build a SaaS", "app with logins and payments", "subscription app" or "micro-SaaS".
---

# build-saas

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## Before you start

Read `plan.md` and `kit/stack.json`. If they are missing, run the `kit` skill. Read `STATUS.md` and resume from "Next step" if work is in progress.

## Steps (update STATUS.md after each one)

1. **Starter.** `npx create-next-app@latest` with TypeScript, the App Router and the `src/` folder.
   If the host in `kit/stack.json` is Cloudflare Workers, follow Cloudflare's current Next.js guide (`npm create cloudflare@latest` offers it).
   If the folder is not empty (kit already wrote `plan.md`, `cost.md` and `kit/`), run the starter in a `_starter` subfolder instead, move its contents up without overwriting `plan.md`, `cost.md`, `kit/`, `CLAUDE.md` or `STATUS.md`, then delete `_starter`.
2. **Overlays.** Write `kit/values.json`, including `ENV_VARS` (one `NAME=` per line: database URL, auth secret, `PAYSTACK_SECRET_KEY`, `RESEND_API_KEY`), then:
   `python <base>/../../shared/tools/apply_overlays.py --ids <overlays from kit/stack.json> --project . --values kit/values.json`
   This adds `paystack-webhook`, the security headers for the host, and `rls-policies` on Supabase rows.
3. **Data and sign-in.** Follow `kit/stack.json`:
   - Neon + Better Auth: create the Neon project (the owner signs up), install Better Auth, store users in your own tables.
   - Supabase: create the project on the right account (the client's for client work), use Supabase Auth, run `db/rls_template.sql` and adapt it.
   If the host in `kit/stack.json` is `vercel-hobby`, Vercel Hobby is for non-commercial use: before switching to live keys, re-run kit with `--commercial yes` and move to the host it picks.
   Every table a user owns gets an owner column (`user_id` or `org_id`) and an access rule.
4. **Thin slice.** One user signs up, does the core action once, and sees the result. Nothing else until this works.
5. **Payments.** Load the `pay` skill for checkout. The webhook from `paystack-webhook` confirms payments on the server.
6. **Features.** Add the rest of `plan.md` one at a time.

## Check after every step

- `npm run build` and the tests pass.
- Browser at 375 px and 1440 px.
- Signed out users cannot reach signed-in pages; one user cannot see another user's data.

## Rules

- Vercel Hobby only while the product earns nothing. When it starts charging, re-run `kit` with `--commercial yes`.
- Test keys during the build. The owner switches to live keys in the host settings.
- When it works, load the `deploy` skill. Run the `cost-guard` skill before launch.
