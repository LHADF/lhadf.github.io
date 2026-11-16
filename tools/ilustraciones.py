#!/usr/bin/env python3
"""Convierte las imágenes del álbum «Liturgical Cliparts» en las ilustraciones de la tarjeta del inicio.

    python3 tools/ilustraciones.py <carpeta del álbum>

Lee base/ilustraciones.yaml y escribe src/assets/ilu/<clave>.webp: una máscara de una sola tinta (el blanco queda
transparente y el negro, tinta plena), recortada al dibujo y de 480 px de lado mayor. La app la pinta con la tinta de
las ilustraciones sobre el pergamino del arco. Las figuras muy angostas llevan a cada costado la guarda que diga
«guarda», tomada del mismo álbum. Borra las que ya no figuran en la base. El álbum no se sube al repositorio.
Necesita Pillow y numpy.
"""
import os, sys
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools', 'importar'))
from yaml_base import leer

LADO = 480
GUARDAS = {'rosetas': 'temaP1-2-1.jpg', 'rombos': 'temaP7-11-1.jpg', 'zigzag': 'temaP7-20-1.jpg'}   # frisos del álbum


def mascara(ruta, lado=1200):
    """Alfa de la tinta: blanco (≥235) transparente, negro (≤25) pleno; recortada al dibujo."""
    im = Image.open(ruta)
    im.draft('L', (lado * 2, lado * 2))
    im = im.convert('L')
    im.thumbnail((lado, lado), Image.LANCZOS)
    a = np.clip((235 - np.asarray(im).astype(float)) / (235 - 25), 0, 1)
    A = Image.fromarray((a * 255).astype('uint8'))
    caja = A.point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, *A.size)
    return A.crop(caja)


def guarda(album, nombre, alto):
    """Columna de friso, del 11 % del alto de la figura, repetida hasta llenarlo."""
    F = mascara(os.path.join(album, GUARDAS[nombre]), 1800)
    if F.width > F.height: F = F.rotate(90, expand=True)
    ancho = round(alto * 0.11)
    F = F.resize((ancho, max(1, round(F.height * ancho / F.width))), Image.LANCZOS)
    col, y = Image.new('L', (ancho, alto), 0), 0
    while y < alto:
        col.paste(F, (0, y)); y += F.height
    return col


def con_guardas(A, album, nombre):
    g, sep = guarda(album, nombre, A.height), round(A.height * 0.07)
    C = Image.new('L', (A.width + 2 * (g.width + sep), A.height), 0)
    C.paste(g, (0, 0)); C.paste(A, (g.width + sep, 0)); C.paste(g.transpose(Image.FLIP_LEFT_RIGHT), (C.width - g.width, 0))
    return C


def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    album = sys.argv[1]
    imagenes = leer(os.path.join(RAIZ, 'base', 'ilustraciones.yaml'))['imagenes']
    destino = os.path.join(RAIZ, 'src', 'assets', 'ilu')
    os.makedirs(destino, exist_ok=True)
    for clave, e in imagenes.items():
        A = mascara(os.path.join(album, e['album']))
        if e.get('guarda'): A = con_guardas(A, album, e['guarda'])
        A.thumbnail((LADO, LADO), Image.LANCZOS)
        rgba = Image.new('RGBA', A.size, (0, 0, 0, 0)); rgba.putalpha(A)
        rgba.save(os.path.join(destino, clave + '.webp'), 'WEBP', quality=70, alpha_quality=65, method=6)
    sobran = [f for f in os.listdir(destino) if f.endswith('.webp') and f[:-5] not in imagenes]
    for f in sobran: os.remove(os.path.join(destino, f))
    total = sum(os.path.getsize(os.path.join(destino, f)) for f in os.listdir(destino))
    print(f'src/assets/ilu: {len(imagenes)} imágenes, {total // 1024} KB' + (f' · borradas: {len(sobran)}' if sobran else ''))


if __name__ == '__main__':
    main()
