"""Carga única de Laudes desde sync a la base propia (base/).

Uso:
  SEPTIES_FUENTES=/ruta/a/fuentes ORDO=/ruta/a/ordo-telegram python3 tools/importar/importar_laudes.py

Recorre todas las Laudes de sync (2015 en adelante) y etiqueta cada fecha con el motor del Ordo
(tiempo, semana, semana del salterio, feria). Luego reparte cada parte del oficio en tres capas:

  1. salterio  (base/salterio/laudes.yaml): las cuatro semanas, tomadas de las ferias del Tiempo Ordinario;
  2. tiempo    (base/tiempo/laudes.yaml): por feria (y ciclo A/B/C en los domingos), solo lo que cambia respecto del salterio;
  3. santoral  (base/santoral/laudes.yaml): por celebración, solo lo que cambia respecto de las dos capas anteriores.

Para cada texto queda la versión que más se repite; las demás van a base/informes/laudes.md.
Después de esta carga, sync ya no hace falta: las correcciones se hacen en base/.
"""
import collections, json, os, re, sys, tomllib, unicodedata
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
sys.path.insert(0, AQUI)
import laudes_sync as L
from yaml_base import escribir as _escribir


def _aleluia(x):
    if isinstance(x, str): return x.replace('aleluya', 'aleluia').replace('Aleluya', 'Aleluia').replace('ALELUYA', 'ALELUIA')
    if isinstance(x, list): return [_aleluia(y) for y in x]
    if isinstance(x, dict): return {_aleluia(k): _aleluia(v) for k, v in x.items()}
    return x


def escribir(ruta, datos, cabecera=''):
    """En español, «aleluia» (nunca «aleluya»): docs/diseno.md."""
    _escribir(ruta, _aleluia(datos), cabecera)
from importar_completas import Votos, sin_gloria

FUENTES = os.environ.get('SEPTIES_FUENTES', os.path.join(RAIZ, '..', 'fuentes'))
SYNC = os.path.join(FUENTES, 'sync')
ORDO = os.environ.get('ORDO', os.path.join(RAIZ, '..', 'ordo-telegram'))
BASE = os.path.join(RAIZ, 'base')
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
CAMPOS = ['inv_ant', 'himno', 'salmodia', 'lectura', 'responsorio', 'ant_benedictus', 'preces', 'padrenuestro_intro', 'oracion']


def cargar():
    sys.path.insert(0, ORDO)
    from ordo.calendario import Ordo
    O = Ordo(ORDO, tomllib.load(open(os.path.join(ORDO, 'config.toml'), 'rb')))
    out = []
    for fecha, var, f, idx in L.archivos(SYNC):
        d = L.estructura(f); d['celebracion'] = L.celebracion(idx)
        D = O.dia(date.fromisoformat(fecha))
        d.update(fecha=fecha, var=var, tiempo=D.tiempo, semana=D.semana, salterio=D.salterio, feria=D.feria.nombre)
        out.append(d)
    return out


# ---------- identificación de salmos y cánticos ----------
def sin_tildes(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def id_salmo(h):
    """'Salmo 118, 145-152 TE INVOCO…' → ('salmo-118-145-152', 'Salmo 118, 145-152', 'TE INVOCO…');
       'SALMO 18 A - ALABANZA…' → ('salmo-18-a', 'Salmo 18 A', 'ALABANZA…');
       'Cántico: TODA LA CREACIÓN… - Dn 3, 57-88. 56' → ('cantico-dn-3-57-88-56', 'Cántico Dn 3, 57-88. 56', 'TODA LA CREACIÓN…')."""
    h = re.sub(r'\s+', ' ', h).strip().rstrip('.').replace('—', '-').replace('–', '-')
    m = re.match(r'(?i)salmo\s+(\d+)(?:\s+([AB])\b)?\s*([,\s]\s*\d[\d\s\-.,ab]*?)?\s*(?:-\s*|\s)([^\d].*)?$', h)
    if m:
        num = m.group(1) + (f' {m.group(2).upper()}' if m.group(2) else ''); vv = (m.group(3) or '').strip(' ,')
        vv = re.sub(r'\s*-\s*', '-', re.sub(r'\s*\.\s*', '. ', vv)).strip()
        nombre = f'Salmo {num}' + (f', {vv}' if vv else '')
        ident = 'salmo-' + '-'.join(re.findall(r'\d+[ab]?|\b[AB]\b', num + ' ' + vv)).lower()
        return ident, nombre, (m.group(4) or '').strip(' -.')
    # cántico: referencia bíblica al final (libro con o sin punto; versículos que pasan de capítulo)
    m = re.search(r'([1-3]?\s?[A-ZÁÉÍÓÚ][a-záéíóú]{0,4})\.?\s+(\d+)\s*,\s*(\d[\d\s\-.,;ab]*)$', h)
    if m:
        libro = m.group(1).replace(' ', ''); cap = m.group(2)
        vv = re.sub(r'\s*-\s*', '-', re.sub(r'\s*\.\s*', '. ', re.sub(r'\s*,\s*', ', ', m.group(3)))).strip(' .,')
        sub = re.sub(r'(?i)^c[aá]ntico\s*:?\s*', '', h[:m.start()]).strip(' -.')
        ident = 'cantico-' + sin_tildes(libro).lower() + '-' + cap + '-' + '-'.join(re.findall(r'\d+[ab]?', vv))
        return ident, f'Cántico {libro} {cap}, {vv}', sub
    return None, h, ''


def ciclo(fecha):
    """Ciclo dominical A/B/C del año litúrgico que contiene la fecha."""
    d = date.fromisoformat(fecha)
    def adviento(y):
        n = date(y, 12, 25); return n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
    y = d.year if d >= adviento(d.year) else d.year - 1
    return 'ABC'[(y - 2016) % 3]


def dia_semana(fecha): return DIAS[date.fromisoformat(fecha).weekday()]


def preces(ls):
    """[intro, respuesta, a1, b1, a2, b2, …] → {'intro', 'respuesta', 'preces': [[a, b], …]}; si no encaja, renglones tal cual."""
    if not ls: return None
    if len(ls) >= 4 and len(ls) % 2 == 0:
        return {'intro': ls[0], 'respuesta': ls[1], 'preces': [[ls[i], ls[i + 1]] for i in range(2, len(ls), 2)]}
    return {'renglones': ls}


def partes(d, S):
    """Las partes del día, ya normalizadas (salmos citados por clave; S guarda los textos)."""
    p = {}
    if d.get('inv_ant'): p['inv_ant'] = d['inv_ant']
    if d.get('himno') and d['himno'].get('titulo'):
        t = d['himno']['titulo']
        pr = (d['himno']['texto'] or [''])[0].split('\n')[0].strip().rstrip('.,;:').strip()
        # título: el primer verso (sync lo trae en mayúsculas); si no hay texto, el título de sync
        p['himno'] = re.sub(r'^[¡¿]?(.*?)[!?]?$', lambda m: m.group(0), pr) if pr else (t[:1] + t[1:].lower() if t.isupper() else t)
        S('himno/' + p['himno'], d['himno']['texto'], d['fecha'])
    if d['salmodia'] and len(d['salmodia']) == 3:
        sal = []
        for g in d['salmodia']:
            ident, nombre, sub = id_salmo(g['salmo'] or '')
            if not ident: sal = None; break
            ident = ALIAS.get(ident, ident)
            est, _ = sin_gloria(g['texto'])
            S('salmo/' + ident, {'titulo': nombre, 'subtitulo': sub, 'texto': est}, d['fecha'])
            x = {'ant': g['ant'], 'salmo': ident}
            if g.get('ant_fin') and g['ant_fin'] != g['ant']: x['ant_fin'] = g['ant_fin']
            sal.append(x)
        if sal: p['salmodia'] = sal
    for k in ('lectura', 'responsorio', 'ant_benedictus', 'padrenuestro_intro', 'oracion'):
        if d.get(k): p[k] = d[k]
    if d.get('preces'): p['preces'] = preces(d['preces'])
    if d.get('_otros'):
        for h, ls in d['_otros']:
            if h.startswith('En lugar del responsorio') and ls: p['en_lugar_del_responsorio'] = ls[0]
    return p


def clave_tiempo(d):
    k = d['feria']
    if dia_semana(d['fecha']) == 'domingo': k += f' ({ciclo(d["fecha"])})'
    return k


ALIAS = {}
PENDIENTES = {}   # el IX Domingo del T. O. se completó a mano (11/2026) con el libro


def alias_salmos(todos):
    """«Salmo 5» sin versículos = «Salmo 5, 2-10. 12-13» si es el único con ese número."""
    ids = {id_salmo(g['salmo'] or '')[0] for d in todos for g in d['salmodia']} - {None}
    for i in ids:
        if re.fullmatch(r'salmo-\d+', i):
            largos = [x for x in ids if x.startswith(i + '-') and not re.fullmatch(r'salmo-\d+-[ab]', x)]
            if len(largos) == 1: ALIAS[i] = largos[0]


def importar(todos):
    alias_salmos(todos)
    S = Votos()          # textos compartidos: salmos, himnos, ordinario
    V = Votos()          # partes por capa
    dias = []
    for d in todos:
        p = partes(d, S)
        cel = d['celebracion'].get('nombre') if d['celebracion'].get('grado') else None
        dias.append((d, p, cel))
        if d.get('inv_texto'): S('invitatorio/salmo94', [e for e in d['inv_texto'] if not e.startswith('Gloria al Padre')], d['fecha'])
        if d.get('benedictus_texto'): S('benedictus', [e for e in d['benedictus_texto'] if not e.startswith('Gloria al Padre')], d['fecha'])
        if d.get('conclusion'): S('conclusion', d['conclusion'], d['fecha'])

    # 1) salterio: ferias del Tiempo Ordinario sin celebración
    for d, p, cel in dias:
        if cel or d['tiempo'] != 'Ordinario': continue
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
        for k in CAMPOS:
            if dia_semana(d['fecha']) == 'domingo' and k in ('ant_benedictus', 'oracion'): continue   # propios de cada domingo
            if k in p: V(f'salterio/{sk}/{k}', p[k], d['fecha'])
    sal = lambda sk, k: V.ganador(f'salterio/{sk}/{k}')

    # 2) tiempo: lo que difiere del salterio (por feria; en domingo, con ciclo)
    for d, p, cel in dias:
        if cel: continue
        if d['tiempo'] == 'Ordinario' and dia_semana(d['fecha']) != 'domingo': continue   # ferias del T. O.: todo del salterio
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"
        for k in CAMPOS + ['en_lugar_del_responsorio']:
            if k in p and p[k] != sal(sk, k): V(f'tiempo/{clave_tiempo(d)}/{k}', p[k], d['fecha'])
            elif k in p: V(f'tiempo/{clave_tiempo(d)}/{k}', '=', d['fecha'])   # igual al salterio
    def base_dia(d):
        sk = f"{d['salterio']}/{dia_semana(d['fecha'])}"; kt = clave_tiempo(d)
        def g(k):
            t = V.ganador(f'tiempo/{kt}/{k}')
            return sal(sk, k) if t in (None, '=') else t
        return g

    # 3) santoral: lo que difiere de salterio + tiempo, por celebración
    fechas_cel = collections.defaultdict(collections.Counter); info = {}
    for d, p, cel in dias:
        if not cel: continue
        g = base_dia(d)
        fechas_cel[cel][d['fecha'][5:]] += 1
        info.setdefault(cel, collections.Counter())[(d['celebracion']['grado'], d['celebracion'].get('comun', ''))] += 1
        for k in CAMPOS + ['en_lugar_del_responsorio']:
            if k in p and p[k] != g(k): V(f'santoral/{cel}/{k}', p[k], d['fecha'])
            elif k in p: V(f'santoral/{cel}/{k}', '=', d['fecha'])
    return S, V, dias, fechas_cel, info


def escribir_base(S, V, dias, fechas_cel, info):
    G = V.ganador
    # salterio
    salterio = {}
    for s in '1234':
        salterio[f'semana_{s}'] = {}
        for dia in DIAS[6:] + DIAS[:6]:
            e = {k: G(f'salterio/{s}/{dia}/{k}') for k in CAMPOS}
            salterio[f'semana_{s}'][dia] = {k: v for k, v in e.items() if v is not None}
    escribir(os.path.join(BASE, 'salterio', 'laudes.yaml'), salterio,
             'Salterio de Laudes: cuatro semanas (Tiempo Ordinario). Los salmos se citan por su clave (base/salmos/).\n'
             'En los domingos, la antífona del Benedictus y la oración son propias (base/tiempo/laudes.yaml).')

    def capa(pref):
        claves = collections.OrderedDict()
        for c in V.v:
            if c.startswith(pref):
                nombre, k = c[len(pref):].rsplit('/', 1)
                claves.setdefault(nombre, {})[k] = G(c)
        return claves

    # tiempo: quitar lo que coincide con el salterio; los domingos sin diferencia entre ciclos se juntan
    T = capa('tiempo/')
    tiempo = collections.OrderedDict()
    for nombre, e in T.items():
        e = {k: v for k, v in e.items() if v != '='}
        if e: tiempo[nombre] = e
    juntos = collections.defaultdict(dict)
    for nombre in list(tiempo):
        m = re.match(r'^(.*) \(([ABC])\)$', nombre)
        if m: juntos[m.group(1)][m.group(2)] = tiempo[nombre]
    for base_n, cs in juntos.items():
        campos = set().union(*cs.values())
        comunes = {k: cs[next(iter(cs))].get(k) for k in campos if len({json.dumps(c.get(k), ensure_ascii=False, sort_keys=True) for c in cs.values()}) == 1 and len(cs) == 3}
        if comunes:
            tiempo[base_n] = comunes
            for c in cs:
                resto = {k: v for k, v in tiempo[f'{base_n} ({c})'].items() if k not in comunes}
                if resto: tiempo[f'{base_n} ({c})'] = resto
                else: del tiempo[f'{base_n} ({c})']
    # orden litúrgico: días desde el comienzo del Adviento de cada año
    def desde_adviento(f):
        d = date.fromisoformat(f)
        def adv(y):
            n = date(y, 12, 25); return n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
        a = adv(d.year) if d >= adv(d.year) else adv(d.year - 1)
        return (d - a).days
    pos = {}
    for d, p, c in dias:
        if not c: pos[d['feria']] = min(pos.get(d['feria'], 999), desde_adviento(d['fecha']))
    orden_t = sorted(tiempo, key=lambda n: (pos.get(re.sub(r' \([ABC]\)$', '', n), 999), n))
    # días que sync no trae (siempre cayeron bajo una solemnidad entre 2015 y 2025): quedan marcados para completar a mano
    for n, nota in PENDIENTES.items():
        if n not in tiempo: tiempo[n] = {'pendiente': nota}; orden_t.append(n)
    escribir(os.path.join(BASE, 'tiempo', 'laudes.yaml'), {n: tiempo[n] for n in orden_t},
             'Propio del tiempo de Laudes: por feria (nombre del Ordo); en los domingos, «(A)», «(B)» o «(C)» cuando cambia con el ciclo.\n'
             'Solo figura lo que cambia respecto del salterio (base/salterio/laudes.yaml).')

    Sa = capa('santoral/')
    santoral = collections.OrderedDict()
    for nombre in sorted(Sa, key=lambda n: fechas_cel[n].most_common(1)[0][0]):
        e = {k: v for k, v in Sa[nombre].items() if v != '='}
        (grado, comun), _ = info[nombre].most_common(1)[0]
        fe = [f for f, _ in fechas_cel[nombre].most_common()]
        santoral[nombre] = {'grado': grado, 'fecha': fe[0] if len(fe) == 1 or fechas_cel[nombre][fe[0]] > sum(fechas_cel[nombre].values()) / 2 else 'variable',
                            **({'comun': comun} if comun else {}), **e}
    escribir(os.path.join(BASE, 'santoral', 'laudes.yaml'), dict(santoral),
             'Santoral de Laudes (calendario de sync, a revisar con el calendario ADF): por celebración.\n'
             'Solo figura lo que cambia respecto del salterio y del tiempo; «fecha: variable» = celebración movible.')

    # himnos de Laudes
    himnos = {}
    for c in sorted(S.v):
        if c.startswith('himno/'): himnos[c[6:]] = S.ganador(c)
    escribir(os.path.join(BASE, 'himnos', 'laudes.yaml'), himnos, 'Himnos de Laudes en español, por título.')

    # ordinario de Laudes
    concl = S.ganador('conclusion')
    escribir(os.path.join(BASE, 'ordinario', 'laudes.yaml'), {
        'nombre': 'Laudes', 'subtitulo': 'Oración de la mañana',
        'invitatorio': {'V': 'Señor, abre mis labios.', 'R': 'Y mi boca proclamará tu alabanza.',
                        'salmo': {'titulo': 'Salmo 94', 'subtitulo': 'INVITACIÓN A LA ALABANZA DIVINA', 'texto': S.ganador('invitatorio/salmo94')}},
        'cantico_evangelico': {'titulo': 'Cántico de Zacarías', 'subtitulo': 'EL MESÍAS Y SU PRECURSOR', 'ref': 'Lc 1, 68-79', 'texto': S.ganador('benedictus')},
        'conclusion': [{(a or 'texto'): b} for a, b in concl] if concl else None,
    }, 'Ordinario de Laudes: invitatorio (solo los domingos), Benedictus en español (referencia; se reza en latín, Neovulgata) y conclusión.')

    # salmos y cánticos que usa Laudes (los de Completas no se tocan)
    nuevos = 0
    for c in S.v:
        if c.startswith('salmo/'):
            ruta = os.path.join(BASE, 'salmos', c.split('/', 1)[1] + '.yaml')
            if os.path.exists(ruta): continue
            x = S.ganador(c); nuevos += 1
            escribir(ruta, x, f"{x['titulo']}. Texto de la Liturgia de las Horas en español; estrofas separadas por renglón en blanco.")
    return len(tiempo), len(santoral), len(himnos), nuevos


def informe(S, V, todos):
    L_ = ['# Laudes: variantes encontradas en sync', '',
          f'Se leyeron {len(todos)} Laudes ({todos[0]["fecha"]} a {todos[-1]["fecha"]}). Para cada texto quedó en la base la versión más frecuente. '
          'Abajo, las demás versiones con cuántas veces aparecen y algunas fechas, para revisarlas.', '']
    for W in (V, S):
        for clave, vs in W.variantes():
            if clave.startswith('himno/'): continue
            vs = [(v, f) for v, f in vs if v != '=']
            if len(vs) < 2: continue
            L_.append(f'## {clave}')
            for i, (val, fechas) in enumerate(vs[:6]):
                muestra = json.dumps(val, ensure_ascii=False)
                if len(muestra) > 240: muestra = muestra[:240] + '…'
                L_.append(f'- {"**en la base**" if i == 0 else "variante"} · {len(fechas)} veces · {", ".join(fechas[:4])}{"…" if len(fechas) > 4 else ""}')
                if i: L_.append(f'  `{muestra}`')
            L_.append('')
    open(os.path.join(BASE, 'informes', 'laudes.md'), 'w', encoding='utf-8').write(_aleluia('\n'.join(L_)))


if __name__ == '__main__':
    cache = '/tmp/laudes_sync.json'
    if os.environ.get('CACHE') and os.path.exists(cache):
        todos = json.load(open(cache))
    else:
        todos = cargar(); json.dump(todos, open(cache, 'w'), ensure_ascii=False)
    S, V, dias, fc, info = importar(todos)
    nt, ns, nh, nsal = escribir_base(S, V, dias, fc, info)
    informe(S, V, todos)
    print(f'{len(todos)} Laudes leídas; tiempo: {nt} ferias con propio; santoral: {ns} celebraciones; {nh} himnos; {nsal} salmos/cánticos nuevos')
