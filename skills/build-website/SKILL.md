---
name: build-website
description: Builds a fast business website, portfolio or landing page with Astro on Cloudflare Pages at zero hosting cost, with a contact form that emails the owner through Resend and an optional Keystatic editor for clients. Use after /kit picks a website stack, or when the user says "build my website", "landing page", "portfolio site" or "business site".
---

# build-website

Shared files: `<base>/../../shared/` (`<base>` is the "Base directory for this skill" line).

## Before you start

Read `plan.md` and `kit/stack.json`. If they are missing, run the `kit` skill first. Read `STATUS.md` and continue from "Next step" if work is in progress.

## Steps (update STATUS.md after each one)

1. **Starter.** Run the official starter in the project folder: `npm create astro@latest`. Pick the empty or minimal template.
   If the folder is not empty (kit already wrote `plan.md`, `cost.md` and `kit/`), run the starter in a `_starter` subfolder instead, move its contents up without overwriting `plan.md`, `cost.md`, `kit/`, `CLAUDE.md` or `STATUS.md`, then delete `_starter`.
2. **Overlays.** Write `kit/values.json` (`PROJECT_NAME`, `STACK_SUMMARY`, `CONTEXT`, `ENV_VARS` with `RESEND_API_KEY=`, `CONTACT_TO_EMAIL=`, `CONTACT_FROM_EMAIL=`), then apply the row's overlays:
   `python <base>/../../shared/tools/apply_overlays.py --ids <overlays from kit/stack.json> --project . --values kit/values.json`
   This adds `contact-form-worker`, `security-headers-cloudflare`, `env-example` and the git and Claude files.
3. **Thin slice first.** Build the home page with the one main action from the plan (book, call, buy, enquire) and the working contact form. Check it end to end before adding pages.
4. **Pages.** Add the pages in `plan.md` one at a time.
5. **Client sites only.** Add Keystatic so the client can edit text in the browser. Skip it for personal and startup sites.

## Check after every step

- `npm run build` passes.
- In a browser at 375 px and 1440 px: nothing overflows, text is readable, the main action is visible without scrolling on a phone.
- Every page has one H1, a title under 60 characters, a description under 155 characters, and alt text on every image.

## Rules

- Real content only: the owner's words, photos and facts. Missing content goes on a list for the owner, never invented.
- Env var names go in `.env.example`. The owner pastes the values into the Cloudflare dashboard.
- When the site works, load the `deploy` skill.
