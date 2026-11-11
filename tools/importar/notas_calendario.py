"""Notas al pie del Calendario litúrgico ADF (PDF) → base/calendario/notas.yaml. Se corre una sola vez:
después las notas se corrigen en la base (como el resto de los textos).

    pdftotext -layout Calendario.pdf cal.txt
    ORDO=/ruta/a/ordo-telegram python3 tools/importar/notas_calendario.py cal.txt

Cada nota queda unida a la celebración del Ordo (fecha y nombre) y con la sigla del calendario al que se refiere.
Las del Propio del tiempo (Navidad, Epifanía, Bautismo) se unen por el nombre."""
import csv, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from calendario_pdf import leer
from yaml_base import escribir

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ORDO = os.environ.get('ORDO') or os.path.join(RAIZ, '..', 'lucasfelixjhs', 'ordo-telegram')
R = list(csv.DictReader(open(os.path.join(ORDO, 'data', 'santoral.csv'), encoding='utf-8')))
TEMPORAL = {'NATIVIDAD DEL SEÑOR': 'Natividad del Señor', 'Bautismo del Señor': 'Bautismo del Señor', 'EPIFANÍA DEL SEÑOR': 'Epifanía del Señor'}
norm = lambda s: re.sub(r'[^a-z ]', ' ', unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode())
STOP = {'san', 'santa', 'santos', 'santas', 'beato', 'beata', 'de', 'la', 'el', 'y', 'del', 'los', 'las', 'bienaventurada', 'virgen', 'senor',
        'obispo', 'presbitero', 'martir', 'martires', 'papa', 'doctor', 'doctora', 'iglesia', 'religioso', 'religiosa', 'con', 'dia',
        'conmemoracion', 'octava', 'natividad'}
tok = lambda s: {w for w in norm(s).split() if w not in STOP and len(w) > 2}
def sim(a, b):
    A, B = tok(a), tok(b)
    return len(A & B) / min(len(A), len(B)) if A and B else 0
full = lambda r: r['nombre'] + (', ' + r['titulo'] if r['titulo'] else '')

# Erratas evidentes del PDF
ERRATAS = [('Espiscopado', 'Episcopado'), ('regió guaranítica', 'región guaranítica'), ('cateogoría', 'categoría'), ('extraordinaira', 'extraordinaria'),
           ('octurbre', 'octubre'), ('Alfoso', 'Alfonso'), ('Paz,y', 'Paz, y'), ('de de ', 'de '), ('..', '.'), (' ,', ','), ('Francisco I ', 'Francisco ')]
# Aniversarios de ordenación de personas: no son notas de la celebración (y el calendario es de uso interno)
OMITIR = re.compile(r'Aniversario de la recepción del Orden sagrado del presbiterado de')
# Notas que en el PDF van con la sigla del país pero son de un calendario local
SIGLA = {('11-11', 'Patrono principal de la Ciudad de Buenos Aires'): 'BUE'}


def limpiar(t):
    for a, b in ERRATAS: t = t.replace(a, b)
    t = re.sub(r'\s+', ' ', t).strip()
    if t.endswith('Los fieles que hayan recibido la'):
        t += ' comunión en una Misa pueden recibirla otra vez, solamente dentro de la celebración eucarística en la que participe (c. 917).'
    if t == 'En América Latina se celebra en la fecha tradicional': t += ' (30 de agosto).'
    # oraciones con datos del año que no aplican a otros años («día xx de xx»)
    t = ' '.join(o for o in re.split(r'(?<=\.)\s+', t) if not re.search(r'\bxx\b', o)).strip()
    return t


def main():
    E = [e for e in leer(open(sys.argv[1], encoding='utf-8').read()) if 'grado' in e and e['nombre'] and not e['nombre'].startswith('Feria')]
    out, sin = {}, []
    for e in E:
        if not e['notas']: continue
        if e['nombre'] in TEMPORAL:
            clave, fecha = TEMPORAL[e['nombre']], 'movible'
        else:
            c = [(sim(e['nombre'], full(r)), r) for r in R if r['fecha'] == e['fecha']]
            sc, r = max(c, key=lambda x: x[0]) if c else (0, None)
            if sc < .5: sin.append(e); continue
            clave, fecha = full(r), r['fecha']
        sig0 = (re.findall(r'[A-Z]{3}', e.get('cal_txt', '')) or ['ADF'])[-1]
        notas = []
        for sig, t in e['notas']:
            t = limpiar(t)
            if not t or OMITIR.search(t): continue
            sig = next((v for (f, ini), v in SIGLA.items() if f == e['fecha'] and t.startswith(ini)), sig or sig0)
            notas.append({'calendario': sig, 'texto': t})
        for a in e.get('alt', []):
            for sig, t in a['notas']: notas.append({'calendario': sig or 'ADF', 'texto': limpiar(t)})
        if notas: out[f'{fecha} {clave}'] = notas
    escribir(os.path.join(RAIZ, 'base', 'calendario', 'notas.yaml'), dict(sorted(out.items())),
             'Notas del Calendario litúrgico ADF, por celebración: «MM-DD Nombre, título» como en el Ordo («movible» para las del Propio del tiempo).\n'
             'Cada nota lleva la sigla del calendario al que se refiere. Se muestran con el signo (!) en el inicio.\n'
             'Importadas una vez del PDF (tools/importar/notas_calendario.py); se corrigen acá.')
    print(len(out), 'celebraciones con nota;', sum(len(v) for v in out.values()), 'notas;', len(sin), 'sin pareja:', [e['nombre'] for e in sin])


if __name__ == '__main__':
    main()
