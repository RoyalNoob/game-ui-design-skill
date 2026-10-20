# Game UI pattern cards

Read only the cards that apply to the current screen. Each card gives the decisions to make and a starting point for each one.

Status of the numbers:

- **[std]** comes from a published guideline. The source is given.
- **[heur]** is a common industry starting point with no single source. Treat it as a default to justify or change. Do not treat it as a rule.

Parts of these cards are adapted from the `game-ui-design` skill by omer-metin (Apache 2.0), github.com/omer-metin/skills-for-antigravity. The text is rewritten, and the numbers are checked against the sources named here.

---

## 1. Text size and readability

Minimum default body text height (descender to ascender) at launch [std, Xbox Accessibility Guidelines 101]:

| Platform | At 1080p | At 4K |
|---|---|---|
| Console (TV) | 26 px | 52 px |
| PC / VR | 18 px | 36 px |
| Mobile / streaming | 18 px at 100 DPI, 36 px at 200 DPI, 72 px at 400 DPI | — |

- Players must be able to scale text up to 200% of these sizes [std, XAG 101].
- Handheld PCs (Steam Deck and similar) are not in XAG 101. Use the console row until you have a reason to change it [heur].
- Critical HUD numbers (health, ammo) are larger than body text [heur].
- Avoid thin and light font weights for HUD text [heur].
- Contrast [std, XAG 102]: 4.5:1 for standard text and visual elements. 3:1 for large text and disabled elements. 7:1 for all UI when a high-contrast mode is on.

Sources: devdocs.xbox.com/build/game-principles/accessibility/xag-deep-dives/xag-101-text-display and xag-102-contrast

## 2. Text over gameplay

Gameplay backgrounds change every frame. HUD text that is readable on one frame can be lost on the next.

- Every HUD text element over gameplay has one of: an outline (about 2 px, contrasting), a sharp drop shadow, or a semi-transparent panel behind it. The combination is the safest [heur].
- Test against four backgrounds: bright (sky), dark (night), mid-gray (worst for both light and dark text), and busy high-contrast noise (particles, foliage). The inspector "Background" control does this.

## 3. HUD visibility states

Decide for every HUD element when it is on screen. "Always visible" is a decision that needs a reason.

| State | Meaning |
|---|---|
| hidden | Not shown in normal play. Shown only on request or in a special mode. |
| peek | Appears on a trigger, then fades out. |
| persistent | Always shown during gameplay. |
| expanded | Extra detail while the player holds a button or opens it. |

- Give each non-persistent element a trigger. Example: health bar is hidden at full health, peeks on damage, fades out after about 4 s at full health again.
- Starting timings [heur]: critical info appears in 0 ms. Standard elements fade in over about 150 ms. Fade out slower (about 500 ms), so it does not feel sudden. Wait about 2 s before auto-hide.
- Plan the special modes: cinematic (all hidden), photo mode (all hidden), aim mode (center clear).
- Question for every element: "Does the player need this right now?" If not, hide it or put it one button away.

## 4. Progressive disclosure

Layer information from glance to full detail.

| Layer | Content | Gamepad | Mouse | Touch |
|---|---|---|---|---|
| Glance | Name, icon, one key stat | always | always | always |
| Focus | Main stats, short description | on focus | on hover, after about 300 ms [heur] | tap |
| Inspect | Full comparison, lore, upgrades | press or hold a button | button or click | long press |

Map the layers to Phase 2 priorities: P1 is glance, P2 is focus, P3 is inspect.

## 5. Input actions and prompts

- Name actions, not buttons: `confirm`, `back`, `tab-next`, `tab-prev`, `inspect`, `drop`.
- Keep one input map for the whole game. The same action uses the same button on every screen.
- Prompts show the binding of the device in use, after rebinding. Switch glyph sets on the first input from another device. A short delay (about 200 ms) stops flicker when two devices are used together [heur].
- Glyph sets: Xbox (also the default for a generic gamepad), PlayStation, Nintendo Switch, keyboard and mouse, touch.
- Button positions differ: Nintendo A/B and X/Y are mirrored from Xbox.
- PlayStation confirm button in Japan: PS5 changed the system default to Cross for confirm in 2020. Many PS4-era Japanese games used Circle. Offer a setting when the game ships in Japan [std, Sony system change; reported by Kotaku, 2020].
- Destructive actions (delete save, sell rare item, quit without save) need a hold or a confirm dialog. They never sit on the same button as a common action next to them.
- New players read "Press [A] to open" more easily than "[A] Open" [heur].

## 6. Controller navigation

- Every interactive element can get focus. The focus indicator is visible without color: border, glow, or scale, on every background.
- The directional pad moves focus in a predictable grid. Decide on wrap behavior per list.
- Every screen has a back path. Bumpers switch tabs.
- Menus remember the last focused element when the player returns.
- Modal dialogs take focus and give it back when they close.
- Walkthroughs to check, with a controller only:
  - Main menu > Options > every submenu > Back to main menu
  - Gameplay > Pause > every item > Resume
  - Inventory > every slot > Equip > Exit
  - Shop > Browse > Buy > Exit
  - Dialogue > every choice > Advance

Navigation cost (reaching a feature is not enough; reaching it fast matters):

- Count gamepad presses from gameplay: directional moves from the default focus, plus confirm, plus direct buttons. Count depth as the number of screens entered.
- Default budgets [heur]: high-frequency tasks 3 presses and depth 1. Medium 6 and 2. Low 10 and 3.
- Fixes for an expensive task, cheapest first: put the most used item first in the list, give it a direct button, add a quick menu or radial, or make the screen remember the last focus.
- The check uses the first visit (default focus). A screen that remembers the last focus is cheaper on later visits.
- Mouse cost depends on distance and target size, which this model does not count. For PC-first games, also check mouse travel by eye.

## 7. Safe area and resolutions

- Title safe: keep all static HUD, all text, and all interactive elements inside 90% of the screen (5% margin each side) [heur, broadcast convention].
- Action safe: moving elements can reach 93% of the screen [heur].
- Offer a safe-area or HUD-margin setting for TV play.
- Test set:
  - 1280×720 (Switch handheld)
  - 1280×800 (Steam Deck, 16:10)
  - 1920×1080 (reference)
  - 2560×1440
  - 3840×2160 (4K TV)
  - 2560×1080 and 3440×1440 (21:9 ultrawide)
- Ultrawide: decide if the HUD sticks to the screen edges or to a 16:9 center area. Edges far from the center are hard to read during play.

## 8. Touch targets

- Minimum target: 44×44 pt [std, Apple HIG] or 48×48 dp [std, Material Design].
- The touch area can be larger than the visible icon.
- About 8 px between targets [heur].
- Check one-handed use in portrait mode.

## 9. Notification queue

Use this card in the Phase 5b feedback map.

| Priority | Example | Behavior |
|---|---|---|
| critical | low health | Shown at once. Skips the queue. |
| high | quest complete | Next in the queue. |
| normal | achievement | Waits its turn. |
| low | material collected | Merged into batches. |

Starting values [heur]:

- Maximum 2–3 notifications visible at once.
- Entry about 200 ms. Display 3–5 s, depending on length. Exit about 300 ms. Gap about 500 ms.
- Merge repeats of the same type: "Gold +50" and "Gold +30" become "Gold +80". Show "x5" for repeated items.
- Keep a notification log, so the player never loses important information.

## 10. Cooldowns

Design all states: on cooldown (dimmed, sweep), almost ready (small pulse), ready (full brightness, optional sound), active, disabled (not only gray: add a mark).

- A sweep or fill shows progress at a glance. A number overlay shows exact time. Use both for important abilities [heur].

## 11. Radial menus

- Gamepad: 8 segments is a comfortable number. More than 12 is hard to use. Use nested rings for more [heur].
- Choose the interaction: hold and release, toggle and confirm, or flick.
- Put favorite or frequent items in fixed, easy positions.
- Single-player only: optional slow motion while the menu is open.

## 12. Damage and combat numbers

- Show the type with more than color: size, weight, icon, or motion (critical, elemental, heal, blocked).
- Merge fast hits into a running total. Keep at most about 5–6 numbers visible [heur].
- Combat numbers obey the reduced-motion setting.

## 13. Minimaps and navigation aids

- Decide the shape and position (circle, rectangle, or compass bar). The top-right corner is common.
- Order of visual importance: player, objectives, threats, allies, points of interest, terrain.
- Let the player choose north-up or player-up rotation.
- Plan zoom, behavior in vehicles or at speed, and fog of war.

## 14. Diegetic UI

Diegetic UI is UI that exists in the game world, for example a display on the character's suit.

- Good for immersion. Bad for fast competitive play, for information the player checks often, and for stat-heavy games.
- It must stay readable from every camera angle the game uses.
- It needs a non-diegetic fallback for accessibility.
