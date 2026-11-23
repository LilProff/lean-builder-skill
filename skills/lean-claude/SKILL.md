---
name: lean-claude
description: Keeps Claude Code usage low on any project. Sets up a CLAUDE.md under 60 lines, a STATUS.md that survives closed sessions, model choice per task, helper agents for wide searches and one feature per session. Use when the user says "save tokens", "my usage keeps running out", "set up CLAUDE.md", "make this project resumable" or at the start of any lean-builder build.
---

# lean-claude

Every message re-reads the whole conversation, so the cheapest work is short sessions with small context and a written record.

## Set up (once per project)

Apply the two overlays from `<base>/../../shared/` ("Base directory for this skill" is `<base>`):

```bash
python <base>/../../shared/tools/apply_overlays.py --ids claude-md-lean,status-md --project . --values kit/values.json
```

This adds `CLAUDE.md` (under 60 lines) and `STATUS.md`. Existing files are never overwritten.

## Keep CLAUDE.md under 60 lines

- Only what Claude cannot guess: the stack, the commands, the rules, where things are.
- Link to longer docs instead of pasting them in.
- Remove anything Claude has not needed in the last few sessions.

## Rules for every session

1. Read `STATUS.md` first. If something is in progress, check the real files and git before continuing.
2. Before a multi-step task, write it in `STATUS.md` with a checklist.
3. After each step, tick it and update "Stopped at" and "Next step". A session can end at any moment.
4. One feature per session. Start a fresh session for the next feature.
5. Use the strongest model for planning and hard debugging only. Use a lighter model for searching, reading and small edits.
6. Send wide searches ("where is X used across the repo") to a helper agent and keep only its answer.
7. Read only the lines you need. Search before you read whole files. Do not re-read files already read.
8. Keep command output short: filter it, show the tail.
9. Before any compact, update `STATUS.md`. Never compact in the middle of an unrecorded change.

## Signs you are wasting usage

- The same file read three times in one session.
- Long logs pasted into the chat.
- Several features mixed in one session.
- No `STATUS.md`, so every session starts by re-exploring the project.
