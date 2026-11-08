#!/usr/bin/env python3
"""Fuente mínima con «ǽ» y «Ǽ» para la app (src/assets/ae.css).

Source Serif 4 no trae U+01FD/U+01FC: el navegador las toma de otra fuente y se ven más altas. Esta herramienta
las arma con la «æ»/«Æ» y la tilde de la propia Source Serif 4, ubicadas con sus anclas (GPOS), en los pesos que usa
la app, en una familia propia («Septies AE», después de «Cantoral Signos» en la lista) solo para esos dos caracteres.
No usar el nombre «Cantoral Signos»: con pesos distintos, el navegador dejaría de usar esa fuente para ℟, * y ✠.

    pip install fonttools brotli
    npm pack @fontsource-variable/source-serif-4   (y descomprimir)
    python3 tools/fuente_ae.py RUTA/source-serif-4-latin-opsz-normal.woff2

Source Serif 4: © Adobe, SIL Open Font License 1.1. Los glifos derivados van con otro nombre de familia (la licencia
reserva el nombre «Source»).
"""
import base64, io, os, sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.varLib import instancer
from fontTools import subset

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PESOS = (400, 600)   # texto normal y negrita (los dos únicos pesos del texto negro, como en el Cantoral)


def anclas(f, base, marca):
    """Desplazamiento (x, y) de `marca` sobre `base` según el GPOS (mark-to-base)."""
    gpos = f['GPOS'].table
    for lk in gpos.LookupList.Lookup:
        for st in lk.SubTable:
            st = getattr(st, 'ExtSubTable', st)
            if getattr(st, 'Format', None) != 1 or not hasattr(st, 'BaseCoverage'): continue
            mc, bc = st.MarkCoverage.glyphs, st.BaseCoverage.glyphs
            if marca in mc and base in bc:
                mr = st.MarkArray.MarkRecord[mc.index(marca)]
                ba = st.BaseArray.BaseRecord[bc.index(base)].BaseAnchor[mr.Class]
                if ba: return ba.XCoordinate - mr.MarkAnchor.XCoordinate, ba.YCoordinate - mr.MarkAnchor.YCoordinate
    raise SystemExit(f'Sin anclas para {marca} sobre {base}')


def compuesta(f, base, marca, nombre, unicode):
    dx, dy = anclas(f, base, marca)
    g = Glyph(); g.numberOfContours = -1; g.components = []
    for n, x, y in ((base, 0, 0), (marca, dx, dy)):
        c = GlyphComponent(); c.glyphName, c.x, c.y, c.flags = n, x, y, 0
        g.components.append(c)
    g.components[0].flags = 0x0200   # USE_MY_METRICS
    f['glyf'][nombre] = g
    f['hmtx'][nombre] = f['hmtx'][base]
    orden = f.getGlyphOrder()
    if nombre not in orden:
        orden = orden + [nombre]; f.setGlyphOrder(orden); f['glyf'].glyphOrder = orden
        if hasattr(f, '_reverseGlyphOrderDict'): del f._reverseGlyphOrderDict
        f['maxp'].numGlyphs = len(orden)
    for t in f['cmap'].tables:
        if t.isUnicode(): t.cmap[unicode] = nombre


def instancia(origen, peso):
    f = TTFont(origen)
    f = instancer.instantiateVariableFont(f, {'wght': peso, 'opsz': 20})
    cmap = f.getBestCmap()
    ae, AE, acu = cmap[0xE6], cmap[0xC6], cmap[0x301]
    acu_may = next((c.glyphName for c in f['glyf'][cmap[0xC9]].components if c.glyphName != cmap[0x45]), acu)  # tilde de mayúscula
    compuesta(f, ae, acu, 'aeacute', 0x1FD)
    compuesta(f, AE, acu_may if anclas_ok(f, AE, acu_may) else acu, 'AEacute', 0x1FC)
    tmp = io.BytesIO(); f.save(tmp); tmp.seek(0); f = TTFont(tmp)   # releer: tabla de glifos al día
    opt = subset.Options(); opt.layout_features = []; opt.name_IDs = []; opt.notdef_outline = True; opt.flavor = 'woff2'
    sub = subset.Subsetter(opt); sub.populate(unicodes=[0x1FD, 0x1FC]); sub.subset(f)
    for r in f['name'].names: r.string = 'Septies AE'
    f.flavor = 'woff2'; b = io.BytesIO(); f.save(b)
    return b.getvalue()


def anclas_ok(f, base, marca):
    try: anclas(f, base, marca); return True
    except SystemExit: return False


def main():
    if len(sys.argv) != 2: sys.exit(__doc__)
    css = ['/* «ǽ» y «Ǽ» armadas con glifos de Source Serif 4 (© Adobe, SIL OFL 1.1). Generado por tools/fuente_ae.py. Familia propia: si compartiera nombre con «Cantoral Signos», el navegador elegiría por peso y perdería ℟, * y ✠. */']
    for p in PESOS:
        d = base64.b64encode(instancia(sys.argv[1], p)).decode()
        css.append(f"@font-face{{font-family:'Septies AE';font-weight:{p};font-display:swap;unicode-range:U+01FC-01FD;"
                   f"src:url(data:font/woff2;base64,{d}) format('woff2')}}")
    destino = os.path.join(RAIZ, 'src', 'assets', 'ae.css')
    open(destino, 'w', encoding='utf-8').write('\n'.join(css) + '\n')
    print(f'{os.path.relpath(destino, RAIZ)}: {os.path.getsize(destino) // 1024} KB')


if __name__ == '__main__':
    main()
