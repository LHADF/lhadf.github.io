"""Separa cada Completas de sync en sus partes."""
import os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from html_sync import lineas, texto, todo_rojo

MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']

def sin_tildes(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def norm(s):
    s = s.replace(' ', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def bloques(ls):
    """Agrupa renglones en párrafos (lista de listas de renglones de texto)."""
    out, cur = [], []
    for l in ls:
        if not l: 
            if cur: out.append(cur); cur = []
        else: cur.append(l)
    if cur: out.append(cur)
    return out

def secciones(ruta):
    """[(encabezado, [renglones])] partiendo en cada renglón todo en rojo."""
    out = [('', [])]
    for l in lineas(ruta):
        if todo_rojo(l): out.append((norm(texto(l)), []))
        else: out[-1][1].append(l)
    return out

def linea_txt(l):
    """Renglón a texto, marcando rúbricas rojas iniciales (V., R., Ant.) como prefijo."""
    pre = ''
    if l and l[0][0]:
        pre = norm(l[0][1]); l = l[1:]
    return pre, norm(''.join(t for _, t in l))

def parrafos(ls):
    return ['\n'.join(linea_txt(x)[1] if not linea_txt(x)[0] else (linea_txt(x)[0] + ' ' + linea_txt(x)[1]) for x in b) for b in bloques(ls)]

def estructura(ruta):
    S = secciones(ruta)
    d = {'salmodia': [], 'ruta': ruta}
    cur_salmo = None
    for i, (h, ls) in enumerate(S):
        H = sin_tildes(h).upper()
        ps = parrafos(ls)
        if H.startswith('HIMNO'):
            d['himno'] = {'titulo': norm(h.split(':', 1)[1]) if ':' in h else '', 'texto': ps}
        elif H.startswith('SALMODIA') or H.startswith('SALMO') or (H.startswith('CANTICO') and 'SIMEON' not in H and 'EVANGELICO' not in H):
            if not H.startswith('SALMODIA'):
                if not d['salmodia'] or d['salmodia'][-1].get('cerrado'):
                    d['salmodia'].append({'ant': None, 'salmos': []})
                d['salmodia'][-1]['salmos'].append({'titulo': h, 'texto': []})
            for b in bloques(ls):
                pre, t = linea_txt(b[0])
                g = d['salmodia'][-1] if d['salmodia'] else None
                if pre.startswith('Ant'):
                    if g is None or g.get('cerrado') or (g['salmos'] and g['salmos'][-1]['texto'] == [] and g['ant'] is None and False):
                        d['salmodia'].append({'ant': t, 'salmos': []})
                    elif g['salmos'] and g['salmos'][-1]['texto']:
                        g['ant_fin'] = t; g['cerrado'] = True
                    else:
                        g['ant'] = t
                elif g is not None and g['salmos']:
                    g['salmos'][-1]['texto'].append('\n'.join(linea_txt(x)[1] for x in b))
        elif H.startswith('LECTURA BREVE'):
            d['lectura'] = {'ref': norm(h[len('LECTURA BREVE'):]), 'texto': '\n'.join(ps)}
        elif H.startswith('RESPONSORIO'):
            d['responsorio'] = [linea_txt(x) for b in bloques(ls) for x in b]
        elif H.startswith('CANTICO EVANGELICO'):
            for b in bloques(ls):
                pre, t = linea_txt(b[0])
                if pre.startswith('Ant'): d['ant_cantico'] = t
        elif 'SIMEON' in H:
            d['cantico_texto'] = []
            for b in bloques(ls):
                pre, t = linea_txt(b[0])
                if pre.startswith('Ant'): d['ant_cantico_fin'] = t
                elif not t.startswith('Gloria al Padre'): d['cantico_texto'].append('\n'.join(linea_txt(x)[1] for x in b))
        elif H.startswith('ORACION'):
            txt = '\n'.join(ps)
            txt = re.sub(r'^\s*OREMOS[,.:]?\s*\n?', '', txt, flags=re.I)
            m = re.search(r'\n?\s*Amén\.?\s*$', txt)
            d['oracion_amen'] = bool(m)
            d['oracion'] = txt[:m.start()].strip() if m else txt.strip()
        elif H.startswith('BENDICION'):
            d['bendicion'] = [linea_txt(x) for b in bloques(ls) for x in b]
        elif 'ANTIFONA FINAL' in H:
            d['mariana'] = ps
        elif H.startswith('INVOCACION'):
            d['invocacion'] = [linea_txt(x) for b in bloques(ls) for x in b]
        elif H.startswith('EXAMEN'):
            d['examen'] = ps
        elif H in ('COMPLETAS', '') or H.startswith('(ORACION') or H.startswith('OF LA'):
            if H.startswith('(') or H=='COMPLETAS': pass
            elif ls and H=='' and any(ls): d.setdefault('_previo', parrafos(ls))
        else:
            d.setdefault('_otros', []).append((h, ps))
    for g in d['salmodia']: g.pop('cerrado', None)
    return d

def archivos(base):
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
                    f = os.path.join(pd, var, 'completas.htm')
                    if os.path.exists(f): yield fecha, var, f
