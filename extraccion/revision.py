"""Página de revisión lado a lado: imagen de cada página del libro a la izquierda,
piezas extraídas a la derecha (tipo, parte, etiqueta, condición, marcas de revisar).

La llama extraer.py con --revision CARPETA. Las imágenes salen del PDF y se
guardan en CARPETA/img; no van al repo.
"""
import html
import json
from pathlib import Path

ROMANOS = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
NOMBRE_HORA = {
    'visperas1': 'I Vísperas', 'visperas2': 'II Vísperas', 'invitatorio': 'Invitatorio',
    'oficio': 'Oficio de lectura', 'laudes': 'Laudes', 'intermedia': 'Hora intermedia',
    'tercia': 'Tercia', 'sexta': 'Sexta', 'nona': 'Nona',
}
NOMBRE_TIPO = {
    'antifona': 'antífona', 'salmo': 'salmo', 'himno': 'himno', 'lectura_breve': 'lectura breve',
    'responsorio_breve': 'responsorio breve', 'versiculo': 'versículo', 'lectura': 'lectura',
    'responsorio': 'responsorio', 'preces': 'preces', 'oracion': 'oración', 'rubrica': 'rúbrica',
    'texto': 'texto',
}

e = html.escape


def cuando_txt(c):
    if not c:
        return ''
    partes = []
    for k, v in c.items():
        partes.append(f'{k}: {", ".join(v) if isinstance(v, list) else v}')
    return ' · '.join(partes)


def cuerpo(v, tipo, salmos, himnos):
    t = tipo
    if t == 'antifona':
        s = f'<p>{e(v.get("texto") or "")}</p>'
        if v.get('tp_aleluya'):
            s += '<span class="chip tp">T. P. Aleluya</span>'
        return s
    if t == 'himno':
        h = himnos.get(v.get('himno'), {'estrofas': v.get('estrofas', [])})
        est = h.get('estrofas') or v.get('estrofas') or []
        out = [f'<div class="ref">himnos.json → {e(v.get("himno") or "")}</div>'] if v.get('himno') else []
        for es in est:
            out.append('<p class="estrofa">' + '<br>'.join(
                f'<span class="s{vs["sangria"]}">{e(vs["texto"])}</span>' for vs in es) + '</p>')
        if h.get('amen') or v.get('amen'):
            out.append('<p class="estrofa">Amén.</p>')
        return ''.join(out)
    if t == 'salmo':
        sal = salmos.get(v.get('salmo'), {})
        s = f'<div class="ref">salmos.json → {e(v.get("salmo") or "")}{" · parte " + e(v["parte"]) if v.get("parte") else ""}</div>'
        if sal.get('titulo'):
            s += f'<p class="sub">{e(sal["titulo"])}</p>'
        n = sum(len(es) for p in sal.get('partes', []) for es in p['estrofas'])
        s += f'<p class="muted">{n} versos en la biblioteca</p>'
        return s
    if t == 'lectura_breve':
        return f'<p class="cita">{e(v.get("cita") or "")}</p><p>{e(v.get("texto") or "")}</p>'
    if t == 'responsorio_breve':
        s = ''.join(f'<p><b class="r">{l}.</b> {e(v.get(k) or "")}</p>' for l, k in
                    (('V', 'v1'), ('R', 'r1'), ('V', 'v2'), ('R', 'r2')))
        if v.get('gloria'):
            s += '<span class="chip">gloria</span>'
        return s
    if t == 'versiculo':
        s = f'<p><b class="r">V.</b> {e(v.get("v") or "")}</p><p><b class="r">R.</b> {e(v.get("r") or "")}</p>'
        if v.get('gloria'):
            s += '<span class="chip">gloria</span>'
        if v.get('despues_gloria'):
            s += f'<span class="chip">después del Gloria: {e(v["despues_gloria"])}</span>'
        return s
    if t == 'lectura':
        s = f'<p class="enc">{e(v.get("encabezado") or "")} <span class="r">{e(v.get("cita") or "")}</span></p>'
        if v.get('fuente'):
            s += f'<p class="r small">{e(v["fuente"])}</p>'
        if v.get('titulo'):
            s += f'<p class="sub">{e(v["titulo"])}</p>'
        pars = v.get('parrafos') or []
        s += f'<details><summary>{len(pars)} párrafos — «{e((pars[0] if pars else "")[:90])}…»</summary>'
        s += ''.join(f'<p>{e(p)}</p>' for p in pars) + '</details>'
        return s
    if t == 'responsorio':
        r = v.get('r') or ['', '']
        s = f'<p class="cita">{e(v.get("cita") or "")}</p>' if v.get('cita') else ''
        s += f'<p><b class="r">R.</b> {e(r[0] or "")} <b class="r">*</b> {e(r[1] or "")}</p>'
        s += f'<p><b class="r">V.</b> {e(v.get("v") or "")}</p>'
        if v.get('tp_aleluya'):
            s += '<span class="chip tp">T. P. Aleluya</span>'
        return s
    if t == 'preces':
        s = f'<p>{e(v.get("introduccion") or "")}</p>'
        for x in v.get('respuesta') or []:
            s += (f'<p class="resp">{"<b class=r>" + e(x["etiqueta"]) + "</b> " if x["etiqueta"] else ""}'
                  f'<i>{e(x["texto"])}</i></p>')
        s += '<ol class="int">'
        for n, i in enumerate(v.get('intenciones') or []):
            if v.get('libres_despues_de') == n:
                s += '<li class="libres">intenciones libres</li>'
            s += f'<li>{e(i["primera"])}<br><b class="r">—</b> {e(i["segunda"] or "")}</li>'
        if v.get('libres_despues_de') == len(v.get('intenciones') or []):
            s += '<li class="libres">intenciones libres</li>'
        s += '</ol>'
        s += f'<p class="final">{e(v.get("final") or "")}</p>'
        return s
    if t == 'oracion':
        return f'<p>{e(v.get("texto") or "")}</p>'
    if t == 'rubrica':
        rem = v.get('remite')
        rem = ', '.join(rem) if isinstance(rem, list) else rem
        s = f'<p class="r">{e(v.get("texto") or "")}</p>'
        if rem:
            s += f'<span class="chip azul">remite → {e(rem)}</span>'
        return s
    if v.get('estrofas'):
        return ''.join('<p class="estrofa">' + '<br>'.join(
            f'<span class="s{vs["sangria"]}">{"<b class=r>+</b> " if vs.get("cruz") else ""}'
            + (' <b class="r">*</b> '.join(e(x) for x in vs['mitades']) if vs.get('mitades') else e(vs['texto']))
            + '</span>' for vs in es) + '</p>' for es in v['estrofas'])
    if v.get('parrafos'):
        return ''.join(f'<p>{e(x)}</p>' for x in v['parrafos'])
    return f'<p>{e(v.get("texto") or "")}</p>'


def tarjeta(v, u, ctx, salmos, himnos):
    tipo = v['_tipo']
    src = u or v
    et = src.get('etiqueta') if u else v.get('etiqueta')
    cuando = (u or {}).get('cuando') or {}
    rev = (u or {}).get('revisar') or v.get('revisar')
    nota = (u or {}).get('nota') or ' · '.join(v.get('_notas', []))
    tomos = ''.join(ROMANOS[f['tomo']] + ' ' for f in (u or {}).get('fuentes', [])).strip()
    clases = 'card' + (' rub' if tipo == 'rubrica' else '') + (' rev' if rev else '') + (' var' if et or cuando else '')
    cab = f'<span class="tipo">{e(NOMBRE_TIPO.get(tipo, tipo))}</span>'
    cab += f'<span class="ctx">{e(ctx)}</span>'
    if et:
        cab += f'<span class="et">{e(et)}</span>'
    if cuando:
        cab += f'<span class="chip cond">{e(cuando_txt(cuando))}</span>'
    if rev:
        cab += '<span class="chip revisar">revisar</span>'
    pie = f'<div class="pie">en los tomos {e(tomos)}</div>' if tomos else ''
    if u and u.get('etiquetas_en_tomos'):
        pie += '<div class="pie">etiquetas por tomo: ' + e('; '.join(
            f'{ROMANOS[x["tomo"]]}: {x["etiqueta"] or "(sin etiqueta)"}' for x in u['etiquetas_en_tomos'])) + '</div>'
    if u and u.get('otras_redacciones'):
        pie += '<div class="pie">otra redacción: ' + e('; '.join(
            f'{ROMANOS[x["tomo"]]}: {x["texto"]}' for x in u['otras_redacciones'])) + '</div>'
    if nota:
        pie += f'<div class="nota">{e(nota)}</div>'
    data = v if tipo != 'himno' else {**v, 'himno': (u or {}).get('himno')}
    return f'<div class="{clases}"><div class="cab">{cab}</div>{cuerpo(data, tipo, salmos, himnos)}{pie}</div>'


CSS = """
:root{--rojo:#b0261d;--azul:#1f4fa8;--tinta:#1d1b19;--suave:#6b6560;--linea:#e6e1da;--fondo:#faf8f5;--papel:#fff}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 'Source Serif 4',Georgia,serif;color:var(--tinta);background:var(--fondo)}
header{position:sticky;top:0;z-index:5;background:var(--papel);border-bottom:1px solid var(--linea);padding:12px 20px 0}
h1{font:600 18px 'Source Sans 3',sans-serif;margin:0 0 4px}
.lead{font:14px 'Source Sans 3',sans-serif;color:var(--suave);margin:0 0 10px}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{font:600 13px 'Source Sans 3',sans-serif;text-decoration:none;color:var(--suave);padding:8px 12px;border-radius:8px 8px 0 0}
nav a.on{color:var(--tinta);background:var(--fondo);box-shadow:inset 0 -2px var(--rojo)}
main{max-width:1500px;margin:0 auto;padding:16px 20px 80px}
.vista{display:none}.vista.on{display:block}
.pag{display:grid;grid-template-columns:minmax(0,560px) minmax(0,1fr);gap:24px;align-items:start;padding:18px 0;border-bottom:1px solid var(--linea)}
.img{position:sticky;top:110px}
.img img,.hoja{width:100%;border:1px solid var(--linea);border-radius:8px;background:#fff no-repeat}
.indice{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px}.indice a{font:600 12px 'Source Sans 3',sans-serif;color:var(--tinta);background:#fff;border:1px solid var(--linea);border-radius:99px;padding:3px 10px;text-decoration:none}
.img .num{font:600 12px 'Source Sans 3',sans-serif;color:var(--suave);letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}
.piezas{display:flex;flex-direction:column;gap:10px}
.hora{font:600 13px 'Source Sans 3',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--tinta);margin:8px 0 0;padding-top:6px;border-top:2px solid var(--tinta)}
.titulo{font:600 16px 'Source Sans 3',sans-serif;color:var(--tinta)}
.parte{font:600 11px 'Source Sans 3',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--rojo);margin-top:4px}
.card{background:var(--papel);border:1px solid var(--linea);border-radius:8px;padding:10px 14px}
.card.var{border-left:4px solid #c9a227}
.card.rub{background:#fdf6f5;border-color:#efd3cf}
.card.rev{box-shadow:0 0 0 2px #e8a33d}
.card p{margin:4px 0}
.cab{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:4px;font:12px 'Source Sans 3',sans-serif}
.tipo{font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.ctx{color:var(--suave)}
.et{color:var(--rojo);font-weight:600}
.chip{display:inline-block;font:600 11px 'Source Sans 3',sans-serif;padding:1px 8px;border-radius:99px;background:#eee9e2;color:var(--tinta)}
.chip.cond{background:#fbefc7}.chip.revisar{background:#e8a33d;color:#fff}.chip.tp{background:#e6efe1}
.chip.azul{background:#e5ecf8;color:var(--azul)}
.r{color:var(--rojo)}.small{font-size:13px}.muted{color:var(--suave);font-size:13px}
.ref{font:12px 'Source Sans 3',sans-serif;color:var(--azul)}
.sub{font-variant:small-caps;color:var(--rojo);font-size:14px}
.cita{color:var(--rojo);font-size:14px}.enc{font-style:italic}
.estrofa{margin:6px 0}.s1{padding-left:1.2em;display:inline-block}.s2{padding-left:2.4em;display:inline-block}
.int{margin:4px 0;padding-left:1.4em}.int li{margin:4px 0}.libres{color:var(--rojo);font-style:italic;list-style:none;margin-left:-1.4em}
.resp i{color:var(--tinta)}
.pie{font:12px 'Source Sans 3',sans-serif;color:var(--suave);margin-top:6px}
.nota{font:12px 'Source Sans 3',sans-serif;color:#8a4b00;background:#fff4e2;border-radius:6px;padding:4px 8px;margin-top:6px}
details summary{cursor:pointer;color:var(--suave);font-size:14px}
.resumen{max-width:900px;font:15px/1.6 'Source Sans 3',sans-serif}
.resumen h2{font-size:16px;margin:22px 0 6px}
.resumen table{border-collapse:collapse;width:100%;font-size:13px}
.resumen td,.resumen th{border-bottom:1px solid var(--linea);padding:6px 8px;text-align:left;vertical-align:top}
.leyenda{display:flex;gap:10px;flex-wrap:wrap;font:12px 'Source Sans 3',sans-serif;color:var(--suave);margin:6px 0 12px}
@media(max-width:900px){.pag{grid-template-columns:1fr}.img{position:static}}
"""

JS = """
function ver(id){document.querySelectorAll('.vista').forEach(v=>v.classList.toggle('on',v.id===id));
document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+id));window.scrollTo(0,0)}
function ruta(){var h=(location.hash||'#resumen').slice(1);if(!document.getElementById(h))h='resumen';ver(h)}
window.addEventListener('hashchange',ruta);ruta();
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){var d=x.target;d.style.backgroundImage='url('+d.dataset.bg+')';io.unobserve(d)}})},{rootMargin:'800px'});
document.querySelectorAll('.hoja').forEach(function(d){io.observe(d)});
function irA(ev,n){ev.preventDefault();var el=document.getElementById('p'+n);if(el)el.scrollIntoView();}
"""


def generar(doc, parsers, comunes, salmos, himnos, carpeta, tomos, resumen_html='', uni=None,
            nombre='Común de la Santísima Virgen María', por_tira=10, dpi=72):
    carpeta = Path(carpeta)
    (carpeta / 'img').mkdir(parents=True, exist_ok=True)
    pares = getattr(uni, '_pares', {}) if uni else {}
    salmos_d = salmos if isinstance(salmos, dict) else {s['id']: s for s in salmos}
    vistas = []
    for p in parsers:
        a, b = tomos[p.tomo]
        por_pag = {n: [] for n in range(a, b + 1)}
        vistos = set()
        hora = ''
        parte = ''
        for r in p.R:
            d = r.dueno
            if isinstance(d, str):
                if d.startswith('hora:'):
                    hora = d[5:]
                    por_pag[r.pdf].append(f'<div class="hora">{e(NOMBRE_HORA.get(hora, hora))}</div>')
                continue
            if not isinstance(d, dict) or id(d) in vistos:
                continue
            vistos.add(id(d))
            if 'horas' in d:  # título del común
                por_pag[r.pdf].append(f'<div class="titulo">{e(d["titulo"])}</div>')
                continue
            if 'parte' in d and 'piezas' in d:
                parte = d['parte']
                por_pag[r.pdf].append(f'<div class="parte">{e(r.texto.strip())}</div>')
                continue
            tipo = d.get('_tipo')
            if tipo is None and 'partes' in d:   # texto del salmo en la biblioteca
                continue
            if tipo in ('repeticion',):
                rep = ' '.join(x.texto.strip() for x in sorted(d['_raw'], key=lambda x: x.n))
                por_pag[r.pdf].append(f'<div class="card"><div class="cab"><span class="tipo">antífona repetida</span></div><p class="muted">{e(rep)}</p></div>')
                continue
            if tipo == 'remite':
                por_pag[r.pdf].append(f'<div class="card"><span class="chip azul">remite → {e(d["texto"])}</span></div>')
                continue
            if tipo not in NOMBRE_TIPO:
                continue
            u = pares.get(id(d))
            ctx = NOMBRE_HORA.get(hora, hora)
            por_pag[r.pdf].append(tarjeta(d, u, ctx, salmos_d, himnos))
        bloques = []
        # imágenes en tiras verticales de varias páginas (pocas imágenes para publicar)
        paginas = list(range(a, b + 1))
        tiras = [paginas[i:i + por_tira] for i in range(0, len(paginas), por_tira)]
        ubic = {}
        for k, tira in enumerate(tiras):
            nombre_img = f'img/t{p.tomo}-{tira[0]}.jpg'
            ruta = carpeta / nombre_img
            pixs = [doc[n - 1].get_pixmap(dpi=dpi) for n in tira]
            w, h = pixs[0].width, pixs[0].height
            if not ruta.exists():
                from PIL import Image
                hoja = Image.new('RGB', (w, h * len(tira)), 'white')
                for j, px in enumerate(pixs):
                    hoja.paste(Image.frombytes('RGB', (px.width, px.height), px.samples), (0, j * h))
                hoja.save(ruta, 'JPEG', quality=58, optimize=True)
            for j, n in enumerate(tira):
                ubic[n] = (nombre_img, j, len(tira), w, h)
        indice = []
        for c in p.comunes:
            indice.append(f'<a href="#p{c["_pdf"]}" onclick="irA(event,{c["_pdf"]})">{e(c["titulo"].capitalize())}</a>')
        for n in paginas:
            img, j, cnt, w, h = ubic[n]
            pos = 0 if cnt == 1 else j * 100 / (cnt - 1)
            impresa = next((r.impresa for r in p.R if r.pdf == n), '')
            bloques.append(
                f'<section class="pag" id="p{n}"><div class="img"><div class="num">PDF {n} · pág. impresa {e(str(impresa))}</div>'
                f'<div class="hoja" role="img" aria-label="Página {n} del PDF" data-bg="{img}" '
                f'style="aspect-ratio:{w}/{h};background-size:100% {cnt * 100}%;background-position:0 {pos:.4f}%"></div></div>'
                f'<div class="piezas">{"".join(por_pag[n]) or "<p class=muted>Sin piezas que empiecen en esta página.</p>"}</div></section>')
        idx = f'<div class="indice">{"".join(indice)}</div>' if len(indice) > 1 else ''
        vistas.append((f'tomo-{p.tomo}', f'Tomo {ROMANOS[p.tomo]} · {a}–{b}', idx + ''.join(bloques)))
    nav = '<a href="#resumen">Resumen</a>' + ''.join(f'<a href="#{i}">{e(t)}</a>' for i, t, _ in vistas)
    leyenda = ('<div class="leyenda"><span><span class="chip cond">condición</span> variante con condición u opción</span>'
               '<span><span class="chip revisar">revisar</span> marcada para revisión</span>'
               '<span class="r">rojo = rúbrica, etiqueta o rótulo</span><span class="ref">azul = remisión</span></div>')
    cuerpo_html = (f'<section class="vista resumen" id="resumen">{leyenda}{resumen_html}</section>' +
                   ''.join(f'<section class="vista" id="{i}">{leyenda}{h}</section>' for i, _, h in vistas))
    page = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión · {e(nombre)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><h1>Revisión de la extracción · {e(nombre)}</h1>
<p class="lead">LH ADF · prueba de extracción por tipografía, cuatro tomos. A la izquierda la página del libro; a la derecha las piezas que empiezan en ella.</p>
<nav>{nav}</nav></header><main>{cuerpo_html}</main><script>{JS}</script></body></html>"""
    (carpeta / 'index.html').write_text(page, encoding='utf-8')
    return carpeta / 'index.html'
