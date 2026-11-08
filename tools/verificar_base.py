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

if errores:
    print('La base tiene problemas:'); [print(' -', e) for e in errores]; sys.exit(1)
print(f'Base correcta: {len(salmos)} salmos y cánticos, Completas completas.')
