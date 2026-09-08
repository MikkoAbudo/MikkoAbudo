#!/usr/bin/env python3
"""Render shell-style profile SVGs with a blinking block cursor (snowf14k3-style)."""
from __future__ import annotations

import html
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = int((ROOT / ".profile" / "boot_epoch").read_text().strip())
BLOCK = (ROOT / ".profile" / "fastfetch_block.txt").read_text()

THEMES = {
    "light": {
        "bg": "#ffffff",
        "text": "#24292f",
        "muted": "#57606a",
        "green": "#1a7f37",
        "blue": "#0969da",
        "cyan": "#0550ae",
        "red": "#cf222e",
        "arch": "#0969da",
    },
    "dark": {
        "bg": "#0d1117",
        "text": "#c9d1d9",
        "muted": "#8b949e",
        "green": "#3fb950",
        "blue": "#58a6ff",
        "cyan": "#79c0ff",
        "red": "#f85149",
        "arch": "#58a6ff",
    },
}


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


def prompt_lines(theme: dict, command: str, y: float, show_cursor: bool = False) -> str:
    """zsh/bash box prompt: ┌─[user@host]─[~] / └─$"""
    user = "kleelovelife"
    host = "KleeLoveLife-PC"
    # line 1
    t1 = (
        f'<text x="18" y="{y:.1f}" class="body">'
        f'<tspan fill="{theme["muted"]}">┌─[</tspan>'
        f'<tspan fill="{theme["green"]}">{html.escape(user)}</tspan>'
        f'<tspan fill="{theme["muted"]}">@</tspan>'
        f'<tspan fill="{theme["green"]}">{html.escape(host)}</tspan>'
        f'<tspan fill="{theme["muted"]}">]─[</tspan>'
        f'<tspan fill="{theme["blue"]}">~</tspan>'
        f'<tspan fill="{theme["muted"]}">]</tspan>'
        f"</text>"
    )
    # line 2
    cursor = (
        f'<tspan fill="{theme["text"]}" class="cursor">█</tspan>' if show_cursor else ""
    )
    cmd = html.escape(command)
    t2 = (
        f'<text x="18" y="{y + 18:.1f}" class="body">'
        f'<tspan fill="{theme["muted"]}">└─</tspan>'
        f'<tspan fill="{theme["text"]}">$ {cmd}</tspan>'
        f"{cursor}"
        f"</text>"
    )
    return t1 + "\n  " + t2


def colorize_fastfetch_line(line: str, theme: dict) -> str:
    """Arch logo in blue-ish; keys muted separation kept as plain monospace."""
    # Split logo (first 35 chars padded area) from info — logo width is 35 in template
    # Detect by looking for double-space gap near Arch art end, or fixed cut.
    # Our logo block is left-justified to max logo width; find "  " after logo region.
    # Safer: logo is always the Arch art; info starts around column where Title starts.
    # Use: if line has "  " and right side looks like key:value or title
    esc = html.escape(line)
    # Highlight Arch art with arch color for whole line left portion when it's mostly art
    # Simple approach: entire preformatted line in text color; logo columns in arch color
    # Find split at two spaces followed by non-space that looks like info
    import re

    m = re.match(r"^(.*?)(  )(\S.*)?$", line)
    if not m or m.group(3) is None:
        return f'<tspan fill="{theme["arch"]}">{esc}</tspan>'
    left, mid, right = m.group(1), m.group(2), m.group(3)
    # Color key:value
    if ": " in right:
        key, val = right.split(": ", 1)
        right_xml = (
            f'<tspan fill="{theme["text"]}">{html.escape(key)}: </tspan>'
            f'<tspan fill="{theme["muted"]}">{html.escape(val)}</tspan>'
        )
    elif right.startswith("---"):
        right_xml = f'<tspan fill="{theme["muted"]}">{html.escape(right)}</tspan>'
    elif "@" in right and " " not in right.strip():
        # title user@host
        u, _, h = right.partition("@")
        right_xml = (
            f'<tspan fill="{theme["green"]}">{html.escape(u)}</tspan>'
            f'<tspan fill="{theme["text"]}">@</tspan>'
            f'<tspan fill="{theme["green"]}">{html.escape(h)}</tspan>'
        )
    else:
        right_xml = f'<tspan fill="{theme["text"]}">{html.escape(right)}</tspan>'
    return (
        f'<tspan fill="{theme["arch"]}">{html.escape(left)}</tspan>'
        f'<tspan>{html.escape(mid)}</tspan>'
        f"{right_xml}"
    )


def render_svg(mode: str) -> str:
    theme = THEMES[mode]
    uptime = format_uptime(int(time.time()) - BOOT)
    fetch_text = BLOCK.replace("{{UPTIME}}", uptime)
    fetch_lines = fetch_text.rstrip("\n").split("\n")

    line_h = 18.0
    y = 28.0
    parts: list[str] = []

    parts.append(prompt_lines(theme, "fastfetch", y))
    y += 18 * 2 + 6

    for line in fetch_lines:
        content = colorize_fastfetch_line(line, theme)
        parts.append(f'<text x="18" y="{y:.1f}" class="mono">{content}</text>')
        y += line_h

    y += 10
    parts.append(prompt_lines(theme, "pacman -Syu", y))
    y += 18 * 2
    parts.append(
        f'<text x="18" y="{y:.1f}" class="mono">'
        f'<tspan fill="{theme["red"]}">bash: pacman: command not found</tspan>'
        f"</text>"
    )
    y += line_h + 10
    parts.append(prompt_lines(theme, "xdg-open https://zqat.asia", y))
    y += 18 * 2 + 8
    # idle prompt with blinking cursor — the snowf14k3 trick
    parts.append(prompt_lines(theme, "", y, show_cursor=True))
    y += 18 * 2 + 16

    height = int(y)
    width = 920

    body = "\n  ".join(parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">MikkoAbudo shell profile ({mode})</title>
  <desc id="desc">Arch logo on Debian — shell session with a blinking cursor.</desc>
  <style>
    .body {{ font-family: ui-monospace, "Cascadia Mono", "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace; font-size: 14px; font-variant-ligatures: none; }}
    .mono {{ font-family: ui-monospace, "Cascadia Mono", "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace; font-size: 13px; font-variant-ligatures: none; white-space: pre; }}
    .cursor {{ animation: blink 1.1s step-end infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
  </style>
  <rect width="100%" height="100%" fill="{theme["bg"]}"/>
  {body}
</svg>
'''


def main() -> None:
    out = ROOT / "assets"
    out.mkdir(parents=True, exist_ok=True)
    for mode in ("light", "dark"):
        path = out / f"profile-{mode}.svg"
        path.write_text(render_svg(mode), encoding="utf8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
