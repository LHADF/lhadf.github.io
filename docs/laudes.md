# Laudes — decisiones (10/11/2026)

Orden de trabajo: 1) carga única desde sync a `base/` (salterio de cuatro semanas, propio del tiempo, santoral) con su verificador; 2) armado para cualquier fecha con el calendario ADF y elección de la hora en la portada; 3) piezas en latín y gregoriano con interlineal palabra por palabra; 4) revisión a mano de los propios ADF.

## Partes

- **Invitatorio: solo los domingos.** Primero *Dómine, lábia mea apéries* (gregoriano, `base/gregoriano/domine-labia-mea-aperies.gabc`), luego el Salmo 94 con su antífona, y después el *Deus in adiutórium*. Los demás días, solo el *Deus in adiutórium*.
- **Himno.** Ferias, memorias y fiestas: texto, en español y en latín, sin canto. Domingos y solemnidades: con melodía gregoriana, con la opción de solo texto o español. Falta: una fuente de los textos latinos de los himnos y los GABC de domingos y solemnidades (a veces de la forma extraordinaria, a veces de la ordinaria en los domingos del Tiempo Ordinario).
- **Cántico evangélico (Benedictus):** Neovulgata, en latín, con traducción interlineal.
- **Preces:** flexa (†) en el corte del medio de cada prece (el que trae sync; si no hay, en la invocación clara) y asterisco de metro (*) al final de la prece.
- **Padre nuestro:** *Pater noster* en latín.
- **Conclusión:** *Dóminus nos benedícat*. No hay GABC de un libro: `base/gregoriano/dominus-nos-benedicat.gabc` lleva la melodía del *Noctem quiétam* (mediante sol–fa antes del acento en «deféndat»; final con el acento en la y caída al re en «ætérnam»; ℟ Amen la–la). Aprobada el 10/11/2026.

## Estado

- **Paso 1 hecho (10/11/2026):** `tools/importar/importar_laudes.py` leyó 5152 Laudes de sync (2015–2025) y escribió `base/salterio/laudes.yaml`, `base/tiempo/laudes.yaml` (289 días con propio), `base/santoral/laudes.yaml` (130 celebraciones), `base/himnos/laudes.yaml` (118 himnos), `base/ordinario/laudes.yaml` y 73 salmos y cánticos nuevos. Variantes de la fuente: `base/informes/laudes.md`. `tools/verificar_base.py` comprueba que todos los días del calendario tengan Laudes completas.
- **Pendiente:** IX Domingo del Tiempo Ordinario (30/5/2027): sync no lo trae (antífona del Benedictus y oración).
- **Santoral:** es el de sync; en el paso 2 hay que vincularlo con las celebraciones del calendario ADF (nombres distintos, santos propios de ADF y de Argentina/Paraguay) y completar desde los comunes lo que falte.
- **Paso 2 hecho (10/11/2026):** `src/laudes.js` arma Laudes para cualquier fecha (salterio → tiempo → santoral). Los datos van en `dist/laudes.js` (aparte del HTML; la app los carga al abrir la hora). Partes en latín en `base/gregoriano/laudes.yaml`: invitatorio, Benedictus (Neovulgata, recitado, con interlineal), Pater noster y conclusión. Himnos: por ahora, los de sync en español.
- **Santoral ↔ calendario ADF:** `tools/base_js.py` vincula cada celebración del calendario con su entrada del santoral por fecha y nombre (118 vinculadas). Quedan 44 celebraciones ADF sin propio en la base (lista en `LAUDES.sin_vincular`): esos días la app reza el oficio del día y lo avisa. Fiestas y solemnidades sin salmodia propia toman los salmos del domingo I.
- **Himnos latinos:** texto base, el ePub de Universalis (Liturgia Horarum); cotejo palabra por palabra con GregoBase (Liber Hymnarius); las diferencias se revisan en el libro impreso. Falta el tomo de Pentecostés a Adviento.

## Usos ADF (10/11/2026; valen también para las otras horas)

- **Citas bíblicas** al modo «capítulo: versículos» (Dn 3: 26-27). La base guarda la coma; la app la convierte al mostrar (`cita()` en app.js).
- **Cántico evangélico:** la referencia va al final del renglón del título de la sección, como en la lectura breve. Texto y versículos del Benedictus y del Magníficat: los PDF «NVG» de ADF (`base/gregoriano/laudes.yaml`, `magnificat.yaml`).
- **Comienzo de Laudes:** siempre *Dómine, lábia mea apéries* y después el *Deus in adiutórium*; entre ambos, el invitatorio (antífona y Salmo 94) solo los domingos.
- **Padre nuestro:** la monición (la propia del día) se dice solo en domingos, fiestas y solemnidades. *Pater noster* con asterisco después de «noster»: hasta ahí, normal; desde ahí, negrita. Traducción: literal, palabra por palabra.
- **Preces:** † y * en rojo.
- **Conclusión:** cruz después de «Dóminus» (en la bendición del ministro, después de «Pater,»; «[esté] con vosotros» con corchetes). Opción «Con ministro ordenado»: *Dóminus vobíscum… Benedícat vos* (Graduale Romanum 1974, p. 817: tono A en ferias, memorias y fiestas; tono B en domingos y solemnidades; el libro no trae un tercer tono), seguido de *Ite in pace. ℟. Deo grátias.* (por ahora en texto: falta el GABC).
