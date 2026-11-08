#!/usr/bin/env python3
"""Arma Septies en un solo archivo HTML a partir de src/.

    python3 tools/armar.py            -> dist/index.html (página completa, para GitHub Pages)
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

cabeza = '''<title>LH ADF</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="LH ADF · Liturgia de las Horas · Completas">
<meta name="theme-color" content="#ffffff">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..700&display=swap" rel="stylesheet">
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
window.ILU="data:image/png;base64,{ilustracion}";</script>
<script>{leer('completas.js')}</script>
<script>{leer('app.js')}</script>
'''

os.makedirs(DIST, exist_ok=True)
if '--artifact' in sys.argv:
    destino, html = os.path.join(DIST, 'artifact.html'), cabeza + cuerpo
else:
    destino = os.path.join(DIST, 'index.html')
    html = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + cabeza + '</head>\n<body>\n' + cuerpo + '</body>\n</html>\n')
with open(destino, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'{os.path.relpath(destino, RAIZ)}: {len(html.encode()) // 1024} KB')
