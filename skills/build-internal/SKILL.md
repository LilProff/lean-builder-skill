---
name: build-internal
description: Builds an internal tool or ERP for a business, such as dashboards, operations records, approvals and role-based screens, on Next.js and Supabase with row level security, an audit log and an optional FastAPI back end on Cloud Run, set up on the client's own accounts from day one. Use after /kit picks an internal stack, or when the user says "build an ERP", "internal tool", "admin dashboard", "operations system" or "staff portal".
---

# build-internal

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## Before you start

Read `plan.md` and `kit/stack.json`, then `STATUS.md`. For client work, confirm the client has opened the accounts in their own name (Cloudflare, Supabase, Google Cloud if used). You never host a client system on your accounts.

## Steps (update STATUS.md after each one)

1. **Starter.** `npx create-next-app@latest` with TypeScript and the `src/` folder.
   If the folder is not empty (kit already wrote `plan.md`, `cost.md` and `kit/`), run the starter in a `_starter` subfolder instead, move its contents up without overwriting `plan.md`, `cost.md`, `kit/`, `CLAUDE.md` or `STATUS.md`, then delete `_starter`.
2. **Overlays.** Write `kit/values.json`, then:
   `python <base>/../../shared/tools/apply_overlays.py --ids <overlays from kit/stack.json> --project . --values kit/values.json`
   This adds `rls-policies`, `audit-log-table`, and for heavy back ends `cloud-run-fastapi` and `n8n-skeletons`.
3. **Roles first.** Write down the roles (for example admin, manager, staff) and what each may see and do. Turn that into `org_members` roles and policies from `db/rls_template.sql`.
4. **Audit log.** Run `db/audit_log.sql`. Every create, update and approval writes a row from the server.
5. **Thin slice.** One role signs in, opens one list, edits one record, and the change shows in the audit log.
6. **Modules.** Add the departments or screens from `plan.md` one at a time.
7. **Heavy jobs (only if needed).** Reports, imports and AI calls go in `api/` (FastAPI on Cloud Run, scales to zero).
8. **Spreadsheet sync (if the business lives in sheets).** Import `n8n/sheet-sync.json` into n8n on the client's own server. The n8n licence allows a business to self-host for its own internal use; do not host n8n and charge others for access.

## Check after every step

- Build and tests pass. Browser at 375 px and 1440 px (managers use phones).
- Each role sees only what it should. Try one forbidden action per role.

## Rules

- Live client systems need Supabase Pro (free projects pause after a week idle). The client pays.
- No real staff or customer data in screenshots, demos or the repo.
- When it works, load `deploy`, then `handoff`.
