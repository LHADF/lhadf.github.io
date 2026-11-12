"""Lector de la Liturgia de las Horas en libro (PDF de los cuatro tomos pasado a texto con `pdftotext -layout`).

Sirve para lo que sync no trae: los comunes completos, Santa María en sábado y el Propio de los santos.
Devuelve las partes con la misma forma que la base (himno por su primer verso, salmodia con ids de base/salmos,
lectura {ref, texto}, responsorio [[V|R, texto]…], preces {intro, respuesta, preces}, etc.).
"""
import re

HORAS = {'de lectura': 'oficio',   # «Oficio / de lectura» partido por un salto de página
         'i vísperas': 'visperas1', 'ii vísperas': 'visperas', 'vísperas': 'visperas', 'invitatorio': 'invitatorio',
         'oficio de lectura': 'oficio', 'laudes': 'laudes', 'hora intermedia': 'intermedia',
         'tercia': 'tercia', 'sexta': 'sexta', 'nona': 'nona'}
CLAVES = ('HIMNO', 'SALMODIA', 'LECTURA BREVE', 'RESPONSORIO BREVE', 'CÁNTICO EVANGÉLICO', 'PRECES', 'PRIMERA LECTURA',
          'SEGUNDA LECTURA', 'LECTURA BÍBLICA', 'LECTURA PATRÍSTICA', 'CÁNTICO EVANGÉLICO')


def es_basura(l):
    s = l.strip()
    return bool(re.match(r'^-?\s*\d{1,4}\s*-?$', s) or 'LITURGIA DE LAS HORAS' in s or s.startswith('Los himnos latinos'))


def limpiar(L, a, b):
    """Renglones a..b (1-based, b excluido) sin números de página ni encabezados."""
    return [l.rstrip() for l in L[a - 1:b - 1] if not es_basura(l)]


def unir(ls):
    """Junta renglones de un párrafo (saca los guiones de fin de renglón)."""
    t = ''
    for l in ls:
        s = l.strip()
        if not s: continue
        if re.search(r'[a-záéíóúñ]-$', t) and s[:1].islower(): t = t[:-1] + s
        else: t = (t + ' ' + s).strip()
    return re.sub(r'\s+', ' ', t)


def parrafos(ls, sangria=True):
    """Párrafos: separados por blanco o, en prosa, por renglón con sangría."""
    out, cur = [], []
    for l in ls:
        if not l.strip():
            if cur: out.append(cur); cur = []
            continue
        if sangria and re.match(r'^ {2,}\S', l) and cur and not re.match(r'^ {2,}\S', cur[-1] if len(cur) == 1 else 'x'):
            out.append(cur); cur = []
        cur.append(l)
    if cur: out.append(cur)
    return [unir(p) for p in out if unir(p)]


def centrado(l):
    return bool(re.match(r'^ {8,}\S', l)) and len(l.strip()) < 70


def hora_de(l):
    s = l.strip().lower().rstrip('.')
    if s in ('tercia', 'sexta', 'nona'): return s
    return HORAS.get(s) if centrado(l) else None


def partir_horas(ls):
    """[(hora, renglones)] en el orden del libro."""
    out, cur, h = [], [], None
    for l in ls:
        x = hora_de(l)
        if x:
            if h or cur: out.append((h, cur))
            h, cur = x, []
        else: cur.append(l)
    out.append((h, cur))
    return out


def es_clave(l):
    s = l.strip()
    return any(s.startswith(k) for k in CLAVES) and (s.split(',')[0].split(' ')[0].isupper())


def partir_claves(ls):
    """{'HIMNO': [...], 'SALMODIA': [...], 'Oración': [...], ...} (la primera aparición de cada una; las demás, en 'otras')."""
    out, cur, k = {}, [], '_'
    otras = []
    def cerrar():
        if k in out: otras.append((k, cur))
        else: out[k] = cur
    for l in ls:
        s = l.strip()
        nueva = None
        if es_clave(l): nueva = next(c for c in CLAVES if s.startswith(c))
        elif s.rstrip('.') in ('Oración', 'Oración final', 'ORACIÓN'): nueva = 'Oración'   # centrada o no, según el tomo
        if nueva:
            cerrar(); k, cur = nueva, ([s[len(nueva):].strip(' ,.')] if s[len(nueva):].strip(' ,.') else [])
            if nueva in ('LECTURA BREVE', 'PRIMERA LECTURA', 'SEGUNDA LECTURA'): cur = ['@ref ' + s[len(nueva):].strip()] if s[len(nueva):].strip() else []
            continue
        cur.append(l)
    cerrar(); out['_otras'] = otras
    return out


def hasta_o_bien(ls):
    """Corta en «O bien…» (alternativas): devuelve la primera opción."""
    out = []
    for l in ls:
        if re.match(r'^\s*O bien', l): break
        out.append(l)
    return out


# ---------- partes ----------
def himno(ls):
    ls = [l for l in ls if l.strip()]
    if not ls: return None, None
    if re.match(r'(?i)^(como|del|de las|de la|se toma)', ls[0].strip()): return None, None
    if re.match(r'^@ref', ls[0]): ls = ls[1:]
    estrofas, cur = [], []
    blanco = False
    # estrofas: separadas por blanco en el original; acá ya no hay blancos, así que se usan los del bloque crudo
    return ls[0].strip().rstrip(',.;:'), None


def estrofas(ls):
    out, cur = [], []
    for l in ls:
        if re.match(r'^\s*O bien', l): break
        if not l.strip():
            if cur: out.append(cur); cur = []
        else: cur.append(l.strip())
    if cur: out.append(cur)
    return ['\n'.join(e) for e in out]


DOMINGO_I = re.compile(r'(?i)los salmos y el cántico,? del domingo de la I semana[^.]*\.?')


def salmodia(ls, id_v, domingo1=None):
    """[{ant, salmo}] — antífonas «Ant. 1.» y el encabezado del salmo o cántico que sigue. Si el libro remite a los salmos
    del domingo de la I semana, se usan los de `domingo1` (lista de ids)."""
    if domingo1 and any(DOMINGO_I.search(l) for l in ls):
        ants = []
        for l in ls:
            s = l.strip()
            if not s or DOMINGO_I.fullmatch(s): continue
            m = re.match(r'^Ant\.\s*\d\.?\s*(.*)$', s)
            if m: ants.append([m.group(1)])
            elif ants: ants[-1].append(s)
        return [{'ant': DOMINGO_I.sub('', unir(a)).strip(), 'salmo': x} for a, x in zip(ants, domingo1)]
    out, ant, i, ultimo = [], None, 0, None
    ls = [l for l in ls]
    while i < len(ls):
        s = ls[i].strip()
        m = re.match(r'^Ant\.\s*(\d)\.?\s*(.*)$', s)
        if m:
            t = [m.group(2)]; i += 1
            while i < len(ls) and ls[i].strip() and not centrado(ls[i]) and not ls[i].strip().startswith('Ant.'):
                t.append(ls[i]); i += 1
            ant = unir(t); continue
        if centrado(ls[i]) and re.fullmatch(r'I{1,3}|IV|V', s) and ant is not None and ultimo:
            # parte siguiente del mismo salmo («II» después de la antífona, sin repetir «Salmo 117»)
            out.append({'ant': ant, 'salmo': id_v(f'{ultimo} {s}')[0], '_h': f'{ultimo} {s}'}); ant = None; i += 1; continue
        if centrado(ls[i]) and re.match(r'^(Salmo|Cántico)\b', s): ultimo = s
        if centrado(ls[i]) and re.match(r'^(Salmo|Cántico)\b', s) and ant is not None:
            h = s
            j = i + 1
            while j < len(ls) and not ls[j].strip(): j += 1
            if j < len(ls) and re.fullmatch(r'I{1,3}|IV|V', ls[j].strip()): h += ' ' + ls[j].strip()
            ident = id_v(h)[0]
            out.append({'ant': ant, 'salmo': ident, '_h': h}); ant = None
        i += 1
    return out


def lectura(ls):
    ls = hasta_o_bien(ls)
    ref = ''
    if ls and ls[0].startswith('@ref'): ref = ls[0][4:].strip(); ls = ls[1:]
    return {'ref': ref, 'texto': unir(ls)}


def vr(ls):
    """Renglones V./R. → [[V|R, texto]]."""
    out = []
    for l in hasta_o_bien(ls):
        s = l.strip()
        m = re.match(r'^([VR])\.\s*(.*)$', s)
        if m: out.append([m.group(1), m.group(2)])
        elif s and out: out[-1][1] = unir([out[-1][1], s])
    for x in out: x[1] = x[1].strip()
    return out


RUBRICA = re.compile(r'^(?:Se dice[^:]*:|Para el cántico[^:]*:|Como segunda lectura[^.]*\.)\s*')


def antifona_cantico(ls):
    t = []
    for l in ls:
        s = l.strip()
        if s in ('Antífona', ''):
            if t and not s: break
            continue
        if re.match(r'^(Benedictus|Magnificat|O bien)', s): break
        t.append(s)
    return RUBRICA.sub('', re.sub(r'^Ant\.\s*', '', unir(t)))


def preces(ls):
    """{intro, respuesta, preces: [[a, b]], final} — solo la primera serie."""
    bloques, cur = [], []
    final_pn = ''
    for l in ls:
        if re.match(r'^\s*O bien estas otras', l): break
        if re.match(r'^\s*O bien:?\s*$', l) and (bloques or cur) and any('—' in x for b in bloques + [cur] for x in b): break
        if re.search(r'Padre nuestro\.?\s*$', l):
            # la invitación al Padre nuestro puede ocupar más de un renglón
            prev = []
            while cur and not cur[-1].strip().startswith('—') and not re.match(r'^\s*Se pueden', cur[-1]): prev.insert(0, cur.pop())
            final_pn = unir(prev + [l]); continue
        if not l.strip():
            if cur: bloques.append(cur); cur = []
        else: cur.append(l)
    if cur: bloques.append(cur)
    if not bloques: return None
    intro_ls = bloques[0]
    # la respuesta sigue al renglón de la invitación, que termina en «:» (en el mismo bloque o en el siguiente)
    k = next((i + 1 for i, l in enumerate(intro_ls) if l.rstrip().endswith(':') and i + 1 < len(intro_ls)), None)
    if k is not None:
        intro, resp = unir(intro_ls[:k]), unir(hasta_o_bien(intro_ls[k:]))
        resto = bloques[1:]
    else:
        intro, resp = unir(intro_ls), unir(hasta_o_bien(bloques[1])) if len(bloques) > 1 else ''
        resto = bloques[2:]
    pr, final = [], ''
    for b in resto:
        txt = [l for l in b if not re.match(r'^\s*Se pueden añadir', l)]
        j = next((i for i, l in enumerate(txt) if l.strip().startswith('—')), None)
        if j is None:
            t = unir(txt)
            if t.startswith('O bien'): continue
            final = t
            continue
        pr.append([unir(txt[:j]), unir(txt[j:]).lstrip('— ').strip()])
    return {'intro': intro, 'respuesta': resp, 'preces': pr, 'final': final_pn or final}


def padrenuestro_intro(final):
    """«…, pidamos al Padre…: Padre nuestro.» → «…, pidamos al Padre…:»"""
    if not final: return None
    t = re.sub(r'\s*Padre nuestro\.?\s*$', '', final).strip()
    return t if t.endswith(':') else t + ':'


def oraciones(ls):
    """[{'para': '' | 'las mártires vírgenes', 'texto'}] — en los comunes hay varias («O bien:», «Para un obispo:»)."""
    out, para, cur = [], '', []
    def cerrar():
        t = RUBRICA.sub('', unir(cur)).strip()
        if t and not re.match(r'(?i)^(se dice|la oración)', t): out.append({'para': para, 'texto': t})
    for l in ls:
        s = l.strip()
        if not s: continue
        if re.match(r'^(Se dice la oración propia|La oración como|Oración como)', s): continue
        if re.match(r'^O bien:?$', s): cerrar(); cur = []; continue
        m = re.match(r'^(Para [^.]{3,60}?):?$', s)
        if m: cerrar(); cur = []; para = m.group(1)[5:].strip(); continue
        cur.append(s)
    cerrar()
    return out


def oracion(ls):
    o = oraciones(ls)
    return o[0]['texto'] if o else None


def lectura_larga(ls, segunda=False):
    """Primera o segunda lectura del Oficio: {ref|autor, titulo, texto} y su responsorio."""
    ls = hasta_o_bien(ls)
    i = next((k for k, l in enumerate(ls) if l.strip().startswith('Responsorio')), len(ls))
    cuerpo, resp = ls[:i], ls[i:]
    cab, k = [], 0
    while k < len(cuerpo) and not (re.match(r'^ {3,}\S', cuerpo[k]) and not cuerpo[k].strip().isupper() and cab and any(c.strip().isupper() for c in cab)):
        if cuerpo[k].strip(): cab.append(cuerpo[k].strip().replace('@ref ', ''))
        k += 1
    may = [c for c in cab if c.isupper() and len(c) > 2]
    tit = ' '.join(may)
    otros = [c for c in cab if c not in may]
    texto = '\n\n'.join(parrafos(cuerpo[k:]))
    d = {'titulo': tit, 'texto': texto}
    if segunda:
        i0 = next((i for i, o in enumerate(otros) if re.match(r'^(De |Del |De la |Comienza|Inicio)', o)), 0)   # sin rúbricas previas
        d['autor'] = '\n'.join(otros[i0:])
    else: d['ref'] = ' '.join(otros)
    r = {'ref': resp[0].strip()[len('Responsorio'):].strip() if resp else '', 'vr': vr(resp[1:])} if resp else None
    return d, r


DOMINGO1 = {'laudes': ['salmo-62-2-9', 'cantico-dn-3-57-88-56', 'salmo-149']}


def hora(nombre, ls, id_v):
    """Partes de una hora del libro."""
    C = partir_claves(ls)
    d = {}
    if 'HIMNO' in C:
        bloque = C['HIMNO']
        h = [l for l in bloque if l.strip() and not re.fullmatch(r'I{1,3}|IV', l.strip())]
        if h and re.match(r'(?i)^(como|del|de las|de la|se toma)', h[0].strip()):
            # «HIMNO, como en el Propio de los santos. O bien: …»: el himno que sigue a «O bien»
            k = next((i for i, l in enumerate(bloque) if re.match(r'^\s*O bien:?\s*$', l)), None)
            bloque = bloque[k + 1:] if k is not None else []
            h = [l for l in bloque if l.strip() and not re.fullmatch(r'I{1,3}|IV', l.strip())]
        if h and not re.match(r'(?i)^(como|del|de las|de la|se toma|te deum)', h[0].strip()):
            d['himno'] = h[0].strip().rstrip(',.;:')
            d['_himno_texto'] = [e for e in estrofas(bloque) if not re.fullmatch(r'I{1,3}|IV', e)]
    if 'SALMODIA' in C:
        s = salmodia(C['SALMODIA'], id_v, DOMINGO1.get(nombre))
        if s: d['salmodia'] = s
    if 'LECTURA BREVE' in C:
        d['lectura'] = lectura(C['LECTURA BREVE'])
    if 'RESPONSORIO BREVE' in C:
        d['responsorio'] = vr(C['RESPONSORIO BREVE'])
    if 'CÁNTICO EVANGÉLICO' in C:
        a = antifona_cantico(C['CÁNTICO EVANGÉLICO'])
        if a: d['ant_benedictus' if nombre == 'laudes' else 'ant_magnificat'] = a
    if 'PRECES' in C:
        p = preces(C['PRECES'])
        if p:
            pi = padrenuestro_intro(p.pop('final'))
            d['preces'] = p
            if pi: d['padrenuestro_intro'] = pi
    if 'Oración' in C:
        o = oraciones(C['Oración'])
        if o: d['oraciones'] = o
    if nombre == 'oficio':
        pre = C.get('_', [])
        v = vr(C.get('SALMODIA', [])[-12:]) if 'SALMODIA' in C else []
        if v: d['versiculo'] = v[-2:] if len(v) >= 2 else v
        for k, n in (('PRIMERA LECTURA', '1'), ('SEGUNDA LECTURA', '2')):
            if k in C:
                lec, r = lectura_larga(C[k], segunda=(n == '2'))
                if lec.get('texto'): d['lectura' + n] = lec
                if r: d['resp' + n] = r
    if nombre == 'invitatorio':
        t = unir([l for l in ls if l.strip() and l.strip() != 'Antífona'])
        t = re.sub(r'^Ant\.\s*', '', t)
        d['inv_ant'] = re.split(r'\s*(?:El salmo invitatorio|Salmo invitatorio|O bien)', t)[0].strip()
    if nombre in ('tercia', 'sexta', 'nona'):
        pre = C.get('_', []); i = next((i for i, l in enumerate(pre) if l.strip().startswith('Ant.')), None)
        if i is not None:
            j = i + 1
            while j < len(pre) and pre[j].strip(): j += 1
            d['ant'] = re.sub(r'^Ant\.\s*', '', unir(pre[i:j]))
        if 'LECTURA BREVE' in C:
            lb = C['LECTURA BREVE']; k = next((i for i, l in enumerate(lb) if re.match(r'^\s*V\.', l)), len(lb))
            d['lectura'] = lectura(lb[:k]); vv = vr([l for l in lb[k:] if not re.match(r'^\s*La oración', l)])
            if vv: d['versiculo'] = vv
    return d
