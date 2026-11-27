import base64, json, math, os
from xml.sax.saxutils import escape

_FONTS = json.load(open(os.path.join(os.path.dirname(__file__), "glyphs.json"), encoding="utf-8"))["fonts"]

LABEL, MUTED, DIM = "#EEF0F3", "#8A9099", "#525861"
V1, V2, V3 = "#C4DBF7", "#6F9FE0", "#2D5BAD"
G1, G2, GT = "#F3EBDD", "#D2C2A6", "#3A2C1C"
R1, R2, RT = "#FF7A7A", "#E23B3B", "#420909"
SHADE = "#05070B"
LEVELS = ["#1C1F24", "#233A60", "#2D5BAD", "#6F9FE0", "#DCEAFA"]


def num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def measure(font, s, size, tracking=0.0):
    f = _FONTS[font]
    k = size / f["upem"]
    return sum(f["glyphs"][c][0] * k for c in s) + tracking * max(len(s) - 1, 0)


def text(font, s, size, x, y, tracking=0.0, anchor="start"):
    f = _FONTS[font]
    k = size / f["upem"]
    w = measure(font, s, size, tracking)
    x -= w / 2 if anchor == "middle" else w if anchor == "end" else 0
    out = []
    for c in s:
        adv, ops = f["glyphs"][c]
        i = 0
        while i < len(ops):
            op = ops[i]
            i += 1
            n = {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}[op]
            pts = ops[i:i + n]
            i += n
            out.append(op + " ".join(num(x + v * k) if j % 2 == 0 else num(y - v * k) for j, v in enumerate(pts)))
        x += adv * k + tracking
    return "".join(out), w


def attrs(**a):
    return " ".join(f'{k.rstrip("_").replace("_", "-")}="{v}"' for k, v in a.items())


def P(d, **a):
    return f'<path d="{d}" {attrs(**a)}/>'


def T(font, s, size, x, y, fill, tracking=0.0, anchor="start", **a):
    d, w = text(font, s, size, x, y, tracking, anchor)
    return P(d, fill=fill, **a), w


def svg(w, h, body, defs="", style="", label=""):
    label = escape(label, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{label}"><title>{label}</title>'
        f"<defs>{DEFS}{defs}</defs><style>{STYLE}{style}</style>{body}</svg>"
    )


def _lin(id_, stops, x2=0, y2=1):
    s = ""
    for o, c, op in stops:
        extra = "" if op is None else f' stop-opacity="{op}"'
        s += f'<stop offset="{o}" stop-color="{c}"{extra}/>'
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>'


DEFS = (
    _lin("tile", [(0, "#24272C", None), (1, "#191B1F", None)])
    + _lin("edge", [(0, "#FFFFFF", 0.13), (0.25, "#FFFFFF", 0.03), (1, "#000000", 0.5)])
    + _lin("vio", [(0, V1, None), (0.45, V2, None), (1, V3, None)], 1, 1)
    + _lin("vioh", [(0, V3, None), (1, V1, None)], 1, 0)
    + _lin("grn", [(0, G1, None), (1, G2, None)])
    + _lin("red", [(0, R1, None), (1, R2, None)])
    + _lin("track", [(0, "#0D0F12", None), (1, "#17191D", None)])
    + _lin("key", [(0, "#2D3036", None), (1, "#1D1F23", None)])
    + "".join(_lin(f"lv{i}", [(0, c, None), (1, c, 0.72)]) for i, c in enumerate(LEVELS))
    + '<filter id="sh" x="-30%" y="-50%" width="160%" height="300%">'
    f'<feDropShadow dx="0" dy="2" stdDeviation="1.5" flood-color="{SHADE}" flood-opacity=".7"/>'
    f'<feDropShadow dx="2" dy="8" stdDeviation="9" flood-color="{SHADE}" flood-opacity=".6"/></filter>'
    '<filter id="glowv" x="-50%" y="-50%" width="200%" height="200%">'
    f'<feGaussianBlur stdDeviation="6"/></filter>'
    '<filter id="blur2"><feGaussianBlur stdDeviation="1.6"/></filter>'
)

STYLE = """
.up{opacity:0;transform:translateY(10px);animation:up .7s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes up{to{opacity:1;transform:none}}
.pulse{animation:pulse 1.8s ease-in-out infinite}@keyframes pulse{50%{opacity:.3}}
"""


def tile(x, y, w, h, r=14, kebab=True):
    out = [
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{r}" fill="url(#tile)" filter="url(#sh)"/>',
        f'<rect x="{num(x+.5)}" y="{num(y+.5)}" width="{num(w-1)}" height="{num(h-1)}" rx="{r-.5}" fill="none" stroke="url(#edge)"/>',
    ]
    if kebab:
        out += [f'<circle cx="{num(x+w-20)}" cy="{num(y+22+i*5)}" r="1.4" fill="{DIM}"/>' for i in range(3)]
    return "".join(out)


def tag(label, x, y, kind="g", font="bold", size=11, h=20):
    fill, ink = {"g": ("url(#grn)", GT), "r": ("url(#red)", RT), "v": ("url(#vio)", "#0B1B36")}[kind]
    d, w = text(font, label, size, x + 7, y + h / 2 + size * 0.36, 0.4)
    W = w + 14
    return (
        f'<g><rect x="{num(x)}" y="{num(y)}" width="{num(W)}" height="{h}" rx="4" fill="{fill}"/>'
        f'<rect x="{num(x+1)}" y="{num(y+1)}" width="{num(W-2)}" height="{num(h/2-1)}" rx="3" fill="#fff" opacity=".18"/>'
        f'<rect x="{num(x)}" y="{num(y+h-1.5)}" width="{num(W)}" height="1.5" rx=".75" fill="#000" opacity=".25"/>'
        + P(d, fill=ink) + "</g>"
    ), W


def bar(x, y, w, ratio, delay=0.6, h=10):
    fw = max(8, w * ratio)
    return (
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{h}" rx="3" fill="url(#track)" stroke="#000" stroke-opacity=".4"/>'
        f'<rect x="{num(x+1)}" y="{num(y+1)}" width="0" height="{h-2}" rx="2.5" fill="url(#vioh)">'
        f'<animate attributeName="width" from="0" to="{num(fw-2)}" dur="1.1s" begin="{delay}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1"/></rect>'
        f'<rect x="{num(x+1)}" y="{num(y+1)}" width="{num(fw-2)}" height="2" rx="1" fill="#fff" opacity="0">'
        f'<animate attributeName="opacity" to=".22" dur=".3s" begin="{delay+1}s" fill="freeze"/></rect>'
        f'<rect x="{num(x+1)}" y="{num(y-3)}" width="5" height="{h+6}" rx="1.5" fill="#F3EBDD" filter="url(#sh)">'
        f'<animate attributeName="x" from="{num(x+1)}" to="{num(x+fw-6)}" dur="1.1s" begin="{delay}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .7 .2 1"/></rect>'
    )


def gauge(cx, cy, r, ratio, delay=0.6, sw=10):
    def pt(a):
        return num(cx + r * math.cos(a)), num(cy - r * math.sin(a))
    x0, y0 = pt(math.pi)
    x1, y1 = pt(0)
    arc = f"M{x0} {y0}A{r} {r} 0 0 1 {x1} {y1}"
    tx, ty = pt(math.pi * (1 - ratio))
    return (
        P(arc, fill="none", stroke="#0D0F12", stroke_width=sw + 4, stroke_linecap="round")
        + P(arc, fill="none", stroke="url(#vioh)", stroke_width=sw, stroke_linecap="round", pathLength="1",
            stroke_dasharray=f"{ratio:.3f} 1", stroke_dashoffset=f"{ratio:.3f}",
            **{"class": "gauge", "style": f"animation-delay:{delay}s;--r:{ratio:.3f}"})
        + P(arc, fill="none", stroke="#fff", stroke_opacity=".16", stroke_width=2, stroke_linecap="round",
            transform="translate(0 -3)", pathLength="1", stroke_dasharray=f"{ratio:.3f} 1")
        + f'<circle cx="{tx}" cy="{ty}" r="{sw/2+1.5}" fill="#F3EBDD" filter="url(#sh)" opacity="0">'
        f'<animate attributeName="opacity" to="1" dur=".3s" begin="{delay+1}s" fill="freeze"/></circle>'
    )


GAUGE_CSS = ".gauge{animation:g 1.2s cubic-bezier(.2,.7,.2,1) forwards}@keyframes g{to{stroke-dashoffset:0}}"


def keycap(cx, cy, w, h, legend, font="black", size=None, tone="vio", rot=0):
    body = "url(#vio)" if tone == "vio" else "url(#key)"
    ink = "#FFFFFF" if tone == "vio" else V1
    x, y = cx - w / 2, cy - h / 2
    tw, th = w * 0.74, h * 0.66
    tx, ty = cx - tw / 2 - w * 0.02, y + h * 0.07
    size = size or th * 0.55
    d, _ = text(font, legend, size, tx + tw / 2, ty + th / 2 + size * 0.36, 0, "middle")
    return (
        f'<g transform="rotate({rot} {num(cx)} {num(cy)})">'
        f'<ellipse cx="{num(cx+w*.06)}" cy="{num(y+h+h*.06)}" rx="{num(w*.46)}" ry="{num(h*.09)}" fill="{SHADE}" opacity=".75" filter="url(#glowv)"/>'
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{num(w*.2)}" fill="{body}"/>'
        f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" rx="{num(w*.2)}" fill="url(#edge)" opacity=".9"/>'
        f'<rect x="{num(tx)}" y="{num(ty)}" width="{num(tw)}" height="{num(th)}" rx="{num(w*.15)}" fill="{body}"/>'
        f'<rect x="{num(tx)}" y="{num(ty)}" width="{num(tw)}" height="{num(th)}" rx="{num(w*.15)}" fill="#fff" opacity=".10"/>'
        f'<rect x="{num(tx+1)}" y="{num(ty+1)}" width="{num(tw-2)}" height="{num(th-2)}" rx="{num(w*.15-1)}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.5"/>'
        f'<ellipse cx="{num(tx+tw*.3)}" cy="{num(ty+th*.2)}" rx="{num(tw*.22)}" ry="{num(th*.08)}" fill="#fff" opacity=".35" filter="url(#blur2)"/>'
        + P(d, fill=ink, opacity=".95")
        + "</g>"
    )


def img(path, x, y, w, h=None, **a):
    data = open(os.path.join(os.path.dirname(__file__), "renders", path), "rb").read()
    if h is None:
        from PIL import Image
        iw, ih = Image.open(os.path.join(os.path.dirname(__file__), "renders", path)).size
        h = w * ih / iw
    hh = f' height="{num(h)}"'
    return (f'<image href="data:image/webp;base64,{base64.b64encode(data).decode()}" x="{num(x)}" y="{num(y)}" '
            f'width="{num(w)}"{hh} {attrs(**a)}/>')
