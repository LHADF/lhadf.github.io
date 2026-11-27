#!/usr/bin/env python3
"""Arma Cervus en un solo archivo HTML a partir de src/.

    python3 tools/armar.py            -> dist/index.html (página completa, para GitHub Pages),
                                         con lo de la app instalable: manifest, sw.js e íconos (src/app, src/assets/app)
    python3 tools/armar.py --artifact -> dist/artifact.html (sin <head>, para publicar como Artifact)
"""
import base64, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, 'src')
DIST = os.path.join(RAIZ, 'dist')

def leer(*partes):
    with open(os.path.join(SRC, *partes), encoding='utf-8') as f:
        return f.read()

def ico(d):
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">{d}</svg>'

import subprocess
subprocess.run([sys.executable, os.path.join(RAIZ, 'tools', 'base_js.py')], check=True)

ilustracion = base64.b64encode(open(os.path.join(SRC, 'assets', 'coro.png'), 'rb').read()).decode()
datos = sorted(f for f in os.listdir(os.path.join(SRC, 'datos')) if f.endswith('.js'))

cabeza = '''<title>Cervus</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Cervus · Liturgia de las Horas según el calendario ADF, con canto gregoriano">
<meta name="theme-color" content="#ffffff">
'''
# App instalable (no en el Artifact): manifest, íconos y lo que se ve al compartir el enlace
app = '''<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" href="app/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="app/apple-touch-icon.png">
<meta name="application-name" content="Cervus">
<meta name="apple-mobile-web-app-title" content="Cervus">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Cervus">
<meta property="og:title" content="Cervus · Liturgia de las Horas">
<meta property="og:description" content="Liturgia de las Horas según el calendario ADF, con canto gregoriano.">
<meta property="og:url" content="https://lhadf.github.io/">
<meta property="og:image" content="https://lhadf.github.io/app/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
'''
cabeza += '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&display=swap" rel="stylesheet">
'''

cuerpo = f'''<style>{leer('assets', 'signos.css')}
{leer('assets', 'ae.css')}
{leer('app.css')}</style>
<header class="top" id="top"><div class="wrap">
  <div class="top-in">
    <button class="iconbtn" id="atras" data-act="atras" aria-label="Volver a hoy" hidden>{ico('<path d="M15 5l-7 7 7 7"/>')}</button>
    <h1 class="brand" id="brand"></h1>
    <button class="iconbtn" data-act="opciones" aria-label="Opciones">{ico('<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>')}</button>
  </div>
</div></header>
<main class="wrap" id="main"></main>
<script>{leer('vendor', 'exsurge.js')}</script>
<script>{leer('cantoral.js')}</script>
<script>{leer('salmodia.js')}</script>
<script>{''.join(leer('datos', f) for f in datos)}
window.ILU="data:image/png;base64,{ilustracion}";window.ILU_DIR={"null" if "--artifact" in sys.argv else "'ilu/'"};</script>
<script>{leer('completas.js')}</script>
<script>{leer('laudes.js')}</script>
<script>{leer('horas.js')}</script>
<script>{leer('latin.js')}</script>
<script>{leer('app.js')}</script>
'''

os.makedirs(DIST, exist_ok=True)
# Laudes: los datos van en un archivo aparte, que la app carga al abrir la hora (con huella, para que no quede viejo en caché)
import hashlib, shutil
_urls = {}
for _h in ('laudes', 'visperas', 'oficio', 'intermedia'):
    _l = open(os.path.join(SRC, 'carga', _h + '.js'), 'rb').read()
    shutil.copyfile(os.path.join(SRC, 'carga', _h + '.js'), os.path.join(DIST, _h + '.js'))
    _urls[_h] = _h + '.js?v=' + hashlib.md5(_l).hexdigest()[:8]
import json as _json
# «Solo latín»: la hora latina de Universalis, un archivo por mes (no se precargan: se bajan al abrir una hora en latín)
import glob as _glob
for _p in sorted(_glob.glob(os.path.join(SRC, 'carga', 'latin-*.js'))):
    _n = os.path.basename(_p)[:-3]
    shutil.copyfile(_p, os.path.join(DIST, _n + '.js'))
    _urls[_n] = _n + '.js?v=' + hashlib.md5(open(_p, 'rb').read()).hexdigest()[:8]
# Imágenes de la tarjeta del inicio (src/assets/ilu, de tools/ilustraciones.py): archivos aparte; la app carga solo la del día.
# Publicada como Artifact no hay archivos aparte: queda el coro.
if '--artifact' not in sys.argv:
    shutil.rmtree(os.path.join(DIST, 'ilu'), ignore_errors=True)
    shutil.copytree(os.path.join(SRC, 'assets', 'ilu'), os.path.join(DIST, 'ilu'))
cuerpo = cuerpo.replace("<script>" + leer('app.js'), "<script>window.HORAS_URL=" + _json.dumps(_urls) + ";" + leer('app.js'))
if '--artifact' in sys.argv:
    destino, html = os.path.join(DIST, 'artifact.html'), cabeza + cuerpo
else:
    destino = os.path.join(DIST, 'index.html')
    html = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + cabeza + app + '</head>\n<body>\n' + cuerpo + '</body>\n</html>\n')
with open(destino, 'w', encoding='utf-8') as f:
    f.write(html)
if '--artifact' not in sys.argv:
    # App instalable: íconos, manifest y service worker (con la huella de esta versión, para que se renueve)
    shutil.rmtree(os.path.join(DIST, 'app'), ignore_errors=True)
    shutil.copytree(os.path.join(SRC, 'assets', 'app'), os.path.join(DIST, 'app'))
    shutil.copyfile(os.path.join(DIST, 'app', 'favicon.ico'), os.path.join(DIST, 'favicon.ico'))
    shutil.copyfile(os.path.join(SRC, 'app', 'manifest.webmanifest'), os.path.join(DIST, 'manifest.webmanifest'))
    precarga = ['./', 'manifest.webmanifest', 'favicon.ico'] + sorted(v for k, v in _urls.items() if not k.startswith('latin-')) + [
        'app/' + n for n in ('icon-192.png', 'icon-512.png', 'maskable-192.png', 'maskable-512.png', 'favicon-32.png', 'apple-touch-icon.png')]
    huella = hashlib.md5((html + leer('app', 'sw.js') + leer('app', 'manifest.webmanifest')).encode())
    for n in sorted(os.listdir(os.path.join(SRC, 'assets', 'app'))):
        huella.update(open(os.path.join(SRC, 'assets', 'app', n), 'rb').read())
    version = huella.hexdigest()[:10]
    sw = leer('app', 'sw.js').replace('__VERSION__', version).replace('__PRECARGA__', _json.dumps(precarga))
    with open(os.path.join(DIST, 'sw.js'), 'w', encoding='utf-8') as f:
        f.write(sw)
print(f'{os.path.relpath(destino, RAIZ)}: {len(html.encode()) // 1024} KB')
