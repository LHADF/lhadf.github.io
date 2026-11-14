"""Corrige en la extracción los himnos con dos estrofas pegadas en un corte de página (y una línea perdida).

    python3 extraccion/corregir_himnos.py

Revisados contra el libro (y contra la base, donde sync los tenía): `estrofas` de cada himno en todos los
`himnos.json`. Se puede volver a correr: si ya está corregido, no cambia nada.
"""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
# id → índice de la estrofa que hay que partir (en dos mitades iguales)
PARTIR = {'nos-apremia-el-amor-virgenes-santas': 0, 'donde-esta-muerte-tu-victoria': 1, 'cuando-la-luz-se-hace-vaga': 3,
          'custodio-virgen-de-la-virgen-madre': 2, 'vienes-del-trono-de-david-profeta': 2,
          'cantemos-al-amor-de-los-amores': 2, 'voceros-de-dios-2': 0}
# líneas que la extracción perdió: id → (estrofa, posición, texto), después de partir
FALTA = {'voceros-de-dios-2': (2, 1, 'de amor es la ley,')}


def corregir(h):
    es = h['estrofas']
    i = PARTIR.get(h['id'])
    if i is None or i >= len(es):
        return False
    n = [len(e) for e in es]
    if n[i] % 2 or n[i] < 4 or (len(es) > i + 1 and n[i] == n[i + 1] and n[i] <= 4):
        return False        # ya está partida
    mitad = n[i] // 2
    es[i:i + 1] = [es[i][:mitad], es[i][mitad:]]
    if h['id'] in FALTA:
        k, pos, texto = FALTA[h['id']]
        if all(v['texto'] != texto for v in es[k]):
            es[k].insert(pos, {'texto': texto, 'sangria': es[k][0].get('sangria', 0)})
    return True


def main():
    for p in sorted(AQUI.glob('**/himnos.json')):
        d = json.loads(p.read_text(encoding='utf-8'))
        hechos = [h['id'] for h in d if corregir(h)]
        if hechos:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print(p.relative_to(AQUI), hechos)


if __name__ == '__main__':
    main()
