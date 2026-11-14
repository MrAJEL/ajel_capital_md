"""Example automation: daily summary of the repo's ideas and apps.

- Standard library only, no secrets, no network.
- Reads ideas/*.md (the "Estado" field) and lists apps/*/ folders.
- Prints Markdown to stdout and, when running in GitHub Actions, also appends it to
  $GITHUB_STEP_SUMMARY so it shows up on the run page (visible from the GitHub mobile app).

Run locally:  python3 automatizaciones/ejemplo_resumen_diario.py [--saludo "Hola"]
"""
from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_RE = re.compile(r"\*\*Estado:\*\*\s*(.+)")


def idea_states() -> list[tuple[str, str]]:
    ideas = []
    for path in sorted((ROOT / "ideas").glob("*.md")):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        match = STATE_RE.search(path.read_text(encoding="utf-8"))
        ideas.append((path.stem, match.group(1).strip() if match else "sin estado"))
    return ideas


def apps() -> list[str]:
    return sorted(
        p.name for p in (ROOT / "apps").iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "index.html").exists()
    ) if (ROOT / "apps").exists() else []


def build_summary(greeting: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ideas = idea_states()
    counts = Counter(state for _, state in ideas)
    lines = [f"## {greeting} — resumen {now}", "", f"**Ideas:** {len(ideas)}"]
    lines += [f"- {state}: {n}" for state, n in counts.most_common()]
    app_list = apps()
    lines += ["", f"**Apps PWA:** {len(app_list)}"]
    lines += [f"- {name}" for name in app_list] or ["- (ninguna todavía)"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saludo", default="Buenos días")
    args = parser.parse_args()

    summary = build_summary(args.saludo)
    print(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(summary)


if __name__ == "__main__":
    main()
