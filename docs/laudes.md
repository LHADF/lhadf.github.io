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
