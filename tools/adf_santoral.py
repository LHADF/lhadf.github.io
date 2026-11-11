"""Celebraciones propias del calendario ADF que la base (sync) no trae: les asigna un común (provisorio, por el nombre)
y arma la lista de diferencias entre el calendario ADF y el general.

  python3 tools/adf_santoral.py            →  base/santoral/adf.yaml (solo agrega las que falten; lo ya escrito se respeta)
                                               docs/calendario-adf-diferencias.json (para la planilla de revisión)
"""
import collections, json, os, re, sys
from datetime import date, timedelta
import yaml
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(RAIZ, 'tools', 'importar'))
import base_js
from yaml_base import escribir
B = os.path.join(RAIZ, 'base')
leer = lambda *p: yaml.safe_load(open(os.path.join(B, *p), encoding='utf-8'))
GRADO = {'Solemnidad': 'Solemnidad', 'Fiesta': 'Fiesta', 'Memoria': 'Memoria', 'Memoria obligatoria': 'Memoria', 'Memoria libre': 'Memoria libre'}


def comun_por_nombre(n):
    m = n.lower()
    if 'arcángel' in m: return {'como': 'SANTOS ARCÁNGELES MIGUEL GABRIEL Y RAFAEL'}
    if 'tránsito de san benito' in m: return {'como': 'SAN BENITO ABAD, patrono de Europa'}
    if 'dedicación' in m: return {'como': 'LA DEDICACIÓN DE LA BASÍLICA DE SAN JUAN DE LETRÁN'}
    if 'difuntos' in m or 'nombre de jesús' in m or 'sacerdote' in m: return {'pendiente': 'Oficio propio: faltan todos los textos.'}
    if re.search(r'virgen maría|nuestra señora|^maría,', m): return {'comun': 'virgen-maria'}
    if 'apóstol' in m or 'puerta latina' in m: return {'comun': 'apostoles'}
    if 'mártires' in m: return {'comun': 'varios-martires'}
    if 'mártir' in m: return {'comun': 'un-martir'}
    if re.search(r'obispo|papa|presbítero', m): return {'comun': 'pastores'}
    if 'doctor' in m and 'virgen' not in m: return {'comun': 'doctores'}
    if re.search(r'virgen|religiosa', m): return {'comun': 'virgenes'}
    if re.search(r'^(santa|beata)\b', m): return {'comun': 'santas-mujeres'}
    return {'comun': 'santos-varones'}


def main():
    cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
    cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
    tab, ix, d0 = cal['tabla'], {c: i for i, c in enumerate(cal['campos'])}, date.fromisoformat(cal['desde'])
    adf = collections.OrderedDict()      # nombre → {grado, fechas, region}
    for reg, filas in (('', [(d0 + timedelta(days=k), r) for k, r in enumerate(cal['ARG'])]), ('Paraguay', [(date.fromisoformat(f), r) for f, r in cal['PGY'].items()])):
        for f, r in filas:
            n, g, fer = tab[r[ix['n']]], tab[r[ix['g']]], tab[r[ix['fer']]]
            if n == fer: continue
            e = adf.setdefault(n, {'grado': g, 'fechas': collections.Counter(), 'region': reg})
            e['fechas'][f.strftime('%m-%d')] += 1
            if not reg: e['region'] = ''
    SaL, SaV = leer('santoral', 'laudes.yaml'), leer('santoral', 'visperas.yaml')
    mapaL, _ = base_js.vincular_santoral(SaL); mapaV, _ = base_js.vincular_santoral(SaV)
    ruta = os.path.join(B, 'santoral', 'adf.yaml')
    A = yaml.safe_load(open(ruta, encoding='utf-8')) if os.path.exists(ruta) else {}
    filas = []
    for n, e in adf.items():
        fe = e['fechas'].most_common(); fecha = fe[0][0] if len(fe) == 1 or fe[0][1] > sum(c for _, c in fe) * .6 else 'movible'
        kL, kV = mapaL.get(n), mapaV.get(n)
        ref = SaL.get(kL) or SaV.get(kV) or {}
        if not kL and not kV and n not in A: A[n] = comun_por_nombre(n)
        gA, gS = GRADO.get(e['grado'], e['grado']), GRADO.get(ref.get('grado'), ref.get('grado'))
        tipo = []
        if not kL and not kV: tipo.append('Propia de ADF (no está en el calendario general de la base)')
        else:
            if gS and gA != gS and not (gA == 'Memoria' and gS == 'Memoria libre'): tipo.append(f'Cambia de grado: {gS} → {gA}')
            if ref.get('fecha') not in (fecha, 'variable') and fecha != 'movible': tipo.append(f'Cambia de fecha: {ref.get("fecha")} → {fecha}')
        if not tipo: continue
        a = A.get(n) or {}
        def falta(Sa, k, hora):
            ce = 'antífona del ' + ('Benedictus' if hora == 'laudes' else 'Magníficat')
            if k:
                x = Sa[k]; f = []
                if gA in ('Solemnidad', 'Fiesta') and not x.get('salmodia'): f.append('antífonas de los salmos (toma las del domingo I)')
                if hora == 'visperas' and gA == 'Solemnidad' and (k + ' · I Vísperas') not in Sa: f.append('I Vísperas')
                return '; '.join(f) or '—'
            if a.get('pendiente'): return 'todo el oficio'
            if a.get('como'): return 'oración propia (usa la de la celebración de referencia)'
            C = leer('comunes', hora + '.yaml').get(a.get('comun'), {})
            f = ['oración propia'] + ([ce] if ('ant_benedictus' if hora == 'laudes' else 'ant_magnificat') not in C else []) + (['preces'] if 'preces' not in C else [])
            if gA in ('Solemnidad', 'Fiesta'): f.append('antífonas de los salmos')
            if hora == 'visperas' and gA == 'Solemnidad': f.append('I Vísperas')
            return '; '.join(f)
        filas.append({'fecha': fecha, 'celebracion': n, 'grado_adf': e['grado'], 'region': e['region'] or 'Argentina y Paraguay', 'general': kL or kV or '—', 'grado_general': ref.get('grado') or '—',
                      'diferencia': '; '.join(tipo), 'comun': (a.get('comun') and base_js_nombre(a['comun'])) or (a.get('como') and 'Como: ' + a['como']) or (a.get('pendiente') and 'Sin común: oficio propio') or '—',
                      'falta_laudes': falta(SaL, kL, 'laudes'), 'falta_visperas': falta(SaV, kV, 'visperas')})
    # del calendario general (base) que ADF no celebra
    usados = set(mapaL.values()) | set(mapaV.values())
    for k, v in SaL.items():
        if k not in usados and v.get('fecha') != 'variable':
            filas.append({'fecha': v['fecha'], 'celebracion': '—', 'grado_adf': '—', 'region': '—', 'general': k, 'grado_general': v.get('grado'), 'diferencia': 'Está en la base (calendario general o argentino) y no en el calendario ADF', 'comun': '—', 'falta_laudes': '—', 'falta_visperas': '—'})
    filas.sort(key=lambda r: (r['fecha'] == 'movible', r['fecha']))
    escribir(ruta, dict(A), 'Celebraciones propias del calendario ADF sin textos en la base. Para cada una, hasta tener sus textos propios:\n'
             '  comun: clave de base/comunes/ (himno, lectura, responsorio, antífona del cántico evangélico y preces del común)\n'
             '  como: nombre de otra celebración del santoral de la base, de la que toma todo\n'
             '  pendiente: oficio propio del que no hay nada\n'
             'La asignación inicial es automática, por el nombre (tools/adf_santoral.py): corregir a mano acá.')
    json.dump(filas, open(os.path.join(RAIZ, 'docs', 'calendario-adf-diferencias.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(A), 'celebraciones ADF con común asignado;', len(filas), 'diferencias;', collections.Counter(r['diferencia'].split(':')[0].split(' (')[0] for r in filas))


def base_js_nombre(c):
    from comunes import NOMBRES
    return NOMBRES.get(c, c)


if __name__ == '__main__':
    main()
