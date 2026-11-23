---
name: deploy
description: Puts a lean-builder project live on Cloudflare, Vercel, Render or Google Cloud Run behind a preflight check (build passes, no secrets, env vars listed, security headers set, limits fresh), writes the exact settings and DNS records for the owner to enter, then checks the live URL. Use when the user says "deploy", "ship it", "put it live", "connect my domain" or after a build skill finishes.
---

# deploy

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## 1. Preflight (must pass)

```bash
python <base>/../../shared/tools/preflight.py --project . --host <host from kit/stack.json> --build-cmd "npm run build"
```

`--host` is the `provider` of the `host` component in `kit/stack.json`. Agent stacks have no `host` role: use the provider of the `webhooks` role (the Cloudflare Worker) instead.

Any FAIL stops the deploy. Fix it and run again. Show the table to the owner.
Before any push to GitHub, also run `python <base>/../../shared/tools/secret_scan.py .`

## 2. Host steps (the owner does every account step)

Write `deploy.md` with the exact steps for the chosen host:

- **Cloudflare Pages (websites):** connect the GitHub repo in the dashboard, set the build command and output folder, add env vars under Settings. Or deploy with `npx wrangler pages deploy dist`.
- **Cloudflare Workers (apps, bots):** `npx wrangler deploy`; secrets with `npx wrangler secret put NAME` (the owner types the value).
- **Vercel:** import the repo; add env vars in Project Settings. Hobby only for builds that earn nothing.
- **Render:** new Web Service from the repo; free services sleep after 15 minutes idle.
- **Cloud Run:** `gcloud run deploy --source api/`; env vars with `--set-env-vars` or Secret Manager.

List every env var NAME from `.env.example` and where it goes. Never ask for the values.

## 3. Domain

After the owner buys the domain at any registrar, write the exact DNS records the host asks for (name, type, value) in `deploy.md`. The owner adds them.

## 4. Check it is live

```bash
curl -s -o /dev/null -w "%{http_code}" https://<the live URL>/
```

Expect 200. Open the site at 375 px and 1440 px. Submit the contact form or a test payment once.

## Rules

- Nothing goes live without the owner's yes after the preflight.
- Claude never buys a domain, enters a card, signs in or pastes a live key.
- Client work deploys to the client's accounts only.
- After launch, run the `cost-guard` skill; for client work, then `handoff`.
