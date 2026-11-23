# Status: lean-builder-skill

## Resume here
- Last updated: 23 Nov 2026, desktop account.
- v0.1.0 public 23 Nov: https://github.com/LilProff/lean-builder-skill (`10c5d35`), 163 Python + 28 TypeScript tests.
- Task 18 dogfood: installed from the local folder, profile saved, `/kit` run for a one-page site in
  `../lean-builder-site/`, deployed 23 Nov: https://lean-builder-skill.pages.dev (200, headers set, ₦0).
- v0.1.1 done locally (see below), staged, not committed. Next: Samuel's OK to commit and push; icon.

## v0.1.1 (23 Nov 2026): done except the icon, staged, not committed

Done, each test-first (suite 189 Python + 29 TypeScript):
- CLAUDE.md overlay fills the tool path (quoted, paths can contain spaces), host, install and build commands,
  and points to a starter's own AGENTS.md. kit and lean-claude write the new values.
- `pick_stack.py --skip-roles forms,email`: leaves roles out of v1 with their overlays and upgrade triggers.
  Role overlays declare `"roles"` in overlay.json. host, app and webhooks cannot be skipped.
- Build skills rename the starter's package (and `wrangler.jsonc` for Workers); values are added, not rewritten.
- deploy skill: device-code Cloudflare login with Pages-only scopes, `npx.cmd`, Pages `--force`, run outside the app.
- Deferred minors: unreadable or non-UTF-8 profile gives a clear error; freetier_check exits 2 on bad input;
  GitHub Pages headers now WARN (it ignores `_headers`); failed builds show their last output; RLS uses
  `(select auth.uid())`; Paystack verify returns currency and the route says to check amount and currency;
  OpenRouter skips and never caches empty answers; cost-guard never edits the plugin's free-tiers.json.
- Dogfooded on ../lean-builder-site: re-picked with --skip-roles, regenerated CLAUDE.md, ran its commands.

Not done:
1. **Plugin icon.** Needs a square PNG (512 to 2048 px) at `.claude-plugin/icon.png`, Samuel's choice of design.
2. **Workers static assets.** Wrangler now prefers Workers over Pages for static sites. Pages still works with
   `--force`; moving websites to Workers needs its limits checked first (v0.2).

## Done (newest first)
- 23 Nov 2026: v0.1.1 fixes (dogfood findings + deferred minors), staged.
- 23 Nov 2026: Task 18 steps 1 to 4: install, profile, /kit, build, deploy live at https://lean-builder-skill.pages.dev.
- 23 Nov 2026: final review fix pass (9 Important + 2 minor), Tasks 1 to 17.
