---
name: kit
description: The front door of lean-builder. Picks the cheapest stack for a website, SaaS, internal tool or AI agent in a personal, client or startup context, then writes plan.md, cost.md, CLAUDE.md and STATUS.md into the project and hands off to the right build skill. Use when the user says "/kit", "start a new build", "what stack should I use", "build me a ...", "cheapest way to build ..." or "plan this project".
---

# kit

You turn a build idea into a one-page plan, a cost sheet and a chosen stack, using a script so the choice is the same every time and costs no extra model calls.

Shared files are in `<base>/../../shared/`, where `<base>` is the "Base directory for this skill" line. Call that folder `<shared>` below.

## 1. Profile

Look for `~/.claude/lean-builder/profile.md`. If it is missing, run the `profile` skill first, or continue with defaults and say so.

## 2. Intake: one round, at most 5 questions, each with a default

- What does it do, and for whom? (one sentence)
- Type: website, saas, internal (internal tool or ERP) or agent (AI agent or automation)? [your best guess from the sentence]
- Context: personal, client or startup? [profile default]
- Does it earn money now or soon? [no for personal, yes otherwise]
- Deadline? [none]

For client work, the client owns every account from day one. Say that in the plan.

## 3. Pick the stack

```bash
python <shared>/tools/pick_stack.py --type <type> --context <context> --commercial <yes|no> --md --out kit/stack.json
```

Show the table it prints. Read every note: a note may say an account is missing, a fallback was used, or limits need re-checking.

## 4. Write the plan files in the project root

`plan.md`, short enough to read in a minute:

```markdown
# <Name>: plan
For: <who>, who want to <job>.
The one thing a user must do: <primary action>.
Pages or screens: <list with purpose>.
Must work: <features>.
Stack: <one line per role, with its one-sentence reason, the `why` field of that component in kit/stack.json>.
Accounts: <yours or the client's, and which new ones are needed>.
Done when: <testable outcomes>.
Not in v1: <cut items>.
```

`cost.md`: monthly cost at zero users, at small use and at growing use, based only on the limits in `kit/stack.json`. Every figure shows its checked-on date and source link. List each upgrade trigger and what to move to. If a provider has no figures (for example Paystack fees), say "copy the current figure from <link>" instead of guessing. Use the profile currency.

## 5. Add the lean files

Write a values file and apply the base overlays:

```bash
python <shared>/tools/apply_overlays.py --ids claude-md-lean,status-md --project . --values kit/values.json
```

`kit/values.json` needs `PROJECT_NAME`, `STACK_SUMMARY` (one line) and `CONTEXT`.

## 6. Stop and ask

Show `plan.md` and `cost.md` and ask for a clear yes. Do not scaffold anything before the yes.

## 7. Hand off

Load the build skill that matches the type: `build-website`, `build-saas`, `build-internal` or `build-agent`.

## Rules

- Never invent users, numbers, prices or results. Unknown facts go in the plan as questions.
- Never type passwords, card numbers or live keys. The owner does every account step.
- Keep the plan to one page.
