import json, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

UF = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
SRC = {
    "black": os.path.join(UF, "Montserrat-Black.ttf"),
    "bold": os.path.join(UF, "Montserrat-Bold.ttf"),
    "med": os.path.join(UF, "Montserrat-Medium.ttf"),
    "mono": r"C:\Windows\Fonts\CascadiaMono.ttf",
}
CHARS = "".join(chr(c) for c in range(32, 127)) + "·—"


class Rec(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.out = []

    def _moveTo(self, p):
        self.out += ["M", *map(round, p)]

    def _lineTo(self, p):
        self.out += ["L", *map(round, p)]

    def _qCurveToOne(self, a, b):
        self.out += ["Q", *map(round, a), *map(round, b)]

    def _curveToOne(self, a, b, c):
        self.out += ["C", *map(round, a), *map(round, b), *map(round, c)]

    def _closePath(self):
        self.out.append("Z")


atlas = {"license": "Montserrat and Cascadia Mono outlines, SIL Open Font License 1.1", "fonts": {}}
for key, path in SRC.items():
    f = TTFont(path)
    cmap, gs, hmtx = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    glyphs = {}
    for ch in CHARS:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        pen = Rec(gs)
        gs[g].draw(pen)
        glyphs[ch] = [hmtx[g][0], pen.out]
    atlas["fonts"][key] = {"upem": f["head"].unitsPerEm, "glyphs": glyphs}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(atlas, fh, separators=(",", ":"), ensure_ascii=False)
print(os.path.getsize(sys.argv[1]) // 1024, "KB")
