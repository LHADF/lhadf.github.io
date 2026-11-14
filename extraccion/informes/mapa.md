# Mapa: qué tiene la app hoy y qué puede sumar el libro

Inventario pieza por pieza de `base/` (lo que la app usa, cargado una vez de `sync`) y de
`extraccion/` (los cuatro tomos de *LH completa*). No cambia nada: solo dice qué hay en cada lado,
qué se puede sumar y qué hay que arreglar.

## 1. Lo que la app tiene hoy

| Sección | En `base/` | Cómo está |
|---|---|---|
| Ordinario | 6 archivos | completo: invocación, examen, responsorio, cántico evangélico, conclusión, antífonas marianas |
| Salterio | 8 archivos, 4 semanas × 7 días | completo en las 8 horas |
| Completas | `salterio/completas` + `ordinario/completas` + Triduo y Octava | completo, con las reglas ADF y el gregoriano |
| Propio del tiempo | 7 horas (`oficio` 21.155 renglones) | completo en los 6 tiempos |
| Oficios comunes | **11** comunes | faltan 3 (ver §2) |
| Propio de los santos | **120 fechas fijas** + `libro.yaml` (77) + `adf.yaml` (133 asignaciones) | la parte más incompleta |
| Himnos | 414 entradas en 7 horas | mezclados con los de otra edición local |
| Salmos y cánticos | 313 archivos | completo |
| Gregoriano | GABC + `completas.yaml` | **solo en la base**, no está en el libro |
| Calendario | `locales.yaml`, `notas.yaml` | **solo en la base** |
| Oficio de difuntos | — | **no está** |
| Apéndices | — | **no está** |

## 2. Lo que suma el libro, de mayor a menor hueco

| Qué | Cuánto | Estado en la base |
|---|---|---|
| **Apéndices** (8, con los himnos latinos y los cánticos de vigilias) | 1.460 piezas | no está nada |
| **Propio de los santos** | 145 celebraciones en 114 fechas que la base no tiene | la base tiene 120 de las 226 fechas del libro |
| **Variantes por tiempo** (antífonas de Adviento, Cuaresma, Pascua en el Salterio y los comunes) | 575 con condición de tiempo, sobre 18.374 variantes en total | la base guarda una sola, la que `sync` eligió |
| **Himnos** | 224 que la base no tiene | la base tiene 414 entradas; el libro, 471 himnos distintos |
| **Oficio de difuntos** | 87 piezas, 8 horas | no está nada |
| **Oficios comunes** que faltan | 3: `religiosos`, `caridad`, `educadores` | los otros 11 están |
| **I y II Vísperas separadas** | el libro las distingue en los 14 comunes y en 40 celebraciones | la base las junta |

### Las 4 celebraciones pendientes de `santoral/adf.yaml`

| Celebración | ¿La trae el libro? |
|---|---|
| Santísimo Nombre de Jesús | **sí** (3 de enero: Oficio de lectura, Laudes y Vísperas) |
| Todos los Fieles Difuntos | **sí** (2 de noviembre, más el Oficio de difuntos entero) |
| Nuestro Señor Jesucristo, Sumo y Eterno Sacerdote | no está en el santoral del libro |
| Divino Niño Jesús | no está: es propio de ADF |

### Qué trae el libro en esas 145 celebraciones nuevas

Casi todas son memorias y traen **solo el Oficio de lectura** —la segunda lectura patrística y la
oración—, que es justo lo que `sync` no publicaba. En números: el libro da Oficio de lectura para 266
de sus 276 celebraciones, Laudes para 123 y Vísperas para 97 (más 40 I Vísperas y 16 II Vísperas).

## 3. Lo que hay que arreglar, y de qué lado está el error

| Qué | Cuántos | De quién es el error |
|---|--:|---|
| Himnos con estrofas pegadas | 13 | **de la extracción**: pegué dos estrofas en un corte de página |
| Himnos con estrofas pegadas | 2 | de la base |
| Himnos con el mismo número de estrofas y otro reparto | 1 | a mirar uno por uno |
| Claves de salmos y cánticos que no coinciden | 80 + 105 | **de ninguno**: son dos maneras de nombrar lo mismo (`cantico-1s-2-1-10` / `cantico-1-sam-2-1-10`, `salmo-101-i` / los tres tramos del libro) |
| Títulos distintos de la misma celebración entre tomos | en `diferencias.csv` | **del libro**: el tomo II imprime «SANTA JOSERFINA BAKHITA» y el tomo III «SANTA JOSEFA BAKHITA» (verificado en las páginas 2242 y 3882) |

**Antífonas duplicadas:** busqué antífonas repetidas dentro de una misma salmodia en toda la base y no
hay ninguna. Lo que sí pasa es que donde el libro imprime dos o tres antífonas —la del tiempo ordinario
y la de Adviento o Cuaresma—, la base guarda una sola. Si el caso que viste es otro, hace falta un ejemplo.

## 4. Lo que el libro no tiene y la base sí

Esto no se toca y tiene que sobrevivir a cualquier carga:

- `gregoriano/`: los GABC con la traducción interlineal literal, propia, y las reglas de qué se canta cuándo.
- `calendario/`: los calendarios locales y las notas.
- `santoral/adf.yaml`: qué común usa cada celebración del calendario ADF.
- Las reglas de Completas de `base/LEEME.md`, incluidas las normas ADF («aleluia» con i) y las Completas del Domingo de Pascua, agregadas a mano.
- 8 fechas del santoral que el libro no trae y la base sí, y las celebraciones movibles propias (Luján, María Madre de la Iglesia).
- 132 himnos que la base tiene y el libro no. Ojo: algunos vienen de otra edición local («Altas primicias de la fe de México»), así que hay que mirar cuáles conviene conservar.

## 5. Orden de trabajo que propongo

Primero lo que suma sin discutir nada, porque la base no tiene nada ahí y no hay con qué chocar:

1. **Oficio de difuntos** (87 piezas) y los **3 comunes que faltan**. Antes hay que decidir en `docs/` cómo los arma la app.
2. **Las 145 celebraciones nuevas del santoral**, que son casi todas Oficio de lectura.
3. **Las variantes por tiempo**, que es el cambio más visible en el rezo diario.
4. **Los apéndices**, que son los más grandes pero los menos urgentes.

Después los arreglos:

5. Los **16 himnos mal cortados**, empezando por los 13 que son míos.
6. La **tabla de claves de salmos**, para que los dos lados se puedan comparar solos de acá en adelante.

Las 2.138 diferencias de palabras del otro informe quedan afuera de todo esto: son de traducción y no
se arreglan sumando ni corrigiendo, sino decidiendo qué edición reza ADF.
