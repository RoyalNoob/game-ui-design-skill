---
name: "game-gui-design"
description: "Use when the user asks to design game GUI, HUD, menus, or game UI mockups; runs a brief-system-critique process instead of one-shot output."
---

# Game GUI Design

This skill makes game UI mockups through a fixed process. The process removes generic output. Do not skip a phase. Do not make visuals before Phase 3.

Output of the skill: mockups (HTML/SVG, or the Design artifact type if the session lists one) plus a design spec with all relevant information for implementation. Optional: a motion spec and motion prototype (Phase 5b).

## Project files

At the start of a project, copy `scripts/validate_ui.py`, `scripts/nav_graph.py`, and `scripts/inspector.js` from this skill folder to the working directory, and create `ui-registry.json`. Do not retype the tools. Copy the files.

The skill folder also has `references/patterns.md`: pattern cards for text size, text over gameplay, HUD visibility, progressive disclosure, input and prompts, controller navigation, safe area and resolutions, touch targets, notifications, cooldowns, radial menus, combat numbers, minimaps, and diegetic UI. Read only the cards that the current phase or screen needs. The phases below name the cards. Each number in the cards is marked [std] (published guideline) or [heur] (starting point to justify or change).

| File | Purpose |
|---|---|
| `ui-registry.json` | Single source of truth: tokens, components, screen tree, motion, rename map, overrides, change log. |
| `validate_ui.py` | Compares mockups with the registry. Run it before every delivery. |
| `inspector.js` | Overlay for visual selection, annotation, and motion preview. Inline it in every mockup. |
| `nav_graph.py` | Draws the navigation graph from the registry as SVG, with task paths and budget status. Needs `validate_ui.py` in the same folder. |

Registry schema:

```json
{
  "brief": {"platforms": ["console", "pc"], "reference_height": 1080},
  "tokens": {"$color.accent.primary": "#d98e2b", "$type.size.body": "28px", "$motion.duration.normal": "180ms", "$motion.ease.out": "cubic-bezier(0.2, 0, 0, 1)"},
  "type_exceptions": {"$type.size.caption": "PC-only footer, not shown on console"},
  "components": {"@bar": {"parts": ["track", "fill"], "variants": ["low"], "states": ["normal"], "tokens": ["$color.accent.primary"]},
                 "@prompt": {"parts": ["glyph", "label"], "variants": ["xbox", "ps", "switch", "kbm"], "states": ["normal"]}},
  "input_map": {"actions": {"confirm": {"xbox": "A", "ps": "Cross", "switch": "A", "kbm": "Enter"}}, "hold_to_confirm": ["delete-save"]},
  "hud_screens": ["hud"],
  "screens": {"hud": {"hud.bottom-left.health-bar": {"component": "@bar", "tags": ["#p1", "#readout"], "visibility": "peek", "trigger": "on damage; fade 4 s after full health"},
                      "hud.center.interact-prompt": {"component": "@prompt", "action": "interact", "tags": ["#p2", "#prompt"], "visibility": "peek", "trigger": "near an interactable"}}},
  "navigation": {
    "start": "hud",
    "screens": {"hud": {}, "pause": {"focus_order": ["pause.menu.item[0]", "pause.menu.item[1]"], "default_focus": "pause.menu.item[0]", "layout": "list", "wrap": true},
                "inventory": {"focus_order": ["inventory.grid.slot[0]", "..."], "layout": "grid", "cols": 6, "wrap": false}, "map": {}},
    "links": [{"from": "hud", "to": "pause", "input": "pause"}, {"from": "hud", "to": "map", "input": "map"},
              {"from": "pause", "via": "pause.menu.item[1]", "to": "inventory"}],
    "tasks": {"open-map": {"frequency": "high", "target": "map"},
              "change-volume": {"frequency": "low", "target": "audio.list.master-volume", "max_presses": 8}},
    "budgets": {},
    "graph": {"output": "docs/nav-graph.svg", "embed_in_handoff": false, "auto_update": true}
  },
  "motion": {"principles": [], "transitions": {}, "state_machines": {}, "feedback": []},
  "extra_tags": [],
  "rename_map": {"old.path": "new.path"},
  "overrides": {"hud.bottom-left.health-bar": "fill uses 6px height instead of 8px"},
  "changelog": ["2026-10-20 @bar.fill height 8px -> 6px"]
}
```

- Screen keys are full paths. A list uses one key with `[*]` (for example `inventory.grid.slot[*]`).
- A removed element keeps its key with `"status": "removed"`.
- `extra_tags` holds user-approved tag patterns (regex, without `#`).
- `motion` stays empty unless the user accepts Phase 5b.
- `brief.platforms` uses `console`, `handheld`, `pc`, `vr`, or `mobile`. The validator takes the strictest text floor (XAG 101) of the listed platforms, scaled to `reference_height`.
- `type_exceptions` lists type tokens that may stay below the floor, each with a reason. Use it rarely.
- `hud_screens` lists the screens that are gameplay HUD. Every `#p1`, `#p2`, or `#p3` element on them needs `visibility` (`hidden`, `peek`, `persistent`, or `expanded`) and, unless persistent, a `trigger`.
- `input_map.actions` lists game actions and their binding per glyph set. Every `@prompt` element names one action.
- `navigation` describes how screens connect, for the navigation cost check:
  - `screens`: per screen, `focus_order` (IDs in focus order), `default_focus` (first item if left out), `layout` (`list` or `grid` with `cols`), and `wrap`.
  - `links`: `via` (a menu item that is confirmed) or `input` (a direct button, an action from `input_map`). Tabs are `input` links on the bumper actions. Add `"presses": n` for an input that needs more than one press.
  - `tasks`: common player goals. `frequency` is `high` (many times per session), `medium`, or `low`. `target` is a screen or a focusable ID. Optional `max_presses` and `max_depth` set a budget for one task.
  - `budgets`: optional budgets per frequency set by the user, for example `{"high": {"presses": 2}}`.
  - Severity: over a default budget = WARN. Over a budget the user set (in `budgets` or on the task) = ERROR. A task with no path = ERROR.
  - Default budgets [heur]: high 3 presses and depth 1, medium 6 and 2, low 10 and 3. Cost = directional moves from the default focus + confirm per menu item + presses per direct button. Depth = links on the path.
  - `graph`: where the SVG goes and if it updates automatically. Empty until the user answers the offer in Phase 2.
- Show the registry to the user as tables or `tree` output, not as raw JSON, unless the user asks for JSON.

## Addressing system

Every element has an address. The user and Claude use addresses to select and change elements at any level. Apply this system from Phase 2 to the end.

### Layers

| Layer | Prefix | Contains | An edit here changes |
|---|---|---|---|
| L0 Tokens | `$` | colors, type, space, motion, shape values | every element that uses the token |
| L1 Components | `@` | reusable definitions (button, bar, slot, panel) | every instance of the component |
| L2 Screens | none | instances placed in screens | only the selected instances |

### Path IDs (tree)

- Format: `screen.region.element.part`, kebab-case, for example `hud.bottom-left.health-bar.fill`.
- Component parts use the same dot form: `@bar.fill`, `@button.label`.
- List items use an index: `inventory.grid.slot[3]`. Use `[*]` for all items, `[0-4]` for a range.
- Variants and states use a colon: `@button:primary`, `@button:focus`, `@button:primary:disabled`.
- Token paths: `$color.accent.primary`, `$type.size.body`, `$motion.duration.fast`.
- Transition IDs use `~`: `pause~open`, `pause~close`, `@button~focus`.
- IDs describe the role, not the look: `health-bar`, not `red-bar`. Then a style change does not break the ID.

### Tags (cross-branch groups)

- Format: `#tag`. One element can have many tags.
- Fixed tag set (extend only with user approval, through `extra_tags`):
  - Priority: `#p1`, `#p2`, `#p3` (from Phase 2).
  - Role: `#interactive`, `#readout`, `#label`, `#decor`, `#icon`, `#prompt`.
  - Semantic: `#danger`, `#warning`, `#success`, `#info`, `#rarity-common` to `#rarity-legendary`.
  - Platform: `#gamepad-only`, `#mouse-only`, `#touch-only`.
  - Localization: `#loc` for all translated text.

### Selectors

| Selector | Selects |
|---|---|
| `hud.bottom-left.health-bar` | one element |
| `hud.bottom-left.*` | direct children |
| `hud.**` | all descendants |
| `#p1` | every element with the tag, on every screen |
| `hud.** #interactive` | tagged elements inside a branch |
| `@button` | the component definition (all instances) |
| `@button in pause.**` | instances of the component inside a branch |
| `$color.accent.*` | a token group |
| `pause~open` | one transition |

### Edit commands

- Format: `<selector>: <change>`. One command per line. Examples:
  - `$type.size.body: 30px`
  - `@bar.fill: add a 2px inner stroke`
  - `hud.** #p3: opacity 60%, hide in combat`
  - `inventory.grid.slot[0]: show the new-item badge state`
  - `pause~open: stagger 20ms instead of 30ms`
- The inspector exports lines in this format. Treat pasted inspector output like typed commands.
- Natural language is also valid. Claude resolves it to a selector, shows the resolved selector, and the number of affected elements, before the edit.
- If the scope is not clear (one instance, the component, or the token), ask which layer. Recommend the highest layer that does not cause unwanted changes.
- An instance edit that differs from its component is an override. Record each override in the registry. If one component gets 3 or more similar overrides, propose a new variant instead.

### Commands for inspection

- `tree [selector]`: show the hierarchy under the selector, with tags and component of each element.
- `find <selector>`: list the matched addresses.
- `uses <$token or @component>`: list every element that depends on it.
- `overrides [selector]`: list instance overrides.
- `diff`: list changes since the last approved version.
- `validate`: run `validate_ui.py` on all mockups and report the result.
- `nav`: show the navigation task table (presses, depth, budget, path) and the steps of each task over budget.
- `graph`: draw or redraw the navigation graph SVG.

### ID stability

- Do not rename IDs silently. A rename goes into `rename_map` (`old -> new`), so old addresses in the conversation still resolve.
- Removed IDs stay in the registry with `"status": "removed"` and the reason in the change log.

### In the mockup files

- Every element carries `data-id` (full path), `data-tags`, and `data-component` attributes.
- All style values come from CSS variables named from the token paths (`$color.accent.primary` becomes `--color-accent-primary`). Hex values appear only inside `:root` blocks.
- Component styles live in one place per component, so an L1 edit changes every instance.
- Button prompts are `@prompt` components with `data-action="<action>"`. Never write "Press A" as plain text. The validator flags it.
- In HUD mockups, put the placeholder gameplay scene in one element with the `data-backdrop` attribute. HUD layers sit above it. The inspector uses it for the readability test.
- Inline `inspector.js` in a `<script>` at the end of `<body>`. Tell the user once: press the backquote key or the "Inspect" button, select elements, check or edit the selector in the Selector field, write the change, then "Copy edits" and paste the result in the chat. If the panel covers an element, click "Move panel". Use "Background" to check HUD text over bright, mid-gray, dark, and busy scenes. If the Japanese IME is on, the backquote key can fail. Then use the button.

## Phase 0: Read the request

1. Read what the user already gave: game, screens, references, constraints.
2. Mark each item of the Brief (Phase 1) as KNOWN, ASSUMED, or MISSING.
3. If the user attached screenshots or concept art, examine them first. Extract palette, shapes, and type mood from them.
4. If `ui-registry.json` exists for this project, load it and continue from it. If not, write the project files.

## Phase 1: Brief

Ask the user for MISSING items in one message (AskUserQuestion when available, max 4 questions per call). Do not ask for items the user already gave. For low-cost items, propose a default and say it is an assumption.

Brief fields:

- Game: genre, camera (FPS, TPS, top-down, side), session length, pacing (twitch vs. slow).
- Platforms: console (TV), handheld, PC, VR, or mobile. This sets the text size floor (pattern card 1).
- Input: gamepad, mouse and keyboard, touch, or a mix. Which glyph sets (Xbox, PlayStation, Switch, keyboard and mouse). If the game ships in Japan on PlayStation, which confirm button (pattern card 5).
- Target resolutions and aspect ratios (pattern card 7).
- Screens in scope: HUD, main menu, pause, inventory, map, dialogue, settings, shop, results, loading.
- Art direction: 3-5 mood words. Diegetic, spatial, meta, or non-diegetic UI.
- References: 3-5 games or works the user likes, and what they like in each (layout, motion, type, color).
- Anti-references: 1-3 things to avoid.
- Languages: list them. Japanese, Chinese, Korean, and German need extra width and line height.
- Accessibility needs: colorblind modes, text scaling, subtitles, reduced motion.
- Engine target: Unity uGUI, Unity UI Toolkit, UE5 UMG/CommonUI, or none.

Write the brief back to the user as a short table. Get confirmation before Phase 1b.

## Phase 1b: Reference research (offer)

When genre, camera, input, and mood words are KNOWN, offer the user these options. The user picks any, all, or none.

### Option A: References the user collects

The user picks the references. Claude does not scrape or bulk-search curated screenshot collections. Those collections are other people's work. The user browses them directly, which also gives the curators their visits.

1. Suggest what to look for: 4-6 shipped games with the same genre, camera, and input, plus at least one game outside the genre that solves the same problem (for example, a strategy game for a dense inventory). Give game names and the screens to look at. Do not choose by review score alone: a high score rates the whole game, not the UI.
2. Ask the user to send what they found, in any of these forms:
   - Screenshots attached to the chat. This is the best form: Claude can examine the image itself.
   - URLs of specific pages. Read only the pages the user gives. Do not follow links to other pages, and do not crawl the site. If a page is mostly images, its text says little. Ask the user to attach the screenshots instead.
   - A short note: the game, the screen, and what they like or dislike.
3. For each reference, write: the game and screen, one specific UI decision worth study, one weakness, and the source (the URL or "screenshot from user").
4. Claude may search for developer talks, postmortems, and press that explain a UI decision in the user's references, and cite them. These explain the reasons. They do not replace the user's own picks.
5. Keep the reference images in the conversation. Do not copy them into mockups, artifacts, or handoff files. Name the source of each reference in the reference log (Phase 7).

### Option B: Prompts for a specialized image model

Write 3-5 prompts that the user can paste into an image model (for example, Midjourney, Flux, or a similar model). Rules:

- Use generated images for mood only: material, light, color, shape language, frame and ornament style. Never use them for layout or information architecture. Layout comes from shipped games and Phase 2.
- Prompts describe materials, eras, crafts, and real-world objects (for example, "enamel instrument dials, brass bezels, worn paint"), not "game UI". The phrase "game UI" pulls the generic average.
- Do not name living artists, studios, or existing game titles in prompts.
- Make the prompts differ on purpose: each one explores a different mood word or material.
- Tell the user to bring back 2-3 images they like. Then extract palette, shape, and texture cues into Phase 3, with the source image named.

### Option C: Skip

If the user skips, continue with the references that they gave. Say once that weak references give generic results.

## Phase 2: Information architecture

For each screen in scope:

0. Once per project, before the screens: list the 5-15 most common player tasks across the game (for example, open map, equip weapon, check quest, change volume) with a frequency. Ask the user to confirm the frequencies, and ask if they want their own budgets. Write them to `navigation.tasks` and `navigation.budgets`.
1. List the player tasks on this screen (for example, "compare two weapons", "see ammo while aiming").
2. List every data item and control.
3. Rank each item: P1 (must see at a glance), P2 (must find in under 2 s), P3 (on request). For menus with detail views, map P1-P3 to the glance, focus, and inspect layers, with the input for each layer (pattern card 4).
4. For HUD screens, give every ranked item a visibility state and a trigger (pattern card 3). "Persistent" needs a reason. Plan the special modes: cinematic, photo, and aim.
5. Define the navigation: entry, exit, back behavior, gamepad focus order, tab or page structure (pattern card 6).
6. Define the input map: the actions on this screen, the same action on the same button on every screen, and hold-to-confirm for destructive actions (pattern card 5).
7. Define states: empty, loading, error, full, locked, new-item badge.
8. Give every item its path ID and tags. Write the screen tree, visibility, and input map into the registry.
9. If the screen has a widget with a pattern card (notifications, cooldowns, radial menu, combat numbers, minimap, diegetic UI), read that card and record the decisions it lists.
10. Write the screen into `navigation`: focus order, default focus, layout, wrap, and its links.

When all screens are in `navigation`, run the validator and show the `nav` table. For a task over budget, propose a fix: a direct button, a quick menu or radial, a different default focus, or moving the item up the list. Do not hide a WARN. Ask the user to accept it or fix it.

Then offer the navigation graph once, in one question:
- Where to put it: a file path the user names (default `docs/nav-graph.svg`), embedded in the handoff document, or both.
- Keep it updated automatically when the structure changes, or only on request.

Write the answers to `navigation.graph`. Run `python3 nav_graph.py ui-registry.json <output>` and send the file. If the user declines, leave `navigation.graph` empty and do not offer again unless the user asks.

When screens, links, focus orders, default focus, or tasks change at any later phase:
- If `navigation.graph.auto_update` is true, run the validator, redraw the graph, send it, and say so in one line.
- If it is false, say in one line that the graph is out of date and offer to redraw it.

Show this as the `tree` output or a wireframe in boxes. No color, no style. A grey-box wireframe with `data-id` attributes and the inspector is a good way to let the user point at items. Compare the structure with the Option A references when available. Get confirmation before Phase 3. Most bad game UI fails here. Push back if the user wants to skip it.

## Phase 3: Design system (tokens and components)

Make one token set (L0). Every later screen uses only these tokens. Give each token its `$` path and write it into the registry.

- Color: background layers (2-3), surface, primary accent, secondary accent, text (high/medium/low), states (danger, warning, success, info), rarity tiers if the game has loot. Give hex values. Give contrast ratios of text on surface: 4.5:1 for standard text, 3:1 for large text (pattern card 1).
- Type: max two families. Name real, licensable fonts (Google Fonts or SIL OFL preferred), with a CJK font if Japanese is in scope. Type scale with 5-7 steps in px at the reference resolution. No step is below the XAG 101 floor for the brief platforms (console 26 px, PC 18 px at 1080p; pattern card 1) unless it is in `type_exceptions`. Plan text scaling to 200%.
- Space: a base unit (4 or 8 px) and a scale. Safe-area margins (5% each side for TV; pattern card 7).
- Text over gameplay: the outline, shadow, or panel treatment for HUD text (pattern card 2).
- Shape language: corner style, stroke weight, cut corners, frames, dividers. Tie each to the mood words.
- Iconography style: stroke vs. fill, grid size, corner treatment.
- Motion: durations (fast/normal/slow in ms), easing curves as cubic-bezier values, what animates on focus, open, close, and value change.
- Interaction states: normal, hover, focus (gamepad), pressed, selected, disabled. Focus must be visible without a mouse.
- Audio cue map (optional): which events need a sound.

Then define the components (L1) that Phase 2 needs. Give each one its `@` ID, parts, variants, states, and the tokens it uses.

State for each token decision which reference, mood image, or mood word it comes from. A token without a reason is a default. Replace it or justify it.

## Phase 4: Directions

1. Pick one key screen (usually the HUD or the main menu).
2. Make 2-3 mockups of it that differ in a real way: layout strategy, density, or diegesis. Do not make three color swaps of one layout.
3. Name each direction and give one line on the trade-off.
4. The user picks one, or mixes. Update the tokens and components to match.

## Phase 5: Build the screens

For each screen in scope:

1. Build the mockup at the reference resolution (1920x1080 unless the brief says otherwise). Use realistic data: real-length item names, large numbers (99999), long Japanese strings, and the worst case of each list.
2. Show at least one non-default state (focus, empty, or error) per screen.
3. Use only tokens and components from the registry. If a new token or component is necessary, add it to the registry first.
4. Use placeholder shapes for art assets and icons that need an artist. Label them. Do not fake detailed illustration.
5. Put the `data-id`, `data-tags`, and `data-component` attributes on every element. Inline `inspector.js`.
6. Run `python3 validate_ui.py ui-registry.json <mockups>`. Fix every ERROR. Fix every WARN or explain it. Deliver only when the result shows 0 errors.

After delivery, the user edits with selectors, natural language, or pasted inspector output (see Edit commands). After each edit round: update the registry, add a change log line, run the validator again.

When the static layout of a screen is approved, offer Phase 5b in one line. Do not start it without a yes.

## Phase 5b: Motion (optional)

Do this phase only when the user accepts it. Do it only on screens with an approved static layout. Motion work on an unapproved layout is wasted.

0. Read pattern card 9 (notifications) before the feedback map.
1. **Principles.** Write 3-5 motion rules, each tied to a mood word or reference. For example, "heavy machinery" gives mechanical steps, hard stops, no overshoot. A rule without a source is a default. Replace it or justify it.
2. **Feedback map.** List the game events that need UI motion (damage, pickup, level up, low health, quest update). Give each a priority (critical, high, normal, low), the queue behavior, and the merge rule for repeats. Low-priority events get small or no motion. This prevents "everything animates".
3. **Transitions.** For each screen transition, write a choreography spec with addresses and tokens:
   - Trigger and ID (`pause~open`).
   - Order and timing: which addresses move first, the stagger, the duration token, the easing token.
   - What moves: opacity, position, scale, clip, color. Name the property.
   - Interrupt rule: what happens if the player presses Back or another input mid-transition. Input must never wait for an animation to end.
   - Reduced-motion version: usually opacity only or instant.
4. **State machines.** For each interactive component, list states, transitions between them, trigger, duration token, and easing token (`@button~focus`, `@slot~select`).
5. **Prototype.** Animate the mockup with CSS transitions or the Web Animations API. Rules:
   - Durations use `calc(var(--motion-duration-normal) / var(--motion-slow, 1))`, so the inspector speed control works.
   - Respect `[data-reduced-motion]` on the root element.
   - Define `window.uiiReplay = (ids) => { ... }`. With an empty list, it replays all transitions on the screen. With IDs, it replays the transitions of those elements.
   - The inspector gives speed control (1x to 0.1x), a reduced-motion toggle, and a replay button.
6. Write principles, transitions, state machines, and feedback map into `motion` in the registry. Run the validator.

Tell the user once: the prototype shows intent and timing, not final engine behavior. CSS easing, frame timing, and layout differ from UMG, DOTween, and UI Toolkit.

## Phase 6: Critique

Score every screen against this rubric before you show it. For each fail, fix it, then score again. Show the final scores to the user. Name failing elements by their address.

| # | Check | Pass condition |
|---|---|---|
| 1 | Hierarchy | `#p1` items read first in a 1 s squint test. |
| 2 | Readability | Text meets the XAG 101 floor for the brief platforms. Contrast 4.5:1 (3:1 for large text). HUD text stays readable with the inspector Background set to bright, mid-gray, dark, and busy. |
| 3 | Gameplay occlusion | HUD keeps the center and the action area clear. Every HUD element has a visibility state, and "persistent" elements have a reason. |
| 4 | Gamepad | Every `#interactive` element is reachable. Focus is visible without color. The controller walkthroughs in pattern card 6 that apply to this game complete without a mouse. Prompts use `@prompt` and the input map. One action, one button, on every screen. |
| 5 | Safe area | No text or interactive item outside the 90% title-safe area. The resolution test set in pattern card 7 does not break the layout (include 1280×800 and 21:9). |
| 6 | Localization | `#loc` strings at +40% length do not overflow. CJK text fits line height. |
| 7 | States | Empty, loading, error, disabled states exist. |
| 8 | Consistency | `validate_ui.py` shows 0 errors. Overrides are few and recorded. |
| 9 | Identity | The screen does not look like a generic template or a copy of one reference. Name the specific choice that ties it to this game. |
| 10 | Accessibility | Color is never the only signal (add icon, shape, or text). |
| 11 | Navigation cost | Every task in `navigation.tasks` is reachable. No task is over a user-set budget. Every task over a default budget is fixed or accepted by the user, with the reason in the change log. |

If Phase 5b was done, also score:

| # | Check | Pass condition |
|---|---|---|
| M1 | Responsiveness | Input is accepted during every transition. No menu blocks input for animation. |
| M2 | Purpose | Each animation has a feedback-map entry or a transition spec. No decorative motion on `#p1` readouts during gameplay. |
| M3 | Consistency | One meaning uses one easing and duration token on every screen. |
| M4 | Reduced motion | Every transition has a reduced-motion version. |
| M5 | Identity | The motion is not the default fade or slide at one duration. Name the specific choice that ties it to the principles. |

Check 9 and M5 are the anti-slop checks. If the honest answer is "it looks like any sci-fi game" or "it looks like reference X", go back to Phase 3 shape language or Phase 5b principles.

The validator checks structure (IDs, tags, components, tokens), the text floor, long motion tokens, focus styles, hard-coded prompts, `@prompt` actions, HUD visibility, and navigation cost. The other checks need your own review of the rendered screen.

## Phase 7: Handoff spec

Deliver with the mockups:

- `ui-registry.json`, plus a readable table version.
- Token table in copy-ready form: CSS variables plus a JSON block.
- Per screen: layout grid, anchors (for engine UI: anchor and pivot per element), focus order, transitions in and out.
- Asset list: icons and art needed, size, format, 9-slice notes.
- Input map: actions, bindings per glyph set, hold-to-confirm actions.
- Navigation: the task table and the navigation graph SVG (in the file and, if the user chose it, embedded in the handoff document).
- Engine notes for the target engine: map path IDs to widget names (for example, UMG widget tree or UI Toolkit UXML names and USS classes, with tags as USS classes), and which parts need custom code.
- If Phase 5b was done: timing tables per transition, easing as cubic-bezier values, state machines, and engine mapping notes (UMG animation tracks, DOTween sequences, or USS transitions).
- Reference log: which reference (game and screen, with its source) or mood image each major decision came from.
- Open questions and assumptions.

## Rules for the whole process

- Never use a default dark-glass, cyan-glow, rounded-card look unless the brief asks for it.
- Never use emoji as icons.
- Never invent data that hides layout problems (short names, small numbers).
- Do not reproduce UI, logos, or characters from existing games. Use references for principles only.
- If the user says "skip to mockups", warn once about the cost, then make the assumptions explicit and continue.
- Keep each phase output short. The user approves each phase before the next one.

## Credits

Parts of `references/patterns.md` are adapted from the `game-ui-design` skill by omer-metin (Apache 2.0, github.com/omer-metin/skills-for-antigravity). The text is rewritten, and the numbers are checked against the sources named in the file.
