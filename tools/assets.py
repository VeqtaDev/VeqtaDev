import os, sys
from svgkit import *


def chip(label, x, y, h=26, size=11.5):
    d, w = text("bold", label, size, x + 14, y + h / 2 + size * 0.36, 0.8)
    W = w + 28
    return (
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(W)}" height="{h}" rx="7" fill="url(#key)" filter="url(#sh)"/>'
        f'<rect x="{num(x+.5)}" y="{num(y+.5)}" width="{num(W-1)}" height="{h-1}" rx="6.5" fill="none" stroke="url(#edge)"/>'
        + P(d, fill=V1)
    ), W


def minikey(label, x, y, h=44):
    d, w = text("bold", label, 14, x + 34, y + 25, 0.3)
    W = w + 50
    return (
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(W)}" height="{h}" rx="10" fill="url(#key)" filter="url(#sh)"/>'
        f'<rect x="{num(x+.5)}" y="{num(y+.5)}" width="{num(W-1)}" height="{h-1}" rx="9.5" fill="none" stroke="url(#edge)"/>'
        f'<rect x="{num(x+5)}" y="{num(y+4)}" width="{num(W-10)}" height="{h-12}" rx="7" fill="#fff" opacity=".04"/>'
        f'<circle cx="{num(x+20)}" cy="{num(y+20)}" r="5" fill="url(#vio)"/>'
        f'<circle cx="{num(x+18.5)}" cy="{num(y+18.5)}" r="1.6" fill="#fff" opacity=".8"/>'
        + P(d, fill=LABEL)
    ), W


def hero():
    W, H = 1200, 430
    b = []
    x = 10
    g = []
    g.append(f'<circle class="pulse" cx="{x+20}" cy="33" r="3.5" fill="{V2}"/>')
    g.append(T("mono", "ONLINE", 11, x + 31, 37, V1, 1)[0])
    sx = x + 31 + measure("mono", "ONLINE", 11, 1) + 14
    g.append(f'<rect x="{num(sx)}" y="22" width="1" height="22" fill="{DIM}"/>')
    g.append(img("avatar.webp", sx + 14, 21, 24, 24))
    g.append(f'<circle cx="{num(sx+26)}" cy="33" r="12" fill="none" stroke="#fff" stroke-opacity=".18"/>')
    nx = sx + 48
    t, tw = T("bold", "VeqtaDev", 14, nx, 38, LABEL)
    g.append(t)
    tg, tgw = tag("FULL STACK", nx + tw + 10, 23, "v")
    g.append(tg)
    ex = nx + tw + 10 + tgw + 12
    g.append(P(f"M{num(ex+4)} 28l4-4 4 4M{num(ex+4)} 38l4 4 4-4", fill="none", stroke=MUTED, stroke_width="1.5", stroke_linecap="round", stroke_linejoin="round"))
    b.append(f'<g class="up">{tile(x, 10, ex + 22 - x, 46, 10, False)}{"".join(g)}</g>')

    rx = 1190
    for i, (k, v) in enumerate([("FR", "UTC+1"), ("Discord", "veqtaaa")]):
        vw = measure("bold", v, 13)
        kw = measure("med", k, 13)
        w = kw + vw + 62
        x0 = rx - w
        inner = T("med", k, 13, x0 + 16, 38, MUTED)[0] + T("bold", v, 13, x0 + 16 + kw + 12, 38, V1 if k == "Discord" else LABEL)[0]
        if k == "Discord":
            inner += f'<rect x="{num(x0+w-24)}" y="27" width="8" height="9" rx="2" fill="none" stroke="{MUTED}" stroke-width="1.3"/><rect x="{num(x0+w-21)}" y="30" width="8" height="9" rx="2" fill="#1F2125" stroke="{MUTED}" stroke-width="1.3"/>'
        else:
            inner += f'<circle cx="{num(x0+w-20)}" cy="33" r="5" fill="none" stroke="{MUTED}" stroke-width="1.3"/><path d="M{num(x0+w-25)} 33h10M{num(x0+w-20)} 28c-2.5 3-2.5 7 0 10M{num(x0+w-20)} 28c2.5 3 2.5 7 0 10" fill="none" stroke="{MUTED}" stroke-width="1.1"/>'
        b.append(f'<g class="up" style="animation-delay:{.08*(i+1)}s">{tile(x0, 10, w, 46, 10, False)}{inner}</g>')
        rx = x0 - 12

    note = (f'<rect x="12" y="74" width="2.5" height="12" rx="1" fill="{DIM}"/>'
            + T("med", "Only a few repositories are public. Most of the work ships from private ones.", 11.5, 22, 84.5, DIM, 0.1)[0])
    b.append(f'<g class="up" style="animation-delay:.2s">{note}</g>')

    hx, hy, hw, hh = 10, 104, 1180, 280
    h = [tile(hx, hy, hw, hh, 18, False)]
    h.append(f'<g clip-path="url(#heroclip)"><ellipse cx="930" cy="250" rx="280" ry="160" fill="{V2}" opacity=".13" filter="url(#glowv)"/></g>')
    h.append(T("bold", "DEVELOPER PROFILE", 13, hx + 28, hy + 40, LABEL, 0.6)[0])
    h.append(tag("FR", hx + 28 + measure("bold", "DEVELOPER PROFILE", 13, 0.6) + 10, hy + 26, "v")[0])
    nd, nw = text("black", "VEQTA", 104, hx + 24, hy + 152, 3)
    h.append(P(nd, fill="url(#nameg)"))
    h.append(P(nd, fill="none", stroke="#fff", stroke_opacity=".08", transform="translate(0 -1.5)"))
    h.append(T("med", "Full-stack developer,", 22, hx + 28, hy + 194, LABEL, 0.2)[0])
    h.append(T("med", "specialised in front-end design.", 22, hx + 28, hy + 222, MUTED, 0.2)[0])
    cx = hx + 28
    for i, s in enumerate(["UI DESIGN", "DESIGN SYSTEMS", "MOTION", "REACT", "NEXT.JS"]):
        c, w = chip(s, cx, hy + 238)
        h.append(f'<g class="up" style="animation-delay:{.5+i*.06}s">{c}</g>')
        cx += w + 10
    b.append(f'<g class="up" style="animation-delay:.25s">{"".join(h)}</g>')
    b.append(f'<g class="up" style="animation-delay:.4s"><g class="drift">{img("cloud.webp", 600, 70, 430, opacity=".96")}</g></g>')
    b.append(f'<g class="up" style="animation-delay:.5s"><g class="float">{img("frame.webp", 846, 84, 296)}</g></g>')
    b.append(f'<g class="up" style="animation-delay:.75s"><g class="hover">{img("cursor.webp", 770, 262, 132)}</g></g>')
    defs = (f'<clipPath id="heroclip"><rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="18"/></clipPath>'
            '<linearGradient id="nameg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#FFFFFF"/><stop offset=".55" stop-color="{V1}"/><stop offset="1" stop-color="{V2}"/></linearGradient>')
    style = """
    .float{animation:float 7s ease-in-out infinite}
    @keyframes float{50%{transform:translateY(-6px)}}
    .drift{animation:drift 14s ease-in-out infinite}
    @keyframes drift{50%{transform:translateX(-22px)}}
    .hover{animation:hover 4.5s ease-in-out 1.5s infinite}
    @keyframes hover{0%,100%{transform:translate(0,0)}40%{transform:translate(14px,-12px)}55%{transform:translate(14px,-12px) scale(.96)}62%{transform:translate(14px,-12px)}}
    """
    return svg(W, H, "".join(b), defs, style, "Veqta - Full-stack developer, specialised in front-end design.")


def about():
    W, H = 1200, 214
    tiles = [
        ("FRONT-END", "React", "DESIGN", ["Pixel-precise interfaces,", "design systems, accessibility."]),
        ("FULL STACK", "Next.js", "END TO END", ["APIs, databases and deploys,", "shipped as one product."]),
        ("DESIGN", "Figma", "UI / UX", ["From wireframes to", "high-fidelity prototypes."]),
        ("MOTION", "Blender", "3D", ["Micro-interactions, motion", "and realistic 3D renders."]),
    ]
    tw = (1180 - 3 * 16) / 4
    b = []
    for i, (lab, val, tg, desc) in enumerate(tiles):
        x, y = 10 + i * (tw + 16), 10
        g = [tile(x, y, tw, 168)]
        g.append(T("bold", lab, 13, x + 22, y + 34, LABEL, 0.6)[0])
        vd, vw = T("black", val, 30, x + 22, y + 84, LABEL)
        g.append(vd)
        g.append(tag(tg, x + 22 + vw + 10, y + 64, "v")[0])
        for j, line in enumerate(desc):
            g.append(T("med", line, 13.5, x + 22, y + 120 + j * 21, MUTED, 0.1)[0])
        b.append(f'<g class="up" style="animation-delay:{.08*i}s">{"".join(g)}</g>')
    return svg(W, H, "".join(b), label="Front-end: React. Full stack: Next.js. Design: Figma. Motion: Blender.")


def stack():
    W, H = 1200, 166
    b = [tile(10, 10, 1180, 120)]
    b.append(T("bold", "STACK", 13, 32, 44, LABEL, 0.6)[0])
    b.append(T("med", "Daily drivers", 13, 32 + measure("bold", "STACK", 13, 0.6) + 12, 44, MUTED)[0])
    items = ["TypeScript", "React", "Next.js", "Tailwind", "Node.js", "Prisma", "PostgreSQL", "Figma", "Blender", "Vercel"]
    widths = [measure("bold", s, 14, 0.3) + 50 for s in items]
    gap = (1180 - 44 - sum(widths)) / (len(items) - 1)
    cx = 32
    for i, s in enumerate(items):
        k, w = minikey(s, cx, 64)
        b.append(f'<g class="up" style="animation-delay:{.15+i*.05}s">{k}</g>')
        cx += w + gap
    return svg(W, H, f'<g class="up">{"".join(b)}</g>', label="Stack: " + ", ".join(items))


def info():
    W, H = 1200, 192
    cells = [("BASED IN", "FRANCE  ·  UTC+1"), ("DISCORD", "VEQTAAA"), ("ROLE", "FULL-STACK DEVELOPER"),
             ("FOCUS", "FRONT-END DESIGN"), ("MAIN STACK", "TYPESCRIPT  ·  REACT  ·  NEXT.JS"), ("ON GITHUB SINCE", "JUN 24, 2025")]
    tw = (1180 - 32) / 3
    b = []
    for i, (k, v) in enumerate(cells):
        x, y = 10 + (i % 3) * (tw + 16), 10 + (i // 3) * 80
        g = tile(x, y, tw, 64, 12, False)
        g += T("bold", k, 12.5, x + 20, y + 28, LABEL, 0.6)[0]
        g += T("med", v, 12, x + 20, y + 48, V1 if k == "DISCORD" else MUTED, 0.6)[0]
        b.append(f'<g class="up" style="animation-delay:{.05*i}s">{g}</g>')
    return svg(W, H, "".join(b), label="Based in France. Discord: veqtaaa. Full-stack developer focused on front-end design.")


files = {"hero.svg": hero(), "about.svg": about(), "stack.svg": stack(), "info.svg": info()}
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for n in os.listdir(out):
    if n.endswith(".svg"):
        os.remove(os.path.join(out, n))
for name, content in files.items():
    open(os.path.join(out, name), "w", encoding="utf-8").write(content)
    print(f"{name:14} {len(content)/1024:6.1f} KB")
