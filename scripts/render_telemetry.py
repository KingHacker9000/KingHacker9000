#!/usr/bin/env python3
import collections
import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path

USER = "KingHacker9000"
OUT = Path("assets/lab-telemetry.svg")


def fetch_repos():
    token = os.environ.get("GITHUB_TOKEN", "")
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=updated&type=owner"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-telemetry"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=20) as response:
            batch = json.load(response)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def esc(value):
    return html.escape(str(value), quote=True)


def render(repos):
    now = dt.datetime.now(dt.timezone.utc)
    active_30 = sum(1 for r in repos if dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) >= now - dt.timedelta(days=30))
    recent = sorted(repos, key=lambda r: r.get("pushed_at") or "", reverse=True)[:5]
    langs = collections.Counter(r.get("language") for r in repos if r.get("language"))
    top_langs = langs.most_common(6)

    recent_rows = []
    for i, repo in enumerate(recent):
        y = 195 + i * 34
        pushed = dt.datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
        age = max(0, (now - pushed).days)
        age_label = "today" if age == 0 else f"{age}d ago"
        lang = repo.get("language") or "—"
        recent_rows.append(
            f'<text x="68" y="{y}" class="mono ink repo">{esc(repo["name"])}</text>'
            f'<text x="410" y="{y}" text-anchor="end" class="mono muted tiny">{esc(lang)} · {age_label}</text>'
        )

    lang_rows = []
    max_count = max([count for _, count in top_langs] or [1])
    for i, (lang, count) in enumerate(top_langs):
        y = 194 + i * 35
        width = int(250 * count / max_count)
        lang_rows.append(
            f'<text x="650" y="{y}" class="mono ink tiny">{esc(lang)}</text>'
            f'<rect x="760" y="{y-11}" width="{width}" height="7" rx="3.5" fill="#16140F" opacity=".72"/>'
            f'<circle cx="{760+width}" cy="{y-7.5}" r="5" fill="#E0491F"/>'
        )

    generated = now.strftime("%Y-%m-%d UTC")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 430" role="img" aria-labelledby="title desc">
<title id="title">Ashish Ajin lab telemetry</title>
<desc id="desc">Automatically refreshed snapshot of Ashish Ajin's public GitHub repository activity and primary repository languages.</desc>
<rect width="1200" height="430" rx="24" fill="#15130F"/>
<style>.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.sans{{font-family:Arial,Helvetica,sans-serif}}.ink{{fill:#EDE9E0}}.muted{{fill:#A19C8F}}.dim{{fill:#6F6A60}}.tiny{{font-size:12px;letter-spacing:1px}}.repo{{font-size:15px;font-weight:700}}</style>
<path d="M48 72H1152M48 344H1152M520 104V324" stroke="#EDE9E0" stroke-opacity=".13"/>
<text x="48" y="48" class="mono ink tiny" letter-spacing="2.5">ASHISH / LAB TELEMETRY</text>
<text x="1152" y="48" text-anchor="end" class="mono muted tiny">AUTO-REFRESH · {generated}</text>

<text x="48" y="115" class="mono muted tiny">PUBLIC SOURCE REPOS</text>
<text x="48" y="154" class="sans ink" font-size="38" font-weight="700">{len(repos):02d}</text>
<text x="225" y="115" class="mono muted tiny">PUSHED / 30D</text>
<text x="225" y="154" class="sans ink" font-size="38" font-weight="700">{active_30:02d}</text>
<circle cx="425" cy="137" r="9" fill="#F5F2EB" stroke="#E0491F" stroke-width="3"/><circle cx="425" cy="137" r="3" fill="#E0491F"/>

<text x="48" y="190" class="mono dim tiny" letter-spacing="1.6">RECENT SIGNAL</text>
{''.join(recent_rows)}

<text x="625" y="115" class="mono muted tiny" letter-spacing="1.6">PRIMARY LANGUAGE SIGNAL / REPOSITORIES</text>
{''.join(lang_rows)}

<text x="48" y="380" class="mono muted tiny">NOT A SCORECARD — JUST A SMALL WINDOW INTO WHAT IS MOVING.</text>
<text x="1152" y="380" text-anchor="end" class="mono dim tiny">SOURCE → GITHUB API</text>
</svg>'''


def main():
    repos = fetch_repos()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(repos), encoding="utf-8")
    print(f"wrote {OUT} from {len(repos)} public source repositories")


if __name__ == "__main__":
    main()
