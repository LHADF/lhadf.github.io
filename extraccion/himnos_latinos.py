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
    ('Comunes', 'Oficio de difuntos', 'tercia', 'Qui lacrimatus Lazarum', 'Si se rezan las tres Horas: Tercia, estrofas 1, 4 y 5; Sexta, 2, 4 y 5; Nona, 3, 4 y 5 (rúbrica del libro).'),
    # ---------- Segunda etapa: Tiempo Ordinario (tomos III y IV), solemnidades del Señor y Propio de los santos ----------
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'visperas1', 'Deus creator omnium', ''),
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'visperas1', 'Dies aetasque ceteris', 'Si se prefiere (rúbrica del libro).'),
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'oficio', 'Primo dierum omnium', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'oficio', 'Dies aetasque ceteris', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'laudes', 'Aeterne rerum conditor', ''),
    ('Tiempo Ordinario', 'Semanas I y III: domingo', 'visperas', 'Lucis creator optime', ''),
    ('Tiempo Ordinario', 'Semanas I y III: lunes', 'oficio', 'Somno refectis artubus', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: lunes', 'oficio', 'Aeterna lux divinitas', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: lunes', 'laudes', 'Splendor paternae gloriae', ''),
    ('Tiempo Ordinario', 'Semanas I y III: lunes', 'visperas', 'Immense caeli conditor', ''),
    ('Tiempo Ordinario', 'Semanas I y III: martes', 'oficio', 'Consors paterni luminis', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: martes', 'oficio', 'O sacrosancta Trinitas', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: martes', 'laudes', 'Pergrata mundo nuntiat', ''),
    ('Tiempo Ordinario', 'Semanas I y III: martes', 'visperas', 'Telluris ingens conditor', ''),
    ('Tiempo Ordinario', 'Semanas I y III: miércoles', 'oficio', 'Rerum creator optime', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: miércoles', 'oficio', 'Scientiarum Domino', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: miércoles', 'laudes', 'Nox et tenebrae et nubila', ''),
    ('Tiempo Ordinario', 'Semanas I y III: miércoles', 'visperas', 'Caeli Deus sanctissime', ''),
    ('Tiempo Ordinario', 'Semanas I y III: jueves', 'oficio', 'Nox atra rerum contegit', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: jueves', 'oficio', 'Christe precamur adnuas', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: jueves', 'laudes', 'Sol ecce surgit igneus', ''),
    ('Tiempo Ordinario', 'Semanas I y III: jueves', 'visperas', 'Magnae Deus potentiae', ''),
    ('Tiempo Ordinario', 'Semanas I y III: viernes', 'oficio', 'Tu Trinitatis Unitas', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: viernes', 'oficio', 'Adesto Christe cordibus', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: viernes', 'laudes', 'Aeterna caeli gloria', ''),
    ('Tiempo Ordinario', 'Semanas I y III: viernes', 'visperas', 'Plasmator hominis Deus', ''),
    ('Tiempo Ordinario', 'Semanas I y III: sábado', 'oficio', 'Summae Deus clementiae', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas I y III: sábado', 'oficio', 'Auctor perennis gloriae', 'De día.'),
    ('Tiempo Ordinario', 'Semanas I y III: sábado', 'laudes', 'Aurora iam spargit polum', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'visperas1', 'Rerum Deus fons omnium', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'visperas1', 'Salve dies dierum gloria', 'Si se prefiere (rúbrica del libro).'),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'oficio', 'Mediae noctis tempus est', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'oficio', 'Salve dies dierum gloria', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'laudes', 'Ecce iam noctis tenuatur umbra', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: domingo', 'visperas', 'O lux beata Trinitas', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: lunes', 'oficio', 'Ipsum nunc nobis tempus est', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: lunes', 'oficio', 'Vita sanctorum via spes salusque', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: lunes', 'laudes', 'Lucis largitor splendide', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: lunes', 'visperas', 'Luminis fons lux et origo lucis', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: martes', 'oficio', 'Nocte surgentes vigilemus omnes', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: martes', 'oficio', 'Ad preces nostras deitatis aures', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: martes', 'laudes', 'Aeterne lucis conditor', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: martes', 'visperas', 'Sator princepsque temporum', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: miércoles', 'oficio', 'O sator rerum reparator aevi', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: miércoles', 'oficio', 'Christe lux vera bonitas et vita', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: miércoles', 'laudes', 'Fulgentis auctor aetheris', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: miércoles', 'visperas', 'Sol ecce lentus occidens', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: jueves', 'oficio', 'Ales diei nuntius', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: jueves', 'oficio', 'Amoris sensus erige', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: jueves', 'laudes', 'Iam lucis orto sidere', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: jueves', 'visperas', 'Deus qui claro lumine', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: viernes', 'oficio', 'Galli cantu mediante', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: viernes', 'oficio', 'Adesto rerum conditor', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: viernes', 'laudes', 'Deus qui caeli lumen es', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: viernes', 'visperas', 'Horis peractis undecim', ''),
    ('Tiempo Ordinario', 'Semanas II y IV: sábado', 'oficio', 'Lux aeterna lumen potens', 'De noche o de madrugada.'),
    ('Tiempo Ordinario', 'Semanas II y IV: sábado', 'oficio', 'Deus de nullo veniens', 'De día.'),
    ('Tiempo Ordinario', 'Semanas II y IV: sábado', 'laudes', 'Diei luce reddita', ''),
    ('Solemnidades del Señor', 'La Santísima Trinidad', 'visperas', 'Immensa et una Trinitas', ''),
    ('Solemnidades del Señor', 'La Santísima Trinidad', 'oficio', 'Te Patrem summum genitumque Verbum', ''),
    ('Solemnidades del Señor', 'La Santísima Trinidad', 'laudes', 'Trinitas summo solio coruscans', ''),
    ('Solemnidades del Señor', 'El Santísimo Cuerpo y Sangre de Cristo', 'visperas', 'Pange lingua gloriosi corporis', ''),
    ('Solemnidades del Señor', 'El Santísimo Cuerpo y Sangre de Cristo', 'oficio', 'Sacris sollemniis iuncta sint gaudia', ''),
    ('Solemnidades del Señor', 'El Santísimo Cuerpo y Sangre de Cristo', 'laudes', 'Verbum supernum prodiens nec Patris', ''),
    ('Solemnidades del Señor', 'El Sagrado Corazón de Jesús', 'visperas', 'Auctor beate saeculi', ''),
    ('Solemnidades del Señor', 'El Sagrado Corazón de Jesús', 'oficio', 'Cor arca legem continens', ''),
    ('Solemnidades del Señor', 'El Sagrado Corazón de Jesús', 'laudes', 'Iesu auctor clementiae', ''),
    ('Solemnidades del Señor', 'Jesucristo, sumo y eterno sacerdote', 'visperas', 'Aeterne Christe pontifex', ''),
    ('Solemnidades del Señor', 'Jesucristo, sumo y eterno sacerdote', 'oficio', 'Pontifex Iesu mediator une', ''),
    ('Solemnidades del Señor', 'Jesucristo, sumo y eterno sacerdote', 'laudes', 'Concinunt caeli parilique tellus', ''),
    ('Propio de los santos', 'San Andrés, apóstol (30 de noviembre)', 'oficio', 'Captator olim piscium', 'El libro trae solo este himno (¿para las tres Horas?).'),
    ('Propio de los santos', 'San Ambrosio, obispo y doctor (7 de diciembre)', 'oficio', 'Fortem piumque praesulem', 'El libro trae solo este himno.'),
    ('Propio de los santos', 'La Inmaculada Concepción (8 de diciembre)', 'visperas', 'Praeclara custos virginum', ''),
    ('Propio de los santos', 'La Inmaculada Concepción (8 de diciembre)', 'oficio', 'Te dicimus praeconio', ''),
    ('Propio de los santos', 'La Inmaculada Concepción (8 de diciembre)', 'laudes', 'In plausu grati carminis', ''),
    ('Propio de los santos', 'San Esteban, protomártir (26 de diciembre)', 'oficio', 'Festum celebre martyris', ''),
    ('Propio de los santos', 'San Esteban, protomártir (26 de diciembre)', 'laudes', 'Christus est vita veniens in orbem', ''),
    ('Propio de los santos', 'San Juan, apóstol y evangelista (27 de diciembre)', 'oficio', 'Virginis virgo venerande custos', ''),
    ('Propio de los santos', 'San Juan, apóstol y evangelista (27 de diciembre)', 'laudes', 'Cohors beata Seraphim', ''),
    ('Propio de los santos', 'Los Santos Inocentes (28 de diciembre)', 'oficio', 'Hymnum canentes martyrum', ''),
    ('Propio de los santos', 'Los Santos Inocentes (28 de diciembre)', 'laudes', 'Audit tyrannus anxius', ''),
    ('Propio de los santos', 'Santa Inés, virgen y mártir (21 de enero)', 'oficio', 'Igne divini radians amoris', ''),
    ('Propio de los santos', 'Santa Inés, virgen y mártir (21 de enero)', 'laudes', 'Agnes beatae virginis', 'Laudes y Vísperas.'),
    ('Propio de los santos', 'La Conversión de san Pablo (25 de enero)', 'oficio', 'Pressi malorum pondere', ''),
    ('Propio de los santos', 'La Conversión de san Pablo (25 de enero)', 'laudes', 'Doctor egregie Paule mores instrue', ''),
    ('Propio de los santos', 'La Conversión de san Pablo (25 de enero)', 'visperas', 'Excelsam Pauli gloriam', ''),
    ('Propio de los santos', 'La Presentación del Señor (2 de febrero)', 'oficio', 'Legis sacratae sanctis caeremoniis', 'Si se prefiere, «Quod chorus vatum» (rúbrica del libro).'),
    ('Propio de los santos', 'La Presentación del Señor (2 de febrero)', 'laudes', 'Adorna Sion thalamum', ''),
    ('Propio de los santos', 'La Presentación del Señor (2 de febrero)', 'visperas', 'Quod chorus vatum venerandus olim', ''),
    ('Propio de los santos', 'La Cátedra de san Pedro (22 de febrero)', 'visperas', 'Divina vox te deligit', ''),
    ('Propio de los santos', 'La Cátedra de san Pedro (22 de febrero)', 'oficio', 'Iam bone pastor Petre clemens accipe', ''),
    ('Propio de los santos', 'La Cátedra de san Pedro (22 de febrero)', 'laudes', 'Petrus beatus catenarum laqueos', ''),
    ('Propio de los santos', 'San José, esposo de la Virgen María (19 de marzo)', 'visperas', 'Te Ioseph celebrent agmina caelitum', ''),
    ('Propio de los santos', 'San José, esposo de la Virgen María (19 de marzo)', 'oficio', 'Iste quem laeti colimus fideles', ''),
    ('Propio de los santos', 'San José, esposo de la Virgen María (19 de marzo)', 'laudes', 'Caelitum Ioseph decus atque nostrae', ''),
    ('Propio de los santos', 'La Anunciación del Señor (25 de marzo)', 'visperas1', 'Agnoscat omne saeculum', 'II Vísperas: «Ave, maris stella» (rúbrica del libro).'),
    ('Propio de los santos', 'La Anunciación del Señor (25 de marzo)', 'oficio', 'Iam caeca vis mortalium', ''),
    ('Propio de los santos', 'La Anunciación del Señor (25 de marzo)', 'laudes', 'O lux salutis nuntia', ''),
    ('Propio de los santos', 'San Marcos, evangelista (25 de abril)', 'oficio', 'O vir beate Apostolis', ''),
    ('Propio de los santos', 'San Marcos, evangelista (25 de abril)', 'laudes', 'Mentibus laetis tua festa Marce', 'Laudes y Vísperas.'),
    ('Propio de los santos', 'San Isidoro, obispo y doctor (26 de abril)', 'laudes', 'Gaude fidelis concio', 'Laudes y Vísperas.'),
    ('Propio de los santos', 'Santa Catalina de Siena (29 de abril)', 'oficio', 'Virgo prudentum comitata coetum', ''),
    ('Propio de los santos', 'Santa Catalina de Siena (29 de abril)', 'laudes', 'Te Catharina maximis', ''),
    ('Propio de los santos', 'San José obrero (1 de mayo)', 'oficio', 'Te pater Ioseph opifex colende', ''),
    ('Propio de los santos', 'San José obrero (1 de mayo)', 'laudes', 'Aurora solis nuntia', 'Vísperas: «Te, Ioseph, celebrent» (rúbrica del libro).'),
    ('Propio de los santos', 'San Felipe y Santiago, apóstoles (3 de mayo)', 'oficio', 'Philippe summae honoribus', 'Laudes: «Claro paschali gaudio»; Vísperas: «Tristes erant Apostoli» (rúbrica del libro).'),
    ('Propio de los santos', 'San Matías, apóstol (14 de mayo)', 'oficio', 'Matthia sacratissimo', 'Oficio de lectura y Laudes.'),
    ('Propio de los santos', 'La Visitación de la Virgen María (31 de mayo)', 'oficio', 'Veni praecelsa Domina', ''),
    ('Propio de los santos', 'La Visitación de la Virgen María (31 de mayo)', 'laudes', 'Veniens mater inclita', ''),
    ('Propio de los santos', 'La Visitación de la Virgen María (31 de mayo)', 'visperas', 'Concito gressu petis alta montis', ''),
    ('Propio de los santos', 'San Bernabé, apóstol (11 de junio)', 'oficio', 'O vir beate Apostolis', ''),
    ('Propio de los santos', 'San Bernabé, apóstol (11 de junio)', 'laudes', 'Barnabae clarum colimus tropaeum', 'Laudes y Vísperas.'),
    ('Propio de los santos', 'La Natividad de san Juan Bautista (24 de junio)', 'visperas', 'Ut queant laxis resonare fibris', ''),
    ('Propio de los santos', 'La Natividad de san Juan Bautista (24 de junio)', 'oficio', 'Antra deserti teneris sub annis', ''),
    ('Propio de los santos', 'La Natividad de san Juan Bautista (24 de junio)', 'laudes', 'O nimis felix meritique celsi', ''),
    ('Propio de los santos', 'San Pedro y San Pablo, apóstoles (29 de junio)', 'visperas1', 'Aurea luce et decore roseo', ''),
    ('Propio de los santos', 'San Pedro y San Pablo, apóstoles (29 de junio)', 'oficio', 'Felix per omnes festum mundi cardines', ''),
    ('Propio de los santos', 'San Pedro y San Pablo, apóstoles (29 de junio)', 'laudes', 'Apostolorum passio', ''),
    ('Propio de los santos', 'San Pedro y San Pablo, apóstoles (29 de junio)', 'visperas', 'O Roma felix quae tantorum principum', ''),
    ('Propio de los santos', 'Santo Tomás, apóstol (3 de julio)', 'laudes', 'Qui luce splendes ordinis', 'El libro trae solo este himno.'),
    ('Propio de los santos', 'San Benito, abad (11 de julio)', 'oficio', 'Inter aeternas superum coronas', 'Oficio de lectura y Vísperas.'),
    ('Propio de los santos', 'San Benito, abad (11 de julio)', 'laudes', 'Legifer prudens venerande doctor', ''),
    ('Propio de los santos', 'Santa María Magdalena (22 de julio)', 'oficio', 'Magdalae sidus mulier beata', 'Oficio de lectura y Vísperas.'),
    ('Propio de los santos', 'Santa María Magdalena (22 de julio)', 'laudes', 'Aurora surgit lucida', ''),
    ('Propio de los santos', 'Santiago, apóstol (25 de julio)', 'laudes', 'Te nostra laetis laudibus', 'El libro trae solo este himno.'),
    ('Propio de los santos', 'San Joaquín y santa Ana (26 de julio)', 'oficio', 'Dum tuas festo pater o colende', 'Oficio de lectura y Vísperas.'),
    ('Propio de los santos', 'San Joaquín y santa Ana (26 de julio)', 'laudes', 'Nocti succedit lucifer', ''),
    ('Propio de los santos', 'Santa Marta (29 de julio)', 'oficio', 'Te gratulantes pangimus', 'Oficio de lectura y Vísperas.'),
    ('Propio de los santos', 'Santa Marta (29 de julio)', 'laudes', 'Quas tibi laudes ferimusque vota', ''),
    ('Propio de los santos', 'San Ignacio de Loyola (31 de julio)', 'laudes', 'Magnae cohortis principem', 'Laudes y Vísperas.'),
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

LINEA_MANO = {'Corda replet, linguas ditat,': 'corda replet, linguas ditat,',   # correcciones puntuales
              # segunda etapa: erratas del libro que la comparación tomó por variantes (se queda el corpus)
              'ne ore te canéntium': 'et ore te canéntium', 'cum Spíritu Sancto Paráclito,': 'cum Spíritu Paráclito,',
              'comes labórum dedite': 'comes labórum sédule', 'et nos tu in cæléstibus': 'et nos ut in cæléstibus',
              # variantes del libro que la comparación tomó por erratas (va el libro: Pedro, en segunda persona)
              'Quodcúmque vinclis super terram strínxerit,': 'Quodcúmque vinclis super terram strínxeris,',
              'et quod resólvit in terris arbítrio,': 'et quod resólvis in terris arbítrio,', 'in fine mundi iudex erit sǽculi.': 'in fine mundi iudex eris sǽculi.',
              # textos que no están en el corpus (del libro): tildes y erratas
              'Nam doctor hic sanctissimus,': 'Nam doctor hic sanctíssimus,', 'exémplar totu sǽculo.': 'exémplar toti sǽculo.',
              'fac Deum Semper cólere': 'fac Deum semper cólere', 'honor, potéstas, Glória,': 'honor, potéstas, glória,',
              'sánguinis prebens decus et lavácrum,': 'sánguinis præbens decus et lavácrum,',
              'Erróris pelle nubilum': 'Erróris pelle núbilum', 'O Sacrosáncta Trínitas,': 'O sacrosáncta Trínitas,'}
# Himnos del corpus de los que el libro toma algunas estrofas (índices): «Iam, bone pastor» (Cátedra de san Pedro) y
# «Doctor egrégie» (Conversión de san Pablo) son estrofas de un mismo himno, con la doxología
SELECCION = {'iam-bone-pastor-petre-clemens-accipe': [0, 2], 'doctor-egregie-paule-mores-instrue': [1, 2]}

ESTROFA_FIJA = {'iam-bone-pastor-petre-clemens-accipe': 4, 'doctor-egregie-paule-mores-instrue': 4, 'angularis-fundamentum': 6, 'fit-porta-christi-pervia': 4, 'lux-iucunda-lux-insignis': [6, 4, 4, 5, 5],
                'vir-celse-forma-fulgida': 4, 'christe-pastorum-caput-atque-princeps': 4, 'inclitus-rector-pater-atque-prudens': 4,
                'qui-vivis-ante-saecula': 4}   # (secuencia: estrofas desiguales)   # estrofas de seis versos (el libro y el corpus no las separan)

# Estrofas que cambian según el caso (la app elige): de otro archivo del corpus (se toman las estrofas que difieren)
# o a mano, del libro (índice de estrofa → versos). El texto principal es el primero que se nombra en la nota del uso.
VARIANTES = {
    'vir-celse-forma-fulgida': {'presbitero': 'Vir celse forma 1', 'papa': 'Vir celse forma 2'},                 # principal: obispo
    'christe-pastorum-caput-atque-princeps': {'obispo': 'Christe pastorum caput 1', 'papa': 'Christe pastorum caput 2'},   # principal: presbítero
    'inclitus-rector-pater-atque-prudens': {'presbitero': 'Inclitus rector pater 1', 'papa': 'Inclitus rector pater 2'},   # principal: obispo
    'deus-tuorum-militum': {'mujer': 'Deus tuorum militum (pro una martyre)'},
    'martyr-dei-qui-unicum': {'mujer': 'Martyr Dei quae'},
    'sanctorum-meritis-inclita-gaudia': {'mujeres': 'Sanctorum meritis inclita (feminine)'},
    'qui-vivis-ante-saecula': {'una': 'Qui vivis ante (pro una defuncta)', 'varios': 'Qui vivis ante (pro pluribus defunctis)'},
    'qui-lacrimatus-lazarum': {'una': 'Qui lacrimatus Lazarum (pro una defuncta)', 'varios': 'Qui lacrimatus Lazarum (pro pluribus defunctis)'},
    'beate-martyr-prospera': {'mujer': {0: ['Beáta martyr, próspera', 'diem triumphálem tuum,', 'quo sánguinis merces tibi', 'coróna vincénti datur.']}},
    'spes-christe-nostrae-veniae': {
        'una': {5: ['Sed et quæ soror córpore', 'nunc dormit pacis réquie,', 'iam te beánte vígilet', 'tibíque laudes réferat.']},
        'varios': {5: ['Sed et qui fratres córpore', 'nunc somno pacis dórmiunt,', 'iam te beánte vígilent', 'tibíque laudes réferant.']}},
    'immensae-rex-potentiae': {
        'una': {5: ['Tuámque voca fámulam,', 'quæ nunc exúta córpore', 'in regna Patris ínhiat,', 'ut te colláudet pérpetim.']},
        'varios': {5: ['Fratres et omnes ádvoca,', 'qui nunc exúti córpore', 'in regna Patris ínhiant,', 'ut te colláudent pérpetim.']}},
    'laeti-colentes-famulum': {'mujer': {
        0: ['Læti coléntes fámulam', 'quæ te perfécte cóluit,', 'tibi gratánter, Dómine,', 'amóris hymnum prómimus.'],
        2: ['Tibi se vovit súbditam', 'humilitáte obœ́diens,', 'Christi, carnis mundítie,', 'sponsi æmulátrix vírginum.'],
        4: ['His caritátis vínculis', 'in terris sibi dédita,', 'líbera ad astra iúgiter', 'triumphatúra pródiit.']}},
}

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
        if pm < 0.5 and lib:   # no está en el corpus (Jesucristo, sumo y eterno sacerdote: fiesta propia de España): el texto del libro
            ck, pm = None, 1.0
            texto = [con_tildes(l, DIC) for e in lib[2] for l in e if l.strip()]
            ESTROFAS['__libro__'] = [len([l for l in e if l.strip()]) for e in lib[2]]
        clave = re.sub(r'[^a-z]+', '-', norm(incipit))[:40].strip('-')
        if clave not in himnos:
            # estrofas: como las del libro (cantidad de versos de cada una); si no coinciden, de a 4
            largos = (ESTROFAS.get('__libro__') if ck is None else ESTROFAS.get(ck)) or ([len(e) for e in lib[2]] if lib else [])
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
                f = ESTROFA_FIJA[clave]
                largos = f if isinstance(f, list) else [f] * (len(cuerpo) // f)
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
            est = [[re.sub(r'"([^"]*)"', r'«\1»', l) for l in e] for e in est]   # comillas latinas
            est = [[LINEA_MANO.get(l, l) for l in e] for e in est]
            if clave in SELECCION:
                est = [est[i] for i in SELECCION[clave]]
                dif = [x for x in dif if x['libro']]
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
            var = {}
            for caso, src in VARIANTES.get(clave, {}).items():
                if isinstance(src, dict):
                    var[caso] = {i: v for i, v in src.items()}
                else:
                    otro = C[src]
                    if amen and otro and otro[-1].endswith('Amen.'):
                        otro = otro[:-1] + [re.sub(r'\s*Amen\.?$', '', otro[-1])]
                    i0, var[caso] = 0, {}
                    for k_e, e in enumerate(est):
                        tramo = otro[i0:i0 + len(e)]; i0 += len(e)
                        if [norm(x) for x in tramo] != [norm(x) for x in e]:
                            var[caso][k_e] = tramo
            himnos[clave] = {
                'incipit': est[0][0] if est and est[0] else incipit,
                'estrofas': est,
                'amen': bool(amen),
                'fuente_texto': f'latin-ecclesiastic-accents, corpus/hymns/{ck}.txt' if ck else None,
                'coincidencia_libro': round(pm, 2),
                'libro': sorted({f"tomo {f['tomo']}, p. {f['pdf']}" for f in lib[3]}) if lib else [],
                'diferencias': dif,
                **({'variantes': var} if var else {}),
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
