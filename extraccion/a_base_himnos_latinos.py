"""Pasa los himnos latinos del Apéndice IV (extraccion/apendices/himnos_latinos.yaml) y su traducción literal
(himnos_latinos_traduccion.yaml) a base/himnos/latinos.yaml (texto). Se corrió una vez (23/11/2026): desde entonces la
base es la fuente y este script no se vuelve a correr (pisaría las correcciones). Cuándo va cada himno se escribió a
mano en base/himnos/latinos_cuando.yaml.

Uso: python3 extraccion/a_base_himnos_latinos.py [--forzar | --agregar]
"""
import os, sys, yaml

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DST = os.path.join(R, 'base', 'himnos', 'latinos.yaml')
AGREGAR = '--agregar' in sys.argv   # agrega al final los himnos que la base todavía no tiene (segunda etapa, 23/11/2026)
if os.path.exists(DST) and not AGREGAR and '--forzar' not in sys.argv: sys.exit('base/himnos/latinos.yaml ya existe: se corrige a mano.')
A = os.path.join(R, 'extraccion', 'apendices')
H = yaml.safe_load(open(os.path.join(A, 'himnos_latinos.yaml'), encoding='utf-8'))['himnos']
T = yaml.safe_load(open(os.path.join(A, 'himnos_latinos_traduccion.yaml'), encoding='utf-8'))
V = T.pop('variantes')

def bloque(la, es, ind):
    assert len(la) == len(es), (la, es)
    return '|-\n' + '\n'.join(f'{ind}{a.strip()} = {b.strip()}' for a, b in zip(la, es))

out = ['# Himnos latinos de la Liturgia de las Horas (Apéndice IV del libro), para rezarlos recitados.',
       '# Texto: Te decet hymnus (A. Lentini, 1984), del corpus «latin-ecclesiastic-accents» (proyecto Gregorio, CC0);',
       '# donde el libro trae otro texto, el del libro. Latín con i, æ y œ.',
       '# Cada renglón: «verso latino = traducción literal del verso». Cada estrofa, un elemento de la lista.',
       '# amen: el himno termina con «Amen.» (traducción: «Amén.»).',
       '# variantes: estrofas que cambian según el caso (número de estrofa, desde 1): papa, obispo, presbitero (pastores);',
       '#   mujer, mujeres (mártires, religiosas); una, varios (difuntos). Sin variante, el texto principal.',
       '# Cuándo va cada himno: latinos_cuando.yaml.', '', 'himnos:']
YA = set()
if AGREGAR:
    YA = set(yaml.safe_load(open(DST, encoding='utf-8'))['himnos'])
    out = [open(DST, encoding='utf-8').read().rstrip('\n')]
for k, h in H.items():
    if k in YA: continue
    out.append(f'  {k}:')
    out.append(f'    titulo: {h["incipit"].rstrip(",;:.")}')
    if h.get('amen'): out.append('    amen: true')
    out.append('    estrofas:')
    for la, es in zip(h['estrofas'], T[k]):
        out.append('    - ' + bloque(la, es, '      '))
    if h.get('variantes'):
        out.append('    variantes:')
        for caso, es_ in h['variantes'].items():
            out.append(f'      {caso}:')
            for i, la in es_.items():
                out.append(f'        {int(i)+1}: ' + bloque(la, V[k][caso][i], '          '))
open(DST, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
# comprobación
Y = yaml.safe_load(open(DST, encoding='utf-8'))['himnos']
assert set(H) <= set(Y)
print('ok', len(Y))
