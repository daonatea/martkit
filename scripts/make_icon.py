"""
Genera el ícono de markIT en múltiples tamaños y lo empaqueta en .icns
Concepto: squircle con gradiente índigo→violeta, símbolo "#" en blanco con
           una flecha descendente sutil — "convierte todo a Markdown".
"""
import math
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent.parent
OUT_ICONSET = ROOT / "assets" / "markIT.iconset"
OUT_ICNS    = ROOT / "assets" / "markIT.icns"


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def make_icon(size: int) -> Image.Image:
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── 1. Squircle background con gradiente ──────────────────────────────
    radius = int(S * 0.225)          # radio estándar macOS (~22.5%)

    # Gradiente vertical: navy-índigo → violeta-morado
    TOP    = (18,  22,  88)          # #12165A deep navy-indigo
    BOTTOM = (100, 60, 200)          # #643CC8 violet-purple
    MID    = (55,  42, 155)          # midpoint

    grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        c = lerp_color(TOP, MID, t) if t < 0.5 else lerp_color(MID, BOTTOM, (t - 0.5) * 2)
        gd.line([(0, y), (S, y)], fill=(*c, 255))

    # Máscara con squircle (superellipse n=4 aproximado)
    mask = Image.new("L", (S, S), 0)
    md   = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)

    img.paste(grad, (0, 0), mask)

    # ── 2. Brillo sutil en la esquina superior izquierda ─────────────────
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    from PIL import ImageDraw as ID2
    gd2 = ID2.Draw(glow)
    # Círculo suave translúcido blanco en arriba-izquierda
    gr = int(S * 0.55)
    glow_alpha = Image.new("L", (S, S), 0)
    for i in range(gr, 0, -1):
        a = int(28 * (i / gr) ** 2)
        glow_alpha_draw = ImageDraw.Draw(glow_alpha)
        glow_alpha_draw.ellipse(
            [-gr + i // 2, -gr + i // 2, i, i], fill=a
        )
    glow.putalpha(glow_alpha)
    img = Image.alpha_composite(img, glow)

    # ── 3. Símbolo "#" en blanco ─────────────────────────────────────────
    # Dibujamos el "#" manualmente como líneas para máxima nitidez
    draw = ImageDraw.Draw(img)
    u = S / 512                    # unidad de escala

    # Color: blanco con ligera translucidez para suavidad
    WHITE  = (255, 255, 255, 245)
    SHADOW = (0,   0,   0,   60)

    lw = max(1, int(22 * u))       # grosor de línea
    pad = int(130 * u)             # padding desde el borde

    # Las cuatro líneas del símbolo "#":
    # Dos verticales y dos horizontales
    x1 = int(185 * u);  x2 = int(275 * u)   # columnas
    x3 = int(240 * u);  x4 = int(330 * u)   # segunda columna (ligeramente desplazadas)
    y1 = int(148 * u);  y2 = int(364 * u)   # rango vertical
    yh1 = int(215 * u); yh2 = int(295 * u)  # las dos horizontales

    # Sombra sutil (offset de 2px)
    so = max(1, int(3 * u))
    for pts, col in [
        # sombra
        ([(x1+so, y1+so, x1+so, y2+so),
          (x2+so, y1+so, x2+so, y2+so),
          (pad+so, yh1+so, S-pad+so, yh1+so),
          (pad+so, yh2+so, S-pad+so, yh2+so)], SHADOW),
        # trazo principal
        ([(x1, y1, x1, y2),
          (x2, y1, x2, y2),
          (pad, yh1, S-pad, yh1),
          (pad, yh2, S-pad, yh2)], WHITE),
    ]:
        for (ax, ay, bx, by) in pts:
            draw.line([(ax, ay), (bx, by)], fill=col, width=lw)

    # ── 4. Flecha descendente pequeña bajo el "#" ─────────────────────────
    ax  = S // 2
    ay1 = int(385 * u)
    ay2 = int(430 * u)
    aw  = int(28 * u)
    ah  = int(20 * u)
    alw = max(1, int(16 * u))
    ARROW = (255, 255, 255, 200)
    # Línea vertical
    draw.line([(ax, ay1), (ax, ay2)], fill=ARROW, width=alw)
    # Punta de flecha
    draw.polygon([(ax - aw, ay2 - ah), (ax + aw, ay2 - ah), (ax, ay2 + ah // 2)],
                 fill=ARROW)

    # ── 5. Borde brillante muy sutil ─────────────────────────────────────
    border_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border_img)
    bd.rounded_rectangle(
        [0, 0, S - 1, S - 1],
        radius=radius,
        outline=(255, 255, 255, 28),
        width=max(1, int(2 * u)),
    )
    img = Image.alpha_composite(img, border_img)

    return img


def build_ico():
    """Genera assets/markIT.ico para Windows (multi-resolución)."""
    import platform as _platform
    out_ico = ROOT / "assets" / "markIT.ico"
    sizes = [16, 32, 48, 64, 128, 256]
    frames = [make_icon(s).convert("RGBA") for s in sizes]
    frames[0].save(
        str(out_ico),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"ícono Windows generado: {out_ico}")


def build_iconset():
    OUT_ICONSET.mkdir(parents=True, exist_ok=True)
    specs = [
        ("icon_16x16.png",      16),
        ("icon_16x16@2x.png",   32),
        ("icon_32x32.png",      32),
        ("icon_32x32@2x.png",   64),
        ("icon_128x128.png",    128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png",    256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png",    512),
        ("icon_512x512@2x.png", 1024),
    ]
    for name, size in specs:
        icon = make_icon(size)
        path = OUT_ICONSET / name
        icon.save(str(path), "PNG")
        print(f"  {name} ({size}px)")

    # Convertir a .icns
    subprocess.run(
        ["iconutil", "-c", "icns", str(OUT_ICONSET), "-o", str(OUT_ICNS)],
        check=True,
    )
    print(f"\nícono macOS generado: {OUT_ICNS}")


if __name__ == "__main__":
    import platform as _platform
    print("Generando íconos de markIT...")
    if _platform.system() == "Darwin":
        build_iconset()
    build_ico()
    print("Listo.")
