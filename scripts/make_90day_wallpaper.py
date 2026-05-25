"""Generate a 1920x1080 desktop wallpaper from the 90-day TL;DR."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1920, 1080
BG = (8, 8, 12)
ACCENT = (255, 59, 59)
GREEN = (68, 255, 68)
TEXT = (235, 235, 240)
DIM = (140, 140, 150)

OUT = Path(r"c:\codetyphoons-aionos26\docs\wallpaper_90day.png")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# subtle grid
for x in range(0, W, 80):
    d.line([(x, 0), (x, H)], fill=(18, 18, 24), width=1)
for y in range(0, H, 80):
    d.line([(0, y), (W, y)], fill=(18, 18, 24), width=1)

# fonts
f_brand = load_font(28, bold=True)
f_title = load_font(64, bold=True)
f_subtitle = load_font(28)
f_step_num = load_font(56, bold=True)
f_step = load_font(34)
f_footer = load_font(26, bold=True)

# top-left brand
d.text((80, 70), "AION OS  /  ECHOWORKS AI", fill=DIM, font=f_brand)

# top-right pulse dot + status (right-anchored)
top_right_text = "OFFLINE  /  90-DAY PLAN"
tr_w = d.textlength(top_right_text, font=f_brand)
tr_x = W - 80 - tr_w
d.ellipse((tr_x - 30, 78, tr_x - 10, 98), fill=GREEN)
d.text((tr_x, 70), top_right_text, fill=GREEN, font=f_brand)

# title block
d.text((80, 160), "NEXT 90 DAYS", fill=ACCENT, font=f_title)
d.text((80, 240), "Bootstrap to revenue. Then choose the room.", fill=TEXT, font=f_subtitle)

# divider
d.line([(80, 310), (W - 80, 310)], fill=(40, 40, 50), width=2)

# 5 steps
steps = [
    ("01", "Keep posting.  The content builds the pipeline."),
    ("02", "Build a list of 25 mid-market law firms (50-500 attorneys, US)."),
    ("03", "Run 10 discovery calls in the next 60 days."),
    ("04", "Close 1 pilot at $25K-$50K by end of June."),
    ("05", "Re-evaluate with real revenue.  Not theory."),
]

y = 360
for num, text in steps:
    d.text((80, y), num, fill=ACCENT, font=f_step_num)
    d.text((200, y + 8), text, fill=TEXT, font=f_step)
    y += 110

# footer
footer_y = H - 110
d.line([(80, footer_y - 20), (W - 80, footer_y - 20)], fill=(40, 40, 50), width=2)
d.text((80, footer_y), "DEFAULT TO INDEPENDENCE.", fill=GREEN, font=f_footer)
footer_right = "Revenue is the only round that doesn't dilute."
fr_w = d.textlength(footer_right, font=f_brand)
d.text((W - 80 - fr_w, footer_y + 4), footer_right, fill=DIM, font=f_brand)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG")
print(f"Saved: {OUT}")
