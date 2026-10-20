# game-gui-design

A Claude skill for game UI design. It makes mockups and a handoff spec through a fixed process:

1. Brief
2. References
3. Information architecture
4. Design system
5. Directions
6. Screens
7. Critique
8. Handoff

Motion is an optional phase.

The process is there to stop one-prompt, generic output. Every element has an address, every value comes from a token, and a validator checks the result before delivery.

> **Status: beta (0.x).** Nobody has tested it on a real project yet. Expect changes.

## What you get

- **A phased process.** The skill asks before it builds, and it waits for your approval after each phase.
- **An addressing system.** Tokens (`$`), components (`@`), screen paths (`hud.bottom-left.health-bar`), tags (`#p1`), and transitions (`pause~open`). You can change any level with one line: `@bar.fill: thinner`.
- **An inspector inside each mockup.** You can:
  - pick elements visually
  - see and edit the selector
  - write changes and copy them as edit commands
  - test readability over bright, mid-gray, dark, and busy backgrounds
  - preview motion at slow speed and with reduced motion
- **A validator** (`validate_ui.py`). It checks:
  - registry and mockup consistency
  - the text size floor from Xbox Accessibility Guidelines 101
  - focus styles
  - hard-coded "Press A" prompts
  - HUD visibility states
  - navigation cost: gamepad presses and menu depth from gameplay to each common task
- **A navigation graph** (`nav_graph.py`): an SVG of the screen graph, with task paths and their budget status.
- **Pattern cards** (`references/patterns.md`). Each number is marked as a published standard [std] or a starting point [heur].

## Install

### claude.ai

1. Download `game-gui-design-v<version>.zip` from [Releases](../../releases).
2. In Claude, go to **Customize > Skills**, click **+**, then **Create skill > Upload a skill**, and upload the ZIP.
3. Turn on code execution in your settings. The skill runs Python scripts.

To update, upload the new ZIP.

### Claude Code

```bash
claude plugin marketplace add RoyalNoob/game-gui-design
claude plugin install game-gui@game-gui-tools
```

In a session, run the skill with `/game-gui:game-gui-design`, or ask for a game UI and let Claude pick the skill.

### Other agents

The skill follows the open [Agent Skills](https://agentskills.io) format. Copy `plugins/game-gui/skills/game-gui-design/` into the skills folder of your agent.

## Use

Start a new chat and ask for a game UI. For example:

> Design the HUD and pause menu for a slow-paced exploration game, played with a gamepad on a TV.

Tips:

- **References.** Attach screenshots of games you like. Claude cannot see the images on most web pages, only their text.
- **Common tasks.** In Phase 2, the skill asks for your most common player tasks and their frequency. The navigation check is only as good as these answers.
- **Inspector.** In a mockup, press the backquote key or click **Inspect**. Select elements, check the **Selector**, write a change, click **Copy edits**, and paste the result into the chat.
- **Panel position.** If the panel covers an element, click **Move panel**.

See the [inspector walkthrough](docs/inspector.md) for a step-by-step guide with screenshots.

## Repository layout

```
.claude-plugin/marketplace.json        Claude Code marketplace (this repo)
plugins/game-gui/
  .claude-plugin/plugin.json           plugin name and version
  skills/game-gui-design/              the skill (this folder is the claude.ai ZIP)
    SKILL.md
    scripts/validate_ui.py             validator and navigation analysis
    scripts/nav_graph.py               navigation graph SVG
    scripts/inspector.js               mockup inspector
    references/patterns.md             pattern cards
tests/validator/                       fixtures and run.sh
tests/browser/                         Playwright tests for the inspector
tools/build_zip.sh                     builds dist/game-gui-design-v<version>.zip
tools/changelog_section.py             release notes from CHANGELOG.md
.github/workflows/                     CI and release
docs/inspector.md                      inspector walkthrough (user manual)
docs/                                  design notes and session history
```

## Develop

Run all tests before you commit:

```bash
bash tests/validator/run.sh

cd tests/browser
npm install
npx playwright install chromium
npm test
```

Edit the skill only in `plugins/game-gui/skills/game-gui-design/`. Do not edit a copy in your claude.ai account. Upload a new ZIP instead.

## Release

1. Change `version` in `plugins/game-gui/.claude-plugin/plugin.json`.
2. Add a section for the version to `CHANGELOG.md`.
3. Commit, then tag and push:

   ```bash
   git tag v0.3.2
   git push origin main --tags
   ```

The release workflow:

1. checks that the tag matches `plugin.json`
2. runs the validator tests
3. builds the ZIP
4. creates a GitHub Release with the changelog section as notes

Versions 0.x are marked as pre-releases.

## Credits

Parts of `references/patterns.md` are adapted from the `game-ui-design` skill by omer-metin (Apache 2.0), [skills-for-antigravity](https://github.com/omer-metin/skills-for-antigravity). See `NOTICE`.

## License

MIT. See `LICENSE`. The adapted parts of `references/patterns.md` keep their Apache 2.0 attribution in `NOTICE`.
