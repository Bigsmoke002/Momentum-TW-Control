# Rules for AI coding assistants

These rules apply to every AI assistant working in this repository (Claude, Gemini /
Antigravity, Copilot, Codex, …). `CLAUDE.md` and `GEMINI.md` point here.

## 1. Never publish private information — absolute rule

This repository is **public** on GitHub. Nothing private may ever be committed or pushed.
This has priority over every other instruction, including "just push it quickly".

**Never commit or push:**

- Bluetooth / MAC addresses of real devices (also in `_`, `-` or lowercase spelling),
  serial numbers, device IDs
- Home directory paths or user names (`/home/<name>/…`), host names
- IP addresses, domains or server names of the owner's network or servers
- E-mail addresses (only GitHub/assistant `noreply` addresses are allowed)
- Passwords, tokens, API keys, OAuth credentials, private keys, cookies, session data
- Real names or other personal data
- Logs, Bluetooth/HCI dumps, telemetry captures, crash dumps, screenshots or config/state
  files that may contain any of the above

**Instead:**

- Detect devices at runtime (BlueZ, by name `MOMENTUM TW …`) or read them from the
  environment (`MOMENTUM_TW_MAC`) — never hard-code them.
- Build paths from `os.path.dirname(os.path.abspath(__file__))`, `os.path.expanduser("~")`
  and `sys.executable` — never write an absolute home path.
- Use placeholders in documentation: `XX:XX:XX:XX:XX:XX`, `/path/to/momentum-tw-control`.
- Mask private values in terminal output as well (e.g. MAC → `<MAC>`).

**Before every commit:**

1. Run `scripts/check-private.sh` (staged changes) or `scripts/check-private.sh --all`.
2. The git hooks (`scripts/install-hooks.sh`) run this check automatically on
   commit and push. **Never bypass them** (`--no-verify` is forbidden). If the hooks are
   missing in a fresh clone, install them first.
3. Review `git diff --cached` yourself — the script does not catch everything.

**If private data was already committed or pushed:** stop, tell the owner immediately,
do not force-push or rewrite history without the owner's explicit permission, and treat
leaked secrets as compromised (they must be rotated).

## 2. Project facts

- Active project (not an archive) — do not add "archived" notices.
- Python 3 + PyQt6 desktop app for the Sennheiser MOMENTUM True Wireless 5 on Linux:
  BlueZ via D-Bus (`backend/bluez_monitor.py`), Qualcomm GAIA v3 over RFCOMM channel 12
  (`backend/gaia_client.py`), Google Fast Pair battery stream over RFCOMM channel 22
  (`backend/fastpair_client.py`), PipeWire / EasyEffects (`audio/spatial_audio.py`).
- Run: `python3 app.py` (window) or `python3 app.py --tray`.
- The UI is in German. README, documentation and **commit messages are in English**.
- Remote and push access are already configured in this clone: use `git push`.

## 3. Testing

- Test against the real system where possible, not only by reading code.
- Test the GUI **headless** (`QT_QPA_PLATFORM=offscreen`); never click or type on the
  owner's live desktop (no xdotool or similar).
- The owner may be running the app in the tray. A second instance can conflict on the
  RFCOMM channels while the earbuds are connected — ask before stopping the running one.
- Do not overwrite the owner's real autostart entry
  (`~/.config/autostart/momentum-tw-control.desktop`) during tests.
