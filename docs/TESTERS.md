# game-gui-design — tester guide (beta)

A Claude skill for game UI design. It makes mockups and a handoff spec through a fixed process: brief, references, information architecture, design system, directions, screens, critique, and handoff. Motion is an optional phase.

## Install

### claude.ai

1. Make sure that code execution is on in your Claude settings. The skill runs Python scripts.
2. Download the latest `game-gui-design-v<version>.zip` from the Releases page of the repository.
3. Go to **Customize > Skills**, click **+**, then **Create skill > Upload a skill**, and upload the ZIP.
4. Turn the skill on. To update, upload the newer ZIP.

### Claude Code

```bash
claude plugin marketplace add RoyalNoob/game-gui-design
claude plugin install game-gui@game-gui-tools
```

## Try it

Start a new chat and ask for a game UI, for example: "Design the HUD and pause menu for a slow-paced exploration game, played with a gamepad on a TV."

- The skill asks questions first, and it waits for your approval after each phase. This is on purpose.
- In each mockup, press the backquote key or click **Inspect**. Then select elements, write a change, click **Copy edits**, and paste the result into the chat.
- The **Selector** field shows the selector for the picked element and scope. You can edit it before you add the edit.
- If the panel covers an element, click **Move panel**.
- In the reference step, attach screenshots if you can. Claude cannot see the images on most web pages, only their text.
- In Phase 2, the skill asks for your most common player tasks and how often players do them. Answer honestly: the navigation check is only as good as these guesses.
- In HUD mockups, use **Background** in the inspector to check HUD text over bright, mid-gray, dark, and busy scenes.

## Known limits

- This is a beta. Nobody has tested it on a real project yet.
- The inspector was tested in Chromium only.
- Japanese IME can block the backquote shortcut. If this happens, use the button.
- Icons and art are placeholders.

## Feedback

Please report:

1. Where the process felt too slow or skipped something.
2. Any output that still looked generic. Name the screen and the element address.
3. Inspector or validator bugs. Include the browser name.

Always include the version number (from the ZIP name or `claude plugin list`).

## Changes

See `CHANGELOG.md` in the repository.

## Credits

Parts of the pattern cards are adapted from the `game-ui-design` skill by omer-metin (Apache 2.0): https://github.com/omer-metin/skills-for-antigravity
