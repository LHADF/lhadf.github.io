"""Comprueba que la base (base/) esté completa y sea coherente. Corre en cada publicación.

Uso: python3 tools/verificar_base.py
"""
import glob, os, sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(RAIZ, 'tools', 'importar'))
from yaml_base import leer

B = os.path.join(RAIZ, 'base')
errores = []


def falta(cond, msg):
    if not cond: errores.append(msg)


def vr(lista, donde):
    falta(isinstance(lista, list) and lista, f'{donde}: falta')
    for e in lista or []:
        falta(isinstance(e, dict) and len(e) == 1 and set(e) <= {'V', 'R', 'texto'}, f'{donde}: cada renglón debe ser «V: …», «R: …» o «texto: …» ({e!r})')


salmos = {os.path.basename(f)[:-5]: leer(f) for f in glob.glob(os.path.join(B, 'salmos', '*.yaml'))}
for k, s in salmos.items():
    for c in ('titulo', 'texto'):
        falta(s.get(c), f'salmos/{k}.yaml: falta «{c}»')
    for e in s.get('texto') or []:
        falta(not e.startswith('Gloria al Padre'), f'salmos/{k}.yaml: el Gloria no va en el texto del salmo')

O = leer(os.path.join(B, 'ordinario', 'completas.yaml'))
vr(O.get('invocacion'), 'ordinario/completas.yaml · invocacion')
vr(O.get('bendicion'), 'ordinario/completas.yaml · bendicion')
for t in ('ordinario', 'pascua'):
    vr(O.get('responsorio', {}).get(t), f'ordinario/completas.yaml · responsorio.{t}')
    falta(O.get('cantico_evangelico', {}).get('antifona', {}).get(t), f'ordinario/completas.yaml · antífona del cántico ({t})')
for c in ('gloria', 'examen', 'oracion_solemnidad'):
    falta(O.get(c), f'ordinario/completas.yaml: falta «{c}»')

S = leer(os.path.join(B, 'salterio', 'completas.yaml'))
for j in ('domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'):
    J = S.get(j) or {}
    falta(J, f'salterio/completas.yaml: falta el {j}')
    for k in ('salmodia', 'salmodia_pascua'):
        for g in J.get(k) or []:
            falta(g.get('ant'), f'salterio/completas.yaml · {j}.{k}: antífona vacía')
            for sid in g.get('salmos') or []:
                falta(sid in salmos, f'salterio/completas.yaml · {j}.{k}: no existe base/salmos/{sid}.yaml')
    falta((J.get('lectura') or {}).get('texto'), f'salterio/completas.yaml · {j}: falta la lectura breve')
    falta(J.get('oracion'), f'salterio/completas.yaml · {j}: falta la oración')

T = leer(os.path.join(B, 'tiempo', 'completas-triduo-octava.yaml'))
for dia, x in T.items():
    falta(x.get('juego') in S, f'tiempo/completas-triduo-octava.yaml · {dia}: juego «{x.get("juego")}» no existe')

H = leer(os.path.join(B, 'himnos', 'completas.yaml'))
for t in ('ordinario', 'adviento_navidad', 'cuaresma', 'pascua'):
    falta(H.get(t), f'himnos/completas.yaml: no hay himnos para «{t}»')
M = leer(os.path.join(B, 'ordinario', 'antifonas-marianas.yaml'))
falta(M.get('año') and M.get('pascua'), 'ordinario/antifonas-marianas.yaml: faltan antífonas')

G = leer(os.path.join(B, 'gregoriano', 'completas.yaml'))
def trad(x, donde):
    if isinstance(x, dict):
        for k, v in x.items(): trad(v, f'{donde}.{k}')
    elif isinstance(x, list) and donde.split('.')[-1] == 'traduccion' or isinstance(x, list) and donde.split('.')[-1].startswith('traduccion_') and donde.split('.')[-1] != 'traduccion_versos':
        for e in x: falta(isinstance(e, str) and ' = ' in e, f'gregoriano/completas.yaml · {donde}: «{e}» debe ser «latín = español» (entre comillas si tiene «: »)')
    elif isinstance(x, str) and x.endswith('.gabc'):
        falta(os.path.exists(os.path.join(B, 'gregoriano', x)), f'gregoriano/completas.yaml · {donde}: no existe base/gregoriano/{x}')
trad(G, 'completas')

# ---------- Laudes ----------
import json, re
from datetime import date, timedelta
CAMPOS_L = ['inv_ant', 'himno', 'salmodia', 'lectura', 'responsorio', 'ant_benedictus', 'preces', 'padrenuestro_intro', 'oracion']
SL = leer(os.path.join(B, 'salterio', 'laudes.yaml'))
TL = leer(os.path.join(B, 'tiempo', 'laudes.yaml'))
SaL = leer(os.path.join(B, 'santoral', 'laudes.yaml'))
HL = leer(os.path.join(B, 'himnos', 'laudes.yaml'))
OL = leer(os.path.join(B, 'ordinario', 'laudes.yaml'))
falta((OL.get('invitatorio') or {}).get('salmo', {}).get('texto'), 'ordinario/laudes.yaml: falta el Salmo 94 del invitatorio')
falta((OL.get('cantico_evangelico') or {}).get('texto'), 'ordinario/laudes.yaml: falta el Benedictus')
def parte_l(e, donde):
    for g in e.get('salmodia') or []:
        falta(g.get('ant'), f'{donde}: antífona vacía')
        falta(g.get('salmo') in salmos, f'{donde}: no existe base/salmos/{g.get("salmo")}.yaml')
    if e.get('himno'): falta(e['himno'] in HL, f'{donde}: el himno «{e["himno"]}» no está en himnos/laudes.yaml')
    if e.get('salmodia') is not None: falta(len(e['salmodia']) == 3, f'{donde}: la salmodia debe tener tres salmos')
    if e.get('preces'): falta(e['preces'].get('preces') or e['preces'].get('renglones'), f'{donde}: preces vacías')
for sem, dias in SL.items():
    for dia, e in dias.items():
        for c in CAMPOS_L:
            if dia == 'domingo' and c in ('ant_benedictus', 'oracion'): continue   # propios de cada domingo (tiempo/laudes.yaml)
            falta(e.get(c), f'salterio/laudes.yaml · {sem}.{dia}: falta «{c}»')
        parte_l(e, f'salterio/laudes.yaml · {sem}.{dia}')
for n, e in TL.items(): parte_l(e, f'tiempo/laudes.yaml · {n}')
for n, e in SaL.items(): parte_l(e, f'santoral/laudes.yaml · {n}')
GLa = leer(os.path.join(B, 'gregoriano', 'laudes.yaml'))
for k in ('invitatorio', 'conclusion'):
    falta(os.path.exists(os.path.join(B, 'gregoriano', GLa[k]['partitura'])), f'gregoriano/laudes.yaml · {k}: no existe la partitura')
falta(len(GLa['benedictus']['versos']) == len(GLa['benedictus']['traduccion_versos']), 'gregoriano/laudes.yaml · benedictus: cada versículo necesita su traducción')
# cobertura: todos los días del calendario tienen Laudes completas (salterio + propio del tiempo)
cal = open(os.path.join(RAIZ, 'src', 'datos', 'calendario.js'), encoding='utf-8').read()
cal = json.loads(cal[cal.index('=') + 1:].rstrip().rstrip(';'))
tab, ix = cal['tabla'], {c: i for i, c in enumerate(cal['campos'])}
DIAS_L = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
def adviento(y):
    n = date(y, 12, 25); return n - timedelta(days=(n.weekday() + 1) % 7 or 7) - timedelta(weeks=3)
sin_propio, pendientes = set(), set()
d0 = date.fromisoformat(cal['desde'])
for k, r in enumerate(cal['ARG']):
    f = d0 + timedelta(days=k); t, fer, sal = tab[r[ix['t']]], tab[r[ix['fer']]], r[ix['sal']]
    dia = DIAS_L[f.weekday()]
    y = f.year if f >= adviento(f.year) else f.year - 1
    claves = [fer] + ([f"{fer} ({'ABC'[(y - 2016) % 3]})"] if dia == 'domingo' else [])
    propio = {}
    for c in claves: propio.update(TL.get(c) or {})
    if t == 'Ordinario' and dia != 'domingo': continue
    if tab[r[ix['g']]] in ('Solemnidad', 'Fiesta'): continue   # propio del santoral (o celebración del Señor)
    if propio.get('pendiente'): pendientes.add(f'{fer}: {propio["pendiente"]}'); continue
    if not propio.get('oracion') and t not in ('Triduo',): sin_propio.add(fer)
falta(not sin_propio, f'tiempo/laudes.yaml: {len(sin_propio)} días del calendario sin oración propia: {sorted(sin_propio)}')

for x in sorted(pendientes): print('Pendiente (Laudes):', x)
if errores:
    print('La base tiene problemas:'); [print(' -', e) for e in errores]; sys.exit(1)
print(f'Base correcta: {len(salmos)} salmos y cánticos, Completas completas; Laudes: salterio de 4 semanas, {len(TL)} días con propio del tiempo, {len(SaL)} celebraciones.')
