# Changelog

All versions are beta (0.x). Format: one section per version, newest first.

## 0.3.1 — 2026-10-20

- Reference research uses references that the user collects: attached screenshots, page URLs, or short notes.
- Claude suggests games and screens to look at, and reads only the pages the user sends.
- Claude no longer searches screenshot collections itself.
- Reference images stay in the conversation and are named in the reference log.

## 0.3.0 — 2026-10-20

- Navigation cost check.
  - Phase 2 asks for the most common player tasks and their frequency (high, medium, low).
  - The validator finds the cheapest gamepad path from gameplay to each task. It counts presses and depth and compares them to budgets.
  - Over a default budget is a warning. Over a budget set by the user is an error. A task with no path is an error.
- New `nav_graph.py` draws the navigation graph as SVG, with task paths, budget status, and a task table.
- The skill offers the graph once in Phase 2, asks where to put it, and updates it automatically if the user chooses that.
- Rubric check 11: navigation cost.

## 0.2.0 — 2026-10-20

- New `references/patterns.md`: 14 pattern cards, adapted in part from omer-metin/skills-for-antigravity (Apache 2.0). They cover:
  - text size from XAG 101 and contrast from XAG 102
  - text over gameplay
  - HUD visibility states
  - progressive disclosure
  - input actions and prompts
  - controller navigation
  - safe area and resolution test set
  - touch targets
  - notifications, cooldowns, radial menus, combat numbers, minimaps, and diegetic UI
- Phase 2 adds HUD visibility states and triggers, an input map, and glance/focus/inspect layers.
- New validator checks:
  - text floor per platform
  - motion tokens over 500 ms
  - `outline: none` without a focus style
  - hard-coded "Press A" text
  - `@prompt` actions
  - HUD visibility
- Inspector: Background control (bright, mid-gray, dark, busy) for readability tests. It needs a `data-backdrop` element.

## 0.1.1 — 2026-10-20

- Inspector picks elements by geometry. Picking now works through `pointer-events: none` layers, full-screen overlays, and scaled stages.
- Inspector: Selector field (shows and edits the selector for the scope), Move panel button, and pointer input blocked in inspect mode.

## 0.1.0 — 2026-10-20

- First beta. The process covers:
  - brief and reference options
  - information architecture
  - tokens and components
  - directions and screens
  - critique rubric and handoff
  - optional motion phase
- Addressing system, registry, validator, and inspector with annotation and motion preview.
