"""Separa en sus partes la Hora intermedia (tercia, sexta, nona) y el Oficio de lectura de sync.

Usa las mismas piezas que laudes_sync.py: secciones partidas en cada renglón todo en rojo, rúbricas iniciales
(V., R., Ant.) como prefijo.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from html_sync import lineas, texto, todo_rojo
from completas_sync import sin_tildes, norm, bloques, linea_txt
from laudes_sync import secciones, renglones, estrofas, ant


def _vr(R):
    """Renglones V./R. → [['V', texto], ['R', texto]]; un prefijo solo en su renglón se une con el renglón siguiente."""
    out = []
    for pre, t in R:
        p = pre.strip().rstrip('.').upper()
        if p in ('V', 'R'): out.append([p, t])
        elif out and not out[-1][1]: out[-1][1] = t
        elif out and t: out[-1][1] = (out[-1][1] + ' ' + t).strip()
    return [x for x in out if x[1]]


def _oracion(ls):
    txt = '\n'.join(estrofas(ls))
    txt = re.sub(r'^\s*OREMOS[,.:]?\s*\n?', '', txt, flags=re.I)
    m = re.search(r'\n?\s*Amén\.?\s*$', txt)
    return (txt[:m.start()] if m else txt).strip()


def _salmo(d, h, ls):
    """Un salmo de la salmodia; las antífonas y el versículo que vienen en su sección."""
    g = d['salmodia'][-1] if d['salmodia'] else None
    if g is None or g['salmo'] is not None:
        g = {'ant': None, 'salmo': None, 'texto': [], 'ant_fin': None}; d['salmodia'].append(g)
    g['salmo'] = h
    texto_salmo = []
    for b in bloques(ls):
        pre, t = linea_txt(b[0])
        if ant(pre):
            if re.match(r'^Ant\.?\s*\d', pre.strip()): d['salmodia'].append({'ant': t, 'salmo': None, 'texto': [], 'ant_fin': None})
            else: g['ant_fin'] = t
        elif pre.strip().rstrip('.').upper() in ('V', 'R'):
            d['versiculo'] = _vr([linea_txt(x) for x in b])
        else:
            texto_salmo.append('\n'.join((linea_txt(x)[0] + ' ' if linea_txt(x)[0] else '') + linea_txt(x)[1] for x in b).strip())
    g['texto'] = texto_salmo


def _comun(d, H, h, ls, R, modo):
    """Partes que comparten las dos horas. Devuelve el modo nuevo, o None si la sección no es de estas."""
    if H.startswith('HIMNO'):
        if modo in ('lect2', 'resp2', 'lect1', 'resp1'):          # Oficio: el segundo himno, después de las lecturas, es el Te Deum
            d['te_deum'] = True; return 'tedeum'
        d['himno'] = {'titulo': norm(h.split(':', 1)[1]).rstrip('.') if ':' in h else '', 'texto': estrofas(ls)}
        return 'himno'
    if H.startswith('SALMODIA'):
        for pre, t in R:
            if ant(pre): d['salmodia'].append({'ant': t, 'salmo': None, 'texto': [], 'ant_fin': None})
        if 'COMPLEMENTARIA' in H: d['complementaria'] = True
        return 'salmodia'
    if H.startswith('ORACION'):
        d['oracion'] = _oracion(ls); return 'oracion'
    if H.startswith('CONCLUSION'):
        d['conclusion'] = [[pre.strip().rstrip('.'), t] for pre, t in R]; return 'fin'
    return None


def estructura_menor(ruta):
    """Tercia, Sexta o Nona."""
    d = {'salmodia': [], 'ruta': ruta}
    modo = None
    for h, ls in secciones(ruta):
        H = sin_tildes(h).upper(); R = renglones(ls)
        m = _comun(d, H, h, ls, R, modo)
        if m: modo = m; continue
        if H.startswith('LECTURA BREVE'):
            modo = 'lectura'
            txt = [b for b in bloques(ls) if linea_txt(b[0])[0].strip().rstrip('.').upper() not in ('V', 'R')]
            vr = [b for b in bloques(ls) if linea_txt(b[0])[0].strip().rstrip('.').upper() in ('V', 'R')]
            d['lectura'] = {'ref': norm(h[len('LECTURA BREVE'):]), 'texto': '\n'.join('\n'.join(linea_txt(x)[1] for x in b) for b in txt).strip()}
            if vr: d['versiculo'] = _vr([linea_txt(x) for b in vr for x in b])
        elif modo == 'salmodia' and not H.startswith(('LECTURA', 'ORACION', 'CONCLUSION')) and re.match(r'(?i)^(salmo|c[aá]ntico)', h):
            _salmo(d, h, ls)
        elif modo == 'lectura' and R and _vr(R):
            d['versiculo'] = _vr(R)
        elif H.startswith(('HORA ', 'INVOCACION')) or not (R or h):
            continue
        else:
            d.setdefault('_otros', []).append((h, [t for _, t in R]))
    return d


def estructura_oficio(ruta):
    d = {'salmodia': [], 'ruta': ruta}
    modo = None
    for h, ls in secciones(ruta):
        H = sin_tildes(h).upper(); R = renglones(ls)
        m = _comun(d, H, h, ls, R, modo)
        if m: modo = m; continue
        if H.startswith('INVITATORIO') or H.startswith('OFICIO DE LECTURA'):
            for pre, t in R:
                if ant(pre): d['inv_ant'] = t
            modo = 'inv'
        elif H.startswith('PRIMERA LECTURA'):
            modo = 'lect1'; d['lectura1'] = {'ref': ' '.join(t for _, t in R).strip(), 'titulo': '', 'texto': ''}
        elif H.startswith('SEGUNDA LECTURA'):
            modo = 'lect2'; d['lectura2'] = {'autor': '\n'.join(t for _, t in R).strip(), 'titulo': '', 'texto': ''}
        elif H.startswith('RESPONSORIO'):
            ref = norm(h[len('RESPONSORIO'):])
            r = {'ref': ref, 'vr': _vr(R)}
            if modo in ('lect1', 'resp1') and 'resp1' not in d: d['resp1'] = r; modo = 'resp1'
            else: d['resp2'] = r; modo = 'resp2'
        elif modo in ('lect1', 'lect2'):
            L = d['lectura1' if modo == 'lect1' else 'lectura2']
            if not L['titulo'] and not L['texto']: L['titulo'] = norm(h)
            elif h: L['texto'] += ('\n' if L['texto'] else '') + norm(h)      # un renglón rojo dentro del texto
            L['texto'] = (L['texto'] + '\n' + '\n'.join(estrofas(ls))).strip()
        elif modo == 'salmodia' and re.match(r'(?i)^(salmo|c[aá]ntico)', h):
            _salmo(d, h, ls)
        elif modo == 'salmodia' and R and _vr(R):
            d['versiculo'] = _vr(R)
        elif modo == 'tedeum':
            continue
        elif not (R or h):
            continue
        else:
            d.setdefault('_otros', []).append((h, [t for _, t in R]))
    return d


if __name__ == '__main__':
    import json
    f = sys.argv[1]
    d = (estructura_oficio if f.endswith('oficio.htm') else estructura_menor)(f)
    for g in d['salmodia']: g['texto'] = [x[:50] for x in g['texto']][:1]
    if 'himno' in d: d['himno']['texto'] = d['himno']['texto'][:1]
    for k in ('lectura1', 'lectura2'):
        if k in d: d[k]['texto'] = d[k]['texto'][:80] + '…' + d[k]['texto'][-60:]
    print(json.dumps(d, ensure_ascii=False, indent=1))
