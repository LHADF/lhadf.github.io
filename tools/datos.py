#!/usr/bin/env python3
"""Arma los datos de Completas del jueves 5/11/2026 para el prototipo (dos ritos, varias versiones)."""
import re, json, html, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Carpeta con los clones de las fuentes (ver docs/fuentes.md). Se puede cambiar con SEPTIES_FUENTES.
FUENTES = os.environ.get('SEPTIES_FUENTES', os.path.join(os.path.dirname(RAIZ), 'fuentes'))
SALIDA = os.path.join(RAIZ, 'src', 'datos', 'completas-2026-11-05.js')
SALMODIA = os.path.join(RAIZ, 'src', 'salmodia.js')

DO = os.path.join(FUENTES, 'divinum-officium', 'web', 'www', 'horas') + '/'
SYNC = os.path.join(FUENTES, 'sync', '2026', 'nov', '05', 'completas.htm')
NV = os.path.join(FUENTES, 'jgabc', 'psalms', 'NovaVulgata.txt')

def secciones(path):
    s = open(path, encoding='utf-8').read(); d = {}
    for sec in re.split(r'\n(?=\[)', s):
        h = sec.split('\n', 1)[0].strip()
        if h.startswith('[') and h not in d:
            d[h] = sec.split('\n', 1)[1] if '\n' in sec else ''
    return d

def limpia(t):
    t = re.sub(r'/:.*?:/', '', t)            # rúbricas internas
    t = re.sub(r'\{[^}]*\}', '', t)
    t = t.replace('+++', '✠').replace('++', '✠').replace(' + ', ' ✠ ').replace('+ ', '✠ ')
    t = re.sub(r'^\s*[vrVR]\.\s*', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def lineas_do(t):
    return [l for l in t.split('\n') if l.strip() and not l.startswith(('(', '@', '$', '&', '!'))]

P = {l: secciones(DO + f'{l}/Psalterium/Common/Prayers.txt') for l in ['Latin', 'Espanol']}
M = {l: secciones(DO + f'{l}/Psalterium/Special/Minor Special.txt') for l in ['Latin', 'Espanol']}
MA = {l: secciones(DO + f'{l}/Psalterium/Mariaant.txt') for l in ['Latin', 'Espanol']}
GM = secciones(DO + 'Latin-gabc/Psalterium/Special/Minor Special.txt')
GP = secciones(DO + 'Latin-gabc/Psalterium/Psalmi/Psalmi minor.txt')

def gabc_archivo(rel):
    g = open(DO + 'Latin-gabc/chants/' + rel, encoding='utf-8').read()
    return g

def salmo_do(lang, num, desde=None, hasta=None):
    vs = []
    for l in open(DO + f'{lang}/Psalterium/Psalmorum/Psalm{num}.txt', encoding='utf-8'):
        l = l.strip()
        m = re.match(r'^(\d+):(\d+)\w?\s+(.*)$', l)
        if not m: continue
        v = int(m.group(2))
        if desde and (v < desde or v > hasta): continue
        t = m.group(3).replace(' + ', ' ✠ ').replace('+ ', '').strip()
        t = re.sub(r'\s*✠\s*', ' ', t) if num != 233 else t
        vs.append(t)
    return vs

def vr(lat, esp):
    a = lineas_do(lat); b = lineas_do(esp)
    return {'v': {'la': limpia(a[0]), 'es': limpia(b[0])}, 'r': {'la': limpia(a[1]), 'es': limpia(b[1])}}

# ---------------- Español 1979 (repositorio sync) ----------------
s = open(SYNC, encoding='latin-1').read()
s = re.sub(r'(?i)<br\s*/?>', '\n', s); s = re.sub(r'<[^>]+>', '', s); s = html.unescape(s)
s = re.sub(r'[ \t]+', ' ', s)
def bloque(ini, fin):
    i = s.index(ini) + len(ini); j = s.index(fin, i)
    return s[i:j]
def estrofas(txt):
    txt = re.sub(r'\n[ \t]+\n', '\n\n', txt)
    txt = re.sub(r'[ \t]*\n[ \t]+(?=\S)', ' ', txt)  # unir cortes del código HTML (salto + sangría) a mitad de verso
    est = [[l.strip() for l in e.split('\n') if l.strip()] for e in re.split(r'\n\s*\n', txt)]
    return [e for e in est if e]
himno_es = estrofas(bloque('CUANDO LA LUZ DEL SOL ES YA PONIENTE', ' Amén.'))
salmo_es = estrofas(bloque('ESPERAN LA RESURRECCIÓN.', ' Gloria al Padre'))
nunc_es = estrofas(bloque('Lc 2, 29-32', ' Gloria al Padre'))
madre_es = estrofas(bloque('ANTIFONA FINAL DE LA SANTISIMA VIRGEN', 'Of La'))

def versos_de_estrofas(est):
    """Agrupa las líneas de cada estrofa en versos salmódicos: pares con mediante; si sobra una, flexa."""
    versos, grupos = [], []
    for e in est:
        g = []
        ls = list(e)
        if len(ls) % 2 == 1 and len(ls) >= 3:
            versos.append(f'{ls[0]} † {ls[1]} * {ls[2]}'); g.append(len(versos) - 1); ls = ls[3:]
        while len(ls) >= 2:
            versos.append(f'{ls[0]} * {ls[1]}'); g.append(len(versos) - 1); ls = ls[2:]
        if ls:
            versos.append(ls[0]); g.append(len(versos) - 1)
        grupos.append(g)
    return versos, grupos

ps15_es, ps15_es_g = versos_de_estrofas(salmo_es)
nunc_es_v, nunc_es_g = versos_de_estrofas(nunc_es)

# ---------------- Latín Nova Vulgata ----------------
nvt = open(NV, encoding='utf-8').read()
m = re.search(r'PSALMUS 16 \(15\)\s*\n(.*?)(?=PSALMUS 17)', nvt, re.S)
ps15_la = [re.sub(r'^\d+\s+', '', l).strip().replace('« ', '«').replace(' »', '»') for l in m.group(1).strip().split('\n') if l.strip()]
nunc_la = ['Nunc dimíttis servum tuum, Dómine, * secúndum verbum tuum in pace,',
           'quia vidérunt óculi mei * salutáre tuum,',
           'quod parásti * ante fáciem ómnium populórum,',
           'lumen ad revelatiónem géntium * et glóriam plebis tuæ Israel.']
# grupos latinos alineados con las estrofas españolas (por versículos bíblicos)
ps15_la_g = [[0, 1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11]]
nunc_la_g = [[0], [1, 2], [3]]

GLORIA = {'la': ['Glória Patri, et Fílio, * et Spirítui Sancto.', 'Sicut erat in princípio, et nunc et semper, * et in sǽcula sæculórum. Amen.'],
          'es': ['Gloria al Padre, y al Hijo, * y al Espíritu Santo.', 'Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']}
GLORIA_V = {'la': ['Glória Patri, et Fílio, * et Spirítui Sancto.', 'Sicut erat in princípio, et nunc, et semper, * et in sǽcula sæculórum. Amen.'],
            'es': ['Gloria al Padre, al Hijo, * y al Espíritu Santo.', 'Como era en el principio, ahora y siempre, * por los siglos de los siglos. Amén.']}

# ---------------- Partituras ----------------
CARO_MEA = "name:Caro mea;\nmode:7;\nannotation:VII c;\n%%\n(c3) CA(i)ro(g) me(i_/jki)a(i.) *(,) re(i)qui(g)és(h)cet(f) in(gf) spe.(e.) (::)"
SALVA_LH = ("name:Salva nos;\nmode:3;\nannotation:III a;\n%%\n(c4) SAl(g)va(hi) nos,(i) *() Dó(ik)mi(j)ne,(ji) vi(h)gi(i)lán(h>)tes,(g.) (;) "
            "cus(g)tó(i)di(j) nos(k') dor(j)mi(h)én(j>)tes,(i.) (;) ut(i) vi(g)gi(i)lé(k)mus(j) cum(h) Chris(j)to(i_j) (,) "
            "et(h) re(h)qui(h)es(h)cá(gf)mus(gh) in(gf) pa(e.)ce.(e.) (::)")
def gabc_inline(txt):
    m = re.search(r'\{(?:name:[^;]*;)?(?:annotation:([^;]*);)?(?:mode:(\d);)?.*?%%(.*)\}', txt, re.S)
    return m
ADJUTOR = "name:Adjutor meus;\nmode:8;\nannotation:VIII G;\n%%\n" + re.search(r'%%(.*?)\}', GP['[Completorium]'].split('Feria V = ')[1]).group(1).strip()
SALVA_V = "name:Salva nos;\nmode:3;\nannotation:III a;\n%%\n" + re.search(r'\{(.*?)\};;', GM['[Ant 4]']).group(1).split('^_T. P.')[0].strip()
CUSTODI = "name:Custodi nos;\n%%\n" + re.search(r'%%(.*?)\}', GM['[Versum 4]']).group(1).strip()
TE_LUCIS_V = gabc_archivo('Psalterium/Feria/hy--te_lucis_ante_terminum_in_fer_et_fest_simpl--solesmes.gabc')
IN_MANUS = gabc_archivo('Psalterium/rb--in_manus_tuas--solesmes_1961.gabc')
SALVE = gabc_archivo('Psalterium/Mariaant/an--salve_regina_simple_tone--solesmes.1.gabc')

# Himno Te lucis (Liturgia Horarum) con la melodía ferial: se aplica la melodía de la 1.ª estrofa a cada estrofa
cuerpo = TE_LUCIS_V.split('%%')[1]
notas1 = re.findall(r'([^()\s]+)\(([^)]*)\)', cuerpo.split('2.(::)')[0])
notas1 = [n for t, n in notas1 if re.search(r'[a-zA-Zæœǽáéíóú]', t)]  # 32 notas, una por sílaba
TE_LUCIS_LH = [['Te lucis ante términum,', 'rerum Creátor, póscimus,', 'ut sólita cleméntia', 'sis præsul ad custódiam.'],
               ['Te corda nostra sómnient,', 'te per sopórem séntiant,', 'tuámque semper glóriam', 'vicína luce cóncinant.'],
               ['Vitam salúbrem tríbue,', 'nostrum calórem réfice,', 'tætram noctis calíginem', 'tua collústret cláritas.'],
               ['Præsta, Pater omnípotens,', 'per Iesum Christum Dóminum,', 'qui tecum in perpétuum', 'regnat cum Sancto Spíritu.']]
TE_LUCIS_LH_GLOSA = [['Te', 'A ti,'], ['lucis ante términum,', 'antes del fin de la luz,'], ['rerum Creátor,', 'Creador de todo,'], ['póscimus,', 'pedimos'], ['ut', 'que'], ['sólita', 'con la acostumbrada'], ['cleméntia', 'clemencia'], ['sis', 'seas'], ['præsul', 'guardián'], ['ad', 'para'], ['custódiam.', 'custodia.'], ['Te', 'Que a ti'], ['corda', 'los corazones'], ['nostra', 'nuestros'], ['sómnient,', 'sueñen,'], ['te', 'a ti'], ['per', 'durante'], ['sopórem', 'el sueño'], ['séntiant,', 'sientan,'], ['tuámque', 'y tu'], ['semper', 'siempre'], ['glóriam', 'gloria'], ['vicína luce', 'al acercarse la luz'], ['cóncinant.', 'canten.'], ['Vitam', 'Vida'], ['salúbrem', 'sana'], ['tríbue,', 'concede,'], ['nostrum', 'nuestro'], ['calórem', 'fervor'], ['réfice,', 'reaviva;'], ['tætram', 'la negra'], ['noctis', 'de la noche'], ['calíginem', 'oscuridad'], ['tua', 'tu'], ['collústret', 'ilumine'], ['cláritas.', 'claridad.'], ['Præsta,', 'Concédelo,'], ['Pater', 'Padre'], ['omnípotens,', 'omnipotente,'], ['per', 'por'], ['Iesum', 'Jesús'], ['Christum', 'Cristo'], ['Dóminum,', 'el Señor,'], ['qui', 'que'], ['tecum', 'contigo'], ['in perpétuum', 'para siempre'], ['regnat', 'reina'], ['cum', 'con'], ['Sancto', 'el Santo'], ['Spíritu.', 'Espíritu.'], ['Amen.', 'Amén.']]
TE_LUCIS_V_GLOSA = [['Te', 'A ti,'], ['lucis ante términum,', 'antes del fin de la luz,'], ['Rerum Creátor,', 'Creador de todo,'], ['póscimus,', 'pedimos'], ['Ut', 'que'], ['pro', 'por'], ['tua', 'tu'], ['cleméntia', 'clemencia'], ['Sis', 'seas'], ['præsul', 'guardián'], ['et', 'y'], ['custódia.', 'custodia.'], ['Procul', 'Lejos'], ['recédant', 'se vayan'], ['sómnia,', 'los sueños'], ['Et nóctium phantásmata;', 'y los fantasmas de la noche;'], ['Hostémque', 'y al enemigo'], ['nostrum', 'nuestro'], ['cómprime,', 'reprime,'], ['Ne', 'para que no'], ['polluántur', 'se manchen'], ['córpora.', 'los cuerpos.'], ['Præsta,', 'Concédelo,'], ['Pater', 'Padre'], ['piíssime,', 'piadosísimo,'], ['Patríque', 'y al Padre'], ['compar', 'igual,'], ['Unice,', 'Unigénito,'], ['Cum', 'con'], ['Spíritu', 'el Espíritu'], ['Paráclito', 'Paráclito'], ['Regnans', 'reinando'], ['per', 'por'], ['omne', 'todo'], ['sǽculum.', 'siglo.'], ['Amen.', 'Amén.']]

def silabas_lat(linea):
    """Silabeo latino sencillo (igual criterio que salmodia.js) para cargar la melodía del himno."""
    out = []
    for w in linea.split():
        pre = re.match(r'^[^\wæœǽ]*', w).group(0); core = w[len(pre):]
        m = re.match(r'^(.*?)([^\wæœǽáéíóú]*)$', core); core, post = m.group(1), m.group(2)
        out.append((core, post))
    return out

def gabc_himno_lh():
    import subprocess
    lineas = [l for e in TE_LUCIS_LH for l in e]
    js = 'const S=require(' + json.dumps(SALMODIA) + ');const L=' + json.dumps(lineas, ensure_ascii=False) + \
         ';console.log(JSON.stringify(L.map(l=>S.palabras(l,"la").map(p=>({pre:p.pre,post:p.post,s:p.sil.map(x=>x.t)})))))'
    pal = json.loads(subprocess.check_output(['node', '-e', js]).decode())
    g = '(c4) '
    for ie, est in enumerate(TE_LUCIS_LH):
        for il in range(4):
            ws = pal[ie * 4 + il]; sil = [(p, k) for p in ws for k in range(len(p['s']))]
            if len(sil) != 8: raise SystemExit(f'Estrofa {ie+1} línea {il+1}: {len(sil)} sílabas')
            for j, (p, k) in enumerate(sil):
                t = (p['pre'] if k == 0 else '') + p['s'][k] + (p['post'] if k == len(p['s']) - 1 else '')
                if ie == 0 and il == 0 and j == 0: t = t.upper()
                g += t + '(' + notas1[il * 8 + j] + ')' + (' ' if k == len(p['s']) - 1 else '')
            g += '(,) ' if il in (0, 2) else ('(;) ' if il == 1 else '')
        g += f'{ie+2}.(::) ' if ie < 3 else '(::) '
    g += 'A(ghg)men.(fg..) (::)'
    return 'name:Te lucis ante terminum;\nmode:8;\nannotation:VIII;\n%%\n' + g

TE_LUCIS_LH_GABC = gabc_himno_lh()

def glosa_ant(pares): return pares
GL_CARO = [['Caro', 'Carne'], ['mea', 'mía'], ['requiéscet', 'descansará'], ['in', 'en'], ['spe.', 'esperanza.']]
GL_SALVA = [['Salva nos,', 'Sálvanos,'], ['Dómine,', 'Señor,'], ['vigilántes,', 'despiertos,'], ['custódi nos', 'guárdanos'], ['dormiéntes,', 'dormidos,'], ['ut', 'para que'], ['vigilémus', 'velemos'], ['cum', 'con'], ['Christo', 'Cristo'], ['et', 'y'], ['requiescámus', 'descansemos'], ['in', 'en'], ['pace.', 'paz.']]
GL_ADJ = [['Adiútor', 'Auxilio'], ['meus', 'mío'], ['et', 'y'], ['liberátor', 'libertador'], ['meus', 'mío'], ['esto,', 'sé,'], ['Dómine.', 'Señor.']]
GL_INMANUS = [['In', 'En'], ['manus', 'manos'], ['tuas', 'tuyas,'], ['Dómine,', 'Señor,'], ['Comméndo', 'encomiendo'], ['spíritum', 'espíritu'], ['meum.', 'mío.'], ['In', 'En'], ['manus.', 'manos.'], ['Redemísti', 'Redimiste'], ['nos', 'nos,'], ['Dómine,', 'Señor,'], ['Deus', 'Dios'], ['veritátis.', 'de verdad.'], ['Comméndo.', 'Encomiendo.'], ['Glória', 'Gloria'], ['Patri,', 'al Padre,'], ['et', 'y'], ['Fílio,', 'al Hijo,'], ['et', 'y'], ['Spirítui', 'al Espíritu'], ['Sancto.', 'Santo.'], ['In', 'En'], ['manus.', 'manos.']]
GL_SALVE = [['Salve,', 'Salve,'], ['Regína,', 'Reina,'], ['mater', 'madre'], ['misericórdiæ:', 'de misericordia,'], ['Vita,', 'vida,'], ['dulcédo,', 'dulzura'], ['et', 'y'], ['spes', 'esperanza'], ['nostra,', 'nuestra,'], ['salve.', 'salve.'], ['Ad', 'A'], ['te', 'ti'], ['clamámus,', 'clamamos,'], ['éxsules,', 'desterrados,'], ['fílii', 'hijos'], ['Hevæ.', 'de Eva.'], ['Ad', 'A'], ['te', 'ti'], ['suspirámus,', 'suspiramos,'], ['geméntes', 'gimiendo'], ['et', 'y'], ['flentes', 'llorando'], ['in', 'en'], ['hac', 'este'], ['lacrimárum valle.', 'valle de lágrimas.'], ['Eia', 'Ea,'], ['ergo,', 'pues,'], ['Advocáta', 'abogada'], ['nostra,', 'nuestra,'], ['illos', 'esos'], ['tuos', 'tus'], ['misericórdes', 'misericordiosos'], ['óculos', 'ojos'], ['ad', 'a'], ['nos', 'nosotros'], ['convérte.', 'vuelve.'], ['Et', 'Y'], ['Iesum,', 'a Jesús,'], ['benedíctum', 'bendito'], ['fructum', 'fruto'], ['ventris', 'del vientre'], ['tui,', 'tuyo,'], ['nobis', 'a nosotros'], ['post', 'después de'], ['hoc', 'este'], ['exsílium', 'destierro'], ['osténde.', 'muestra.'], ['O', 'Oh'], ['clemens:', 'clemente,'], ['O', 'oh'], ['pia:', 'piadosa,'], ['O', 'oh'], ['dulcis', 'dulce'], ['Virgo', 'Virgen'], ['María.', 'María.']]
GL_CUSTODI = [['Custódi', 'Guarda'], ['nos', 'nos,'], ['Dómine', 'Señor,'], ['ut', 'como'], ['pupíllam', 'a la niña'], ['óculi.', 'del ojo.'], ['Sub', 'Bajo'], ['umbra', 'la sombra'], ['alárum', 'de las alas'], ['tuárum', 'tuyas'], ['prótege', 'protege'], ['nos.', 'nos.']]

SALVE_TXT = {'la': [l.strip() for l in lineas_do(MA['Latin']['[Postpentecost]'].split('_')[0].replace('{:S-SalveRegina:}v. ', ''))],
             'es': [l.strip() for l in lineas_do(MA['Espanol']['[Postpentecost]'].split('_')[0].replace('{:S-SalveRegina:} v. ', ''))]}
SALVE_LH_LA = ['Salve, Regína, mater misericórdiæ;', 'vita, dulcédo et spes nostra, salve.', 'Ad te clamámus, éxsules fílii Evæ.',
               'Ad te suspirámus geméntes et flentes', 'in hac lacrimárum valle.', 'Eia ergo, advocáta nostra,',
               'illos tuos misericórdes óculos ad nos convérte.', 'Et Iesum, benedíctum fructum ventris tui,',
               'nobis post hoc exsílium osténde.', 'O clemens, o pia, o dulcis Virgo María.']
SALVE_ES79 = ['Dios te salve, Reina y Madre de misericordia,', 'vida, dulzura y esperanza nuestra; Dios te salve.',
              'A ti llamamos los desterrados hijos de Eva;', 'a ti suspiramos, gimiendo y llorando,', 'en este valle de lágrimas.',
              'Ea, pues, Señora, abogada nuestra,', 'vuelve a nosotros esos tus ojos misericordiosos;',
              'y, después de este destierro, muéstranos a Jesús,', 'fruto bendito de tu vientre.', '¡Oh clementísima, oh piadosa, oh dulce Virgen María!']

# ---------------- Liturgia de las Horas (rito actual) ----------------
novus = {
 'nombre': 'Liturgia de las Horas',
 'sub': 'Rito romano actual (1971)',
 'dia': {'titulo': 'Jueves de la XXXI semana', 'tiempo': 'Tiempo Ordinario', 'salterio': 'Semana III del salterio', 'color': 'verde'},
 'versiones': {
   'la': {'n': 'Latín', 'd': 'Liturgia Horarum, editio typica altera (1985) · Nova Vulgata'},
   'es79': {'n': 'Español 1979', 'd': 'Edición española (Coeditores Litúrgicos, 1979)'},
 },
 'secciones': [
  {'k': 'sec', 'id': 'inicio', 't': 'Invocación inicial'},
  {'k': 'vr', 'v': {'la': 'Deus, ✠ in adiutórium meum inténde.', 'es79': 'Dios mío, ven en mi auxilio.'},
              'r': {'la': 'Dómine, ad adiuvándum me festína.', 'es79': 'Señor, date prisa en socorrerme.'}},
  {'k': 'doxo', 't': {'la': 'Glória Patri, et Fílio, et Spirítui Sancto. Sicut erat in princípio, et nunc et semper, et in sǽcula sæculórum. Amen. Allelúia.',
                     'es79': 'Gloria al Padre, y al Hijo, y al Espíritu Santo. Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén. Aleluya.'}},
  {'k': 'sec', 'id': 'examen', 't': 'Examen de conciencia', 'plegable': True},
  {'k': 'rub', 't': 'Es muy de alabar que, después de la invocación inicial, se haga el examen de conciencia, que en la celebración comunitaria puede concluirse con un acto penitencial.'},
  {'k': 'prosa', 'pleg': 'examen', 't': {'la': 'Confíteor Deo omnipoténti et vobis, fratres, quia peccávi nimis cogitatióne, verbo, ópere et omissióne: mea culpa, mea culpa, mea máxima culpa. Ídeo precor beátam Maríam semper Vírginem, omnes Ángelos et Sanctos, et vos, fratres, oráre pro me ad Dóminum Deum nostrum.',
              'es79': 'Yo confieso ante Dios todopoderoso y ante vosotros, hermanos, que he pecado mucho de pensamiento, palabra, obra y omisión: por mi culpa, por mi culpa, por mi gran culpa. Por eso ruego a santa María, siempre Virgen, a los ángeles, a los santos y a vosotros, hermanos, que intercedáis por mí ante Dios, nuestro Señor.'}},
  {'k': 'vr', 'pleg': 'examen', 'v': {'la': 'Misereátur nostri omnípotens Deus et, dimíssis peccátis nostris, perdúcat nos ad vitam ætérnam.', 'es79': 'El Señor todopoderoso tenga misericordia de nosotros, perdone nuestros pecados y nos lleve a la vida eterna.'},
              'r': {'la': 'Amen.', 'es79': 'Amén.'}},
  {'k': 'sec', 'id': 'himno', 't': 'Himno'},
  {'k': 'himno', 'opciones': [
     {'id': 'telucis', 'n': 'Te lucis ante términum', 'lang': 'la', 'est': TE_LUCIS_LH, 'amen': 'Amen.', 'gabc': TE_LUCIS_LH_GABC, 'glosa': TE_LUCIS_LH_GLOSA},
     {'id': 'cuandoluz', 'n': 'Cuando la luz del sol es ya poniente', 'lang': 'es79', 'est': himno_es, 'amen': 'Amén.'},
  ]},
  {'k': 'sec', 'id': 'salmodia', 't': 'Salmodia'},
  {'k': 'ant', 'id': 'a1', 'n': 'Ant. 1', 't': {'la': 'Caro mea * requiéscet in spe.', 'es79': 'Mi carne descansa serena.'}, 'gabc': CARO_MEA, 'modo': '7c', 'glosa': GL_CARO},
  {'k': 'salmo', 'id': 'ps15', 'ant': 'a1', 'titulo': {'la': 'Psalmus 15 (16)', 'es79': 'Salmo 15'},
   'lema': {'es79': 'Cristo y sus miembros esperan la resurrección', 'la': 'Dominus ipse est hereditas mea'},
   'versos': {'la': ps15_la, 'es79': ps15_es}, 'grupos': {'la': ps15_la_g, 'es79': ps15_es_g}, 'gloria': True},
  {'k': 'ant', 'id': 'a1r', 'rep': 'a1'},
  {'k': 'sec', 'id': 'lectura', 't': 'Lectura breve'},
  {'k': 'lectura', 'ref': {'la': '1 Th 5, 23', 'es79': '1 Ts 5, 23'},
   't': {'la': 'Ipse autem Deus pacis sanctíficet vos per ómnia, et íntegrum vestrum spíritus et ánima et corpus sine queréla in advéntu Dómini nostri Iesu Christi servétur.',
         'es79': 'Que el mismo Dios de la paz os consagre totalmente y que todo vuestro ser, alma y cuerpo, sea custodiado sin reproche hasta la Parusía de nuestro Señor Jesucristo.'},
   'aviso': {'txt': 'Texto latino provisional: falta cotejarlo con la Liturgia Horarum.'}},
  {'k': 'sec', 'id': 'responsorio', 't': 'Responsorio breve'},
  {'k': 'resp', 'gabc': IN_MANUS, 'glosa': GL_INMANUS,
   'l': {'la': [['V', 'In manus tuas, Dómine, * comméndo spíritum meum.'], ['R', 'In manus tuas, Dómine, * comméndo spíritum meum.'], ['V', 'Redemísti nos, Dómine Deus veritátis.'], ['R', 'Comméndo spíritum meum.'], ['V', 'Glória Patri, et Fílio, et Spirítui Sancto.'], ['R', 'In manus tuas, Dómine, * comméndo spíritum meum.']],
         'es79': [['V', 'En tus manos, Señor, encomiendo mi espíritu.'], ['R', 'En tus manos, Señor, encomiendo mi espíritu.'], ['V', 'Tú, el Dios leal, nos librarás.'], ['R', 'Te encomiendo mi espíritu.'], ['V', 'Gloria al Padre, y al Hijo, y al Espíritu Santo.'], ['R', 'En tus manos, Señor, encomiendo mi espíritu.']]}},
  {'k': 'sec', 'id': 'cantico', 't': 'Cántico evangélico'},
  {'k': 'ant', 'id': 'a2', 'n': 'Ant.', 't': {'la': 'Salva nos, * Dómine, vigilántes, custódi nos dormiéntes, ut vigilémus cum Christo et requiescámus in pace.', 'es79': 'Sálvanos, Señor, despiertos, protégenos mientras dormimos, para que velemos con Cristo y descansemos en paz.'}, 'gabc': SALVA_LH, 'modo': '3a', 'glosa': GL_SALVA},
  {'k': 'salmo', 'id': 'nunc', 'ant': 'a2', 'cantico': True, 'titulo': {'la': 'Canticum Simeonis', 'es79': 'Cántico de Simeón'}, 'ref': 'Lc 2, 29-32',
   'lema': {'es79': 'Cristo, luz de las naciones y gloria de Israel'},
   'versos': {'la': nunc_la, 'es79': nunc_es_v}, 'grupos': {'la': nunc_la_g, 'es79': nunc_es_g}, 'gloria': True},
  {'k': 'ant', 'id': 'a2r', 'rep': 'a2'},
  {'k': 'sec', 'id': 'oracion', 't': 'Oración'},
  {'k': 'oremos', 't': {'la': 'Orémus.', 'es79': 'Oremos.'}},
  {'k': 'prosa', 't': {'es79': 'Señor, Dios nuestro, concédenos un descanso tranquilo que restaure nuestras fuerzas, desgastadas ahora por el trabajo del día; así, fortalecidos con tu ayuda, te serviremos siempre con todo nuestro cuerpo y nuestro espíritu. Por Cristo nuestro Señor.'}, 'amen': {'la': 'Amen.', 'es79': 'Amén.'}},
  {'k': 'sec', 'id': 'bendicion', 't': 'Bendición'},
  {'k': 'vr', 'v': {'la': 'Noctem quiétam et finem perféctum concédat nobis Dóminus omnípotens.', 'es79': 'El Señor todopoderoso nos conceda una noche tranquila y una santa muerte.'}, 'r': {'la': 'Amen.', 'es79': 'Amén.'}},
  {'k': 'sec', 'id': 'mariana', 't': 'Antífona a la Virgen'},
  {'k': 'mariana', 'opciones': [
     {'id': 'salve', 'n': 'Salve Regina', 'l': {'la': SALVE_LH_LA, 'es79': SALVE_ES79}, 'gabc': SALVE, 'glosa': GL_SALVE},
     {'id': 'alma', 'n': 'Alma Redemptoris Mater', 'l': {'es79': [l for e in madre_es for l in e]}},
  ]},
 ]
}

# ---------------- Breviario Romano 1960 ----------------
L, E = 'Latin', 'Espanol'
def pr(k, l): return P[l][k]
ps69 = {'la': salmo_do(L, 69), 'es': salmo_do(E, 69)}
ps70a = {'la': salmo_do(L, 70, 1, 12), 'es': salmo_do(E, 70, 1, 12)}
ps70b = {'la': salmo_do(L, 70, 13, 24), 'es': salmo_do(E, 70, 13, 24)}
nunc_v = {'la': [v.replace('✠ ', '') for v in salmo_do(L, 233)], 'es': [v.replace('✠ ', '') for v in salmo_do(E, 233)]}
uno_a_uno = lambda n: [[i] for i in range(n)]
def hymn_do(l):
    t = M[l]['[Hymnus Completorium]'].replace('v. ', '').replace('* ', '')
    est = [[x.strip() for x in e.strip().split('\n') if x.strip()] for e in t.split('_')]
    amen = est[-1].pop() if est[-1][-1].startswith('Am') else ''
    return est, amen
hv_la, amen_la = hymn_do(L); hv_es, amen_es = hymn_do(E)
cap = {l: limpia(lineas_do(M[l]['[Completorium_]'])[0]) for l in (L, E)}
lec = {l: limpia(lineas_do(M[l]['[Lectio Completorium]'])[0]) for l in (L, E)}
resp_l = lambda l: [[x[0], limpia(x)] for x in lineas_do(M[l]['[Responsory Completorium]']) if x[0] in 'VR' and not x.startswith('R.br')]
def resp_do(l):
    if l == L:
        return [['V', 'In manus tuas, Dómine, * comméndo spíritum meum.'], ['R', 'In manus tuas, Dómine, * comméndo spíritum meum.'],
                ['V', 'Redemísti nos, Dómine, Deus veritátis.'], ['R', 'Comméndo spíritum meum.'],
                ['V', 'Glória Patri, et Fílio, et Spirítui Sancto.'], ['R', 'In manus tuas, Dómine, * comméndo spíritum meum.']]
    return [['V', 'A tus manos, Señor, * encomiendo mi espíritu.'], ['R', 'A tus manos, Señor, * encomiendo mi espíritu.'],
            ['V', 'Tú, el Dios leal, nos librarás.'], ['R', 'Encomiendo mi espíritu.'],
            ['V', 'Gloria al Padre, al Hijo, y al Espíritu Santo.'], ['R', 'A tus manos, Señor, * encomiendo mi espíritu.']]
def _resp_do_viejo(l):
    out = []
    for x in lineas_do(M[l]['[Responsory Completorium]']):
        if x.startswith('R.br'): x = 'R' + x[4:]
        if x[0] in 'VR': out.append([x[0], re.sub(r'^[VR]\.\s*', '', x).strip()])
    gl = GLORIA_V['la' if l == L else 'es'][0].replace('* ', '')
    out.insert(4, ['V', gl]); return out[:6] if len(out) > 6 else out

vetus = {
 'nombre': 'Breviario Romano',
 'sub': 'Rúbricas de 1960 (usus antiquior)',
 'dia': {'titulo': 'Feria quinta', 'tiempo': 'Tiempo después de Pentecostés', 'salterio': 'Salterio de la feria', 'color': 'verde'},
 'versiones': {'la': {'n': 'Latín', 'd': 'Breviarium Romanum (1960) · Divinum Officium'},
               'es': {'n': 'Español', 'd': 'Traducción del proyecto Divinum Officium (en desarrollo)'}},
 'secciones': [
  {'k': 'sec', 'id': 'inicio', 't': 'Lectura breve y examen'},
  {'k': 'vr1', 't': {'la': limpia(lineas_do(pr('[Jube domne]', L))[-1]), 'es': limpia(lineas_do(pr('[Jube domne]', E))[0])}},
  {'k': 'prosa', 'n': 'Bendición', 't': {'la': 'Noctem quiétam et finem perféctum concédat nobis Dóminus omnípotens. Amen.', 'es': 'El Señor todopoderoso nos conceda una noche tranquila y una muerte santa. Amén.'}},
  {'k': 'lectura', 'ref': {'la': '1 Pet 5, 8-9', 'es': '1 Pe 5, 8-9'}, 't': {'la': lec[L], 'es': lec[E]}},
  {'k': 'vr', **vr(pr('[Tu autem_]', L), pr('[Tu autem_]', E))},
  {'k': 'vr', **vr(pr('[Adjutorium nostrum]', L), pr('[Adjutorium nostrum]', E))},
  {'k': 'rub', 't': 'Se reza en silencio el Padrenuestro.'},
  {'k': 'prosa', 't': {'la': limpia(pr('[Confiteor_]', L)), 'es': limpia(pr('[Confiteor_]', E))}},
  {'k': 'prosa', 't': {'la': limpia(pr('[Misereatur]', L)), 'es': limpia(pr('[Misereatur]', E))}},
  {'k': 'prosa', 't': {'la': limpia(pr('[Indulgentiam]', L)), 'es': limpia(pr('[Indulgentiam]', E))}},
  {'k': 'vr', **vr(pr('[Converte nos]', L), pr('[Converte nos]', E))},
  {'k': 'vr', **vr(pr('[Deus in adjutorium]', L), pr('[Deus in adjutorium]', E))},
  {'k': 'doxo', 't': {'la': 'Glória Patri, et Fílio, et Spirítui Sancto. Sicut erat in princípio, et nunc, et semper, et in sǽcula sæculórum. Amen. Allelúja.',
                     'es': 'Gloria al Padre, al Hijo y al Espíritu Santo. Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén. Aleluya.'}},
  {'k': 'sec', 'id': 'salmodia', 't': 'Salmodia'},
  {'k': 'ant', 'id': 'v1', 'n': 'Ant.', 't': {'la': 'Adjútor meus * et liberátor meus esto, Dómine.', 'es': 'Señor, * Tú eres mi amparo y mi libertador.'}, 'inc': {'la': 'Adjútor meus *', 'es': 'Señor, *'}, 'gabc': ADJUTOR, 'modo': '8G', 'glosa': GL_ADJ},
  {'k': 'salmo', 'id': 'ps69', 'ant': 'v1', 'titulo': {'la': 'Psalmus 69', 'es': 'Salmo 69'}, 'versos': ps69, 'grupos': {'la': uno_a_uno(len(ps69['la'])), 'es': uno_a_uno(len(ps69['es']))}, 'gloria': True},
  {'k': 'salmo', 'id': 'ps70a', 'ant': 'v1', 'titulo': {'la': 'Psalmus 70 (1-12)', 'es': 'Salmo 70 (1-12)'}, 'versos': ps70a, 'grupos': {'la': uno_a_uno(len(ps70a['la'])), 'es': uno_a_uno(len(ps70a['es']))}, 'gloria': True},
  {'k': 'salmo', 'id': 'ps70b', 'ant': 'v1', 'titulo': {'la': 'Psalmus 70 (13-24)', 'es': 'Salmo 70 (13-24)'}, 'versos': ps70b, 'grupos': {'la': uno_a_uno(len(ps70b['la'])), 'es': uno_a_uno(len(ps70b['es']))}, 'gloria': True},
  {'k': 'ant', 'id': 'v1r', 'rep': 'v1'},
  {'k': 'sec', 'id': 'himno', 't': 'Himno'},
  {'k': 'himno', 'opciones': [{'id': 'telucisv', 'n': 'Te lucis ante términum', 'lang': 'la', 'est': hv_la, 'amen': amen_la, 'gabc': TE_LUCIS_V, 'glosa': TE_LUCIS_V_GLOSA, 'trad': {'es': hv_es, 'amen': amen_es}}]},
  {'k': 'sec', 'id': 'capitulo', 't': 'Capítulo y responsorio'},
  {'k': 'lectura', 'ref': {'la': 'Jer 14, 9', 'es': 'Jer 14, 9'}, 't': {'la': cap[L], 'es': cap[E]}},
  {'k': 'vr1', 't': {'la': 'R. Deo grátias.', 'es': 'R. Demos gracias a Dios.'}},
  {'k': 'resp', 'gabc': IN_MANUS, 'glosa': GL_INMANUS, 'l': {'la': resp_do(L), 'es': resp_do(E)}},
  {'k': 'vr', 'gabc': CUSTODI, 'glosa': GL_CUSTODI, **vr(M[L]['[Versum 4]'], M[E]['[Versum 4]'])},
  {'k': 'sec', 'id': 'cantico', 't': 'Cántico de Simeón'},
  {'k': 'ant', 'id': 'v2', 'n': 'Ant.', 't': {'la': limpia(lineas_do(M[L]['[Ant 4]'])[0]), 'es': limpia(lineas_do(M[E]['[Ant 4]'])[0])}, 'inc': {'la': 'Salva nos, *', 'es': 'Sálvanos, *'}, 'gabc': SALVA_V, 'modo': '3a', 'glosa': GL_SALVA},
  {'k': 'salmo', 'id': 'nuncv', 'ant': 'v2', 'cantico': True, 'titulo': {'la': 'Canticum Simeonis', 'es': 'Cántico de Simeón'}, 'ref': 'Lc 2, 29-32', 'versos': nunc_v, 'grupos': {'la': uno_a_uno(4), 'es': uno_a_uno(4)}, 'gloria': True},
  {'k': 'ant', 'id': 'v2r', 'rep': 'v2'},
  {'k': 'sec', 'id': 'oracion', 't': 'Oración'},
  {'k': 'vr', 'v': {'la': 'Dómine, exáudi oratiónem meam.', 'es': 'Señor, escucha mi oración.'}, 'r': {'la': 'Et clamor meus ad te véniat.', 'es': 'Y llegue a ti mi clamor.'}},
  {'k': 'oremos', 't': {'la': 'Orémus.', 'es': 'Oremos.'}},
  {'k': 'prosa', 't': {'la': limpia(pr('[Oratio Visita_]', L)) + ' Per Dóminum nostrum Iesum Christum, Fílium tuum: qui tecum vivit et regnat in unitáte Spíritus Sancti, Deus, per ómnia sǽcula sæculórum.',
                      'es': limpia(pr('[Oratio Visita_]', E)) + ' Por nuestro Señor Jesucristo, tu Hijo, que vive y reina contigo en la unidad del Espíritu Santo, Dios, por todos los siglos de los siglos.'}, 'amen': {'la': 'Amen.', 'es': 'Amén.'}},
  {'k': 'vr', **vr(pr('[Benedicamus Domino]', L), pr('[Benedicamus Domino]', E))},
  {'k': 'sec', 'id': 'bendicion', 't': 'Bendición'},
  {'k': 'prosa', 't': {'la': limpia(lineas_do(pr('[Benedictio Completorium2]', L))[0].replace('Benedictio. ', '')), 'es': limpia(lineas_do(pr('[Benedictio Completorium2]', E))[0].replace('Bendición. ', ''))}, 'amen': {'la': 'Amen.', 'es': 'Amén.'}},
  {'k': 'sec', 'id': 'mariana', 't': 'Antífona a la Virgen'},
  {'k': 'mariana', 'opciones': [{'id': 'salvev', 'n': 'Salve Regina', 'l': SALVE_TXT, 'gabc': SALVE, 'glosa': GL_SALVE}]},
  {'k': 'vr', 'v': {'la': 'Ora pro nobis, sancta Dei Génetrix.', 'es': 'Ruega por nosotros, santa Madre de Dios.'}, 'r': {'la': 'Ut digni efficiámur promissiónibus Christi.', 'es': 'Para que seamos dignos de alcanzar las promesas de Jesucristo.'}},
  {'k': 'oremos', 't': {'la': 'Orémus.', 'es': 'Oremos.'}},
  {'k': 'prosa', 't': {'la': lineas_do(MA[L]['[Postpentecost]'].split('$Oremus')[1])[0].replace('v. ', '').strip(), 'es': lineas_do(MA[E]['[Postpentecost]'].split('$Oremus')[1])[0].replace('v. ', '').strip()}},
  {'k': 'vr', 'v': {'la': 'Divínum auxílium ✠ máneat semper nobíscum.', 'es': 'Que el auxilio divino ✠ permanezca siempre con nosotros.'}, 'r': {'la': 'Amen.', 'es': 'Amén.'}},
 ]
}

# Gloria del salmo según rito
novus['gloria'] = {'la': GLORIA['la'], 'es79': GLORIA['es']}
vetus['gloria'] = {'la': GLORIA_V['la'], 'es': GLORIA_V['es']}

DATA = {'fecha': '2026-11-05', 'fechaTxt': 'Jueves 5 de noviembre', 'ritos': {'novus': novus, 'vetus': vetus},
        'horas': [['oficio', 'Oficio de lectura', ''], ['laudes', 'Laudes', '7:00'], ['tercia', 'Tercia', '9:00'], ['sexta', 'Sexta', '12:00'],
                  ['nona', 'Nona', '15:00'], ['visperas', 'Vísperas', '19:00'], ['completas', 'Completas', '21:30']],
        'santo': 'San Carlos Borromeo fue ayer; hoy, feria.'}
open(SALIDA, 'w', encoding='utf-8').write('window.DATA=' + json.dumps(DATA, ensure_ascii=False) + ';\n')
print('ok', len(json.dumps(DATA)), 'bytes')
print('Ps15 es:', len(ps15_es), ps15_es_g, '| la:', len(ps15_la))
print('Nunc es:', nunc_es_v)
print('Himno es estrofas:', len(himno_es), [len(e) for e in himno_es])
print('Madre es:', madre_es)
print('Vetus himno:', hv_la, amen_la)
print('Resp vetus:', resp_do(L)); print(resp_do(E))
print('Salve DO la:', SALVE_TXT['la'][:2])
print(TE_LUCIS_LH_GABC[:400])

# ---------------- Traducción interlineal de los salmos (literal, por hemistiquio) ----------------
INTER_PS15 = ['Guárdame, Dios, * porque esperé en ti.',
 'Dije al Señor: «Mi Señor eres tú, * no hay bien para mí sin ti».',
 'Hacia los santos que están en la tierra, varones ilustres, * toda mi voluntad está en ellos.',
 'Se multiplican los dolores de aquellos * que corrieron tras dioses ajenos.',
 'No derramaré sus libaciones de sangre * ni tomaré sus nombres en mis labios.',
 'El Señor es la parte de mi herencia y de mi cáliz: * tú eres quien sostiene mi suerte.',
 'Las cuerdas me cayeron en lugares espléndidos; * además, mi heredad me es hermosa.',
 'Bendeciré al Señor, que me dio entendimiento; * aun de noche me instruyeron mis entrañas.',
 'Tenía siempre al Señor ante mis ojos; * porque está a mi derecha, no vacilaré.',
 'Por esto se alegró mi corazón, † y se gozaron mis entrañas; * además, también mi carne descansará en esperanza.',
 'Porque no abandonarás mi alma en el abismo, * ni dejarás a tu santo ver la corrupción.',
 'Me darás a conocer los caminos de la vida, † plenitud de alegría con tu rostro, * delicias a tu derecha para siempre.']
INTER_NUNC = ['Ahora despides a tu siervo, Señor, * según tu palabra, en paz,',
 'porque han visto mis ojos * tu salvación,',
 'la que preparaste * ante el rostro de todos los pueblos,',
 'luz para revelación a las naciones * y gloria de tu pueblo Israel.']
INTER_GLORIA = ['Gloria al Padre, y al Hijo, * y al Espíritu Santo.', 'Como era en el principio, ahora y siempre, * y por los siglos de los siglos. Amén.']
for sec in novus['secciones']:
    if sec.get('id') == 'ps15': sec['inter'] = INTER_PS15
    if sec.get('id') == 'nunc': sec['inter'] = INTER_NUNC
novus['gloriaInter'] = INTER_GLORIA
for sec in vetus['secciones']:
    if sec.get('k') == 'salmo': sec['inter'] = sec['versos']['es']
vetus['gloriaInter'] = GLORIA_V['es']
assert len(INTER_PS15) == len(ps15_la), (len(INTER_PS15), len(ps15_la))

# ---------------- Traducción interlineal por segmentos (todo el latín) ----------------
def IL(t): return [[a.strip(), b.strip()] for a, b in (x.split(' = ') for x in t.split(' | '))]
GLORIA_IL = 'Glória Patri, = Gloria al Padre, | et Fílio, = y al Hijo, | et Spirítui Sancto. = y al Espíritu Santo. | Sicut erat = Como era | in princípio, = en el principio, | et nunc = y ahora | et semper, = y siempre, | et in sǽcula sæculórum. = y por los siglos de los siglos. | Amen. = Amén. | Allelúia. = Aleluya.'
DEUS_IN = ('Deus, = Dios [mío], | ✠ in adiutórium meum inténde. = ven pronto en mi auxilio.', 'Dómine, = Señor, | ad adiuvándum me festína. = date prisa en socorrerme.')
MISEREATUR = 'Misereátur nostri = Tenga misericordia de nosotros | omnípotens Deus = Dios todopoderoso | et, dimíssis peccátis nostris, = y, perdonados nuestros pecados, | perdúcat nos = nos lleve | ad vitam ætérnam. = a la vida eterna.'
NOCTEM = 'Noctem quiétam = Una noche tranquila | et finem perféctum = y un fin perfecto | concédat nobis = nos conceda | Dóminus omnípotens. = el Señor todopoderoso.'
SALVA_IL = 'Salva nos, = Sálvanos, | Dómine, = Señor, | vigilántes, = despiertos, | custódi nos = guárdanos | dormiéntes, = dormidos, | ut vigilémus = para que velemos | cum Christo, = con Cristo, | et requiescámus = y descansemos | in pace. = en paz.'
RESP_LIT = ['En tus manos, Señor, encomiendo mi espíritu.', 'En tus manos, Señor, encomiendo mi espíritu.', 'Nos redimiste, Señor, Dios de la verdad.', 'Encomiendo mi espíritu.', 'Gloria al Padre, y al Hijo, y al Espíritu Santo.', 'En tus manos, Señor, encomiendo mi espíritu.']
SALVE_LIT = ['Salve, Reina, madre de misericordia;', 'vida, dulzura y esperanza nuestra, salve.', 'A ti clamamos, desterrados hijos de Eva.',
             'A ti suspiramos gimiendo y llorando', 'en este valle de lágrimas.', 'Ea, pues, abogada nuestra,',
             'esos tus ojos misericordiosos vuelve hacia nosotros.', 'Y a Jesús, fruto bendito de tu vientre,',
             'muéstranos después de este destierro.', 'Oh clemente, oh piadosa, oh dulce Virgen María.']
AMEN = 'Amen. = Amén.'

IL_NOVUS = {
 ('vr', 'Deus, ✠'): DEUS_IN,
 ('doxo', ''): GLORIA_IL,
 ('prosa', 'Confíteor'): 'Confíteor = Confieso | Deo omnipoténti = a Dios todopoderoso | et vobis, fratres, = y a vosotros, hermanos, | quia peccávi nimis = que pequé mucho | cogitatióne, = de pensamiento, | verbo, = palabra, | ópere = obra | et omissióne: = y omisión: | mea culpa, = por mi culpa, | mea culpa, = por mi culpa, | mea máxima culpa. = por mi gran culpa. | Ídeo precor = Por eso ruego | beátam Maríam semper Vírginem, = a la bienaventurada María siempre Virgen, | omnes Ángelos et Sanctos, = a todos los ángeles y santos, | et vos, fratres, = y a vosotros, hermanos, | oráre pro me = que oréis por mí | ad Dóminum Deum nostrum. = ante el Señor nuestro Dios.',
 ('vr', 'Misereátur'): (MISEREATUR, AMEN),
 ('lectura', 'Ipse'): 'Ipse autem Deus pacis = Que el mismo Dios de la paz | sanctíficet vos = os santifique | per ómnia, = en todo, | et íntegrum vestrum = y que vuestro ser entero, | spíritus et ánima et corpus = espíritu, alma y cuerpo, | sine queréla = sin reproche | in advéntu = en la venida | Dómini nostri Iesu Christi = de nuestro Señor Jesucristo | servétur. = se conserve.',
 ('ant', 'Caro'): 'Caro mea = Mi carne | requiéscet = descansará | in spe. = en la esperanza.',
 ('ant', 'Salva'): SALVA_IL.replace('cum Christo, =', 'cum Christo =').replace('et requiescámus = y', 'et requiescámus = y'),
 ('oremos', ''): 'Orémus. = Oremos.',
 ('vr', 'Noctem'): (NOCTEM, AMEN),
}
IL_VETUS = {
 ('vr1', 'Iube'): 'Iube, = Dígnate, | Dómine, = Señor, | benedícere. = bendecir.',
 ('prosa', 'Noctem'): NOCTEM + ' | ' + AMEN,
 ('lectura', 'Fratres'): 'Fratres: = Hermanos: | Sóbrii estóte, = sed sobrios | et vigiláte: = y vigilad: | quia adversárius vester = porque vuestro adversario, | diábolus = el diablo, | tamquam leo rúgiens = como león rugiente | círcuit, = ronda, | quærens = buscando | quem dévoret: = a quién devorar: | cui resístite = resistidle | fortes in fide. = firmes en la fe.',
 ('vr', 'Tu autem, Dómine'): ('Tu autem, = Y tú, | Dómine, = Señor, | miserére nobis. = ten piedad de nosotros.', 'Deo grátias. = Gracias a Dios.'),
 ('vr', 'Adiutórium'): ('Adiutórium nostrum = Nuestro auxilio | ✠ in nómine Dómini. = ✠ en el nombre del Señor.', 'Qui fecit = Que hizo | cælum et terram. = el cielo y la tierra.'),
 ('prosa', 'Confíteor'): 'Confíteor Deo omnipoténti, = Confieso a Dios todopoderoso, | beátæ Maríæ semper Vírgini, = a la bienaventurada María siempre Virgen, | beáto Michaéli Archángelo, = al bienaventurado Miguel Arcángel, | beáto Ioánni Baptístæ, = al bienaventurado Juan Bautista, | sanctis Apóstolis Petro et Paulo, = a los santos apóstoles Pedro y Pablo, | et ómnibus Sanctis, = y a todos los santos, | quia peccávi nimis, = que pequé mucho, | cogitatióne, verbo et ópere: = de pensamiento, palabra y obra: | mea culpa, = por mi culpa, | mea culpa, = por mi culpa, | mea máxima culpa. = por mi gran culpa. | Ídeo precor = Por eso ruego | beátam Maríam semper Vírginem, = a la bienaventurada María siempre Virgen, | beátum Michaélem Archángelum, = al bienaventurado Miguel Arcángel, | beátum Ioánnem Baptístam, = al bienaventurado Juan Bautista, | sanctos Apóstolos Petrum et Paulum, = a los santos apóstoles Pedro y Pablo, | et omnes Sanctos, = y a todos los santos, | oráre pro me = que oren por mí | ad Dóminum Deum nostrum. = ante el Señor nuestro Dios.',
 ('prosa', 'Misereátur'): MISEREATUR + ' | ' + AMEN,
 ('prosa', 'Indulgéntiam'): 'Indulgéntiam, = El perdón, | ✠ absolutiónem et remissiónem = ✠ la absolución y la remisión | peccatórum nostrórum = de nuestros pecados | tríbuat nobis = nos conceda | omnípotens et miséricors Dóminus. = el Señor todopoderoso y misericordioso. | ' + AMEN,
 ('vr', 'Convérte'): ('Convérte nos = Conviértenos, | ✠ Deus, salutáris noster. = ✠ oh Dios, salvador nuestro.', 'Et avérte = Y aparta | iram tuam = tu ira | a nobis. = de nosotros.'),
 ('vr', 'Deus ✠'): ('Deus ✠ = Dios [mío], | in adiutórium meum inténde. = ven pronto en mi auxilio.', DEUS_IN[1]),
 ('doxo', ''): GLORIA_IL.replace('et nunc = y ahora', 'et nunc, = y ahora,'),
 ('ant', 'Adiútor'): 'Adiútor meus = Auxilio mío | et liberátor meus = y libertador mío | esto, Dómine. = sé, Señor.',
 ('lectura', 'Tu autem in nobis'): 'Tu autem = Pero tú | in nobis es, = estás en nosotros, | Dómine, = Señor, | et nomen sanctum tuum = y tu santo nombre | invocátum est = ha sido invocado | super nos: = sobre nosotros: | ne derelínquas nos, = no nos abandones, | Dómine, Deus noster. = Señor, Dios nuestro.',
 ('vr1', 'Deo'): 'Deo grátias. = Gracias a Dios.',
 ('vr', 'Custódi'): ('Custódi nos, = Guárdanos, | Dómine, = Señor, | ut pupíllam óculi. = como a la niña del ojo.', 'Sub umbra = Bajo la sombra | alárum tuárum = de tus alas | prótege nos. = protégenos.'),
 ('ant', 'Salva'): SALVA_IL.replace('dormiéntes, =', 'dormiéntes; ='),
 ('vr', 'Dómine, exáudi'): ('Dómine, = Señor, | exáudi oratiónem meam. = escucha mi oración.', 'Et clamor meus = Y mi clamor | ad te véniat. = llegue a ti.'),
 ('oremos', ''): 'Orémus. = Oremos.',
 ('prosa', 'Vísita'): 'Vísita, = Visita, | quǽsumus, = te pedimos, | Dómine, = Señor, | habitatiónem istam, = esta morada, | et omnes insídias inimíci = y todas las asechanzas del enemigo | ab ea longe repélle: = aleja lejos de ella: | Ángeli tui sancti = tus santos ángeles | hábitent in ea, = habiten en ella, | qui nos in pace custódiant; = que nos guarden en paz; | et benedíctio tua = y tu bendición | sit super nos semper. = esté siempre sobre nosotros. | Per Dóminum nostrum Iesum Christum, = Por nuestro Señor Jesucristo, | Fílium tuum: = tu Hijo, | qui tecum vivit et regnat = que vive y reina contigo | in unitáte Spíritus Sancti, = en la unidad del Espíritu Santo, | Deus, = Dios, | per ómnia sǽcula sæculórum. = por todos los siglos de los siglos. | ' + AMEN,
 ('vr', 'Benedicámus'): ('Benedicámus Dómino. = Bendigamos al Señor.', 'Deo grátias. = Gracias a Dios.'),
 ('prosa', 'Benedícat'): 'Benedícat et custódiat nos = Nos bendiga y nos guarde | omnípotens et miséricors Dóminus, = el Señor todopoderoso y misericordioso, | ✠ Pater, et Fílius, et Spíritus Sanctus. = ✠ Padre, Hijo y Espíritu Santo. | ' + AMEN,
 ('vr', 'Ora pro nobis'): ('Ora pro nobis, = Ruega por nosotros, | sancta Dei Génetrix. = santa Madre de Dios.', 'Ut digni efficiámur = Para que seamos hechos dignos | promissiónibus Christi. = de las promesas de Cristo.'),
 ('prosa', 'Omnípotens'): 'Omnípotens sempitérne Deus, = Dios todopoderoso y eterno, | qui gloriósæ Vírginis Matris Maríæ = que de la gloriosa Virgen Madre María | corpus et ánimam, = el cuerpo y el alma, | ut dignum Fílii tui habitáculum = para que digna morada de tu Hijo | éffici mererétur, = mereciera llegar a ser, | Spíritu Sancto cooperánte, = con la cooperación del Espíritu Santo, | præparásti: = preparaste: | da, ut, = concede que, | cuius commemoratióne lætámur, = quienes nos alegramos con su memoria, | eius pia intercessióne, = por su piadosa intercesión, | ab instántibus malis = de los males presentes | et a morte perpétua = y de la muerte eterna | liberémur. = seamos librados. | Per eúmdem Christum Dóminum nostrum. = Por el mismo Cristo nuestro Señor. | ' + AMEN,
 ('vr', 'Divínum'): ('Divínum auxílium = El auxilio divino | ✠ máneat semper nobíscum. = ✠ permanezca siempre con nosotros.', AMEN),
}
# ---------------- Normas de latín: i (no j), ligaduras æ/œ ----------------
EXC = re.compile(r'Micha[eé]l|Israel|aer\b', re.I)
def lat(s):
    if not isinstance(s, str): return s
    def palabra(m):
        w = m.group(0)
        if EXC.search(w): return w.replace('j', 'i').replace('J', 'I')
        w = w.replace('j', 'i').replace('J', 'I')
        w = w.replace('aé', 'ǽ').replace('ae', 'æ').replace('Ae', 'Æ').replace('AE', 'Æ').replace('oe', 'œ').replace('Oe', 'Œ')
        return w
    return re.sub(r"[A-Za-zÀ-ÿæœǽ]+", palabra, s)
def lat_gabc(g):
    if '%%' in g: cab, cuerpo = g.split('%%', 1); cab += '%%'
    else: cab, cuerpo = '', g
    partes = re.split(r'(\([^)]*\)|<[^>]*>)', cuerpo)
    return cab + ''.join(p if (p.startswith('(') or p.startswith('<')) else lat(p) for p in partes)
def lat_rec(o):
    if isinstance(o, str): return lat(o)
    if isinstance(o, list): return [lat_rec(x) for x in o]
    return o
def normalizar(o):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k == 'la': o[k] = lat_rec(v)
            elif k == 'gabc' and isinstance(v, str): o[k] = lat_gabc(v)
            elif k == 'glosa' and isinstance(v, list): o[k] = [[lat(a), b] for a, b in v]
            elif k == 'est' and o.get('lang') == 'la': o[k] = lat_rec(v)
            elif k == 'amen' and o.get('lang') == 'la': o[k] = lat(v)
            else: normalizar(v)
    elif isinstance(o, list):
        for x in o: normalizar(x)
normalizar(DATA)

# ---------------- Asignar la interlineal y comprobar que cubre el latín ----------------
def _n(t): return re.sub(r'[^a-zæœǽáéíóúý✠]', '', t.lower().replace('*', ''))
def asignar(rito, tabla):
    usadas = set(); faltan = []
    for sec in rito['secciones']:
        k = sec.get('k')
        if k == 'resp': sec['lit'] = RESP_LIT; continue
        if k == 'mariana':
            for o in sec['opciones']:
                if o['l'].get('la') and len(o['l']['la']) == len(SALVE_LIT): o['lit'] = SALVE_LIT
            continue
        if k not in ('vr', 'vr1', 'prosa', 'doxo', 'lectura', 'ant', 'oremos') or sec.get('rep'): continue
        texto = (sec.get('v') or sec.get('t') or {}).get('la')
        if texto is None: continue
        clave = next((c for c in tabla if c[0] == k and texto.replace('R. ', '').startswith(c[1])), None)
        if not clave: faltan.append((k, texto[:40])); continue
        usadas.add(clave); val = tabla[clave]
        if k == 'vr':
            sec['ilv'], sec['ilr'] = IL(val[0]), IL(val[1])
            pares = [(sec['v']['la'], sec['ilv']), (sec['r']['la'], sec['ilr'])]
        else:
            sec['il'] = IL(val); extra = (' ' + sec['amen']['la']) if sec.get('amen') and k == 'prosa' and 'Amen' not in texto else ''
            pares = [(texto.replace('R. ', '') + extra, sec['il'])]
        for lat_, il in pares:
            if _n(lat_) != _n(' '.join(a for a, b in il)): print('  NO COINCIDE:', lat_[:50], '|', ' '.join(a for a, b in il)[:50])
    print('  sin interlineal:', faltan, '| no usadas:', [c for c in tabla if c not in usadas])
print('novus'); asignar(novus, IL_NOVUS)
print('vetus'); asignar(vetus, IL_VETUS)

open(SALIDA, 'w', encoding='utf-8').write('window.DATA=' + json.dumps(DATA, ensure_ascii=False) + ';\n')
print('latín normalizado')
