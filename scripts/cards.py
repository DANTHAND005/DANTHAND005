"""Render the profile cards (ident, activity, projects) as dark/light SVGs and refresh the README repo table.

    GITHUB_TOKEN=... python scripts/cards.py          # live data (what the workflow runs)
    python scripts/cards.py --preview preview.json    # offline: day counts + repos from a JSON file
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from html import escape

USER = "DANTHAND005"
PROFILE = {
    "handle": "daniel@danthand005",
    "title": "SOFTWARE ENGINEER / AI ENGINEER",
    "focus": "Multi-Agent AI · LLM Apps · Full-Stack · Mobile",
    "rows": [
        ("EDUCATION", ["B.S. AI-Enabled Software Engineering", "Northern Kentucky University · May 2027"]),
        ("STACK", ["Python · JavaScript · Java · SQL · Dart", "React · FastAPI · Node · Flutter · Supabase"]),
        ("AI", ["Claude Code · MCP · Ollama · LiteLLM", "Gemini API · PyTorch · Reinforcement Learning"]),
        ("WINS", ["4th Place · NKU Hackathon", "DQN research presented to 500+ people"]),
    ],
}
PROJECTS = [  # (name, tagline, stack, status, url or "")
    ("Night City Office", "Claude lead + 5 local LLMs, applies work via MCP", "Python · FastAPI · Ollama", "ACTIVE", ""),
    ("Norse Whiteboard", "AI study whiteboard · 4th place hackathon", "React · Supabase · Gemini", "LIVE",
     "https://github.com/DANTHAND005/Hackathon-Norse-Whiteboard"),
    ("Step Quest", "Steps → coins → friend leaderboards", "FastAPI · Flutter · 35 tests", "SHIPPED",
     "https://github.com/DANTHAND005/step-quest"),
    ("ClassKeeper", "Student planner with Canvas import", "React · Express · MongoDB", "SHIPPED",
     "https://github.com/DANTHAND005/classkeeper"),
]
THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", line="#30363d", text="#c9d1d9", dim="#8b949e", acc="#ff9d42",
                 cells=["#161b22", "#4a2a0c", "#8a4a12", "#cc6f1c", "#ff9d42"]),
    "light": dict(bg="#ffffff", panel="#f6f8fa", line="#d0d7de", text="#1f2328", dim="#656d76", acc="#c2410c",
                  cells=["#ebedf0", "#fed7aa", "#fdba74", "#f97316", "#c2410c"]),
}
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
W = 900


def fetch_live(token):
    q = """query($u:String!){user(login:$u){
      contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}
      repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER,orderBy:{field:PUSHED_AT,direction:DESC}){
        nodes{name url description pushedAt primaryLanguage{name}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token}"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    days = {d["date"]: d["contributionCount"]
            for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]}
    repos = [dict(name=r["name"], url=r["url"], desc=r["description"] or "", pushed=r["pushedAt"][:10],
                  lang=(r["primaryLanguage"] or {}).get("name", "")) for r in u["repositories"]["nodes"]]
    return days, repos


def frame(t, h, label, body):
    c = t["acc"]
    corners = "".join(f'<path d="{d}" stroke="{c}" stroke-width="2" fill="none"/>' for d in (
        "M4 16V4h12", f"M{W-16} 4h12v12", f"M4 {h-16}v12h12", f"M{W-16} {h-4}h12v-12"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
            f'font-family="{FONT}"><rect width="{W}" height="{h}" rx="6" fill="{t["bg"]}"/>{corners}{body}'
            f'<text x="{W-24}" y="{h-10}" text-anchor="end" font-size="9" letter-spacing="1.5" fill="{t["dim"]}">'
            f'DT / {label}</text></svg>')


def txt(x, y, s, fill, size=13, weight="normal", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{escape(s)}</text>')


def portrait(t, x, y, size, path="assets/avatar.jpg", n=80):
    """Halftone dot portrait: one dot per cell, radius from brightness (dark theme) or darkness (light theme)."""
    if not os.path.exists(path):
        return ""
    from PIL import Image, ImageOps  # only needed when a photo is present
    img = ImageOps.autocontrast(ImageOps.fit(Image.open(path).convert("L"), (n, n)), cutoff=2)
    step = size / n
    dots = []
    for j in range(n):
        for i in range(n):
            v = img.getpixel((i, j)) / 255
            v = v if t is THEMES["dark"] else 1 - v
            d = ((i - n / 2) ** 2 + (j - n / 2) ** 2) ** .5 / (n / 2)  # fade dots outside the HUD circle
            v *= max(0.0, min(1.0, (1.0 - d) / 0.12))
            r = step * 0.5 * v ** 1.3
            if r > 0.25:
                dots.append(f'<circle cx="{x+(i+.5)*step:.1f}" cy="{y+(j+.5)*step:.1f}" r="{r:.2f}"/>')
    c, cx, cy = t["acc"], x + size / 2, y + size / 2
    hud = (f'<circle cx="{cx}" cy="{cy}" r="{size/2-6}" fill="none" stroke="{c}" stroke-opacity=".5" stroke-dasharray="2 6"/>'
           f'<rect x="{x+8}" y="{y+8}" width="22" height="16" fill="none" stroke="{c}"/>'
           f'<text x="{x+12}" y="{y+20}" font-size="9" fill="{c}">&gt;_</text>'
           + "".join(f'<rect x="{x+size-12}" y="{y+40+k*14}" width="4" height="4" fill="{c}"/>' for k in range(4)))
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="6" fill="{t["panel"]}"/>'
            f'<g fill="{t["text"]}">{"".join(dots)}</g>{hud}')


def ident(t):
    pic = portrait(t, 28, 60, 260)
    x0 = 316 if pic else 40
    b = [f'<circle cx="{28+i*14}" cy="24" r="4" fill="{t["acc"]}"/>' for i in range(3)]
    b += [pic, txt(72, 28, f"{USER.lower()}@github: ~/profile", t["dim"], 12),
          f'<line x1="20" y1="42" x2="{W-20}" y2="42" stroke="{t["line"]}"/>',
          txt(x0, 78, PROFILE["handle"], t["acc"], 16, "bold"),
          f'<rect x="{x0+len(PROFILE["handle"])*9.8+6}" y="64" width="8" height="16" fill="{t["acc"]}">'
          '<animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></rect>',
          f'<line x1="{x0}" y1="90" x2="{x0+340}" y2="90" stroke="{t["acc"]}"/>',
          txt(x0, 112, PROFILE["title"], t["acc"], 14), txt(x0, 130, PROFILE["focus"], t["dim"], 12)]
    y = 160
    for i, (head, lines) in enumerate(PROFILE["rows"]):
        if pic:  # one column beside the portrait
            b.append(txt(x0, y, head, t["acc"], 12, "bold"))
            b += [txt(x0, y + 16 * (j + 1), ln, t["text"], 12) for j, ln in enumerate(lines)]
            y += 50
            continue
        x, yy = (40, y) if i % 2 == 0 else (470, y)
        b.append(txt(x, yy, head, t["acc"], 12, "bold"))
        b += [txt(x, yy + 18 * (j + 1), ln, t["text"], 12) for j, ln in enumerate(lines)]
        if i % 2:
            y += 72
    return frame(t, max(y + 20, 350 if pic else 0), "00 · IDENT", "".join(b))


def activity(t, days):
    today = max(days) if days else dt.date.today().isoformat()
    end = dt.date.fromisoformat(today)
    start = end - dt.timedelta(days=end.weekday() + 1 + 52 * 7)  # back to a Sunday, 53 columns
    span = lambda n: sum(days.get((end - dt.timedelta(i)).isoformat(), 0) for i in range(n))
    streak = 0
    while days.get((end - dt.timedelta(streak)).isoformat(), 0):
        streak += 1
    stats = [(span(1), "Today"), (span(7), "Last 7 Days"), (span(30), "Last 30 Days"),
             (span(365), "Last Year"), (f"{streak}d", "Current Streak")]
    b = []
    for i, (v, label) in enumerate(stats):
        x = 28 + i * 172
        b += [f'<rect x="{x}" y="28" width="3" height="40" fill="{t["acc"]}"/>',
              txt(x + 14, 52, str(v), t["text"], 22), txt(x + 14, 68, label, t["dim"], 11)]
    top = max(days.values() or [1]) or 1
    cell, gap, gx, gy = 13, 3, 28, 104
    b.append(txt(W - 28, 96, "CONTRIBUTION TERRAIN", t["text"], 11, "bold", "end"))
    month = None
    for col in range(53):
        for row in range(7):
            d = start + dt.timedelta(col * 7 + row)
            if d > end:
                continue
            n = days.get(d.isoformat(), 0)
            lvl = 0 if n == 0 else min(4, 1 + int(3 * n / top))
            b.append(f'<rect x="{gx+col*(cell+gap)}" y="{gy+row*(cell+gap)}" width="{cell}" height="{cell}" '
                     f'rx="2" fill="{t["cells"][lvl]}"><title>{d}: {n}</title></rect>')
        first = start + dt.timedelta(col * 7)
        if first.month != month:
            month = first.month
            b.append(txt(gx + col * (cell + gap), gy + 7 * (cell + gap) + 14, first.strftime("%b"), t["dim"], 10))
    return frame(t, 262, "01 · ACTIVITY · 53 WK", "".join(b))


def projects(t):
    b = [txt(28, 40, "FEATURED PROJECTS", t["acc"], 18, "bold"),
         txt(28, 58, "WHAT GETS BUILT HERE", t["dim"], 10),
         f'<line x1="28" y1="70" x2="{W-28}" y2="70" stroke="{t["line"]}"/>']
    pw = (W - 56 - 3 * 16) / 4
    for i, (name, tag, stack, status, _) in enumerate(PROJECTS):
        x = 28 + i * (pw + 16)
        live = status in ("LIVE", "ACTIVE")
        b += [f'<rect x="{x}" y="86" width="{pw}" height="150" rx="4" fill="{t["panel"]}" '
              f'stroke="{t["acc"] if live else t["line"]}"/>',
              f'<rect x="{x+12}" y="100" width="8" height="8" fill="{t["acc"] if live else t["dim"]}"/>',
              txt(x + 26, 108, status, t["acc"] if live else t["dim"], 10),
              txt(x + 12, 136, name, t["text"], 14, "bold")]
        words, line, ly = tag.split(), "", 158
        for w in words:  # wrap the tagline to the panel width
            if len(line) + len(w) > 26:
                b.append(txt(x + 12, ly, line, t["dim"], 11)); line, ly = "", ly + 15
            line = f"{line} {w}".strip()
        b += [txt(x + 12, ly, line, t["dim"], 11), txt(x + 12, 222, stack, t["acc"], 10)]
    return frame(t, 268, "02 · PROJECTS", "".join(b))


# Only these public repos are listed, in this order; private ones appear once made public.
FEATURED = ["Hackathon-Norse-Whiteboard", "step-quest", "AI-Snake-Game", "christmas-addon", "classkeeper"]


def readme_table(repos):
    by_name = {r["name"]: r for r in repos}
    rows = [f"| [{r['name']}]({r['url']}) | {r['lang'] or '—'} | {r['pushed']} | {r['desc'].replace('|', '/')} |"
            for r in (by_name[n] for n in FEATURED if n in by_name)]
    return "\n".join(["| REPO | LANG | LAST PUSH | NOTE |", "|---|---|---|---|", *rows])


def main():
    if "--preview" in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index("--preview") + 1]))
        days, repos = data["days"], data["repos"]
    else:
        days, repos = fetch_live(os.environ["GITHUB_TOKEN"])
    for mode, t in THEMES.items():
        for name, svg in (("ident", ident(t)), ("activity", activity(t, days)), ("projects", projects(t))):
            open(f"{name}_{mode}.svg", "w").write(svg)
    readme = open("README.md").read()
    readme = re.sub(r"(<!-- repos:start -->).*?(<!-- repos:end -->)",
                    lambda m: m.group(1) + "\n" + readme_table(repos) + "\n" + m.group(2), readme, flags=re.S)
    open("README.md", "w").write(readme)


if __name__ == "__main__":
    main()
