# Fuentes de los textos y partituras

`tools/datos.py` lee estas fuentes desde una carpeta `../fuentes` (o `SEPTIES_FUENTES`) y escribe `src/datos/completas-2026-11-05.js`.

| Carpeta | Repositorio | Commit usado | Qué se toma |
| --- | --- | --- | --- |
| `divinum-officium` | [DivinumOfficium/divinum-officium](https://github.com/DivinumOfficium/divinum-officium) | `85183a9b1161f4242c9199177b5d6c9dd16be620` | Breviario de 1960: textos latinos y españoles, partituras GABC (himno, antífonas, responsorio, versículo, Salve). |
| `jgabc` | [bbloomf/jgabc](https://github.com/bbloomf/jgabc) | `df683eac32c3323f7247555ba5ce395e8c2a5650` | Nova Vulgata (salmos con acentos) y definiciones de los tonos salmódicos. |
| `sync` | [geronimoarteaga/sync](https://github.com/geronimoarteaga/sync) | `9995f11748dc332988eb8cccc4c0321c48f6f763` | Liturgia de las Horas en español (edición de 1979) del 5/11/2026. |

Las antífonas gregorianas del rito actual («Caro mea», «Salva nos») se transcribieron a mano del *Antiphonale* de [igneus/antiphonale83](https://github.com/igneus/antiphonale83) (commit `e2d8697cbc325d93fd9d350edb047bf6c97c6f75`).

## Textos provisionales

- **Latín de la Liturgia de las Horas:** salmo y Nunc dimittis de la Nova Vulgata; lectura breve sin cotejar con la edición típica. Falta la oración del jueves.
- **Traducciones interlineales:** literales, redactadas para Septies; deben revisarse.
- **Himno Te lucis (rito actual):** melodía ferial aplicada al texto de la Liturgia Horarum.

## Derechos

Los textos oficiales en español (Coeditores Litúrgicos) y la *Liturgia Horarum* (Librería Editrice Vaticana) tienen derechos de autor. Su uso en un prototipo privado o comunitario no requiere trámite práctico; para publicar la app abiertamente hace falta permiso. Divinum Officium (MIT) y jgabc (dominio público) se pueden usar libremente. Ver [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
