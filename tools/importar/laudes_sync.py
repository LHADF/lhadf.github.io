"""Separa cada Laudes de sync en sus partes (y lee del index.htm del día la celebración)."""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from html_sync import lineas, texto, todo_rojo
from completas_sync import MESES, sin_tildes, norm, bloques, linea_txt


def secciones(ruta):
    out = [('', [])]
    for l in lineas(ruta):
        if todo_rojo(l): out.append((norm(texto(l)), []))
        else: out[-1][1].append(l)
    return out


def renglones(ls):
    """[(prefijo_rojo, texto)] sin renglones vacíos."""
    return [linea_txt(l) for l in ls if l]


def estrofas(ls):
    return ['\n'.join(linea_txt(x)[1] for x in b) for b in bloques(ls)]


def ant(pre):
    return bool(re.match(r'^Ant\.?\s*\d*\.?$', pre.strip()))


def estructura(ruta):
    S = secciones(ruta)
    d = {'salmodia': [], 'ruta': ruta}
    modo = None
    for h, ls in S:
        H = sin_tildes(h).upper()
        R = renglones(ls)
        if H.startswith('INVITATORIO'):
            modo = 'inv'
            for pre, t in R:
                if ant(pre): d['inv_ant'] = t
        elif H.startswith('SALMO 94') or H.startswith('SALMO 99') or H.startswith('SALMO 66') or H.startswith('SALMO 23'):
            if modo == 'inv':
                d['inv_salmo'] = h
                d['inv_texto'] = [e for e in estrofas([l for l in ls if not (l and l[0][0])])]
                continue
        if H.startswith('HIMNO'):
            modo = 'himno'
            d['himno'] = {'titulo': norm(h.split(':', 1)[1]).rstrip('.') if ':' in h else '', 'texto': estrofas(ls)}
        elif H.startswith('SALMODIA'):
            modo = 'salmodia'
            for pre, t in R:
                if ant(pre): d['salmodia'].append({'ant': t, 'salmo': None, 'texto': [], 'ant_fin': None})
        elif modo == 'salmodia' and not H.startswith(('LECTURA', 'RESPONSORIO', 'CANTICO EVANGELICO', 'PRECES', 'ORACION')) and 'ZACARIAS' not in H and 'CANTICO DE MARIA' not in H:
            g = d['salmodia'][-1] if d['salmodia'] else None
            if g is None or g['salmo'] is not None:
                g = {'ant': None, 'salmo': None, 'texto': [], 'ant_fin': None}; d['salmodia'].append(g)
            g['salmo'] = h
            texto_salmo = []
            for b in bloques(ls):
                pre, t = linea_txt(b[0])
                if ant(pre):
                    # antífona al final de este salmo o comienzo del siguiente
                    if re.match(r'^Ant\.?\s*\d', pre.strip()):
                        d['salmodia'].append({'ant': t, 'salmo': None, 'texto': [], 'ant_fin': None})
                    else:
                        g['ant_fin'] = t
                else:
                    texto_salmo.append('\n'.join((linea_txt(x)[0] + ' ' if linea_txt(x)[0] else '') + linea_txt(x)[1] for x in b).strip())
            g['texto'] = texto_salmo
        elif H.startswith('LECTURA BREVE'):
            modo = 'lectura'
            d['lectura'] = {'ref': norm(h[len('LECTURA BREVE'):]), 'texto': '\n'.join(estrofas(ls))}
        elif H.startswith('RESPONSORIO'):
            modo = 'resp'
            d['responsorio'] = [[pre.strip().rstrip('.'), t] for pre, t in R]
        elif H.startswith('CANTICO EVANGELICO'):
            modo = 'ce'
            for pre, t in R:
                if ant(pre): d['ant_benedictus'] = t
        elif 'ZACARIAS' in H or 'CANTICO DE MARIA' in H:
            modo = 'zac'
            d['benedictus_texto'] = []
            for b in bloques(ls):
                pre, t = linea_txt(b[0])
                if ant(pre): d['ant_benedictus_fin'] = t
                else: d['benedictus_texto'].append('\n'.join(linea_txt(x)[1] for x in b))
        elif H.startswith('PRECES'):
            modo = 'preces'
            d['preces'] = [t for pre, t in R]
        elif H.startswith('ORACION'):
            modo = 'oracion'
            txt = '\n'.join(estrofas(ls))
            txt = re.sub(r'^\s*OREMOS[,.:]?\s*\n?', '', txt, flags=re.I)
            m = re.search(r'\n?\s*Amén\.?\s*$', txt)
            d['oracion'] = txt[:m.start()].strip() if m else txt.strip()
        elif H.startswith('CONCLUSION'):
            modo = 'fin'
            d['conclusion'] = [[pre.strip().rstrip('.'), t] for pre, t in R]
        elif modo == 'inv' and (H.startswith('(SI LAUDES') or H.startswith('SE SIGUE')):
            for pre, t in R:
                if ant(pre): d['inv_ant'] = t
        elif re.match(r'^(I|II)? ?VISPERAS\b', H) and 'visperas' not in d:
            d['visperas'] = H.split()[0] if H.split()[0] in ('I', 'II') else ''
        elif H.startswith('SE PUEDEN') or H.startswith('PADRE NUESTRO') or H in ('LAUDES', '(ORACION DE LA MAÑANA)', '(ORACION DE LA TARDE)', 'INVOCACION INICIAL') or H.startswith('(SI LAUDES') or H.startswith('SE SIGUE'):
            if R and modo == 'preces': d['padrenuestro_intro'] = ' '.join(t for _, t in R)
        else:
            if R or h: d.setdefault('_otros', []).append((h, [t for _, t in R]))
    return d


def celebracion(ruta_index):
    """Lee el encabezado del día: tiempo y feria, común, salterio, celebración (con su grado) si la hay."""
    if not os.path.exists(ruta_index): return {}
    raw = open(ruta_index, 'rb').read()
    try: s = raw.decode('utf-8')
    except UnicodeDecodeError: s = raw.decode('latin-1')
    s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', s, flags=re.S | re.I)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', s))
    ls = [norm(x) for x in t.split('\n') if norm(x)]
    out = {'cabecera': ls[:12]}
    for i, x in enumerate(ls[:24]):
        m = re.search(r'\((MEMORIA|FIESTA|SOLEMNIDAD)[^)]*\)', sin_tildes(x).upper()) or re.fullmatch(r'(MEMORIA|FIESTA|SOLEMNIDAD)(?: LIBRE| OBLIGATORIA)?\.?', sin_tildes(x).upper())
        if m and 'nombre' not in out:
            nom = re.sub(r'\s*\((?:MEMORIA|FIESTA|SOLEMNIDAD)[^)]*\)\.?$', '', x, flags=re.I).strip()
            if re.fullmatch(r'(?i)(memoria|fiesta|solemnidad)(?: libre| obligatoria)?\.?', nom): nom = ''
            k = i - 1
            while not re.search(r'\w', nom) and k >= 0: nom = ls[k]; k -= 1   # el nombre está en el renglón anterior
            nom = nom.strip().rstrip('.,;: ').strip()
            out['nombre'] = nom
            out['grado'] = m.group(1).capitalize()
        if x.lower().startswith('del común'): out['comun'] = re.sub(r'\s*Salterio\s+[IV]+\.?$', '', x).strip()
        m2 = re.search(r'Salterio\s+([IV]+)', x)
        if m2: out['salterio'] = m2.group(1)
    return out


def archivos(base, hora='laudes'):
    for y in sorted(os.listdir(base)):
        if not re.fullmatch(r'20\d\d', y): continue
        for m in MESES:
            pm = os.path.join(base, y, m)
            if not os.path.isdir(pm): continue
            for dd in sorted(os.listdir(pm)):
                pd = os.path.join(pm, dd)
                if not re.fullmatch(r'\d\d', dd) or not os.path.isdir(pd): continue
                fecha = f'{y}-{MESES.index(m)+1:02d}-{dd}'
                for var in [''] + sorted(x for x in os.listdir(pd) if x.isdigit()):
                    f = os.path.join(pd, var, hora + '.htm')
                    if os.path.exists(f): yield fecha, var, f, os.path.join(pd, var, 'index.htm')


if __name__ == '__main__':
    import json
    d = estructura(sys.argv[1])
    d['celebracion'] = celebracion(os.path.join(os.path.dirname(sys.argv[1]), 'index.htm'))
    for g in d['salmodia']: g['texto'] = [x[:60] for x in g['texto']][:2]
    if 'himno' in d: d['himno']['texto'] = d['himno']['texto'][:1]
    d.pop('benedictus_texto', None); d.pop('inv_texto', None)
    print(json.dumps(d, ensure_ascii=False, indent=1))
