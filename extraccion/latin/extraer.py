"""Extrae el ePub de Universalis (Liturgia Horarum en latín, por día) a JSON estructurado, sin interpretar:
por día, la celebración y los datos («De die»), y por hora, la secuencia de bloques tal como vienen
(título y cita, subtítulos, epígrafe, renglones con sangría, comienzo de estrofa y cursiva, párrafos, rúbricas).
Sale un archivo por mes en extraccion/latin/dias/ (AAAA-MM.json).
Uso: python3 extraccion/latin/extraer.py RUTA/libro.epub"""
import sys, re, json, os, zipfile, tempfile, warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
from bs4 import BeautifulSoup, NavigableString, Tag

HORAS = {'Ad Officium lectionis': 'oficio', 'Ad Laudes matutinas': 'laudes', 'Ad Tertiam': 'tercia', 'Ad Sextam': 'sexta',
         'Ad Nonam': 'nona', 'Ad Vesperas': 'visperas', 'Ad Completorium': 'completas', 'De die': 'de_die'}
MESES = {'ianuarii': 1, 'februarii': 2, 'martii': 3, 'aprilis': 4, 'maii': 5, 'iunii': 6, 'iulii': 7, 'augusti': 8,
         'septembris': 9, 'octobris': 10, 'novembris': 11, 'decembris': 12}

def limpio(s):
    s = s.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()

def texto(el):
    """Texto de un elemento sin los números de versículo; ℣/℟ quedan al comienzo."""
    el = BeautifulSoup(str(el), 'lxml')
    for n in el.select('span.versenumber'): n.decompose()
    return limpio(el.get_text())

def todo_cursiva(el):
    t = texto(el)
    it = ''.join(limpio(i.get_text()) for i in el.find_all('i'))
    return bool(t) and limpio(it) == t

def hora(path):
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    body = soup.body
    nav = body.find('div', class_='navigation')
    cel = limpio(nav.find('strong').get_text()) if nav and nav.find('strong') else ''
    bloques = []
    cur = None
    def nuevo(alt=None):
        nonlocal cur
        cur = {'titulo': '', 'ref': '', 'sub': [], 'epigrafe': '', 'lineas': [], 'rubricas': []}
        if alt: cur['alternativa'] = alt
        bloques.append(cur)
    nuevo()
    def recorrer(nodo, alt=None):
        for el in nodo.children:
            if not isinstance(el, Tag): continue
            cls = el.get('class') or []
            if el.name == 'div' and 'navigation' in cls: continue
            if el.name == 'hr': nuevo(alt); continue
            if el.name == 'div' and any(c in cls for c in ('firstblock', 'lastblock', 'middleblock')):
                nuevo(); recorrer(el, alt=(cls[0])); nuevo(); continue
            if el.name == 'h2':
                t = limpio(el.get_text())
                if HORAS.get(t) or not bloques: continue
                if cur['lineas'] or cur['titulo']: nuevo(alt)
                cur['titulo'] = t; continue
            if el.name == 'table' and 'each' in cls:
                th = el.find_all('th')
                if cur['lineas'] or cur['titulo']: nuevo(alt)
                cur['titulo'] = limpio(th[0].get_text()) if th else ''
                cur['ref'] = limpio(th[1].get_text()) if len(th) > 1 else ''
                continue
            if el.name == 'h4':
                partes = [limpio(x) for x in el.get_text('\n').split('\n') if limpio(x)]
                if cur['lineas']: nuevo(alt)
                cur['sub'] += partes; continue
            if el.name == 'p':
                if el.find('a') and not limpio(re.sub(r'\s+', '', el.get_text())) == '': 
                    if all(isinstance(c, Tag) and c.name == 'a' for c in el.children if not (isinstance(c, NavigableString) and not c.strip())): continue
                if 'rubric' in cls: cur['rubricas'].append(texto(el)); continue
                t = texto(el)
                if t: cur['lineas'].append({'t': t, 'p': True})
                continue
            if el.name == 'div' and any(c in cls for c in ('v', 'vi', 'p', 'pi')):
                if el.find('blockquote'):
                    cur['epigrafe'] = texto(el); continue
                t = texto(el)
                if not t: continue
                l = {'t': t}
                if 'vi' in cls: l['sangria'] = True
                if 'gb' in cls: l['estrofa'] = True
                if 'p' in cls or 'pi' in cls: l['p'] = True
                if todo_cursiva(el): l['cursiva'] = True
                if el.find('b') and limpio(el.find('b').get_text()) == t: l['negrita'] = True
                if 'id' in el.attrs: pass
                cur['lineas'].append(l); continue
            if el.name == 'div':
                recorrer(el, alt); continue
            t = texto(el)
            if t: cur['lineas'].append({'t': t, 'otro': el.name})
    recorrer(body)
    bloques = [b for b in bloques if b['lineas'] or b['titulo'] or b['sub'] or b['rubricas']]
    for b in bloques:
        for k in ('ref', 'epigrafe'):
            if not b[k]: del b[k]
        for k in ('sub', 'rubricas'):
            if not b[k]: del b[k]
    return cel, bloques

def main(epub):
    tmp = tempfile.mkdtemp()
    zipfile.ZipFile(epub).extractall(tmp)
    oebps = os.path.join(tmp, 'OEBPS')
    titulo = re.search(r'<dc:title>(.*?)</dc:title>', open(os.path.join(oebps, 'content.opf'), encoding='utf-8').read()).group(1)
    toc = open(os.path.join(oebps, 'toc.ncx'), encoding='utf-8').read()
    items = re.findall(r'<text>(.*?)</text>\s*</navLabel>\s*<content src="([^"]+)"', toc)
    dias, dia = [], None
    for lab, src in items:
        m = re.match(r'Dies (\d+) (\w+) (\d{4})', lab)
        if m:
            dia = {'fecha': f'{m.group(3)}-{MESES[m.group(2)]:02d}-{int(m.group(1)):02d}', 'horas': {}}
            dias.append(dia); continue
        if dia is None or lab not in HORAS: continue
        cel, bl = hora(os.path.join(oebps, src))
        dia['celebracion'] = cel
        if HORAS[lab] == 'de_die':
            dia['de_die'] = [r for b in bl for r in b.get('rubricas', []) if not r.startswith('Check this page')] + [l['t'] for b in bl for l in b['lineas']]
        else:
            dia['horas'][HORAS[lab]] = bl
    salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dias')
    os.makedirs(salida, exist_ok=True)
    meses = {}
    for d in dias: meses.setdefault(d['fecha'][:7], []).append(d)
    for m, ds in meses.items():
        json.dump({'fuente': f'Universalis Publishing, «{titulo}» (ePub)', 'dias': ds},
                  open(os.path.join(salida, m + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(dias), 'días;', sum(len(d['horas']) for d in dias), 'horas;', len(meses), 'meses')

if __name__ == '__main__':
    main(*sys.argv[1:])
