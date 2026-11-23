#!/usr/bin/env python3
"""Himnos latinos del libro (Apéndice IV de la Liturgia de las Horas), primera etapa: propio del tiempo y comunes.

Toma de la extracción del libro (extraccion/apendices/apendices.json) qué himno va en cada tiempo, común y hora, y el
texto de cada himno con tildes, æ/œ e i del corpus «latin-ecclesiastic-accents» (gregorio-project, CC0; textos de *Te
decet hymnus*, A. Lentini, 1984: la edición oficial de los himnos de la Liturgia Horarum). Compara cada verso con el
libro (sin tildes) y anota las diferencias. No toca la app.

Uso: python3 extraccion/himnos_latinos.py RUTA/latin-ecclesiastic-accents/corpus/hymns
Escribe extraccion/apendices/himnos_latinos.yaml.
"""
import difflib, json, os, re, sys, unicodedata
import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))

# Qué himno va en cada lugar (orden del libro, tomos I y II; la asignación sigue las rúbricas y el orden de páginas de la
# extracción). (grupo, sección, hora, incipit, nota). Hora: visperas1, visperas (II o única), completas, oficio, laudes,
# tercia, sexta, nona.
USO = [
    # ---------- Adviento (tomo I, pp. 1063-1069) ----------
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'visperas', 'Conditor alme siderum', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'completas', 'Te lucis ante terminum', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'oficio', 'Verbum supernum prodiens', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'laudes', 'Vox clara ecce intonat', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'tercia', 'Nunc Sancte nobis Spiritus', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'sexta', 'Rector potens verax Deus', ''),
    ('Tiempo de Adviento', 'Hasta el 16 de diciembre', 'nona', 'Rerum Deus tenax vigor', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'visperas', 'Verbum salutis omnium', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'completas', 'Christe qui splendor et dies', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'oficio', 'Veni redemptor gentium', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'laudes', 'Magnis prophetae vocibus', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'tercia', 'Certum tenentes ordinem', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'sexta', 'Dicamus laudes Domino', ''),
    ('Tiempo de Adviento', 'Desde el 17 de diciembre', 'nona', 'Ternis horarum terminis', ''),
    # ---------- Navidad (tomo I, pp. 1070-1082) ----------
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'visperas', 'Christe redemptor omnium ex Patre', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'completas', 'Te lucis ante terminum', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'oficio', 'Candor aeternae Deitatis alme', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'laudes', 'A solis ortus cardine', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'tercia', 'Nunc Sancte nobis Spiritus', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'sexta', 'Rector potens verax Deus', ''),
    ('Tiempo de Navidad', 'Hasta la Epifanía', 'nona', 'Rerum Deus tenax vigor', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'visperas', 'Hostis Herodes impie', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'completas', 'Christe qui splendor et dies', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'oficio', 'Magi videntes parvulum', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'laudes', 'Quicumque Christum quaeritis', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'tercia', 'Certum tenentes ordinem', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'sexta', 'Dicamus laudes Domino', ''),
    ('Tiempo de Navidad', 'Desde la Epifanía', 'nona', 'Ternis horarum terminis', ''),
    ('Tiempo de Navidad', 'Sagrada Familia', 'visperas', 'O lux beata caelitum', ''),
    ('Tiempo de Navidad', 'Sagrada Familia', 'oficio', 'Dulce fit nobis memorare parvum', ''),
    ('Tiempo de Navidad', 'Sagrada Familia', 'laudes', 'Christe splendor Patris', ''),
    ('Tiempo de Navidad', 'Santa María, Madre de Dios (1 de enero)', 'visperas', 'Corde natus ex Parentis', ''),
    ('Tiempo de Navidad', 'Santa María, Madre de Dios (1 de enero)', 'oficio', 'Radix Iesse floruit', ''),
    ('Tiempo de Navidad', 'Santa María, Madre de Dios (1 de enero)', 'laudes', 'Fit porta Christi pervia', ''),
    ('Tiempo de Navidad', 'Bautismo del Señor', 'visperas1', 'A Patre Unigenite', ''),
    ('Tiempo de Navidad', 'Bautismo del Señor', 'oficio', 'Implente munus debitum', 'También para las II Vísperas (rúbrica del libro).'),
    ('Tiempo de Navidad', 'Bautismo del Señor', 'visperas', 'Implente munus debitum', ''),
    ('Tiempo de Navidad', 'Bautismo del Señor', 'laudes', 'Iesus refulsit omnium', ''),
    # ---------- Cuaresma (tomo II, pp. 2708-2713) ----------
    ('Tiempo de Cuaresma', 'Oficio dominical', 'visperas', 'Audi benigne Conditor', ''),
    ('Tiempo de Cuaresma', 'Oficio dominical', 'oficio', 'Ex more docti mystico', ''),
    ('Tiempo de Cuaresma', 'Oficio dominical', 'laudes', 'Precemur omnes cernui', ''),
    ('Tiempo de Cuaresma', 'Oficio ferial', 'visperas', 'Iesu quadragenariae', ''),
    ('Tiempo de Cuaresma', 'Oficio ferial', 'oficio', 'Nunc tempus acceptabile', ''),
    ('Tiempo de Cuaresma', 'Oficio ferial', 'laudes', 'Iam Christe sol iustitiae', ''),
    ('Tiempo de Cuaresma', 'Oficio dominical y ferial', 'tercia', 'Dei fide qua vivimus', ''),
    ('Tiempo de Cuaresma', 'Oficio dominical y ferial', 'sexta', 'Qua Christus hora sitiit', ''),
    ('Tiempo de Cuaresma', 'Oficio dominical y ferial', 'nona', 'Ternis ter horis numerus', ''),
    ('Tiempo de Cuaresma', 'Semanas I, III y V', 'completas', 'Te lucis ante terminum', ''),
    ('Tiempo de Cuaresma', 'Semanas II y IV', 'completas', 'Christe qui splendor et dies', ''),
    # ---------- Semana Santa y Triduo (tomo II, pp. 2713-2719) ----------
    ('Semana Santa', 'Semana Santa (y ferias de la semana V de Cuaresma)', 'visperas', 'Vexilla regis prodeunt', 'Rúbrica del libro (p. 2713): en las ferias de la semana V de Cuaresma, en el Oficio de lectura, Laudes y Vísperas, se pueden tomar estos himnos.'),
    ('Semana Santa', 'Semana Santa (y ferias de la semana V de Cuaresma)', 'completas', 'Christe qui splendor et dies', ''),
    ('Semana Santa', 'Semana Santa (y ferias de la semana V de Cuaresma)', 'oficio', 'Pange lingua gloriosi proelium', ''),
    ('Semana Santa', 'Semana Santa (y ferias de la semana V de Cuaresma)', 'laudes', 'En acetum fel arundo', ''),
    ('Semana Santa', 'Domingo de Ramos', 'tercia', 'Celsae salutis gaudia', 'El libro lo da para la Hora intermedia; para las otras Horas, uno de los de Cuaresma (Tercia: Dei fide; Sexta: Qua Christus; Nona: Ternis ter horis).'),
    ('Semana Santa', 'Jueves de la Cena del Señor', 'visperas', 'O memoriale mortis Domini', ''),
    ('Semana Santa', 'Viernes Santo', 'tercia', 'Salva Redemptor plasma tuum nobile', ''),
    ('Semana Santa', 'Viernes Santo', 'sexta', 'Crux mundi benedictio', ''),
    ('Semana Santa', 'Viernes Santo', 'nona', 'Per crucem Christe quaesumus', ''),
    ('Semana Santa', 'Sábado Santo', 'oficio', 'Christe caelorum Domine', ''),
    ('Semana Santa', 'Sábado Santo', 'laudes', 'Tibi Redemptor omnium', 'Tercia, Sexta y Nona: como el Viernes Santo (rúbrica del libro).'),
    ('Semana Santa', 'Sábado Santo', 'visperas', 'Auctor salutis unice', ''),
    # ---------- Pascua (tomo II, pp. 2720-2732) ----------
    ('Tiempo pascual', 'Hasta la Ascensión', 'visperas', 'Ad cenam Agni providi', ''),
    ('Tiempo pascual', 'Hasta la Ascensión', 'visperas', 'O rex aeterne Domine', 'Si se prefiere, en las ferias después de la Octava de Pascua.'),
    ('Tiempo pascual', 'Todo el tiempo', 'completas', 'Iesu redemptor saeculi', ''),
    ('Tiempo pascual', 'Hasta la Ascensión', 'oficio', 'Hic est dies verus Dei', ''),
    ('Tiempo pascual', 'Hasta la Ascensión', 'oficio', 'Laetare caelum desuper', 'Si se prefiere, en las ferias después de la Octava de Pascua.'),
    ('Tiempo pascual', 'Hasta la Ascensión', 'laudes', 'Aurora lucis rutilat', ''),
    ('Tiempo pascual', 'Hasta la Ascensión', 'laudes', 'Chorus novae Ierusalem', 'Si se prefiere, en las ferias después de la Octava de Pascua.'),
    ('Tiempo pascual', 'Todo el tiempo', 'tercia', 'Iam surgit hora tertia', 'También después de la Ascensión (rúbrica del libro).'),
    ('Tiempo pascual', 'Todo el tiempo', 'sexta', 'Venite servi supplices', ''),
    ('Tiempo pascual', 'Todo el tiempo', 'nona', 'Haec hora quae resplenduit', ''),
    ('Tiempo pascual', 'La Ascensión del Señor (y hasta Pentecostés)', 'visperas', 'Iesu nostra redemptio', ''),
    ('Tiempo pascual', 'La Ascensión del Señor (y hasta Pentecostés)', 'oficio', 'Aeterne rex altissime', ''),
    ('Tiempo pascual', 'La Ascensión del Señor (y hasta Pentecostés)', 'laudes', 'Optatus votis omnium', ''),
    ('Tiempo pascual', 'Después de la Ascensión', 'visperas', 'Veni creator Spiritus', 'Ferias después de la Ascensión; Oficio de lectura, «Ætérne rex altíssime»; Laudes, «Optatus votis ómnium» (rúbrica del libro).'),
    ('Tiempo pascual', 'Domingo de Pentecostés', 'visperas', 'Veni creator Spiritus', ''),
    ('Tiempo pascual', 'Domingo de Pentecostés', 'oficio', 'Lux iucunda lux insignis', ''),
    ('Tiempo pascual', 'Domingo de Pentecostés', 'laudes', 'Beata nobis gaudia', ''),
    ('Tiempo pascual', 'Domingo de Pentecostés', 'tercia', 'Iam Christus astra ascenderat', ''),
    # ---------- Comunes (tomo I, pp. 1090-1119; tomos II y III para lo que agregan) ----------
    ('Comunes', 'Dedicación de una iglesia', 'visperas', 'Urbs Ierusalem beata', ''),
    ('Comunes', 'Dedicación de una iglesia', 'oficio', 'Christe cunctorum dominator alme', ''),
    ('Comunes', 'Dedicación de una iglesia', 'laudes', 'Angularis fundamentum', ''),
    ('Comunes', 'Santa María Virgen', 'visperas1', 'Maria quae mortalium', ''),
    ('Comunes', 'Santa María Virgen', 'oficio', 'Quem terra pontus aethera', ''),
    ('Comunes', 'Santa María Virgen', 'laudes', 'O gloriosa Domina', ''),
    ('Comunes', 'Santa María Virgen', 'visperas', 'Ave maris stella', ''),
    ('Comunes', 'Santa María en sábado', 'oficio', 'O virgo mater filia', 'Tomo III. O bien los himnos O gloriosa Domina o Ave maris stella.'),
    ('Comunes', 'Santa María en sábado', 'laudes', 'Quae caritatis fulgidum', 'Tomo III.'),
    ('Comunes', 'Apóstoles', 'visperas', 'Exsultet caelum laudibus', ''),
    ('Comunes', 'Apóstoles', 'oficio', 'O sempiternae curiae', ''),
    ('Comunes', 'Apóstoles', 'laudes', 'O sempiternae curiae', 'Tomo II (tiempo pascual: Laudes). El tomo I no trae himno de Laudes.'),
    ('Comunes', 'Apóstoles en el tiempo pascual', 'visperas', 'Tristes erant Apostoli', 'Tomo II. Para el Oficio de lectura, como en el Propio de los santos.'),
    ('Comunes', 'Apóstoles en el tiempo pascual', 'laudes', 'Claro paschali gaudio', 'Tomo II.'),
    ('Comunes', 'Varios mártires', 'visperas', 'Sanctorum meritis inclita gaudia', ''),
    ('Comunes', 'Varios mártires', 'oficio', 'Rex gloriose martyrum', ''),
    ('Comunes', 'Varios mártires', 'laudes', 'Aeterna Christi munera', ''),
    ('Comunes', 'Un mártir', 'visperas', 'Deus tuorum militum', ''),
    ('Comunes', 'Un mártir', 'oficio', 'Beate martyr prospera', 'Para una mártir: «Beata martyr».'),
    ('Comunes', 'Un mártir', 'laudes', 'Martyr Dei qui unicum', 'Para una mártir: «Martyr Dei, quae unicum».'),
    ('Comunes', 'Una virgen mártir / una santa mártir', 'visperas', 'Virginis Proles opifexque Matris', ''),
    ('Comunes', 'Una virgen mártir / una santa mártir', 'oficio', 'O Christe flos convallium', ''),
    ('Comunes', 'Una virgen mártir / una santa mártir', 'laudes', 'O castitatis signifer', ''),
    ('Comunes', 'Pastores', 'visperas', 'Vir celse forma fulgida', 'La estrofa 4 cambia: para un papa, «Tu Petri ovile caelitus»; para un obispo, «Virtute factus ditior»; para un presbítero, «Regalis huius culminis».'),
    ('Comunes', 'Pastores', 'visperas', 'Sacrata nobis gaudia', ''),
    ('Comunes', 'Pastores', 'oficio', 'Christe pastorum caput atque princeps', 'La estrofa 2 cambia: papa, «Quas oves Petro dederas»; obispo, «Strenuum bello pugilem»; presbítero, «Hunc tibi electum faciens ministrum».'),
    ('Comunes', 'Pastores', 'oficio', 'Dum sacerdotum celebrant fideles', ''),
    ('Comunes', 'Pastores', 'laudes', 'Inclitus rector pater atque prudens', 'La estrofa 2 cambia: papa, «Qui Petri summa cathedra residens»; obispo, «Qui sacerdotis, ducis ac magistri»; presbítero, «Ipse dux clarus fuit et magister».'),
    ('Comunes', 'Pastores', 'laudes', 'Hi sacerdotes Domini sacrati', ''),
    ('Comunes', 'Doctores de la Iglesia', 'visperas', 'Aeterne sol qui lumine', 'Vísperas y Oficio de lectura.'),
    ('Comunes', 'Doctores de la Iglesia', 'oficio', 'Aeterne sol qui lumine', ''),
    ('Comunes', 'Doctores de la Iglesia', 'laudes', 'Doctor aeternus coleris piusque', ''),
    ('Comunes', 'Vírgenes', 'visperas', 'Iesu corona virginum', 'También para Laudes cuando son varias vírgenes (rúbrica del libro).'),
    ('Comunes', 'Vírgenes', 'oficio', 'Dulci depromat carmine', ''),
    ('Comunes', 'Vírgenes', 'oficio', 'Gaudentes festum colimus', ''),
    ('Comunes', 'Vírgenes', 'laudes', 'Aptata virgo lampade', ''),
    ('Comunes', 'Santos varones', 'visperas', 'Iesu redemptor omnium perpes corona', 'Vísperas y Oficio de lectura.'),
    ('Comunes', 'Santos varones', 'oficio', 'Iesu redemptor omnium perpes corona', ''),
    ('Comunes', 'Santos varones (varios)', 'visperas', 'Inclitos Christi famulos canamus', 'Vísperas y Oficio de lectura.'),
    ('Comunes', 'Santos varones (varios)', 'oficio', 'Inclitos Christi famulos canamus', ''),
    ('Comunes', 'Santos varones', 'laudes', 'Iesu corona celsior', ''),
    ('Comunes', 'Santos varones', 'laudes', 'Beata caeli gaudia', ''),
    ('Comunes', 'Santas mujeres', 'visperas', 'Fortem virili pectore', ''),
    ('Comunes', 'Santas mujeres', 'visperas', 'Christe cunctorum sator et redemptor', ''),
    ('Comunes', 'Santas mujeres', 'oficio', 'Haec femina laudabilis', ''),
    ('Comunes', 'Santas mujeres (varias)', 'oficio', 'Hae feminae laudabiles', ''),
    ('Comunes', 'Santas mujeres', 'laudes', 'Nobilem Christi famulam diserta', ''),
    ('Comunes', 'Santas mujeres (varias)', 'laudes', 'Nobiles Christi famulas diserta', ''),
    ('Comunes', 'Santos religiosos', 'visperas', 'Laeti colentes famulum', 'Vísperas y Oficio de lectura. Para una religiosa: «famulam».'),
    ('Comunes', 'Santos religiosos', 'oficio', 'Laeti colentes famulum', ''),
    ('Comunes', 'Santos religiosos', 'laudes', 'O Redemptoris pietas colenda', ''),
    ('Comunes', 'Oficio de difuntos', 'oficio', 'Qui vivis ante saecula', 'La estrofa 4 cambia: por un difunto, por una difunta, por varios.'),
    ('Comunes', 'Oficio de difuntos', 'laudes', 'Spes Christe nostrae veniae', 'La estrofa 4 cambia: por un difunto («Sed et qui frater»), por una difunta («Sed et quae soror»), por varios («Sed et qui fratres»).'),
    ('Comunes', 'Oficio de difuntos', 'visperas', 'Immensae rex potentiae', 'La estrofa 4 cambia: «Tuumque voca famulum», «Tuamque voca famulam», «Fratres et omnes advoca».'),
    ('Comunes', 'Oficio de difuntos', 'tercia', 'Qui lacrimatus Lazarum', 'Hora intermedia: el libro da estrofas para repartir entre Tercia, Sexta y Nona.'),
]

# Donde el libro trae otra doxología que *Te decet hymnus*, va la del libro (con tildes puestas a mano) y se anota.
DOXOLOGIA_LIBRO = {
    'nunc-sancte-nobis-spiritus': ['Præsta, Pater piíssime,', 'Patríque compar Únice,', 'cum Spíritu Paráclito', 'regnans per omne sǽculum.'],
    'rector-potens-verax-deus': ['Præsta, Pater piíssime,', 'Patríque compar Únice,', 'cum Spíritu Paráclito', 'regnans per omne sǽculum.'],
    'rerum-deus-tenax-vigor': ['Præsta, Pater piíssime,', 'Patríque compar Únice,', 'cum Spíritu Paráclito', 'regnans per omne sǽculum.'],
    'veni-redemptor-gentium': ['Glória tibi, Dómine,', 'qui natus es de Vírgine,', 'cum Patre et Sancto Spíritu,', 'in sempitérna sǽcula.'],
}

# Palabras de tres sílabas o más que el corpus no trae con tilde (mayúscula inicial, o texto propio del libro): a mano
ACENTO_MANO = {'Abrahæ': 'Ábrahæ', 'Angeli': 'Ángeli', 'Angelus': 'Ángelus', 'Assidet': 'Ássidet', 'Edomant': 'Edómant',
               'Inclitos': 'Ínclitos', 'Inclitus': 'Ínclitus', 'Intonat': 'Íntonat', 'Omega': 'Ómega', 'Unice': 'Únice',
               'Unitas': 'Únitas', 'damnabit': 'damnábit', 'Damnabit': 'Damnábit', 'flammarum': 'flammárum',
               'prænites': 'prǽnites', 'turbines': 'túrbines', 'Vocabit': 'Vocábit', 'vocabit': 'vocábit',
               'Volvamur': 'Volvámur', 'volvamur': 'volvámur', 'noxios': 'nóxios'}

ESTROFA_FIJA = {'angularis-fundamentum': 6, 'fit-porta-christi-pervia': 4}   # estrofas de seis versos (el libro y el corpus no las separan)

HORAS = {'visperas1': 'I Vísperas', 'visperas': 'Vísperas', 'completas': 'Completas', 'oficio': 'Oficio de lectura',
         'laudes': 'Laudes', 'tercia': 'Tercia', 'sexta': 'Sexta', 'nona': 'Nona'}


def norm(s):
    s = re.sub(r'\[[^\]]*\]', ' ', s)   # alternativas del libro: «Hi [Hae]» → «Hi»
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('æ', 'ae').replace('Æ', 'ae').replace('œ', 'oe').replace('Œ', 'oe').replace('AE', 'ae').replace('OE', 'oe')
    s = s.lower().replace('j', 'i')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', s)).strip()


def libro():
    """Todas las piezas con estrofas del Apéndice IV: lista de (bloque, hora, estrofas, fuentes)."""
    d = json.load(open(os.path.join(AQUI, 'apendices', 'apendices.json'), encoding='utf-8'))
    IV = [a for a in d['apendices'] if a['numero'] == 'IV'][0]
    out = []
    for b in IV['bloques']:
        for h, partes in b['horas'].items():
            for p in partes:
                for pz in p['piezas']:
                    for v in pz['variantes']:
                        if 'estrofas' in v:
                            out.append((b['titulo'], h, [[l['texto'] for l in e] for e in v['estrofas']], v['fuentes']))
    return out


ESTROFAS = {}


def corpus(ruta):
    c = {}
    for f in sorted(os.listdir(ruta)):
        if f.endswith('.txt'):
            crudo = open(os.path.join(ruta, f), encoding='utf-8').read().replace('\ufeff', '').strip()
            bloques = [[l.strip() for l in b.split('\n') if l.strip()] for b in re.split(r'\n\s*\n', crudo)]
            ls = [l for b in bloques for l in b]
            if ls and re.fullmatch(r'Amen\.?', ls[-1]):   # «Amen.» en renglón aparte
                ls = ls[:-1]; ls[-1] += ' Amen.'
                if bloques[-1] == ['Amen.'] or bloques[-1] == ['Amen']: bloques = bloques[:-1]
                else: bloques[-1] = bloques[-1][:-1]
            c[f[:-4]] = ls
            ESTROFAS[f[:-4]] = [len(b) for b in bloques] if len(bloques) > 1 else None
    return c


def con_tildes(linea, dic):
    """Un verso del libro (sin tildes, con ae/oe) con las formas del corpus: cada palabra como aparece en el corpus."""
    def una(m):
        w = m.group(0); f = dic.get(norm(w))
        if not f:
            f = w.replace('ae', 'æ').replace('oe', 'œ').replace('AE', 'Æ').replace('Ae', 'Æ')
            return f
        return f[0].upper() + f[1:] if w[0].isupper() else f[0].lower() + f[1:]
    return re.sub(r"[A-Za-zÀ-ÿǼǽæœÆŒ]+", una, linea)


def mejor_corpus(C, lineas_ref):
    """El archivo del corpus que más versos comparte con el texto dado (normalizados)."""
    ref = [norm(l) for l in lineas_ref if norm(l)]
    mejor, pm = None, 0
    for k, ls in C.items():
        n = set(norm(l) for l in ls)
        p = sum(1 for l in ref if l in n) / max(len(ref), 1)
        p -= 0.001 * len(k)   # a igual coincidencia, el archivo de nombre más corto (sin «feminine», «1»…)
        if re.search(r'feminine|pro una|pro pluribus|defuncta', k):
            p -= 0.05             # la forma masculina y singular es la principal; las otras, variantes
        if p > pm:
            mejor, pm = k, p
    return mejor, pm


def main():
    ruta = sys.argv[1]
    C = corpus(ruta)
    import collections
    cuenta = collections.defaultdict(collections.Counter)
    for ls in C.values():
        for l in ls:
            for w in re.findall(r"[A-Za-zÀ-ÿǼǽæœÆŒ]+", l):
                cuenta[norm(w)][w.lower()] += 1
    global DIC
    DIC = {k: c.most_common(1)[0][0] for k, c in cuenta.items()}
    L = libro()
    himnos, uso = {}, []
    for grupo, seccion, hora, incipit, nota in USO:
        ni = norm(incipit)
        # en el libro: la pieza más larga cuyo comienzo coincide con el incipit
        n3 = min(3, len(ni.split()))
        tres = lambda t: ' '.join(norm(t).split()[:n3])
        cand = [x for x in L if tres(' '.join(x[2][0])) == tres(incipit) or (incipit.startswith('A ') and tres('A ' + ' '.join(x[2][0])) == tres(incipit))]
        # el del bloque del libro que corresponde (Adviento, Cuaresma, Común de…); si no, el más largo
        claves = [w for w in norm(grupo + ' ' + seccion).split() if len(w) > 4 and w not in ('tiempo', 'desde', 'hasta', 'oficio', 'comunes')]
        cand.sort(key=lambda x: (-sum(1 for w in claves if w in norm(x[0])), -sum(len(e) for e in x[2])))
        lib = cand[0] if cand else None
        lineas_libro = [l for e in lib[2] for l in e] if lib else []
        # en el corpus: por el incipit y los versos del libro
        lineas_libro = [re.sub(r'\s*Am[eé]n\.?$', '', l) for l in lineas_libro]
        lineas_libro = [l for l in lineas_libro if l.strip()]
        ck, pm = mejor_corpus(C, lineas_libro or [incipit])
        pm = max(0, round(pm + 0.001 * len(ck or ''), 2))
        texto = C.get(ck, [])
        clave = re.sub(r'[^a-z]+', '-', norm(incipit))[:40].strip('-')
        if clave not in himnos:
            # estrofas: como las del libro (cantidad de versos de cada una); si no coinciden, de a 4
            largos = ESTROFAS.get(ck) or ([len(e) for e in lib[2]] if lib else [])
            amen = texto and re.search(r'\s*Amen\.?$', texto[-1])
            cuerpo = texto[:-1] + [re.sub(r'\s*Amen\.?$', '', texto[-1])] if amen else texto
            if sum(largos) == len(cuerpo) and len(set(largos)) > 1:
                # el libro partió o juntó estrofas: estrofas iguales, con el largo que dé la cuenta exacta
                n = next((m for m in (len(cuerpo) // max(len(largos), 1), 4, 6, 3, 5) if m and len(cuerpo) % m == 0), 4)
                largos = [n] * (len(cuerpo) // n)
            if sum(largos) != len(cuerpo):
                # el libro parte o recorta; se toma el largo más común
                ne = len(lib[2]) if lib else 0
                n = len(cuerpo) // ne if ne and len(cuerpo) % ne == 0 else (max(set(largos), key=largos.count) if largos else 4)
                largos = [n] * (len(cuerpo) // n) + ([len(cuerpo) % n] if len(cuerpo) % n else [])
            if clave in ESTROFA_FIJA:
                largos = [ESTROFA_FIJA[clave]] * (len(cuerpo) // ESTROFA_FIJA[clave])
            est, i = [], 0
            for n in largos:
                est.append(cuerpo[i:i + n]); i += n
            # diferencias con el libro, verso por verso (sin tildes)
            nl = [norm(l) for l in lineas_libro]
            nc = [norm(l) for l in cuerpo]
            dif = []
            if lineas_libro:
                sm = difflib.SequenceMatcher(None, nl, nc, autojunk=False)
                for op, a1, a2, b1, b2 in sm.get_opcodes():
                    if op == 'equal':
                        continue
                    A, B = lineas_libro[a1:a2], cuerpo[b1:b2]
                    # mismo largo y casi iguales: error de la extracción del PDF (taetran, gigans, saneto…)
                    def parecidas(x, y):   # palabra por palabra: cada una casi igual (letras cambiadas por el OCR)
                        px, py = norm(x).split(), norm(y).split()
                        return len(px) == len(py) and all(difflib.SequenceMatcher(None, a, b).ratio() >= 0.6 for a, b in zip(px, py))
                    def falta_palabra(x, y):   # al libro le falta una palabra (la capitular que no se extrajo: «Patre» por «A Patre»; «iam»)
                        px, py = norm(x).split(), norm(y).split()
                        return len(py) == len(px) + 1 and any(py[:i] + py[i + 1:] == px for i in range(len(py)))
                    errata = len(A) == len(B) and all(parecidas(x, y) or falta_palabra(x, y) for x, y in zip(A, B))
                    # encabezados que la extracción metió dentro del himno («COMÚN DE MÁRTIRES») o estrofas que no extrajo
                    if not B and all(re.fullmatch(r'[A-ZÁÉÍÓÚÑ ,]+|Para .*|TIEMPO .*', x.strip()) for x in A):
                        continue
                    dif.append({'tipo': 'errata del PDF' if errata else 'texto distinto', 'libro': A, 'corpus': B})
            ultima_corpus = list(est[-1]) if est else []
            # variantes de texto del libro (mismo número de versos): va el texto del libro, con las tildes del corpus
            for x in dif:
                if x['tipo'] == 'texto distinto' and x['libro'] and len(x['libro']) == len(x['corpus']):
                    nuevo = [con_tildes(l, DIC) for l in x['libro']]
                    for e in est:
                        for j, l in enumerate(e):
                            if l in x['corpus']:
                                v = nuevo[x['corpus'].index(l)]
                                if l[:1].islower():   # mayúscula solo donde la pone el corpus (no al comienzo de cada verso)
                                    v = v[:1].lower() + v[1:]
                                e[j] = v
                    x['tipo'] = 'variante del libro'
                    x['va'] = nuevo
            if clave in DOXOLOGIA_LIBRO:
                otra = est[-1]
                est[-1] = DOXOLOGIA_LIBRO[clave]
                dif = [x for x in dif if x['tipo'] not in ('texto distinto', 'variante del libro') or not set(x['corpus']) & set(ultima_corpus)] + [{'tipo': 'doxología del libro', 'libro': est[-1], 'corpus': ultima_corpus}]
            est = [[re.sub(r"[A-Za-zÀ-ÿǼǽæœÆŒ]+", lambda m: ACENTO_MANO.get(m.group(0), m.group(0)), l) for l in e] for e in est]
            # mayúscula solo al comienzo del himno, de una oración o de un nombre (el libro de este himno la pone en cada verso)
            plano = [l for e in est for l in e]
            if sum(1 for l in plano[1:] if l[:1].isupper()) > 0.8 * (len(plano) - 1):
                prev = ''
                for e in est:
                    for j, l in enumerate(e):
                        if prev and not re.search(r'[.!?]$', prev) and l[:1].isupper() and not re.match(r'(Deus|Dómin|Christ|Iesu|Pat|Fíli|Spíri|Sancte|Virgo|Marí|Trínit|Agnus|Iúdic)', l):
                            e[j] = l[0].lower() + l[1:]
                        prev = e[j]
                        l = e[j]
            himnos[clave] = {
                'incipit': cuerpo[0] if cuerpo else incipit,
                'estrofas': est,
                'amen': bool(amen),
                'fuente_texto': f'latin-ecclesiastic-accents, corpus/hymns/{ck}.txt' if ck else None,
                'coincidencia_libro': round(pm, 2),
                'libro': sorted({f"tomo {f['tomo']}, p. {f['pdf']}" for f in lib[3]}) if lib else [],
                'diferencias': dif,
            }
        uso.append({'grupo': grupo, 'seccion': seccion, 'hora': hora, 'himno': clave, **({'nota': nota} if nota else {})})
    out = {'leeme': 'Himnos latinos del Apéndice IV (tiempo y comunes), para revisar antes de pasarlos a la base. '
                    'Texto: latin-ecclesiastic-accents (CC0, Te decet hymnus). Falta la traducción literal.',
           'uso': uso, 'himnos': himnos}
    p = os.path.join(AQUI, 'apendices', 'himnos_latinos.yaml')
    yaml.safe_dump(out, open(p, 'w', encoding='utf-8'), allow_unicode=True, sort_keys=False, width=200)
    print(f'{len(himnos)} himnos, {len(uso)} usos → {p}')
    for k, h in himnos.items():
        if h['coincidencia_libro'] < 0.9 or h['diferencias']:
            print(f"  {k}: coincidencia {h['coincidencia_libro']}, {len(h['diferencias'])} diferencias, {h['fuente_texto']}")


if __name__ == '__main__':
    main()
