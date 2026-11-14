"""Pasa los Oficios comunes de la extracción del libro a `base/comunes/`.

    python3 extraccion/a_base_comunes.py

Reemplaza los comunes que se habían cargado a mano del libro (tools/importar/comunes_libro.py, desde el texto del
tomo III), que arrastraban rúbricas pegadas a los textos y erratas, por la extracción limpia de los cuatro tomos.
Escribe `base/comunes/{laudes,visperas,oficio,intermedia}.yaml` con el mismo formato que usa la app, y agrega a
`base/himnos/` y `base/salmos/` los himnos y salmos de los comunes que la base no tenía.

Cómo elige entre las variantes del libro:
- La principal: la que no tiene condición; si hay varias opciones sin otra condición («O bien:»), la que coincide
  con lo que ya tenía la base (que estaba revisado) o, si no, la primera.
- Oraciones: todas, con su «para» («un santo obispo», «varias santas vírgenes»): la app elige por el nombre.
- Tiempo pascual: en `pascua`, con los mismos campos (la app lo usa en Pascua).
- Tiempo pascual: además, donde el libro marca «(T. P. Aleluya.)», la antífona o el versículo con «Aleluia» al final.
- Las otras opciones para el mismo caso («O bien:», «O bien esta otra:»): en `opciones`; la app las alterna de una
  celebración a la siguiente que use el mismo común.
- Las demás («Para un santo presbítero:», «En tiempo de cuaresma:»): en `variantes`, con su etiqueta, para no perder
  nada (la app todavía no las usa).
- I Vísperas: en `primeras`, dentro de visperas.yaml (la app ya las usa).
- Los comunes que el libro da «todo como en el común de santos varones, o de santas mujeres, excepto…» (religiosos,
  caridad, educadores) y el de doctores (que remite al de pastores) guardan solo lo propio y dicen de cuál heredan
  (`hereda`, y `hereda_mujeres` para las santas): la app completa el resto.
- «aleluya» → «aleluia», como escribe ADF.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
BASE = REPO / 'base'
sys.path.insert(0, str(REPO / 'tools' / 'importar'))
from yaml_base import escribir, leer  # noqa: E402

# clave en la extracción → clave en la base (la que usan base/santoral/adf.yaml y la app)
CLAVE = {'dedicacion': 'dedicacion', 'virgen': 'virgen-maria', 'santa-maria-sabado': 'santa-maria-sabado',
         'apostoles': 'apostoles', 'martires-varios': 'varios-martires', 'martires-uno': 'un-martir',
         'pastores': 'pastores', 'doctores': 'doctores', 'virgenes': 'virgenes', 'santos-varones': 'santos-varones',
         'santas-mujeres': 'santas-mujeres', 'religiosos': 'religiosos', 'caridad': 'caridad',
         'educadores': 'educadores'}
NOMBRE = {'dedicacion': 'Común de la dedicación de una iglesia', 'virgen-maria': 'Común de la Santísima Virgen María',
          'santa-maria-sabado': 'Memoria de santa María en sábado', 'apostoles': 'Común de apóstoles',
          'varios-martires': 'Común de mártires: para varios mártires', 'un-martir': 'Común de mártires: para un mártir',
          'pastores': 'Común de pastores', 'doctores': 'Común de doctores de la Iglesia',
          'virgenes': 'Común de vírgenes', 'santos-varones': 'Común de santos varones',
          'santas-mujeres': 'Común de santas mujeres',
          'religiosos': 'Común de santos varones o de santas mujeres: para religiosos',
          'caridad': 'Común de santos varones o de santas mujeres: para los que se han consagrado a una actividad caritativa',
          'educadores': 'Común de santos varones o de santas mujeres: para educadores'}
HEREDA = {'doctores': ('pastores', None), 'religiosos': ('santos-varones', 'santas-mujeres'),
          'caridad': ('santos-varones', 'santas-mujeres'), 'educadores': ('santos-varones', 'santas-mujeres')}
ORDEN = ['dedicacion', 'virgen-maria', 'santa-maria-sabado', 'apostoles', 'varios-martires', 'un-martir', 'pastores',
         'doctores', 'virgenes', 'santos-varones', 'santas-mujeres', 'religiosos', 'caridad', 'educadores']


def sin_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def fuerte(s):
    return re.sub(r'[^a-z0-9 ]', '', sin_tildes(str(s or '')).lower()).strip()


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', sin_tildes(str(s)).lower()).strip('-')


def aleluia(x):
    if isinstance(x, str):
        x = re.sub(r'(?i)(alel)uya', lambda m: m.group(1) + ('IA' if m.group(0).isupper() else 'uia'), x)
        x = re.sub(r'\{N\}\.?', 'N.', x)          # la extracción marca el nombre como {N}; la base, como el libro: N.
        return re.sub(r'\.\.$', '.', x)
    if isinstance(x, list):
        return [aleluia(v) for v in x]
    if isinstance(x, dict):
        return {k: aleluia(v) for k, v in x.items()}
    return x


# ─────────────── bibliotecas ───────────────

SAL_BASE = {p.stem for p in (BASE / 'salmos').glob('*.yaml')}
SAL_LIBRO = {}
for f in sorted(AQUI.glob('**/salmos.json')):
    for s in json.loads(f.read_text(encoding='utf-8')):
        SAL_LIBRO.setdefault(s['id'], s)
HIM_LIBRO = {}
for f in sorted(AQUI.glob('**/himnos.json')):
    for h in json.loads(f.read_text(encoding='utf-8')):
        HIM_LIBRO.setdefault(h['id'], h)
HIM_BASE = {h: leer(BASE / 'himnos' / f'{h}.yaml') or {} for h in ('laudes', 'visperas', 'oficio')}
HIM_NUEVOS = {h: {} for h in HIM_BASE}
SAL_NUEVOS = {}
AVISOS = []


def estrofas_salmo(s, parte=None):
    partes = [p for p in s['partes'] if parte is None or str(p.get('numero')) == str(parte)] or s['partes']
    return ['\n'.join(v['texto'] for v in e) for p in partes for e in p['estrofas']]


# las claves de la base que no son la de la extracción: emparejadas por el texto
POR_TEXTO = {}
for k in SAL_BASE:
    b = leer(BASE / 'salmos' / f'{k}.yaml') or {}
    POR_TEXTO.setdefault(fuerte(' '.join(b.get('texto') or []))[:300], k)


ALIAS_SAL = {'cantico-cf-ap-19-1-7': 'cantico-ap-19-1-2-5-7'}   # el cántico de las II Vísperas del domingo


def salmo(sid, parte):
    """La clave de la base para el salmo (y la parte) del libro; si la base no lo tiene, se agrega."""
    if sid in ALIAS_SAL:
        return ALIAS_SAL[sid]
    sid2 = re.sub(r'-(\d)-([a-z]{1,3})-', r'-\1\2-', sid)    # «cantico-1-pe-…» = «cantico-1pe-…»
    if not parte and sid2 in SAL_BASE:
        return sid2
    cand = f'{sid}-{str(parte).lower()}' if parte else sid
    if cand in SAL_BASE:
        return cand
    s = SAL_LIBRO.get(sid)
    if s is None:
        AVISOS.append(f'salmo {sid} {parte or ""}: no está ni en la base ni en el libro')
        return cand
    k = POR_TEXTO.get(fuerte(' '.join(estrofas_salmo(s, parte)))[:300])
    if k:
        return k
    if not parte and sid in SAL_BASE:
        return sid
    SAL_NUEVOS[cand] = ((s.get('cita') or sid) + (f' {parte}' if parte else ''),
                        {'subtitulo': s.get('titulo'), 'texto': aleluia(estrofas_salmo(s, parte))})
    return cand


def titulo_himno(h):
    return re.sub(r'[\s,;:.]+$', '', h.get('primer_verso') or h['id'])


def himno(hid, hora):
    """El título con que la base nombra el himno; si no lo tiene en esa hora, lo agrega."""
    h = HIM_LIBRO.get(hid)
    if h is None:
        AVISOS.append(f'himno {hid}: no está en la extracción')
        return None
    tit = titulo_himno(h)
    for t in HIM_BASE[hora]:
        if slug(t) == slug(tit):
            return t
    for otra, d in HIM_BASE.items():
        for t, est in d.items():
            if slug(t) == slug(tit):
                HIM_NUEVOS[hora][t] = est
                return t
    est = ['\n'.join(v['texto'] for v in e) for e in h['estrofas']]
    if h.get('amen') and est:
        est[-1] += '\nAmén.'
    HIM_NUEVOS[hora][tit] = aleluia(est)
    return tit


# ─────────────── variantes ───────────────

def principal(variantes, previo=None, campo=None):
    """(la variante principal, las de tiempo pascual, las demás)."""
    sin = [v for v in variantes if not v.get('cuando') or set(v['cuando']) == {'opcion'}]
    pas = [v for v in variantes if (v.get('cuando') or {}).get('tiempo') == 'pascua' and set(v['cuando']) <= {'tiempo', 'opcion'}]
    elegida = None
    if previo is not None and campo:
        fp = fuerte(json.dumps(previo, ensure_ascii=False))
        for v in sin:
            if fuerte(json.dumps(campo(v), ensure_ascii=False)) == fp:
                elegida = v
                break
    if elegida is None:
        elegida = sin[0] if sin else (variantes[0] if variantes and not pas else None)
    resto = [v for v in variantes if v is not elegida and v not in pas]
    return elegida, (pas[0] if pas else None), resto


def etiqueta(v):
    e = (v.get('etiqueta') or '').strip()
    if not e and v.get('cuando'):
        e = ', '.join(f'{k}: {x}' for k, x in v['cuando'].items())
    return e


def es_opcion(etiqueta):
    """«O bien:», «O bien esta otra:», «I», «II», o una opción sin etiqueta: otra opción para el mismo caso (la app las
    alterna de una celebración a la siguiente). «Para un santo presbítero:», «En tiempo de cuaresma:», no."""
    e = (etiqueta or '').strip().lower()
    if re.search(r'\bpara\b|tiempo|cuaresma|adviento|navidad|pascua|region|iglesia|oficio', e):
        return False
    return bool(re.match(r'^(o bien|i+:?$|otra)', e))


def repartir(k, resto, var, opc):
    """Las demás variantes de un campo: las opciones van a «opciones» (se alternan) y el resto a «variantes»."""
    o = [x for e, x in resto if es_opcion(e)]
    v = [{'etiqueta': e, 'texto': x} for e, x in resto if not es_opcion(e)]
    if o:
        opc[k] = o
    if v:
        var[k] = v


def vr(pares):
    return [[a, b] for a, b in pares if b]


def rotulo(x, defecto):
    return (x.get('rotulo') or x.get('quien') or defecto).strip('. ') or defecto


def rb(v):
    """Responsorio breve → [[V, …], [R, …], …] como en la base."""
    if v.get('secuencia'):
        return [[rotulo(x, 'V'), x['texto']] for x in v['secuencia']]
    out = vr([('V', v.get('v1')), ('R', v.get('r1')), ('V', v.get('v2')), ('R', v.get('r2'))])
    if v.get('gloria', True):
        out += [['V', 'Gloria al Padre, y al Hijo, y al Espíritu Santo.'], ['R', v.get('r1')]]
    return out


def versiculo(v):
    if v.get('secuencia'):
        return [[rotulo(x, 'V'), x['texto']] for x in v['secuencia']]
    return vr([('V', v.get('v')), ('R', v.get('r'))])


def lectura_breve(v):
    return {'ref': v.get('cita'), 'texto': v.get('texto')}


def preces(v):
    return {'intro': v.get('introduccion'), 'respuesta': ' / '.join(r['texto'] for r in v.get('respuesta') or []),
            'preces': [[i['primera'], i['segunda']] if i.get('segunda') else [i['primera']] for i in v.get('intenciones') or []]}


def lectura_larga(v, segunda=False):
    out = {'titulo': v.get('titulo')}
    texto = '\n\n'.join(v.get('parrafos') or [])
    if segunda:
        out['texto'] = texto
        out['autor'] = '\n'.join(x for x in (v.get('encabezado'), v.get('fuente')) if x)
    else:
        out['texto'] = texto
        out['ref'] = ' '.join(x for x in (v.get('encabezado'), v.get('cita')) if x)
    return out


def responsorio(v):
    if v.get('secuencia'):
        pares = [[rotulo(x, 'R'), x['texto']] for x in v['secuencia']]
    else:
        r = v.get('r') or []
        pares = ([['R', ' * '.join(r)]] if r else []) + ([['V', v['v']]] if v.get('v') else []) + ([['R', r[-1][:1].upper() + r[-1][1:]]] if len(r) > 1 else [])
    return {'ref': v.get('cita'), 'vr': pares}


# ─────────────── una hora ───────────────

def piezas(hora, parte, tipo=None):
    for p in hora or []:
        if p['parte'] == parte:
            for pz in p['piezas']:
                if tipo is None or pz['tipo'] == tipo:
                    yield pz


def con_aleluia(t):
    """«(T. P. Aleluya.)»: en el tiempo pascual, la antífona (o el versículo) termina con «Aleluia»."""
    if not t or re.search(r'aleluia\W*$', t, re.I):
        return t
    return t.rstrip() + ' Aleluia.'


def tp(v):
    """La variante en su forma pascual, si el libro la marca «T. P. Aleluya.»; si no, None."""
    if not v or not v.get('tp_aleluya'):
        return None
    w = dict(v)
    for k in ('texto', 'v', 'r'):
        if isinstance(w.get(k), str):
            w[k] = con_aleluia(w[k])
    return w


def campo(hora, parte, tipo, conv, previo=None):
    """(principal, pascua, [demás]) ya convertidos, para la primera pieza de ese tipo en esa parte."""
    pz = next(piezas(hora, parte, tipo), None)
    if pz is None:
        return None, None, []
    p, pas, resto = principal(pz['variantes'], previo, conv)
    pas = pas or tp(p)
    return (conv(p) if p else None), (conv(pas) if pas else None), [(etiqueta(v), conv(v)) for v in resto]


def salmodia(hora, h_libro, nombre_hora, previo=None):
    """Antífonas y salmos. Si el libro remite al salterio (Laudes: «del domingo de la I semana»), los salmos de ahí."""
    ants, sals, remite = [], [], None
    for pz in piezas(hora, 'salmodia'):
        if pz['tipo'] == 'antifona':
            p, pas, resto = principal(pz['variantes'])
            ants.append((p, pas))
        elif pz['tipo'] == 'salmo':
            v = principal(pz['variantes'])[0] or pz['variantes'][0]
            k = salmo(v['salmo'], v.get('parte'))
            if not (sals and sals[-1] == k):    # el mismo salmo repetido con su alternativa (p. ej. la de Cuaresma)
                sals.append(k)
        elif pz['tipo'] == 'rubrica':
            for v in pz['variantes']:
                if isinstance(v.get('remite'), str) and v['remite'].startswith('salterio/'):
                    remite = v['remite']
    if not sals and remite:
        m = re.match(r'salterio/semana-(\d)/(\w+)/(\w+)/salmodia', remite)
        if m:
            sv = leer(BASE / 'salterio' / f'{m.group(3)}.yaml') or {}
            sals = [g['salmo'] for g in ((sv.get(f'semana_{m.group(1)}') or {}).get(m.group(2)) or {}).get('salmodia') or []]
    if not ants and not sals:
        return None, None
    if len(ants) != len(sals) and sals:
        AVISOS.append(f'{nombre_hora}: {len(ants)} antífonas y {len(sals)} salmos')
    out = [{'ant': a[0].get('texto') if a[0] else None, 'salmo': s} for a, s in zip(ants + [(None, None)] * 9, sals)]
    pas = None
    if any(a[1] or tp(a[0]) for a in ants):
        pas = [{'ant': (a[1] or tp(a[0]) or a[0] or {}).get('texto'), 'salmo': s} for a, s in zip(ants, sals)]
    return out, pas


def oraciones(hora):
    out = []
    for pz in piezas(hora, 'oracion', 'oracion'):
        for v in pz['variantes']:
            e = (v.get('etiqueta') or '').strip().rstrip(':')
            e = re.sub(r'^(o bien( esta otra)?|para)\s*,?\s*', '', e, flags=re.I).strip()
            e = re.sub(r'^(esta otra,?\s*)?(especialmente\s+)?para\s+', '', e, flags=re.I)
            out.append({'para': e, 'texto': v.get('texto')})
    return out


def hora_comun(H, nombre, previo, es_visperas=False, es_oficio=False):
    """Una hora del común en el formato de la base. previo: lo que tenía la base (para elegir entre opciones)."""
    out, pas, var, opc = {}, {}, {}, {}

    def poner(k, trio):
        p, ps, resto = trio
        if p is not None:
            out[k] = p
        if ps is not None:
            pas[k] = ps
        if resto:
            repartir(k, resto, var, opc)

    pz = next(piezas(H, 'himno', 'himno'), None)
    if pz:
        p, ps, resto = principal(pz['variantes'])
        if p and p.get('himno'):
            out['himno'] = himno(p['himno'], 'oficio' if es_oficio else ('visperas' if es_visperas else 'laudes'))
        if resto:
            hora_h = 'oficio' if es_oficio else ('visperas' if es_visperas else 'laudes')
            repartir('himno', [(etiqueta(v), himno(v['himno'], hora_h)) for v in resto if v.get('himno')], var, opc)
    sal, sal_p = salmodia(H, None, nombre)
    if sal:
        out['salmodia'] = sal
    if sal_p:
        pas['salmodia'] = sal_p
    if es_oficio:
        poner('versiculo', campo(H, 'versiculo', 'versiculo', versiculo, previo.get('versiculo')))
        poner('lectura1', campo(H, 'primera_lectura', 'lectura', lectura_larga))
        poner('resp1', campo(H, 'primera_lectura', 'responsorio', responsorio))
        poner('lectura2', campo(H, 'segunda_lectura', 'lectura', lambda v: lectura_larga(v, True)))
        poner('resp2', campo(H, 'segunda_lectura', 'responsorio', responsorio))
    else:
        poner('lectura', campo(H, 'lectura_breve', 'lectura_breve', lectura_breve, previo.get('lectura')))
        poner('responsorio', campo(H, 'responsorio_breve', 'responsorio_breve', rb, previo.get('responsorio')))
        ant = 'ant_magnificat' if es_visperas else 'ant_benedictus'
        poner(ant, campo(H, 'cantico_evangelico', 'antifona', lambda v: v.get('texto'), previo.get(ant)))
        pr = campo(H, 'preces', 'preces', lambda v: v)
        if pr[0]:
            out['preces'] = preces(pr[0])
            if pr[0].get('final'):
                out['padrenuestro_intro'] = re.sub(r'\s*Padre nuestro\.?\s*$', '', pr[0]['final'])
        if pr[2]:
            repartir('preces', [(e, preces(x)) for e, x in pr[2]], var, opc)
    o = oraciones(H)
    if o:
        out['oraciones'] = o
    if opc:
        out['opciones'] = opc
    if pas:
        out['pascua'] = pas
    if var:
        out['variantes'] = var
    return out


def intermedia(C, previo):
    out = {}
    for h in ('tercia', 'sexta', 'nona'):
        H = C['horas'].get(h)
        if not H:
            continue
        d, pas, var, opc = {}, {}, {}, {}
        lb = campo(H, 'lectura_breve', 'lectura_breve', lectura_breve, (previo.get(h) or {}).get('lectura'))
        an = next((pz for pz in piezas(H, 'salmodia', 'antifona')), None) or next(piezas(H, 'antifona', 'antifona'), None)
        ve = campo(H, 'versiculo', 'versiculo', versiculo, (previo.get(h) or {}).get('versiculo'))
        if lb[0]:
            d['lectura'] = lb[0]
        if an:
            p, ps, resto = principal(an['variantes'])
            if p:
                d['ant'] = p.get('texto')
            ps = ps or tp(p)
            if ps:
                pas['ant'] = ps.get('texto')
        if ve[0]:
            d['versiculo'] = ve[0]
        for k, t in (('lectura', lb), ('versiculo', ve)):
            if t[1]:
                pas[k] = t[1]
            if t[2]:
                repartir(k, t[2], var, opc)
        if opc:
            d['opciones'] = opc
        if pas:
            d['pascua'] = pas
        if var:
            d['variantes'] = var
        if d:
            out[h] = d
    return out


def guardar_bibliotecas():
    """Agrega a base/himnos/ los himnos nuevos (al final del archivo, sin tocar lo que ya estaba) y a base/salmos/ los salmos."""
    import tempfile
    for h, nuevos in HIM_NUEVOS.items():
        if nuevos:
            tmp = Path(tempfile.mkdtemp()) / 'h.yaml'
            escribir(tmp, aleluia(nuevos), 'Himnos del libro que la base no tenía (extracción del libro).')
            p = BASE / 'himnos' / f'{h}.yaml'
            p.write_text(p.read_text(encoding='utf-8').rstrip('\n') + '\n' + tmp.read_text(encoding='utf-8'), encoding='utf-8')
            HIM_BASE[h].update(nuevos)
            nuevos.clear()
    for k, (tit, s) in list(SAL_NUEVOS.items()):
        escribir(BASE / 'salmos' / f'{k}.yaml', s, f'{tit}. Texto de la Liturgia de las Horas en español (extracción del libro).')
        SAL_BASE.add(k)
    SAL_NUEVOS.clear()


def main():
    d = json.loads((AQUI / 'comunes' / 'comunes.json').read_text(encoding='utf-8'))
    previos = {h: leer(BASE / 'comunes' / f'{h}.yaml') or {} for h in ('laudes', 'visperas', 'oficio', 'intermedia')}
    salida = {h: {} for h in previos}
    for C in d['comunes']:
        k = CLAVE[C['id']]
        cab = {'nombre': NOMBRE[k]}
        if k in HEREDA:
            cab['hereda'] = HEREDA[k][0]
            if HEREDA[k][1]:
                cab['hereda_mujeres'] = HEREDA[k][1]
        hs = C['horas']
        pv = lambda h: previos[h].get(k) or {}
        L = hora_comun(hs.get('laudes'), f'{k}/laudes', pv('laudes'))
        inv = next(piezas(hs.get('invitatorio'), 'antifona', 'antifona'), None)
        if inv:
            p, ps, _ = principal(inv['variantes'])
            if p:
                L['inv_ant'] = p['texto']
            ps = ps or tp(p)
            if ps:
                L.setdefault('pascua', {})['inv_ant'] = ps['texto']
        if L:
            salida['laudes'][k] = {**cab, **L}
        V2 = hs.get('visperas2') or hs.get('visperas')
        if V2:
            V = hora_comun(V2, f'{k}/visperas', pv('visperas'), es_visperas=True)
            if hs.get('visperas1'):
                V1 = hora_comun(hs['visperas1'], f'{k}/visperas1', pv('visperas').get('primeras') or {}, es_visperas=True)
                # «HIMNO, como en las II Vísperas»: lo que el libro no repite, se toma de las II
                V1.pop('himno', None)
                if V1:
                    V['primeras'] = V1
            salida['visperas'][k] = {**cab, **V}
        if hs.get('oficio'):
            salida['oficio'][k] = {**cab, **hora_comun(hs['oficio'], f'{k}/oficio', pv('oficio'), es_oficio=True)}
        I = intermedia(C, pv('intermedia'))
        if I:
            salida['intermedia'][k] = {**cab, **I}
    cabecera = ('Comunes de {h}, de la extracción del libro (los cuatro tomos; extraccion/a_base_comunes.py).\n'
                'Se usan para las celebraciones sin textos propios en la base (base/santoral/adf.yaml) y para lo que les falte.\n'
                '«oraciones»: con N. en lugar del nombre; «para» dice a quién corresponde cada una (la app elige por el nombre).\n'
                '«pascua»: lo que cambia en el tiempo pascual. «variantes»: las otras opciones del libro, con su etiqueta.\n'
                '«hereda» (y «hereda_mujeres», para las santas): el común del que se toma lo que este no trae.\n'
                'Desde ahora la base es la fuente: se corrige acá.')
    for h, datos in salida.items():
        orden = {k: datos[k] for k in ORDEN if k in datos}
        escribir(BASE / 'comunes' / f'{h}.yaml', aleluia(orden), cabecera.format(h=h))
    print('comunes:', {h: len(x) for h, x in salida.items()})
    print('himnos agregados:', {h: len(x) for h, x in HIM_NUEVOS.items()}, '· salmos agregados:', sorted(SAL_NUEVOS))
    for a in AVISOS:
        print('aviso:', a)
    guardar_bibliotecas()


if __name__ == '__main__':
    main()
