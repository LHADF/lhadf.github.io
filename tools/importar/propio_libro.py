"""Propio de los santos desde el libro (Liturgia de las Horas, los cuatro tomos en texto) → base/santoral/libro.yaml.

Para las celebraciones que la base no trae (base/santoral/adf.yaml: propias de ADF y memorias libres): la oración propia
y lo que el libro tenga de propio (segunda lectura del Oficio, antífonas, himnos, a veces el oficio entero). Lo que falte
sale del común. Se corre una sola vez; después se corrige en la base.

    python3 tools/importar/propio_libro.py lh.txt
"""
import csv, difflib, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
import libro_lh as LB
from yaml_base import leer, escribir

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
B = os.path.join(RAIZ, 'base')
ORDO = os.environ.get('ORDO') or os.path.join(RAIZ, '..', 'lucasfelixjhs', 'ordo-telegram')
sys.path.insert(0, ORDO)
from importar_horas import id_v
from comunes_libro import aleluia

# Propio de los santos de cada tomo (renglones del texto de pdftotext -layout)
TOMOS = ((38832, 43100), (115986, 126561), (199083, 212802), (287155, 305925))
MES = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
NO_ENC = set(MES) | {'tercia', 'sexta', 'nona'}
CLAVE = re.compile(r'^(HIMNO|SALMODIA|LECTURA|RESPONSORIO|CÁNTICO|PRECES|PRIMERA|SEGUNDA|INVITATORIO|ORACIÓN)')
COMUNES = {'Común de la dedicación': 'dedicacion', 'Común de santa María': 'virgen-maria', 'Común de la Santísima Virgen': 'virgen-maria',
           'Común de apóstoles': 'apostoles', 'Común de varios mártires': 'varios-martires', 'Común de mártires: para varios': 'varios-martires',
           'Común de un mártir': 'un-martir', 'Común de mártires: para un': 'un-martir', 'Común de pastores': 'pastores',
           'Común de doctores': 'doctores', 'Común de vírgenes': 'virgenes', 'Común de santos varones': 'santos-varones',
           'Común de santas mujeres': 'santas-mujeres'}

norm = lambda s: re.sub(r'[^a-z ]', ' ', unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode())
COMUNES_NOMBRE = {'san', 'santa', 'santo', 'santos', 'santas', 'beato', 'beata', 'de', 'la', 'el', 'y', 'del', 'los', 'las', 'e',
                  'bienaventurada', 'virgen', 'senor', 'obispo', 'presbitero', 'martir', 'martires', 'papa', 'doctor', 'doctora',
                  'iglesia', 'religioso', 'religiosa', 'nuestra', 'nuestro', 'abad', 'diacono', 'rey', 'reina', 'companeros', 'patrona', 'patrono',
                  # nombres de pila frecuentes: no alcanzan para identificar a un santo
                  'juan', 'pedro', 'maria', 'jose', 'luis', 'francisco', 'antonio', 'pablo', 'teresa', 'catalina', 'isabel'}
tok = lambda s: [w for w in norm(s.split('(')[0]).split() if w not in COMUNES_NOMBRE and len(w) > 2]


def parecido(a, b):
    """Fracción de las palabras distintivas de `a` que tienen una parecida en `b` (tolera grafías: Mérici/Médici)."""
    A, Bb = tok(a), tok(b)
    if not A or not Bb: return 0
    return sum(1 for x in A if any(difflib.SequenceMatcher(None, x, y).ratio() >= .72 for y in Bb)) / len(A)


def entradas(L):
    """Celebraciones del Propio de los santos: [{fecha, nombre, ini, fin}] (fin: comienzo de la siguiente)."""
    out = []
    for a, b in TOMOS:
        fecha, prev = None, ''
        for i in range(a - 1, b - 1):
            s = L[i].strip()
            m = re.match(r'^(?:El mismo día\s+)?(\d{1,2}) de ([a-z]+)$', s)
            if m and m.group(2) in MES: fecha = f'{MES.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}'; prev = 'fecha'; continue
            if re.match(r'^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\b.*\b(Pentecostés|Pascua)$', s): fecha = 'movible'; prev = 'fecha'; continue
            if s and not LB.es_basura(L[i]): antes, prev = prev, 'txt'    # pasa a 'enc' solo si de verdad es un encabezado
            else: continue
            # el renglón que sigue a la fecha es siempre el nombre, aunque no esté en mayúsculas («Nuestra Señora de…»)
            if antes == 'fecha' and not s.isupper() and LB.centrado(L[i]):
                out.append({'fecha': fecha, 'nombre': s.upper(), 'ini': i + 1, 'fin': i + 1}); prev = 'enc'; continue
            # un encabezado de celebración va justo después de la fecha (o sigue a otro renglón del mismo nombre)
            if antes not in ('fecha', 'enc'): continue
            if not fecha or not s or not s.isupper() or len(s) < 6 or CLAVE.match(s) or 'LITURGIA DE LAS HORAS' in s or s.lower() in NO_ENC: continue
            if re.match(r'^[«(]', s): continue
            prev = 'enc'
            if antes == 'enc' and out and out[-1]['fecha'] == fecha:      # nombre en dos renglones
                out[-1]['nombre'] += ' ' + s; out[-1]['fin'] = i + 1; continue
            out.append({'fecha': fecha, 'nombre': s, 'ini': i + 1, 'fin': i + 1})
    for k, e in enumerate(out):
        fin_tomo = next(b for a, b in TOMOS if a <= e['ini'] < b)   # la última de cada tomo termina donde empiezan los comunes
        e['hasta'] = min(out[k + 1]['ini'] if k + 1 < len(out) and out[k + 1]['ini'] > e['ini'] else fin_tomo, fin_tomo)
    return out


ALIAS = {'salmo-39-2-13': 'salmo-39-2-14-17-18-i'}   # el mismo texto, con otra referencia
HIMNOS = {}   # himnos propios que aparezcan, por hora


def leer_entrada(L, e):
    """Partes propias de una celebración del libro."""
    ls = LB.limpiar(L, e['fin'] + 1, e['hasta'])
    pre = []
    for l in ls:
        if LB.hora_de(l): break
        pre.append(l)
    txt = LB.unir(pre)
    comun = next((v for k, v in COMUNES.items() if k.lower() in txt.lower()), None)
    d = {'nombre_libro': e['nombre'].title(), 'comun_libro': comun}
    m = re.search(r'(Del [Cc]omún[^.]*\.)', txt)
    if m: d['indicacion'] = m.group(1)
    for h, blk in LB.partir_horas(ls):
        if not h: continue
        x = LB.hora(h, blk, id_v)
        for g in x.get('salmodia', []):
            g.pop('_h', None)
            if g['salmo'] and g['salmo'] not in SAL and g['salmo'] + '-i' in SAL: g['salmo'] += '-i'   # «Salmo 49» con su «I» más abajo
            g['salmo'] = ALIAS.get(g['salmo'], g['salmo'])
        if x.get('himno') and x.get('_himno_texto'): HIMNOS.setdefault({'visperas1': 'visperas'}.get(h, h), {})[x['himno']] = x['_himno_texto']
        x.pop('_himno_texto', None)
        ors = x.pop('oraciones', None)
        if ors and 'oracion' not in d: d['oracion'] = ors[0]['texto']
        if x: d.setdefault(h, {}).update(x)
    # la oración suele ir al final de la entrada, fuera de las horas
    if 'oracion' not in d:
        C = LB.partir_claves(ls)
        if 'Oración' in C:
            o = LB.oraciones(C['Oración'])
            if o: d['oracion'] = o[0]['texto']
    return d


SAL = {f[:-5] for f in os.listdir(os.path.join(B, 'salmos'))}


def main(txt):
    L = open(txt, encoding='utf-8').read().split('\n')
    E = entradas(L)
    A = leer(os.path.join(B, 'santoral', 'adf.yaml'))
    fechas = {}
    for r in csv.DictReader(open(os.path.join(ORDO, 'data', 'santoral.csv'), encoding='utf-8')):
        fechas[r['nombre'].strip() + (', ' + r['titulo'].strip() if r['titulo'].strip() else '')] = r['fecha']
    out, sin = {}, []
    for n, a in A.items():
        if a.get('es') or a.get('como'): continue
        f = fechas.get(n)
        def cerca(x):   # la misma fecha o la de al lado (san Hilario: 13 en el libro, 14 en ADF)
            if not f or x == 'movible': return not f
            m1, d1 = map(int, f.split('-')); m2, d2 = map(int, x.split('-'))
            return m1 == m2 and abs(d1 - d2) <= 1
        c = [(parecido(n, e['nombre']) + (.01 if f == e['fecha'] else 0), e) for e in E if cerca(e['fecha'])]
        sc = max((x[0] for x in c), default=0)
        if sc < (.99 if not f else .5): sin.append(n); continue
        # la misma celebración puede estar en más de un tomo: se juntan, prefiriendo los del Tiempo Ordinario (III y IV)
        iguales = sorted((e for x, e in c if x == sc), key=lambda e: e['ini'] < TOMOS[2][0])
        d = {}
        for e in iguales:
            for k, v in leer_entrada(L, e).items():
                if isinstance(v, dict) and isinstance(d.get(k), dict): d[k] = {**v, **d[k]}
                elif k not in d: d[k] = v
        if len(d) > 2: out[n] = aleluia(d)
    escribir(os.path.join(B, 'santoral', 'libro.yaml'), dict(sorted(out.items())),
             'Propio de los santos tomado del libro (Liturgia de las Horas, tools/importar/propio_libro.py), para las celebraciones\n'
             'que la base no traía (base/santoral/adf.yaml). Clave: el nombre en el Ordo. «oracion»: la propia; por hora, lo que el\n'
             'libro trae de propio (lo demás sale del común). «comun_libro» e «indicacion»: lo que dice el libro. Se corrige acá.')
    usados = {d[h]['himno'] for d in out.values() for h in ('laudes', 'visperas', 'visperas1', 'oficio', 'tercia', 'sexta', 'nona') if d.get(h, {}).get('himno')}
    import yaml
    for h, nuevos in HIMNOS.items():
        p = os.path.join(B, 'himnos', f'{h}.yaml')
        if not os.path.exists(p): continue
        H = leer(p); add = {k: v for k, v in aleluia(nuevos).items() if k not in H and k in usados}
        if add:
            with open(p, 'a', encoding='utf-8') as f: f.write(yaml.safe_dump(add, allow_unicode=True, width=10**6, sort_keys=False))
            print(f'himnos/{h}: {len(add)} nuevos')
    faltan = [(n, g['salmo']) for n, d in out.items() for h in d.values() if isinstance(h, dict) for g in (h.get('salmodia') or []) if g['salmo'] not in SAL]
    print('salmos que no están en la base:', faltan or 'ninguno')
    print(len(out), 'celebraciones con propio del libro;', len(sin), 'sin propio en el libro:', sin)


if __name__ == '__main__':
    main(sys.argv[1])
