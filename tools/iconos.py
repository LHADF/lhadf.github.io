#!/usr/bin/env python3
"""Íconos de Cervus (app instalable) a partir del logo.

    python3 tools/iconos.py   -> src/assets/app/*.png y favicon.ico

El logo es src/assets/cervus.png (ciervo bebiendo dentro de la C, sobre crema).
Lo que se genera se sube al repositorio; armar.py lo copia a dist/.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(RAIZ, 'src', 'assets', 'cervus.png')
SAL = os.path.join(RAIZ, 'src', 'assets', 'app')
CREMA = (254, 248, 230)          # el fondo del logo: #FEF8E6
GRANDE = 2048                    # se compone grande y se achica al final

logo = Image.open(LOGO).convert('RGB')
a = np.asarray(logo).astype(int)
ys, xs = np.where(np.abs(a - CREMA).sum(2) > 60)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
radio = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).max()   # círculo que contiene el dibujo
alto = y1 - y0


def lienzo(escala, lado=GRANDE):
    """Logo centrado (por su caja) sobre crema, con la escala pedida."""
    base = Image.new('RGB', (lado, lado), CREMA)
    w, h = round(logo.width * escala), round(logo.height * escala)
    chico = logo.resize((w, h), Image.LANCZOS)
    base.paste(chico, (round(lado / 2 - cx * escala), round(lado / 2 - cy * escala)))
    return base


def redondeado(img, frac):
    """Esquinas redondeadas transparentes (frac = radio / lado)."""
    lado = img.width
    m = Image.new('L', (lado, lado), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, lado - 1, lado - 1), radius=round(lado * frac), fill=255)
    out = img.convert('RGBA'); out.putalpha(m)
    return out


def guardar(img, nombre, lado):
    # paleta de 256 colores: el logo tiene tres tintas, y el archivo pesa un tercio
    chico = img.resize((lado, lado), Image.LANCZOS)
    chico.quantize(256, method=Image.Quantize.FASTOCTREE).save(os.path.join(SAL, nombre), optimize=True)


os.makedirs(SAL, exist_ok=True)
# «any»: baldosa crema con esquinas redondeadas; el dibujo ocupa el 74 % del alto
cualquiera = redondeado(lienzo(GRANDE * .74 / alto), .2)
for n in (192, 512):
    guardar(cualquiera, f'icon-{n}.png', n)
# «maskable»: a sangre; todo el dibujo dentro del círculo seguro (80 % del lado)
enmascarable = lienzo(GRANDE * .39 / radio)
for n in (192, 512):
    guardar(enmascarable, f'maskable-{n}.png', n)
# iOS redondea solo: cuadrado a sangre, un poco más holgado que «any»
guardar(lienzo(GRANDE * .72 / alto), 'apple-touch-icon.png', 180)
# Pestaña: más justo, para que el ciervo se lea a 16 y 32 px
pestana = redondeado(lienzo(GRANDE * .9 / alto), .18)
guardar(pestana, 'favicon-32.png', 32)
pestana.resize((256, 256), Image.LANCZOS).save(
    os.path.join(SAL, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])
print('íconos en', os.path.relpath(SAL, RAIZ))
