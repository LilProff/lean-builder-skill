# Status: lean-builder-skill

## Resume here
- Last updated: 23 Nov 2026, desktop account.
- v0.1.0 code done: 163 Python + 28 TypeScript tests pass, final review fixes in, everything staged, no commits.
- Task 18 dogfood: installed from the local folder, profile saved, `/kit` run for a one-page site in
  `../lean-builder-site/`, deployed 23 Nov: https://lean-builder-skill.pages.dev (200, headers set, ₦0).
- Next: Samuel picks the repo name and says whether to commit, create the public repo and push.

## v0.1.1 items (found while dogfooding, 23 Nov 2026)

1. **Plugin icon missing.** `claude plugin validate` warns ICON_MISSING. Add a square PNG (512 to 2048 px) at
   `.claude-plugin/icon.png` before the first directory submission (the icon is taken only once).
2. **CLAUDE.md placeholders left unfilled.** The `claude-md-lean` overlay writes `<lean-builder>` and `<host>`.
   kit should pass the plugin's shared path and the chosen host provider as values.
3. **"Install: see plan.md" points nowhere.** plan.md has no starter commands. Write the starter command into
   the values (or drop the line).
4. **Stack roles cannot be dropped.** website-personal always brings forms + email (Resend) and the
   `contact-form-worker` overlay, even for a page with no form. kit should let the plan mark a role "not in v1"
   and skip its overlays and triggers.
5. **Starter package name.** Running the starter in `_starter` leaves `"name": "starter"` in package.json.
   The build skills should say to rename it to the project name.
6. **Astro now ships AGENTS.md.** The Astro starter writes its own `AGENTS.md`. Harmless, but CLAUDE.md should
   point to it rather than repeat Astro advice.
7. **Wrangler not preinstalled.** deploy's direct-upload route needs `npx wrangler login` first; say so in the
   deploy skill and note it is the owner's sign-in step.
8. **Wrangler 4.166 changed Pages.** `pages project create` now delegates to Workers static assets and fails for
   a plain static folder; `--force` keeps classic Pages. Run it outside the Astro folder, or Wrangler's auto-config
   runs `astro add cloudflare`. Decide in v0.1.1 whether websites move to Workers static assets (re-check limits)
   or the deploy skill documents `--force`.
9. **Login on Windows and in Claude's sandbox.** Plain `wrangler login` timed out (sandbox blocks the localhost
   callback) and was refused with the full scope list. What worked: `wrangler login --device --scopes
   account:read user:read pages:write`. PowerShell blocks `npx.ps1`; use `npx.cmd`. Put both in the deploy skill.
10. **Deferred minors from the final review** (see `.superpowers/sdd/.../progress.md`, "Final: minor (deferred)").

## Done (newest first)
- 23 Nov 2026: Task 18 steps 1 to 4: install, profile, /kit, build, deploy live at https://lean-builder-skill.pages.dev.
- 23 Nov 2026: final review fix pass (9 Important + 2 minor), Tasks 1 to 17.
