---
name: session-handoff
description: Record or resume the actionable state of the G435 media-control project. Use when the user asks to save progress, hand off work, continue in a later session, or resume previous work; do not use for a transcript or a general summary.
---

# G435 Media Control Session Handoff

Leave a short project-local handoff that lets the next session continue the current G435 control or Galaxy integration work without repeating discovery.

## Handoff location

- Use a path specified by the user when provided.
- Otherwise, write to `.claude/session-handoff.md` at this repository's root.
- Keep this project's handoff separate from records for other projects.

## Project context to preserve

This project explores practical ways to improve Logitech G435 control, particularly:

- media controls such as play/pause and next/previous track;
- the distinction between documented G435 controls, hypothetical remaps, and controls proven on a real device;
- Galaxy phone notification readout over a Bluetooth-connected G435.

Do not state that a proposed control mapping is supported by the G435 firmware unless it has been tested. Record the connection mode involved (`Bluetooth` or `LIGHTSPEED`) whenever it affects the result. Treat Galaxy Buds-only Galaxy Wearable features separately from phone-level Assistant, Gemini, or Modes and Routines behavior.

## When saving a handoff

First inspect the current conversation, relevant project files, and any existing `.claude/session-handoff.md`. Preserve still-valid unfinished work and replace stale next steps.

Use this format, omitting empty sections:

```markdown
# Session handoff

- Updated: YYYY-MM-DD HH:mm (timezone)
- Objective: One-sentence desired outcome
- Status: in progress | blocked | complete

## Current state
- Confirmed current behavior and context

## Completed
- Work actually completed and verified

## Decisions and constraints
- User decisions, supported/unsupported boundaries, and safety constraints

## Device and integration evidence
- Device model, phone/OS if known, connection mode, tested input, observed result

## Files and evidence
- Relevant files, source links, commands, and validation results needed to continue

## Remaining TODO
- Concrete unfinished work

## Next action
- The first useful action for the next session

## Blockers or open questions
- Missing device access, unresolved behavior, or a decision required from the user
```

Follow these rules:

- Record only facts required to continue. Do not save a conversation transcript.
- Clearly label items as `documented`, `proposed`, `tested`, or `unverified` when discussing controls or compatibility.
- Include button timing and simultaneous-press details only when they are relevant to a mapping or test.
- Do not store passwords, tokens, personal notification text, phone numbers, or other sensitive notification contents.
- Preserve user requirements over previous plans. Do not turn a speculative workaround into a completed feature.
- After saving, tell the user the record path and the next action.

## When resuming

1. Read `.claude/session-handoff.md` first, if it exists.
2. Confirm current project files and, when relevant, the actual G435/phone connection state before relying on the record.
3. Continue from `Next action` and `Remaining TODO`; do not repeat completed research or tests.
4. If the user's new request conflicts with the record, follow the new request.
5. Update the handoff after meaningful verified progress when the user asks for it or the current task is a handoff task.
