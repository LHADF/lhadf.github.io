"""Planilla de revisión del santoral: todas las celebraciones del calendario ADF, qué tiene cada una en la base y de qué
común toma lo que le falta; y la lista de las que no tienen propio en ninguna de nuestras fuentes.

    node extraccion/calendario_adf.mjs          # después de tools/armar.py
    python3 extraccion/planilla_santos.py [SALIDA.xlsx]

Sale en extraccion/informes/santoral-revision.csv y santoral-sin-propio.csv; con SALIDA.xlsx, además la planilla con
formato (dos pestañas y la leyenda), para subir a Google Drive.
"""
import csv
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import a_base_comunes as AC  # noqa: E402
from a_base_santoral import comun_de, nombre_libro, rubricas  # noqa: E402
from emparejar_santoral import buscar  # noqa: E402

BASE = AC.BASE
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']
HORAS = [('invitatorio', 'Invitatorio'), ('oficio', 'Oficio'), ('laudes', 'Laudes'), ('tercia', 'Tercia'),
         ('sexta', 'Sexta'), ('nona', 'Nona'), ('visperas1', 'I Vísperas'), ('visperas', 'Vísperas')]
CAMPO = OrderedDict([('inv_ant', 'antífona'), ('himno', 'himno'), ('salmodia', 'salmodia'), ('ant', 'antífona'),
                     ('versiculo', 'versículo'), ('lectura1', '1.ª lectura'), ('resp1', '1.er responsorio'),
                     ('lectura2', '2.ª lectura'), ('resp2', '2.º responsorio'), ('lectura', 'lectura breve'),
                     ('responsorio', 'responsorio'), ('ant_benedictus', 'ant. Benedictus'),
                     ('ant_magnificat', 'ant. Magníficat'), ('preces', 'preces'), ('oracion', 'oración'),
                     ('te_deum', 'Te Deum')])
NUEVOS = {'religios': 'religiosos', 'caritativ|caridad': 'caridad', 'educador': 'educadores'}
DONDE = {'ARG': 'Conferencia Episcopal Argentina', 'PGY': 'Conferencia Episcopal Paraguaya',
         'BRS': 'CNBB (Brasil)', 'CHL': 'Conferencia Episcopal de Chile', 'ESP': 'Conferencia Episcopal Española',
         'FRC': 'Conférence des évêques de France', 'BUE': 'Arquidiócesis de Buenos Aires',
         'CDE': 'Diócesis de Ciudad del Este',
         'CRG': 'Dicasterio para el Culto Divino (decretos y textos posteriores a la edición de 1979)',
         'ADF': 'Propio de la orden o del instituto del santo; Dicasterio para el Culto Divino'}


def fecha_txt(fs):
    if not fs:
        return 'móvil (no cae en 2026–2028)'
    if len(set(fs)) > 2:
        return 'móvil'
    return ' / '.join(f'{int(f[3:])} de {MESES[int(f[:2]) - 1]}' for f in sorted(set(fs)))


def elementos(por_hora):
    """{hora: dict} → «Oficio: 2.ª lectura, oración · Laudes: …»."""
    partes = []
    for h, nombre in HORAS:
        d = por_hora.get(h)
        if not isinstance(d, dict):
            continue
        cs = [v for k, v in CAMPO.items() if d.get(k)]
        if cs:
            partes.append(f'{nombre}: ' + ', '.join(dict.fromkeys(cs)))
    return ' · '.join(partes)


def nuevo_de(texto):
    t = (texto or '').lower()
    for rx, k in NUEVOS.items():
        if re.search(rx, t):
            return k
    return None


def main():
    cal = json.loads((AQUI / 'informes' / 'calendario-adf.json').read_text(encoding='utf-8'))
    adf = AC.leer(BASE / 'santoral' / 'adf.yaml') or {}
    lib = AC.leer(BASE / 'santoral' / 'libro.yaml') or {}
    sant = {h: AC.leer(BASE / 'santoral' / f'{h}.yaml') or {} for h in
            ('laudes', 'visperas', 'oficio', 'tercia', 'sexta', 'nona')}
    nombres_comun = {k: v.get('nombre', k) for k, v in (AC.leer(BASE / 'comunes' / 'laudes.yaml') or {}).items()}
    en_cal = {e['n'] for e in cal}
    cal = cal + [{'n': n, 'fechas': [], 'g': [], 'cal': [], 'mapa': None} for n in adf if n not in en_cal]
    filas, sin = [], []
    for e in cal:
        n, k = e['n'], e.get('mapa')
        a = adf.get(n) if isinstance(adf.get(n), dict) else {}
        c, _ = buscar(n, e['fechas'])
        ind = ''
        if c:
            rub = rubricas(c)
            ind = next((r for r in rub if re.search(r'^(del?|todo)\b.*\bcom[uú]n', r, re.I)), '') or \
                next((r for r in rub if re.search(r'com[uú]n', r, re.I)), '')
        comun_hoy, origen, elem = '', '', ''
        if k:
            origen = 'Propio de sync'
            por_hora = {h: sant[h].get(k) for h in sant}
            por_hora['visperas1'] = sant['visperas'].get(k + ' · I Vísperas')
            por_hora['invitatorio'] = {'inv_ant': (sant['laudes'].get(k) or {}).get('inv_ant')}
            elem = elementos(por_hora)
            txt = next((d.get('comun') for d in por_hora.values() if isinstance(d, dict) and d.get('comun')), '')
            comun_hoy = (nombres_comun.get(comun_de(txt), comun_de(txt)) or '') + (f' («{txt}»)' if txt else '')
        elif a.get('como') or a.get('es'):
            origen = 'Toma todo de otra celebración'
            elem = f'todo de «{a.get("como") or a.get("es")}»'
        else:
            comun_hoy = a.get('comun', '')
            if n in lib:
                origen = 'Propio del libro + común' if comun_hoy else 'Propio del libro'
                elem = elementos({**{h: lib[n].get(h) for h, _ in HORAS},
                                  'laudes': {**(lib[n].get('laudes') or {}), 'oracion': lib[n].get('oracion')}})
            elif a.get('pendiente'):
                origen = 'Pendiente: no hay nada'
            else:
                origen = 'Solo el común'
        cal_s = ', '.join(e.get('cal') or [])
        exclusivo = bool(e.get('cal')) and 'CRG' not in (e.get('cal') or [])
        propuesta = nuevo_de(ind) or comun_de(ind) or ''
        fila = OrderedDict([
            ('Fecha', fecha_txt(e['fechas'])), ('Celebración', n), ('Grado', ' / '.join(e.get('g') or [])),
            ('Calendarios', cal_s), ('Qué tiene hoy', origen), ('Elementos propios en la base', elem),
            ('Común asignado hoy', nombres_comun.get(comun_hoy, comun_hoy)),
            ('En el santoral del libro', nombre_libro(c['titulo']) if c else 'no está (puede estar en el Propio del tiempo)' if k else 'no está'),
            ('Indica el libro', ind),
            ('Común según el libro', nombres_comun.get(propuesta, propuesta)),
            ('Decisión CRU', ''), ('Observaciones', ''),
        ])
        filas.append(fila)
        if not k and not (a.get('como') or a.get('es')) and n not in lib and a.get('comun') != 'santa-maria-sabado':
            falta = 'todo: oración, 2.ª lectura y lo propio de cada hora' if not comun_hoy else \
                'oración propia y 2.ª lectura (lo demás sale del común)'
            fuentes = [DONDE[x] for x in (e.get('cal') or []) if x in DONDE and x != 'ADF']
            if 'ADF' in (e.get('cal') or []) and not fuentes:
                fuentes = [DONDE['ADF']]
            sin.append(OrderedDict([
                ('Fecha', fila['Fecha']), ('Celebración', n), ('Grado', fila['Grado']), ('Calendarios', cal_s),
                ('Agregado por', 'ADF' if exclusivo and 'ADF' in (e.get('cal') or []) and len(e['cal']) == 1 else
                 ('calendario nacional o local' if exclusivo else 'Roma, después de 1979 (o el libro no la trae)')),
                ('Común asignado hoy', fila['Común asignado hoy']), ('Qué falta', falta),
                ('Dónde buscar', '; '.join(dict.fromkeys(fuentes))), ('Encontrado (sí/no)', ''),
                ('Fuente (documento, año, página o enlace)', ''), ('Observaciones', '')]))
    orden = lambda f: (f['Fecha'][:1].isdigit() is False, MESES.index(f['Fecha'].split(' de ')[1].split(' / ')[0])
                       if ' de ' in f['Fecha'] else 99, int(f['Fecha'].split(' ')[0]) if f['Fecha'][:1].isdigit() else 0)
    filas.sort(key=orden)
    sin.sort(key=orden)
    for nombre, datos in (('santoral-revision.csv', filas), ('santoral-sin-propio.csv', sin)):
        with open(AQUI / 'informes' / nombre, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, list(datos[0]))
            w.writeheader()
            w.writerows(datos)
    print(f'{len(filas)} celebraciones; {len(sin)} sin propio en nuestras fuentes')
    if len(sys.argv) > 1:
        xlsx(sys.argv[1], filas, sin, sorted(nombres_comun.values()))


def xlsx(ruta, filas, sin, comunes):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    F, FB = Font(name='Arial', size=10), Font(name='Arial', size=10, bold=True, color='FFFFFF')
    cab = PatternFill('solid', fgColor='5B3A29')
    entrada = PatternFill('solid', fgColor='FFF4C2')
    linea = Border(bottom=Side(style='thin', color='DDDDDD'))
    leyenda_txt = ('Las celdas amarillas son para completar. El resto sale de la base de la app, del calendario ADF y '
                   'de la extracción del libro (Liturgia de las Horas, 4 tomos).')

    def hoja(ws, titulo, datos, anchos, editables, lista=None):
        ws['A1'] = titulo
        ws['A1'].font = Font(name='Arial', size=13, bold=True)
        ws['A2'] = leyenda_txt
        ws['A2'].font = Font(name='Arial', size=9, italic=True, color='666666')
        cols = list(datos[0])
        for j, c in enumerate(cols, 1):
            x = ws.cell(row=4, column=j, value=c)
            x.font, x.fill = FB, cab
            x.alignment = Alignment(wrap_text=True, vertical='center')
        for i, f in enumerate(datos, 5):
            for j, c in enumerate(cols, 1):
                x = ws.cell(row=i, column=j, value=f[c] or None)
                x.font, x.border = F, linea
                x.alignment = Alignment(wrap_text=True, vertical='top')
                if c in editables:
                    x.fill = entrada
        for j, w in enumerate(anchos, 1):
            ws.column_dimensions[ws.cell(row=4, column=j).column_letter].width = w
        ws.freeze_panes = 'C5'
        ws.auto_filter.ref = f'A4:{ws.cell(row=4, column=len(cols)).column_letter}{len(datos) + 4}'
        if lista:
            col = ws.cell(row=4, column=cols.index('Decisión CRU') + 1).column_letter
            dv = DataValidation(type='list', formula1=lista, allow_blank=True, showErrorMessage=False)
            ws.add_data_validation(dv)
            dv.add(f'{col}5:{col}{len(datos) + 4}')

    ws = wb.active
    ws.title = 'Todo el santoral'
    hoja(ws, 'LH ADF · Revisión del santoral: qué tiene cada celebración y de qué común toma', filas,
         [14, 38, 16, 14, 20, 48, 26, 30, 40, 24, 24, 30], {'Decisión CRU', 'Observaciones'},
         "=Comunes!$A$2:$A$40")
    ws2 = wb.create_sheet('Sin propio')
    hoja(ws2, 'LH ADF · Celebraciones sin propio en nuestras fuentes (para buscar)', sin,
         [14, 40, 16, 14, 22, 26, 34, 40, 12, 40, 30], {'Encontrado (sí/no)', 'Fuente (documento, año, página o enlace)',
                                                       'Observaciones'})
    ws3 = wb.create_sheet('Comunes')
    ws3['A1'] = 'Comunes disponibles en la app'
    ws3['A1'].font = Font(name='Arial', size=10, bold=True)
    for i, c in enumerate(comunes + ['Propio (no usa común)', 'Otra celebración (anotar cuál)'], 2):
        ws3.cell(row=i, column=1, value=c).font = F
    ws3.column_dimensions['A'].width = 70
    wb.save(ruta)
    print('planilla:', ruta)


if __name__ == '__main__':
    main()
