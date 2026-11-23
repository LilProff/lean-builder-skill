---
name: profile
description: Creates or updates your private lean-builder profile (which accounts you have, currency, region, default build context, how client work is owned, and the NAMES of your keys). Run it once before your first /kit, or when you open a new account. Use when the user says "set up my profile", "I now have a Cloudflare account", "update my accounts" or when /kit finds no profile.
---

# profile

Saves the facts `kit` needs to pick a stack you can actually use, so it never suggests an account you do not have.

## Where it lives

`~/.claude/lean-builder/profile.md` on this computer, outside every repo, so it can never be pushed.
Find the shared tools from the "Base directory for this skill" line: they are in `<base>/../../shared/tools/`.

## Ask these six questions in one message

Offer the default in brackets so the user can just say "ok".

1. Which accounts do you have? Pick from: `vercel`, `cloudflare`, `github`, `gcp`, `render`, `supabase`, `neon`, `resend`, `openrouter`, `paystack`, `grey`, `n8n-selfhosted`, `meta` (WhatsApp Business), `telegram`. [cloudflare, github, neon, resend]
2. Currency for cost sheets? [NGN]
3. Region? [lagos]
4. Default build context: personal, client or startup? [personal]
5. Client work rule? [client-owned-accounts: every client build starts on the client's own accounts]
6. The NAMES of the keys you use, never the values. [PAYSTACK_SECRET_KEY, OPENROUTER_API_KEY, RESEND_API_KEY]

## Save it

Write the answers with `profile_io.write_profile` (in `tools/profile_io.py`), for example:

```bash
python -c "import sys; sys.path.insert(0, '<base>/../../shared/tools'); from pathlib import Path; from profile_io import DEFAULT_PATH, write_profile; write_profile(DEFAULT_PATH, {'accounts': ['cloudflare','neon'], 'currency': 'NGN', 'region': 'lagos', 'default_context': 'personal', 'client_rule': 'client-owned-accounts', 'secret_names': ['PAYSTACK_SECRET_KEY']})"
```

Then show the saved path and the file contents.

## Rules

- Never store a key, password or token. If the user pastes one, refuse, explain that only the NAME belongs here, and tell them to put the value in their host's environment variables. `write_profile` also refuses anything that looks like a real key.
- Never ask for a password. Never sign in to anything for the user.
- If the file exists, read it first and change only what the user changes.
