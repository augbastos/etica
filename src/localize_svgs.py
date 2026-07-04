# -*- coding: utf-8 -*-
"""
localize_svgs.py — localiza o TEXTO embutido nas figuras SVG por idioma.

8 SVGs têm texto PT (diagramas). Sem isso, todas as línguas mostram PT = quebrado.

  python localize_svgs.py extract   -> i18n/_svg_strings.json (lista única p/ traduzir)
  python localize_svgs.py apply      -> lê i18n/_svg_translations.json {pt:{en,es,ru,zh,ja}}
                                        e gera i18n/<lang>/assets/<name>.svg p/ os 8 svgs
"""
import sys, json
from pathlib import Path
from lxml import etree
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
I18N = ROOT / "i18n"
NS = "{http://www.w3.org/2000/svg}"
LANGS = ["en", "es", "ru", "zh", "ja"]

# só estes têm texto (os decorativos ficam compartilhados)
TEXT_SVGS = ["diagram-substance.svg", "fig-affects.svg", "fig-knowledge.svg",
             "fig-parallel.svg", "fig-scale.svg", "fig-substance.svg",
             "fig-triangle.svg", "proof-triangle.svg"]

CJK_FONT = "Noto Serif SC, Noto Serif JP, Source Han Serif SC, Songti SC, Yu Mincho, MS Mincho, serif"


def text_nodes(tree):
    return tree.iter(f"{NS}text")


def full_text(el):
    return "".join(el.itertext()).strip()


def extract():
    strings = []
    for name in TEXT_SVGS:
        tree = etree.parse(str(ASSETS / name))
        for t in text_nodes(tree.getroot()):
            s = full_text(t)
            if s and s not in strings:
                strings.append(s)
    out = I18N / "_svg_strings.json"
    out.write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK extract -> {out}  ({len(strings)} strings únicas)")
    for s in strings:
        print("  •", s)


def adjust_font(el, code):
    ff = el.get("font-family", "")
    if code in ("zh", "ja"):
        el.set("font-family", CJK_FONT)
    elif code == "ru":
        if "Cormorant" in ff:
            el.set("font-family", "Cormorant Garamond, Georgia, serif")
        elif "Inter" in ff:
            el.set("font-family", "Inter, Arial, sans-serif")


def apply():
    tmap = json.loads((I18N / "_svg_translations.json").read_text(encoding="utf-8"))
    miss = set()
    for code in LANGS:
        d = I18N / code / "assets"
        d.mkdir(parents=True, exist_ok=True)
        for name in TEXT_SVGS:
            tree = etree.parse(str(ASSETS / name))
            root = tree.getroot()
            for t in text_nodes(root):
                src = full_text(t)
                if not src:
                    continue
                tr = tmap.get(src, {}).get(code)
                if not tr:
                    miss.add((code, src))
                    tr = src  # fallback: keep PT (better than empty)
                for child in list(t):
                    t.remove(child)
                t.text = tr
                adjust_font(t, code)
            tree.write(str(d / name), encoding="utf-8", xml_declaration=False)
        print("OK svgs ->", code)
    if miss:
        print(f"!! {len(miss)} traduções faltando (mantido PT como fallback):")
        for c, s in list(miss)[:20]:
            print(f"   [{c}] {s}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "extract"
    (extract if mode == "extract" else apply)()
