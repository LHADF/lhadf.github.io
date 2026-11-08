#!/usr/bin/env python3
"""Normaliza el latín de un GABC según docs/diseno.md y lo copia a base/gregoriano/.

    python3 tools/normalizar_gabc.py ORIGEN.gabc destino.gabc

- j → i; ae → æ, oe → œ (y con tilde: ǽ, œ́), solo en la letra (no toca notas ni etiquetas).
- Avisa las palabras de tres sílabas o más sin tilde: hay que agregarla a mano en el archivo.
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILDES = 'áéíóúýǽÁÉÍÓÚÝǼ'


def latin(t):
    t = t.replace('j', 'i').replace('J', 'I')
    t = re.sub(r'ae', 'æ', t); t = re.sub(r'aé', 'ǽ', t); t = re.sub(r'A[eE]', 'Æ', t)
    t = re.sub(r'oe', 'œ', t); t = re.sub(r'oé', 'œ́', t)
    return t


def partes(cuerpo):
    """Divide el cuerpo en (es_letra, texto)."""
    i = 0
    for m in re.finditer(r'\([^)]*\)|<[^>]+>|\[[^\]]*\]|\{|\}', cuerpo):
        yield True, cuerpo[i:m.start()]
        yield False, m.group(0)
        i = m.end()
    yield True, cuerpo[i:]


def normalizar(s):
    cab, sep, cuerpo = s.partition('%%')
    if not sep: cab, cuerpo = '', s
    cab = re.sub(r'^(name:.*)$', lambda m: latin(m.group(1)), cab, flags=re.M)
    cuerpo = ''.join(latin(t) if letra else t for letra, t in partes(cuerpo))
    return cab + sep + cuerpo


PREFIJO = re.compile(r'^(\s*(?:<sp>[^<]*</sp>\.?|<alt>.*?</alt>|<i>T\. ?P\.</i>|\*+)?\s*)', re.S)


def negrita(g, desde=0, hasta=None):
    """Pone en negrita la letra (lo que canta la asamblea) desde la posición `desde` del cuerpo hasta `hasta`.
    No toca rúbricas (℣/℟, <alt>, «T. P.»), asteriscos ni lo que ya está en negrita."""
    cab, sep, cuerpo = g.partition('%%')
    if not sep: cab, cuerpo = '', g
    hasta = len(cuerpo) if hasta is None else hasta
    def f(m):
        t, notas = m.group(1), m.group(2)
        if not (m.end(1) > desde and m.start() < hasta) or '<b>' in t or not re.search(r'[A-Za-zÀ-ÿæœǽ{]', re.sub(r'<alt>.*?</alt>|<sp>.*?</sp>|<i>T\. ?P\.</i>', '', t, flags=re.S)):
            return m.group(0)
        pre = PREFIJO.match(t).group(1)
        resto = t[len(pre):]
        fin = re.search(r'\s*$', resto).group(0); resto = resto[:len(resto) - len(fin)]
        return f'{pre}<b>{resto}</b>{fin}{notas}' if resto else m.group(0)
    cuerpo = re.sub(r'([^()]*)(\([^)]*\))', f, cuerpo, flags=re.S)
    return cab + sep + cuerpo


def desde_asterisco(g):
    """Posición (en el cuerpo) del primer asterisco de la letra: desde ahí canta la asamblea."""
    cuerpo = g.partition('%%')[2] or g
    m = re.search(r'(?:^|\s|\))\*+\s*\(', cuerpo)
    return m.start() if m else 0


def palabras(cuerpo):
    """Palabras de la letra con su número de sílabas (cada sílaba lleva notas entre paréntesis)."""
    cuerpo = re.sub(r'<alt>.*?</alt>|<eu>.*?</eu>', '', cuerpo)
    cuerpo = re.sub(r'<[^>]+>|\[[^\]]*\]|[{}]', '', cuerpo)
    out, cur, sil = [], '', 0
    for m in re.finditer(r'([^()]*)\(([^)]*)\)', cuerpo):
        t = m.group(1)
        if re.match(r'\s', t) or not t.strip():
            if cur: out.append((cur, sil))
            cur, sil = '', 0
        t = t.strip()
        if re.search(r'[A-Za-zÀ-ÿæœǽ]', t):
            cur += t; sil += 1
    if cur: out.append((cur, sil))
    return out


def sin_tilde(s):
    cuerpo = s.partition('%%')[2] or s
    return sorted({re.sub(r'[^\wæœǽ́]', '', w) for w, n in palabras(cuerpo) if n >= 3 and not any(c in TILDES or c == '́' for c in w)})


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    s = normalizar(open(sys.argv[1], encoding='utf-8').read())
    destino = sys.argv[2] if os.path.dirname(sys.argv[2]) else os.path.join(RAIZ, 'base', 'gregoriano', sys.argv[2])
    open(destino, 'w', encoding='utf-8').write(s)
    print(os.path.relpath(destino, RAIZ))
    f = sin_tilde(s)
    if f: print('  Sin tilde (3 sílabas o más):', ', '.join(f))
