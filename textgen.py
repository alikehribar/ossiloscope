import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_SIZE = 200
CURVE_STEPS = 6
TRACKING = -18.0


def render_bitmap(text, path, tracking=TRACKING):
    # Characters are drawn one at a time so tracking can be negative. Overlapping
    # the glyphs makes them touch, and potrace then traces the whole word as one
    # outline with no connecting line exposed between letters.
    font = ImageFont.truetype(FONT, FONT_SIZE)
    widths = [font.getlength(ch) for ch in text]
    total = (sum(widths) + (tracking * (len(text) - 1)))
    img = Image.new("L", (int((total + 40)), int((FONT_SIZE * 1.6))), 255)
    draw = ImageDraw.Draw(img)
    x = 20.0
    for (ch, w) in zip(text, widths):
        draw.text((x, 20), ch, font=font, fill=0)
        x += (w + tracking)
    box = img.point(lambda v: (255 if (v < 128) else 0)).getbbox()
    img = img.crop(((box[0] - 20), (box[1] - 20), (box[2] + 20), (box[3] + 20)))
    img.convert("1").save(path)
    return img.size


def bezier(p0, p1, p2, p3, steps):
    out = []
    for i in range(1, (steps + 1)):
        t = (i / steps)
        u = (1.0 - t)
        a, b = (u * u * u), ((3.0 * u * u) * t)
        c, d = ((3.0 * u) * (t * t)), (t * t * t)
        out.append((
            (((a * p0[0]) + (b * p1[0])) + ((c * p2[0]) + (d * p3[0]))),
            (((a * p0[1]) + (b * p1[1])) + ((c * p2[1]) + (d * p3[1]))),
        ))
    return out


def parse_contours(svg_text):
    # potrace writes one absolute M then relative m/l/c under a
    # translate(0,H) scale(0.1,-0.1) transform, which yields SVG coordinates
    # with y growing downward. The scope needs y upward, and the two flips
    # cancel, leaving a plain 0.1 scale.
    contours = []
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', svg_text, re.S):
        tokens = re.findall(r"[MmLlCcZz]|-?\d*\.?\d+", d)
        contour, cur, cmd, i = [], (0.0, 0.0), "", 0
        while (i < len(tokens)):
            if tokens[i].isalpha():
                cmd = tokens[i]
                i += 1
                if (cmd in "Zz"):
                    if (len(contour) > 2):
                        contours.append(contour)
                    contour = []
                    continue
            count = (6 if (cmd in "Cc") else 2)
            nums = [float(v) for v in tokens[i:(i + count)]]
            i += count
            rel = cmd.islower()
            pts = [((cur[0] + nums[j]) if rel else nums[j],
                    (cur[1] + nums[(j + 1)]) if rel else nums[(j + 1)])
                   for j in range(0, len(nums), 2)]
            if (cmd in "Cc"):
                contour += bezier(cur, pts[0], pts[1], pts[2], CURVE_STEPS)
            else:
                contour.append(pts[0])
            cur = contour[-1]
    return [[((x * 0.1), (y * 0.1)) for (x, y) in c] for c in contours]


def route(contours, gap=0.0):
    # One continuous stroke: run along the letters' own baseline, climb into
    # each shape at its lowest point, trace it, drop back down. With gap=0 the
    # travel line lies on the bottom edge of the letters and stays invisible.
    # Sorting by left edge puts each counter directly after its parent letter.
    contours = sorted(contours, key=lambda c: min(p[0] for p in c))
    floor = (min(p[1] for c in contours for p in c) - gap)
    path = []
    for contour in contours:
        low = min(range(len(contour)), key=lambda i: contour[i][1])
        loop = (contour[low:] + contour[:low])
        path.append((loop[0][0], floor))
        path += loop
        path.append(loop[0])
        path.append((loop[0][0], floor))
    return path


def fit(path, size=255.0, margin=8.0):
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    scale = ((size - (2.0 * margin)) / max((max(xs) - min(xs)), (max(ys) - min(ys))))
    return [((margin + ((x - min(xs)) * scale)), (margin + ((y - min(ys)) * scale)))
            for (x, y) in path]


def generate(text):
    render_bitmap(text, "/tmp/textgen.pbm")
    subprocess.run(["potrace", "-s", "-o", "/tmp/textgen.svg", "/tmp/textgen.pbm"], check=True)
    contours = parse_contours(open("/tmp/textgen.svg").read())
    return fit(route(contours))


def as_table(name, values, per_line=12):
    rows = []
    for i in range(0, len(values), per_line):
        rows.append("    " + ", ".join(("%4d" % round(v)) for v in values[i:(i + per_line)]) + ",")
    return ("%s = (\n%s\n)\n" % (name, "\n".join(rows)))


if __name__ == "__main__":
    word = (sys.argv[1] if (len(sys.argv) > 1) else "W2AEW")
    points = generate(word)
    sys.stderr.write("%s -> %d points\n" % (word, len(points)))
    print(as_table("X_POINTS", [p[0] for p in points]))
    print(as_table("Y_POINTS", [p[1] for p in points]))
