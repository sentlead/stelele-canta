"""Put the Stelele Cântă cover text on Midjourney art.

    python covers/compose.py covers/example.json

Writes one 1080x1920 cover per entry, plus grid.jpg: the batch as the TikTok
profile grid shows it (3:4 centre crop, view-count fade at the bottom).
"""
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, TOP = 1080, 1920, 240          # 9:16 cover; the 3:4 grid crop keeps y 240..1680
IVORY, GOLD, MUTED = (240, 233, 218), (226, 194, 122), (205, 196, 176)

FONT_DIR = Path(__file__).parent / "fonts"
FONTS = {  # Google Fonts, OFL; fetched on first run
    "cinzel": "cinzel/Cinzel%5Bwght%5D.ttf",
    "cormorant-italic": "cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf",
    "literata-italic": "literata/Literata-Italic%5Bopsz,wght%5D.ttf",
}


def font(name, size, wght, opsz=None):
    path = FONT_DIR / Path(FONTS[name]).name
    if not path.exists():
        FONT_DIR.mkdir(exist_ok=True)
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/" + FONTS[name], path)
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_axes([wght] if opsz is None else [opsz, wght])
    return f


def spaced(draw, y, text, f, fill, track):
    widths = [draw.textlength(c, font=f) for c in text]
    x = (W - sum(widths) - track * (len(text) - 1)) / 2
    for c, w in zip(text, widths):
        draw.text((x + 2, y + 3), c, font=f, fill=(0, 0, 0, 200))
        draw.text((x, y), c, font=f, fill=fill)
        x += w + track


def centered(draw, y, text, f, fill):
    w = draw.textlength(text, font=f)
    for dx in (0, 2, -2):
        draw.text(((W - w) / 2 + dx, y + 4), text, font=f, fill=(0, 0, 0, 170))
    draw.text(((W - w) / 2, y), text, font=f, fill=fill)


def tint(img, colour, strength=0.9):
    """Black-and-white art with only the light (god rays) coloured in the sign's colour."""
    g = ImageOps.grayscale(img)
    coloured = ImageOps.colorize(g, black=(0, 0, 0), mid=colour, white=(255, 255, 255), midpoint=150)
    mask = g.point(lambda v: int(255 * strength * (v / 255) ** 1.4))
    return Image.composite(coloured, g.convert("RGB"), mask)


def canvas(art):
    """Place 3:4 art in the grid-safe band and extend it to 9:16 with its own blurred edges."""
    art = art.convert("RGB").resize((W, round(art.height * W / art.width)), Image.LANCZOS)
    c = Image.new("RGB", (W, H), "black")
    below = H - TOP - art.height
    if below > 0:
        bot = art.crop((0, art.height - 40, W, art.height)).resize((W, below)).filter(ImageFilter.GaussianBlur(30))
        c.paste(bot.point(lambda v: v * 0.4), (0, TOP + art.height))
    top = art.crop((0, 0, W, 40)).resize((W, TOP)).filter(ImageFilter.GaussianBlur(30))
    c.paste(top.point(lambda v: v * 0.6), (0, 0))
    c.paste(art, (0, TOP))
    return c


def scrims(c, bottom_alpha, top_alpha):
    ov = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(0, 470):                       # top: so the wordmark reads
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(top_alpha * (1 - y / 470))))
    for y in range(880, H):                       # bottom: so the name and hook read
        d.line([(0, y), (W, y)], fill=(0, 0, 0, bottom_alpha if y >= 1180 else int(bottom_alpha * (y - 880) / 300)))
    return Image.alpha_composite(c.convert("RGBA"), ov)


def cover(entry, base):
    kind = entry["kind"]                          # "weekly" (Caravaggio) or "monthly" (Doré)
    colour = tuple(int(entry["colour"][i:i + 2], 16) for i in (1, 3, 5))
    art = Image.open(base / entry["art"])
    if kind == "monthly":
        art = tint(art, colour)
    c = scrims(canvas(art), 215 if kind == "weekly" else 170, 150 if kind == "weekly" else 200)
    d = ImageDraw.Draw(c)

    spaced(d, 292, "STELELE CÂNTĂ", font("cinzel", 42, 600), GOLD, 14)
    spaced(d, 352, entry["subline"], font("cinzel", 25, 500), MUTED, 6)
    if kind == "weekly":
        spaced(d, 1035, entry["sign"].upper(), font("cinzel", 150, 700), colour, 16)
    else:
        centered(d, 990, entry["sign"], font("cormorant-italic", 210, 700), GOLD)
    hook_font = font("literata-italic", 74, 650, opsz=72)
    for i, line in enumerate(entry["hook"]):      # at most 2 lines; keep clear of the view count
        centered(d, 1225 + i * 96, line, hook_font, IVORY)
    return c.convert("RGB")


def grid(covers, cols=3):
    tw, th = 360, 480
    rows = -(-len(covers) // cols)
    g = Image.new("RGB", (cols * (tw + 4), rows * (th + 4)), "black")
    for i, c in enumerate(covers):
        t = c.crop((0, TOP, W, TOP + 1440)).resize((tw, th), Image.LANCZOS).convert("RGBA")
        ov = Image.new("RGBA", t.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for y in range(th - 80, th):
            d.line([(0, y), (tw, y)], fill=(0, 0, 0, int(160 * (y - th + 80) / 80)))
        t = Image.alpha_composite(t, ov)
        g.paste(t.convert("RGB"), ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
    return g


if __name__ == "__main__":
    spec = Path(sys.argv[1])
    entries = json.loads(spec.read_text(encoding="utf-8"))
    out = spec.parent / "out"
    out.mkdir(exist_ok=True)
    covers = []
    for e in entries:
        c = cover(e, spec.parent)
        c.save(out / f"{e['kind']}-{e['sign'].lower()}.jpg", quality=92)
        covers.append(c)
    grid(covers).save(out / "grid.jpg", quality=88)
    print(f"{len(covers)} covers + grid.jpg in {out}")
