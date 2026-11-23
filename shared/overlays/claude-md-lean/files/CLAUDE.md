# {{PROJECT_NAME}}

## What this is
A {{CONTEXT}} build. The plan is in `plan.md`, the costs and free-tier limits in `cost.md`.
Progress and the exact stop point are in `STATUS.md`. Read `STATUS.md` first, every session.

## Stack
{{STACK_SUMMARY}}

## Commands
- Install: `{{INSTALL_CMD}}`
- Build: `{{BUILD_CMD}}`, and it must pass before saying anything is done.
- Before any push: `python "{{SHARED_DIR}}/tools/secret_scan.py" .`
- Before any deploy: `python "{{SHARED_DIR}}/tools/preflight.py" --project . --host {{HOST}} --build-cmd "{{BUILD_CMD}}"`
- The tool path is the lean-builder plugin's folder; after a plugin update, change the version in it.
- If the starter wrote an `AGENTS.md`, read it for framework advice instead of repeating it here.

## Rules
- No secrets in the repo. Env var NAMES go in `.env.example`; values go in the host's settings.
- Work in small steps. After each step: build, test, check the browser at 375 px and 1440 px.
- Update `STATUS.md` after every step ("Stopped at", "Next step"). A session can end at any time.
- One feature per session. Update `STATUS.md` before any compact.
- Use the strongest model only for planning and hard debugging; a lighter one for search and small edits.
- Send broad searches to a helper agent; keep only the answer here.
- Never type passwords, card numbers or live keys. The owner does every account, billing and DNS step.
- No invented users, numbers or testimonials in any page or README.

## Where things are
- `plan.md`: what we are building and what is not in v1.
- `cost.md`: monthly cost now and later, with upgrade triggers.
- `kit/stack.json`: the chosen stack (from the lean-builder kit).
- `STATUS.md`: done, in progress, next step.
