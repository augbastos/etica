"""
Arte vetorial (SVG) do livro, gerada por código (determinística).
Estética: geometria sagrada / precisão matemática — o 'ordine geometrico'
de Spinoza tornado visível. Saída em assets/.
"""
import math
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

INK = "#16263d"
GOLD = "#a9853f"
GOLD_SOFT = "#c8a868"
PAPER = "#faf6ec"
MUTED = "#6c6555"
PHI = (1 + 5 ** 0.5) / 2


def _poly(cx, cy, r, n, rot=-math.pi / 2):
    pts = []
    for i in range(n):
        a = rot + 2 * math.pi / n * i
        pts.append(f"{cx + r*math.cos(a):.2f},{cy + r*math.sin(a):.2f}")
    return " ".join(pts)


def _wrap(svg_inner, w, h, slice_=False):
    pa = ' preserveAspectRatio="xMidYMid slice"' if slice_ else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"{pa}>{svg_inner}</svg>')


# ---------------------------------------------------------------- aberturas
def part_opener(n, polys, spiral_turns=9, rays=96):
    """Diagrama cósmico-geométrico, um por parte (variação por 'polys')."""
    W = H = 760
    cx = cy = W / 2
    el = []
    for i in range(rays):
        a = (2 * math.pi / rays) * i
        x2 = cx + math.cos(a) * 560
        y2 = cy + math.sin(a) * 560
        op = 0.04 + 0.06 * (i % 4 == 0)
        el.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                  f'stroke="{GOLD_SOFT}" stroke-width="0.5" opacity="{op:.2f}"/>')
    r = 26
    for _ in range(7):
        op = max(0.28 - _ * 0.03, 0.05)
        el.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{GOLD_SOFT}" stroke-width="0.7" opacity="{op:.2f}"/>')
        r *= PHI ** 0.5
    for (sides, rad, op, rot) in polys:
        el.append(f'<polygon points="{_poly(cx, cy, rad, sides, rot)}" fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="{op}"/>')
    # espiral áurea
    a = 6.0
    ang = 0
    path = f"M {cx:.1f} {cy:.1f}"
    sweep = 1 if n % 2 else 0
    for _ in range(spiral_turns):
        ang += math.pi / 2
        a *= PHI ** 0.5
        nx = cx + math.cos(ang) * a
        ny = cy + math.sin(ang) * a
        path += f" A {a:.1f} {a:.1f} 0 0 {sweep} {nx:.1f} {ny:.1f}"
    el.append(f'<path d="{path}" fill="none" stroke="{GOLD}" stroke-width="1" opacity="0.45"/>')
    el.append(f'<circle cx="{cx}" cy="{cy}" r="20" fill="none" stroke="{GOLD}" stroke-width="1.6" opacity="0.95"/>')
    el.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{GOLD}"/>')
    (ASSETS / f"part-opener-{n}.svg").write_text(_wrap("".join(el), W, H, slice_=True), encoding="utf-8")


def all_openers():
    # cada parte com seu "tema" geométrico
    part_opener(1, [(3, 210, 0.55, -math.pi/2), (6, 250, 0.3, 0), (12, 290, 0.2, 0)])           # Deus — triângulo
    part_opener(2, [(2, 230, 0.0, 0), (4, 165, 0.45, -math.pi/4), (8, 270, 0.25, 0)], spiral_turns=8)  # Mente — dualidade/quadrado
    part_opener(3, [(6, 230, 0.5, 0), (3, 150, 0.35, math.pi/2), (12, 285, 0.2, 0)])             # Afetos — hexagrama
    part_opener(4, [(4, 215, 0.55, -math.pi/4), (8, 260, 0.28, 0), (16, 295, 0.16, 0)])          # Servidão — grade/quadrado
    part_opener(5, [(12, 250, 0.5, 0), (6, 175, 0.3, 0), (3, 110, 0.4, -math.pi/2)], spiral_turns=10)  # Liberdade — círculo/12


# ---------------------------------------------------------------- divisor
def geo_divider():
    W, H = 240, 34
    cy = H / 2
    cx = W / 2
    el = [f'<line x1="6" y1="{cy}" x2="92" y2="{cy}" stroke="{GOLD}" stroke-width="0.8" opacity="0.6"/>',
          f'<line x1="{W-92}" y1="{cy}" x2="{W-6}" y2="{cy}" stroke="{GOLD}" stroke-width="0.8" opacity="0.6"/>',
          f'<circle cx="{cx-9}" cy="{cy}" r="11" fill="none" stroke="{GOLD}" stroke-width="0.9"/>',
          f'<circle cx="{cx+9}" cy="{cy}" r="11" fill="none" stroke="{GOLD}" stroke-width="0.9"/>',
          f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="{GOLD}"/>']
    (ASSETS / "divider.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


# ---------------------------------------------------------------- figuras-assinatura
def fig_substance():
    """Parte I — Substância → Atributos → Modos."""
    W, H = 680, 470
    cx, cy = 150, 230
    el = []
    for rr, op in [(86, 0.25), (110, 0.16)]:
        el.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{GOLD_SOFT}" stroke-width="0.7" opacity="{op}"/>')
    el.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="{INK}"/>')
    el.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" fill="{PAPER}" font-family="Cormorant Garamond, serif" font-size="22" font-weight="600">UMA</text>')
    el.append(f'<text x="{cx}" y="{cy+20}" text-anchor="middle" fill="{GOLD_SOFT}" font-family="Inter, sans-serif" font-size="11" letter-spacing="2">SUBSTÂNCIA</text>')
    ax = 400
    for ay, lab in zip([95, 235, 370], ["Pensamento", "Extensão", "infinitos atributos…"]):
        el.append(f'<line x1="{cx+58}" y1="{cy}" x2="{ax-8}" y2="{ay}" stroke="{GOLD}" stroke-width="1.3" opacity="0.8"/>')
        inf = "infinitos" in lab
        dash = ' stroke-dasharray="3 4"' if inf else ''
        fill = 'none' if inf else PAPER
        el.append(f'<rect x="{ax}" y="{ay-22}" width="210" height="44" fill="{fill}" stroke="{INK}" stroke-width="1.3"{dash}/>')
        col = GOLD if inf else INK
        st = 'italic' if inf else 'normal'
        el.append(f'<text x="{ax+105}" y="{ay+6}" text-anchor="middle" fill="{col}" font-family="Cormorant Garamond, serif" font-size="19" font-style="{st}">{lab}</text>')
        if not inf:
            for k in range(4):
                mx = ax + 22 + k * 58
                el.append(f'<line x1="{mx}" y1="{ay+22}" x2="{mx}" y2="{ay+46}" stroke="{GOLD_SOFT}" stroke-width="1"/>')
                el.append(f'<circle cx="{mx}" cy="{ay+52}" r="4.5" fill="none" stroke="{GOLD_SOFT}" stroke-width="1.3"/>')
    el.append(f'<text x="{cx}" y="{H-12}" text-anchor="middle" fill="{MUTED}" font-family="Inter, sans-serif" font-size="10" letter-spacing="0.5">os MODOS — tudo o que existe: você, uma pedra, uma ideia</text>')
    (ASSETS / "fig-substance.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def fig_triangle():
    """Parte I — a necessidade geométrica."""
    W, H = 520, 360
    cx, cy, R = 230, 185, 150
    el = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{GOLD_SOFT}" stroke-width="0.9" opacity="0.7"/>']
    A = (cx - 130, cy + 95); B = (cx + 135, cy + 95); C = (cx - 10, cy - 140)
    el.append(f'<polygon points="{A[0]},{A[1]} {B[0]},{B[1]} {C[0]},{C[1]}" fill="rgba(169,133,63,0.06)" stroke="{INK}" stroke-width="1.4"/>')
    for P in (A, B, C):
        el.append(f'<line x1="{cx}" y1="{cy}" x2="{P[0]}" y2="{P[1]}" stroke="{GOLD}" stroke-width="0.5" opacity="0.45" stroke-dasharray="2 3"/>')
        el.append(f'<circle cx="{P[0]}" cy="{P[1]}" r="3" fill="{INK}"/>')
    el.append(f'<text x="{A[0]+14}" y="{A[1]-6}" fill="{INK}" font-family="Cormorant Garamond, serif" font-size="18" font-style="italic">α</text>')
    el.append(f'<text x="{B[0]-26}" y="{B[1]-6}" fill="{INK}" font-family="Cormorant Garamond, serif" font-size="18" font-style="italic">β</text>')
    el.append(f'<text x="{C[0]+6}" y="{C[1]+22}" fill="{INK}" font-family="Cormorant Garamond, serif" font-size="18" font-style="italic">γ</text>')
    el.append(f'<text x="{cx+R+14}" y="{cy+4}" fill="{GOLD}" font-family="Inter, sans-serif" font-size="20" font-weight="600">α+β+γ = 180°</text>')
    el.append(f'<text x="{cx+R+14}" y="{cy+30}" fill="{MUTED}" font-family="Inter, sans-serif" font-size="11">necessário, não escolhido</text>')
    (ASSETS / "fig-triangle.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def fig_parallel():
    """Parte II — paralelismo: a ordem das ideias = a ordem das coisas."""
    W, H = 560, 430
    lx, rx = 160, 400
    el = []
    el.append(f'<text x="{lx}" y="40" text-anchor="middle" fill="{INK}" font-family="Inter, sans-serif" font-size="12" letter-spacing="1.5" font-weight="600">PENSAMENTO</text>')
    el.append(f'<text x="{lx}" y="57" text-anchor="middle" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="13" font-style="italic">as ideias</text>')
    el.append(f'<text x="{rx}" y="40" text-anchor="middle" fill="{INK}" font-family="Inter, sans-serif" font-size="12" letter-spacing="1.5" font-weight="600">EXTENSÃO</text>')
    el.append(f'<text x="{rx}" y="57" text-anchor="middle" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="13" font-style="italic">os corpos</text>')
    ys = [110, 180, 250, 320]
    for y in ys:
        el.append(f'<circle cx="{lx}" cy="{y}" r="13" fill="{INK}"/>')
        el.append(f'<circle cx="{rx}" cy="{y}" r="13" fill="none" stroke="{INK}" stroke-width="1.6"/>')
        el.append(f'<line x1="{lx+15}" y1="{y}" x2="{rx-15}" y2="{y}" stroke="{GOLD}" stroke-width="1" stroke-dasharray="3 4" opacity="0.8"/>')
    el.append(f'<line x1="{lx}" y1="{ys[0]}" x2="{lx}" y2="{ys[-1]}" stroke="{GOLD_SOFT}" stroke-width="1" opacity="0.5"/>')
    el.append(f'<line x1="{rx}" y1="{ys[0]}" x2="{rx}" y2="{ys[-1]}" stroke="{GOLD_SOFT}" stroke-width="1" opacity="0.5"/>')
    el.append(f'<text x="{(lx+rx)/2}" y="{H-26}" text-anchor="middle" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="15" font-style="italic">“a ordem e conexão das ideias é a mesma</text>')
    el.append(f'<text x="{(lx+rx)/2}" y="{H-8}" text-anchor="middle" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="15" font-style="italic">que a ordem e conexão das coisas”</text>')
    (ASSETS / "fig-parallel.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def fig_affects():
    """Parte III — os três afetos primários e seus derivados."""
    W, H = 620, 420
    el = []
    roots = [("DESEJO", 150), ("ALEGRIA", 310), ("TRISTEZA", 470)]
    cy = 90
    for name, cx in roots:
        el.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="{INK}"/>')
        el.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" fill="{PAPER}" font-family="Inter, sans-serif" font-size="12" letter-spacing="1">{name}</text>')
    deriv = {
        150: [("ambição", 70), ("gula", 230)],
        310: [("amor", 250), ("esperança", 370)],
        470: [("ódio", 400), ("medo", 545)],
    }
    for cx, items in deriv.items():
        for lab, dx in items:
            dy = 250
            el.append(f'<line x1="{cx}" y1="{cy+40}" x2="{dx}" y2="{dy-16}" stroke="{GOLD}" stroke-width="1" opacity="0.7"/>')
            el.append(f'<circle cx="{dx}" cy="{dy}" r="26" fill="none" stroke="{GOLD}" stroke-width="1.3"/>')
            el.append(f'<text x="{dx}" y="{dy+5}" text-anchor="middle" fill="{INK}" font-family="Cormorant Garamond, serif" font-size="14" font-style="italic">{lab}</text>')
    el.append(f'<text x="{W/2}" y="{H-20}" text-anchor="middle" fill="{MUTED}" font-family="Inter, sans-serif" font-size="11">de 3 afetos primários (desejo, alegria, tristeza) derivam todos os outros</text>')
    (ASSETS / "fig-affects.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def fig_scale():
    """Parte IV — escala servidão → liberdade."""
    W, H = 620, 260
    x0, x1, y = 70, 550, 120
    el = []
    el.append(f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient></defs>')
    el.append(f'<rect x="{x0}" y="{y-7}" width="{x1-x0}" height="14" rx="7" fill="url(#g)"/>')
    el.append(f'<text x="{x0}" y="{y-22}" fill="{INK}" font-family="Inter, sans-serif" font-size="12" font-weight="600" letter-spacing="1">SERVIDÃO</text>')
    el.append(f'<text x="{x0}" y="{y+30}" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="13" font-style="italic">paixões · causas externas · padecer</text>')
    el.append(f'<text x="{x1}" y="{y-22}" text-anchor="end" fill="{GOLD}" font-family="Inter, sans-serif" font-size="12" font-weight="600" letter-spacing="1">LIBERDADE</text>')
    el.append(f'<text x="{x1}" y="{y+30}" text-anchor="end" fill="{MUTED}" font-family="Cormorant Garamond, serif" font-size="13" font-style="italic">razão · causa interna · agir</text>')
    for i in range(11):
        xx = x0 + (x1 - x0) * i / 10
        el.append(f'<line x1="{xx:.0f}" y1="{y-12}" x2="{xx:.0f}" y2="{y+12}" stroke="{PAPER}" stroke-width="1" opacity="0.5"/>')
    el.append(f'<text x="{W/2}" y="{H-22}" text-anchor="middle" fill="{MUTED}" font-family="Inter, sans-serif" font-size="11">a liberdade não é fugir da ordem, mas compreendê-la a ponto de agir por razão</text>')
    (ASSETS / "fig-scale.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def fig_knowledge():
    """Parte V — os três gêneros de conhecimento, ascendendo à beatitude."""
    W, H = 620, 420
    el = []
    steps = [("1º · IMAGINAÇÃO", "opinião, ouvir dizer", 60, 330),
             ("2º · RAZÃO", "noções comuns, ciência", 230, 250),
             ("3º · INTUIÇÃO", "ver as coisas em Deus", 400, 170)]
    sw = 170
    for i, (title, sub, x, y) in enumerate(steps):
        h = 330 - y + 50
        el.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{h}" fill="{INK if i==2 else "none"}" stroke="{INK}" stroke-width="1.4" opacity="{1 if i==2 else 0.9}"/>')
        col = PAPER if i == 2 else INK
        el.append(f'<text x="{x+sw/2}" y="{y+26}" text-anchor="middle" fill="{col}" font-family="Inter, sans-serif" font-size="12" font-weight="600" letter-spacing="1">{title}</text>')
        el.append(f'<text x="{x+sw/2}" y="{y+46}" text-anchor="middle" fill="{GOLD_SOFT if i==2 else MUTED}" font-family="Cormorant Garamond, serif" font-size="12" font-style="italic">{sub}</text>')
    el.append(f'<text x="{400+sw/2}" y="150" text-anchor="middle" fill="{GOLD}" font-family="Cormorant Garamond, serif" font-size="15" font-style="italic">→ beatitude</text>')
    el.append(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" fill="{MUTED}" font-family="Inter, sans-serif" font-size="11">quanto mais alto o conhecimento, mais a mente repousa no amor intelectual de Deus</text>')
    (ASSETS / "fig-knowledge.svg").write_text(_wrap("".join(el), W, H), encoding="utf-8")


def title_mark():
    el = [f'<circle cx="40" cy="40" r="34" fill="none" stroke="{GOLD}" stroke-width="1.3"/>',
          f'<polygon points="{_poly(40,40,34,3)}" fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.8"/>',
          f'<polygon points="{_poly(40,40,30,4,rot=-math.pi/4)}" fill="none" stroke="{GOLD}" stroke-width="0.6" opacity="0.5"/>',
          f'<circle cx="40" cy="40" r="6" fill="{INK}"/>']
    (ASSETS / "mark.svg").write_text(_wrap("".join(el), 80, 80), encoding="utf-8")


if __name__ == "__main__":
    all_openers()
    geo_divider()
    fig_substance(); fig_triangle(); fig_parallel(); fig_affects(); fig_scale(); fig_knowledge()
    title_mark()
    print("arte gerada:", len(list(ASSETS.glob("*.svg"))), "SVGs em", ASSETS)
