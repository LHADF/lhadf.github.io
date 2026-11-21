#!/usr/bin/env python3
"""Marca las sinalefas de los himnos en español (base/himnos/*.yaml) con «‿» entre las palabras que se unen.

Reglas (métrica española):
- Sinalefa: si una palabra termina en vocal y la siguiente empieza por vocal (también con h muda), las dos vocales
  forman una sola sílaba métrica. Puede unir tres palabras («que‿a‿Europa»); la conjunción «y» se une a los dos lados.
- No hay sinalefa si la segunda palabra empieza por h + diptongo (hie-, hia-, hue-, hui-: «hierba», «hueso»), ni si la
  primera termina en «y» consonántica («hoy es» = ho-yes) ni con «y» consonántica al principio («ya», «yo»).
- Hiato (sinalefa que no se hace): solo cuando la medida del verso lo pide. Se mide cada verso con todas las sinalefas
  (con la última palabra aguda +1, esdrújula −1) y se toma la medida del himno: la de cada lugar de la estrofa si
  las estrofas son iguales, o las medidas que más se repiten. Si a un verso le falta una sílaba (o dos) para esa
  medida y deshaciendo sinalefas la alcanza, se deshacen las más naturales para el hiato: la segunda vocal tónica
  («la‿alma» → «la alma» si el verso lo pide), una pausa (coma) entre las palabras, la primera palabra aguda.

Uso: python3 tools/sinalefas.py [--escribir] [--informe archivo.md]
Sin --escribir, solo informa. Se corre una vez sobre el texto sin marcar: un archivo que ya tiene «‿» no se toca
(las correcciones se hacen a mano en la base), salvo con --rehacer, que borra todas las marcas y las vuelve a poner.
"""
import os, re, sys, collections

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'base', 'himnos')
ARCO = '‿'
VOC = 'aeiouáéíóúü'
FUERTES = set('aeoáéóíú')   # í y ú acentuadas: hiato con la vocal de al lado
ATONAS = set('el la lo los las un unos al del a ante con de en entre para por sin so sobre tras y e o u ni que si mi tu su mis tus sus me te se nos os le les como cuando donde pues aun mas cual quien'.split())


def limpia(w):
    return re.sub(r'[^\wáéíóúüñÁÉÍÓÚÜÑ]', '', w).lower()


def nucleos(w):
    """Núcleos silábicos de una palabra (lista de (inicio, fin) en la palabra normalizada) y la palabra normalizada."""
    w = limpia(w)
    w = re.sub(r'([qg])u([eiéí])', r'\1\2', w)      # que, qui, gue, gui: la u no suena
    letras = []
    for i, c in enumerate(w):
        es_v = c in VOC or (c == 'y' and (w == 'y' or (i == len(w) - 1 and i > 0 and w[i - 1] in VOC)))
        letras.append((c, es_v))
    nuc = []
    i = 0
    while i < len(letras):
        if not letras[i][1]:
            i += 1
            continue
        j = i
        ini = i
        while j + 1 < len(letras) and letras[j + 1][1]:
            a, b = letras[j][0], letras[j + 1][0]
            if (a in FUERTES and b in FUERTES) or (a == b):   # dos fuertes (o acentuada): hiato
                nuc.append((ini, j))
                ini = j + 1
            j += 1
        nuc.append((ini, j))
        i = j + 1
    return nuc, w


def acento(w):
    """Índice del núcleo tónico."""
    nuc, n = nucleos(w)
    if not nuc:
        return -1, nuc, n
    for k, (a, b) in enumerate(nuc):
        if any(ch in 'áéíóú' for ch in n[a:b + 1]):
            return k, nuc, n
    if len(nuc) == 1:
        return 0, nuc, n
    if n[-1] in 'aeiouns':
        return len(nuc) - 2, nuc, n
    return len(nuc) - 1, nuc, n


def empieza_vocal(w):
    n = limpia(w)
    if not n:
        return False
    if n == 'y':
        return True
    if n[0] == 'h':
        if re.match(r'h[iu][aeiouáéíóú]', n):   # hie-, hue-, hui-…: suena consonante
            return False
        n = n[1:]
    return bool(n) and n[0] in VOC


def termina_vocal(w):
    n = limpia(w)
    return bool(n) and (n[-1] in VOC or n == 'y')


AMEN = re.compile(r'\s*\bAm[ée]n\.?\s*$')


def medir_ws(ws):
    """Sílabas de un verso (lista de palabras) sin sinalefas, con la regla de la última palabra, y las uniones posibles."""
    ws_l = [w for w in ws if limpia(w)]
    if not ws_l:
        return 0, []
    sil = sum(len(nucleos(w)[0]) for w in ws_l)
    k, nuc, _ = acento(ws_l[-1])
    if nuc:
        resto = len(nuc) - 1 - k
        sil += 1 if resto == 0 else (-1 if resto >= 2 else 0)
    uniones = []
    for i in range(len(ws) - 1):
        a, b = ws[i], ws[i + 1]
        if not limpia(a) or not limpia(b):
            continue
        if re.search(r'[.;:!?…»)\]]$', a):   # punto, punto y coma, dos puntos, cierre: pausa fuerte, sin sinalefa
            continue
        if termina_vocal(a) and empieza_vocal(b):
            na = limpia(a)
            if na != 'y' and na.endswith('y'):   # «hoy es», «rey eterno»: la y pasa a la sílaba siguiente
                continue
            uniones.append(i)
    return sil, uniones


def medir(linea):
    ws = AMEN.sub('', linea).split()
    sil, un = medir_ws(ws)
    return ws, sil, un


def compuesto(ws, h):
    """Verso compuesto de dos hemistiquios de h sílabas (alejandrino 7+7, dodecasílabo 6+6): la cesura impide la
    sinalefa y cada hemistiquio se mide aparte. Devuelve (hiatos necesarios, corte, uniones de cada lado) o None."""
    mejor = None
    for j in range(1, len(ws)):
        s1, u1 = medir_ws(ws[:j]); s2, u2 = medir_ws(ws[j:])
        m1, m2 = s1 - len(u1), s2 - len(u2)
        if m1 <= h <= s1 and m2 <= h <= s2:
            costo = (h - m1) + (h - m2) + (0 if re.search(r'[,;:.!?»]$', ws[j - 1]) else 0.5)   # mejor, la cesura en una pausa
            if mejor is None or costo < mejor[0]:
                mejor = (costo, j, u1, [j + i for i in u2], h - m1, h - m2)
    return mejor


def puntaje_hiato(ws, i):
    a, b = ws[i], ws[i + 1]
    p = 0
    kb, nb, _ = acento(b)
    if kb == 0 and limpia(b) not in ATONAS:
        p += 3   # segunda vocal tónica
    ka, na, _ = acento(a)
    if na and ka == len(na) - 1 and limpia(a) not in ATONAS and len(na) > 1:
        p += 2   # primera palabra aguda («está en»)
    if re.search(r'[,]$', a) or re.match(r'^[¡¿«(—]', b):
        p += 2   # pausa
    if limpia(b).startswith('h'):
        p += 1
    return p


def estrofas_de(lineas):
    """Agrupa las líneas del archivo en himnos y estrofas: [(himno, [estrofa: [(nº de línea, texto)]])]."""
    himnos = []
    actual = None
    est = None
    bloque = None   # sangría de la estrofa (block scalar)
    for n, l in enumerate(lineas):
        if bloque is not None:
            if l.strip() and (len(l) - len(l.lstrip(' '))) >= bloque:
                est.append((n, l))
                continue
            bloque = None
        m = re.match(r'^([^ #-][^:]*):\s*$', l)
        if m:
            actual = [m.group(1), []]
            himnos.append(actual)
            continue
        if re.match(r'^\s*- titulo:', l):
            actual = [l.split('titulo:', 1)[1].strip(), []]
            himnos.append(actual)
            continue
        if re.match(r'^\s*- \|-\s*$', l):
            est = []
            actual[1].append(est)
            bloque = len(l) - len(l.lstrip(' ')) + 2
    return himnos


def decidir(himno):
    """Para cada verso: las uniones que se marcan. Devuelve {nº de línea: (texto nuevo, hiatos)}."""
    titulo, ests = himno
    datos = []   # (ie, il, nlinea, texto, ws, sil, uniones)
    for ie, e in enumerate(ests):
        for il, (n, l) in enumerate(e):
            sang = l[:len(l) - len(l.lstrip(' '))]
            t = l.strip()
            ws, sil, un = medir(t)
            datos.append((ie, il, n, sang, t, ws, sil, un))
    if not datos:
        return {}
    minimo = lambda d: d[6] - len(d[7])
    # ¿Versos compuestos? Si la mitad o más se miden sin hiatos como 7+7 (o 6+6), el himno es de alejandrinos (o dodecasílabos)
    comp = None
    for h in (7, 6):
        ok = sum(1 for d in datos if (lambda c: c and c[0] < 1)(compuesto(d[5], h)))
        if ok >= 0.5 * len(datos):
            comp = h
            break
    # medida esperada de cada verso
    largos = collections.Counter(len(e) for e in ests)
    iguales = len(largos) == 1 and len(ests) > 1
    meta = {}
    if iguales:
        for pos in range(len(ests[0])):
            vs = [d for d in datos if d[1] == pos]
            c = collections.Counter(minimo(d) for d in vs)
            v, f = c.most_common(1)[0]
            if f / len(vs) >= 0.5:
                for d in vs:
                    meta[d[2]] = [v]
    simples = [d for d in datos if not (comp and (lambda c: c and c[0] < 1)(compuesto(d[5], comp)))]
    c = collections.Counter(minimo(d) for d in simples)
    tot = max(1, len(simples))
    frec = sorted(v for v, f in c.items() if f / tot >= 0.2 and v >= 4)
    for d in datos:
        meta.setdefault(d[2], frec)
    out = {}
    for d in datos:
        ie, il, n, sang, t, ws, sil, un = d
        if ARCO in t or not un:
            continue
        m = minimo(d)
        hiatos = []
        objetivos = meta.get(n) or []
        c = compuesto(ws, comp) if comp else None
        if c and c[0] >= 1 and (m in objetivos or m in frec):   # verso simple entre compuestos (p. ej., un endecasílabo)
            c = None
        if c and c[0] <= 2.5:
            # cesura entre los hemistiquios (sin sinalefa) y, dentro de cada uno, los hiatos que pida la medida
            _, j, u1, u2, f1, f2 = c
            for us, falta in ((u1, f1), (u2, f2)):
                if falta:
                    orden = sorted(us, key=lambda i: -puntaje_hiato(ws, i))
                    hiatos += orden[:int(falta)]
            if (j - 1) in un:
                hiatos.append(j - 1)
        elif objetivos and m not in objetivos:
            alcanzables = [v for v in objetivos if m < v <= sil and v - m <= 2]
            if alcanzables:
                falta = min(alcanzables) - m
                orden = sorted(un, key=lambda i: -puntaje_hiato(ws, i))
                cand = [i for i in orden if puntaje_hiato(ws, i) >= 2][:falta]
                if len(cand) == falta:
                    hiatos = cand
        marcar = [i for i in un if i not in hiatos]
        nuevo = ''
        for i, w in enumerate(ws):
            nuevo += w
            if i < len(ws) - 1:
                nuevo += ARCO if i in marcar else ' '
        cuerpo = AMEN.sub('', t)
        nuevo += t[len(cuerpo):]   # el «Amén» final, tal cual
        out[n] = (sang + nuevo, [(ws[i], ws[i + 1]) for i in hiatos], t)
    return out


def main():
    escribir = '--escribir' in sys.argv
    informe = None
    if '--informe' in sys.argv:
        informe = sys.argv[sys.argv.index('--informe') + 1]
    total_u = total_h = 0
    rep = ['# Sinalefas de los himnos en español', '',
           'Las sinalefas de los himnos en español van marcadas en `base/himnos/` con «‿» (`tools/sinalefas.py`, 21/11/2026).',
           'Este informe lista los versos en los que **no** se marcó una sinalefa posible (hiato), porque la medida del himno lo',
           'pide: la segunda vocal tónica («su Hijo», «la hora»), una pausa, o la cesura de los alejandrinos (7+7) y dodecasílabos',
           '(6+6). Para corregir un verso, se edita a mano en `base/himnos/`.', '']
    for f in sorted(os.listdir(B)):
        if not f.endswith('.yaml'):
            continue
        p = os.path.join(B, f)
        texto = open(p, encoding='utf-8').read()
        if ARCO in texto:
            if '--rehacer' not in sys.argv:
                print(f'{f}: ya tiene sinalefas marcadas (se deja como está; --rehacer para volver a marcar)')
                continue
            texto = texto.replace(ARCO, ' ')
        lineas = texto.split('\n')
        cambios = {}
        for h in estrofas_de(lineas):
            d = decidir(h)
            for n, (nuevo, hi, viejo) in d.items():
                total_u += nuevo.count(ARCO)
                if hi:
                    total_h += len(hi)
                    rep.append(f'- **{h[0]}** ({f}): «{viejo}» — sin sinalefa en ' + ', '.join(f'«{a} {b}»' for a, b in hi))
                cambios[n] = nuevo
        if escribir:
            for n, nuevo in cambios.items():
                lineas[n] = nuevo
            open(p, 'w', encoding='utf-8').write('\n'.join(lineas))
    print(f'sinalefas marcadas: {total_u} · hiatos por la medida: {total_h}')
    if informe:
        open(informe, 'w', encoding='utf-8').write('\n'.join(rep) + '\n')


if __name__ == '__main__':
    main()
