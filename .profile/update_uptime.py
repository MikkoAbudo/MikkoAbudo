#!/usr/bin/env python3
"""Rewrite the Uptime: line in README.md from boot_epoch."""
from __future__ import annotations

import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = int((ROOT / ".profile" / "boot_epoch").read_text().strip())
README = ROOT / "README.md"


def format_uptime(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{mins} min{'s' if mins != 1 else ''}")
    return ", ".join(parts)


def main() -> None:
    uptime = format_uptime(int(time.time()) - BOOT)
    text = README.read_text()
    new, n = re.subn(
        r"(Uptime: )[^\n]*",
        rf"\g<1>{uptime}",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"expected 1 Uptime line, found {n}")
    if new != text:
        README.write_text(new)
        print(f"updated -> {uptime}")
    else:
        print(f"unchanged -> {uptime}")


if __name__ == "__main__":
    main()
