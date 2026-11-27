import datetime as dt, json, os, sys, urllib.request
from svgkit import *

USER = os.environ.get("PROFILE_USER", "VeqtaDev")
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def gql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]["user"]


def fetch():
    cal = gql(f'{{user(login:"{USER}"){{contributionsCollection{{contributionCalendar{{totalContributions '
              'weeks{contributionDays{date contributionCount contributionLevel}}}}}}')["contributionsCollection"]["contributionCalendar"]
    first = dt.date.fromisoformat(cal["weeks"][0]["contributionDays"][0]["date"])
    frm, to = first.replace(year=first.year - 1), first - dt.timedelta(days=1)
    prev = gql(f'{{user(login:"{USER}"){{contributionsCollection(from:"{frm}T00:00:00Z",to:"{to}T23:59:59Z")'
               '{contributionCalendar{totalContributions}}}}')["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    return cal, prev


def pct(a, b):
    if not b:
        return None
    return round((a - b) * 100 / b)


def metrics(cal, prev):
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    last = dt.date.fromisoformat(days[-1]["date"])
    cur, i = 0, len(days) - 1
    if counts[i] == 0:
        i -= 1
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    best_run = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best_run = max(best_run, run)
    best = max(days, key=lambda d: d["contributionCount"])
    active = sum(1 for c in counts if c)
    pm = (last.replace(day=1) - dt.timedelta(days=1))
    month = sum(d["contributionCount"] for d in days if d["date"][:7] == last.isoformat()[:7])
    month_prev = sum(d["contributionCount"] for d in days if d["date"][:7] == pm.isoformat()[:7])
    return {
        "total": cal["totalContributions"], "total_pct": pct(cal["totalContributions"], prev),
        "month": month, "month_pct": pct(month, month_prev * last.day / ((last.replace(day=1) - dt.timedelta(days=1)).day)) if month_prev else None,
        "streak": cur, "best_streak": best_run,
        "active": active, "days": len(days),
        "best": best["contributionCount"], "best_date": dt.date.fromisoformat(best["date"]),
        "avg": cal["totalContributions"] / max(active, 1),
        "first": dt.date.fromisoformat(days[0]["date"]), "last": last,
    }


def kpi(m):
    W, H = 1200, 256
    tw = (1180 - 32) / 3
    def ptag(p, fallback):
        if p is None or p < 0 or p > 999:
            return fallback, "v"
        return f"+{p}%", "g"
    tiles = [
        ("CONTRIBUTIONS", f"{m['total']:,}", ptag(m["total_pct"], "12 MONTHS"), None),
        ("THIS MONTH", f"{m['month']:,}", ptag(m["month_pct"], m["last"].strftime("%b").upper()), None),
        ("CURRENT STREAK", f"{m['streak']}", ("DAYS", "v"), ("bar", m["streak"] / max(m["best_streak"], 1), f"BEST {m['best_streak']}")),
        ("CONSISTENCY", f"{round(m['active']*100/m['days'])}%", ("ACTIVE", "g"), ("gauge", m["active"] / m["days"])),
        ("BEST DAY", f"{m['best']:,}", (m["best_date"].strftime("%b %d").upper(), "v"), None),
        ("DAILY AVERAGE", f"{m['avg']:.1f}", ("PER ACTIVE DAY", "v"), None),
    ]
    b = []
    for i, (lab, val, tg, widget) in enumerate(tiles):
        x, y = 10 + (i % 3) * (tw + 16), 10 + (i // 3) * 112
        g = [tile(x, y, tw, 96)]
        g.append(T("bold", lab, 13, x + 22, y + 32, LABEL, 0.6)[0])
        vd, vw = T("black", val, 30, x + 22, y + 74, LABEL)
        g.append(vd)
        if tg:
            g.append(tag(tg[0], x + 22 + vw + 10, y + 54, tg[1])[0])
        if widget and widget[0] == "gauge":
            g.append(gauge(x + tw - 92, y + 80, 40, widget[1], .5 + i * .08))
        if widget and widget[0] == "bar":
            g.append(bar(x + tw - 172, y + 62, 146, widget[1], .5 + i * .08))
            g.append(T("bold", widget[2], 10.5, x + tw - 26, y + 52, DIM, 0.6, "end")[0])
        b.append(f'<g class="up" style="animation-delay:{i*.07}s">{"".join(g)}</g>')
    return svg(W, H, "".join(b), style=GAUGE_CSS,
               label=f"{m['total']:,} contributions in the last year, current streak {m['streak']} days")


def activity(cal, m):
    W, H = 1200, 334
    x, y, w, h = 10, 10, 1180, 288
    b = [tile(x, y, w, h, 16, False)]
    b.append(T("bold", "ACTIVITY TRACKER", 13, x + 22, y + 34, LABEL, 0.6)[0])
    b.append(T("med", "Consistency beats intensity.", 13, x + 22, y + 56, MUTED)[0])
    lab = "LAST 12 MONTHS"
    lw = measure("bold", lab, 12, 0.6) + 28
    kx = x + w - 22 - 26 - 10 - lw - 10 - 26
    b.append(f'<circle cx="{kx+13}" cy="{y+38}" r="13" fill="url(#key)" filter="url(#sh)"/>'
             + P(f"M{kx+16} {y+33}l-5 5 5 5", fill="none", stroke=LABEL, stroke_width="2", stroke_linecap="round", stroke_linejoin="round"))
    k2 = kx + 36
    b.append(f'<rect x="{k2}" y="{y+25}" width="{num(lw)}" height="26" rx="7" fill="url(#key)" filter="url(#sh)"/>'
             f'<rect x="{k2+.5}" y="{y+25.5}" width="{num(lw-1)}" height="25" rx="6.5" fill="none" stroke="url(#edge)"/>'
             + T("bold", lab, 12, k2 + 14, y + 42.5, LABEL, 0.6)[0])
    k3 = k2 + lw + 10
    b.append(f'<circle cx="{num(k3+13)}" cy="{y+38}" r="13" fill="#1C1E22" stroke="#000" stroke-opacity=".4"/>'
             + P(f"M{num(k3+11)} {y+33}l5 5-5 5", fill="none", stroke=DIM, stroke_width="2", stroke_linecap="round", stroke_linejoin="round"))

    gx, gy, pitch, cs = x + 64, y + 104, 20, 16
    prev_month = None
    cols = []
    for ci, wk in enumerate(cal["weeks"]):
        d0 = dt.date.fromisoformat(wk["contributionDays"][0]["date"])
        if d0.month != prev_month and ci < len(cal["weeks"]) - 2:
            prev_month = d0.month
            mx = gx + ci * pitch
            b.append(f'<rect x="{mx}" y="{gy-30}" width="34" height="16" rx="4" fill="#26282D" stroke="#000" stroke-opacity=".35"/>'
                     + T("bold", MONTHS[d0.month - 1], 9.5, mx + 17, gy - 18.5, MUTED, 0.6, "middle")[0])
        cells = []
        for day in wk["contributionDays"]:
            wd = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
            lv = LEVEL[day["contributionLevel"]]
            cx_, cy_ = gx + ci * pitch, gy + wd * pitch
            cells.append(f'<rect x="{cx_}" y="{cy_}" width="{cs}" height="{cs}" rx="3.5" fill="url(#lv{lv})"'
                         + (' stroke="#000" stroke-opacity=".35"/>' if lv == 0 else "/>"))
            if lv >= 3:
                cells.append(f'<rect x="{cx_+2}" y="{cy_+1.5}" width="{cs-4}" height="3" rx="1.5" fill="#fff" opacity=".28"/>')
            if day["date"] == m["last"].isoformat():
                cells.append(f'<rect class="pulse" x="{cx_-2.5}" y="{cy_-2.5}" width="{cs+5}" height="{cs+5}" rx="5" fill="none" stroke="{V1}" stroke-width="1.5"/>')
        cols.append(f'<g class="up" style="animation-delay:{.2+ci*.015:.3f}s">{"".join(cells)}</g>')
    b += cols
    for wd, letter in ((1, "M"), (3, "W"), (5, "F")):
        b.append(T("bold", letter, 10, x + 34, gy + wd * pitch + 12, DIM, 0, "middle")[0])
    sweep_w = 7 * pitch
    b.append(f'<rect x="{gx}" y="{gy-4}" width="40" height="{sweep_w+4}" rx="6" fill="url(#sweep)" opacity="0">'
             f'<animate attributeName="x" values="{gx-40};{gx + len(cal["weeks"])*pitch}" dur="5s" begin="2.2s;sw.end+3s" id="sw"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.9;1" dur="5s" begin="2.2s;sw.end+3s"/></rect>')
    fy = y + h - 20
    b.append(T("med", f"{m['first'].strftime('%b %d, %Y')}  -  {m['last'].strftime('%b %d, %Y')}  ·  {m['total']:,} contributions",
               12, gx, fy, DIM, 0.2)[0])
    lx = x + w - 22
    lt, ltw = T("med", "More", 12, lx, fy, DIM, anchor="end")
    b.append(lt)
    lx -= ltw + 8
    for lv in range(4, -1, -1):
        lx -= 14
        b.append(f'<rect x="{lx}" y="{fy-10}" width="12" height="12" rx="3" fill="url(#lv{lv})"/>')
        lx -= 4
    b.append(T("med", "Less", 12, lx - 4, fy, DIM, anchor="end")[0])
    defs = ('<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{V1}" stop-opacity="0"/><stop offset=".5" stop-color="{V1}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{V1}" stop-opacity="0"/></linearGradient>')
    return svg(W, H, f'<g class="up">{b[0]}</g>' + "".join(b[1:]), defs,
               label=f"Activity tracker: {m['total']:,} contributions in the last 12 months")


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    cal, prev = fetch()
    m = metrics(cal, prev)
    for name, content in (("kpi.svg", kpi(m)), ("activity.svg", activity(cal, m))):
        open(os.path.join(out, name), "w", encoding="utf-8").write(content)
        print(f"{name:14} {len(content)/1024:6.1f} KB")
