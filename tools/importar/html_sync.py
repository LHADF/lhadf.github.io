"""Lectura de las páginas HTML de sync: rúbricas (rojo) y texto (negro), renglón por renglón."""
import html, re
from html.parser import HTMLParser

ROJOS = {'#ff0000', 'red', '#cc0000', '#990000', '#c00000'}

class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila = []          # colores abiertos
        self.lineas = [[]]      # cada línea: lista de [rojo, texto]
        self.dentro = False     # dentro de #cuerpo
        self.prof = 0
        self.it = 0             # cursiva abierta
    def _rojo(self):
        for c in reversed(self.pila):
            if c is not None: return c in ROJOS
        return False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'div':
            if a.get('id') == 'cuerpo': self.dentro, self.prof = True, 1
            elif self.dentro: self.prof += 1
        if not self.dentro: return
        if tag == 'font': self.pila.append((a.get('color') or '').lower() or None)
        elif tag == 'span':
            m = re.search(r'color:\s*([#\w]+)', a.get('style') or '')
            self.pila.append(m.group(1).lower() if m else None)
        elif tag == 'br': self.lineas.append([])
        elif tag == 'p': self.lineas.append([]); self.lineas.append([])
        elif tag == 'i': self.it += 1
    def handle_endtag(self, tag):
        if not self.dentro: return
        if tag in ('font', 'span') and self.pila: self.pila.pop()
        elif tag == 'i': self.it = max(0, self.it - 1)
        elif tag == 'p': self.lineas.append([])
        elif tag == 'div':
            self.prof -= 1
            if self.prof == 0: self.dentro = False
    def handle_data(self, d):
        if not self.dentro: return
        d = re.sub(r'\s+', ' ', d)
        if not d.strip() and not (self.lineas[-1] and self.lineas[-1][-1][1].strip()): return
        r = self._rojo(); l = self.lineas[-1]
        if l and l[-1][0] == r: l[-1][1] += d
        else: l.append([r, d])

def lineas(ruta):
    """Devuelve una lista de renglones; cada renglón es una lista de (rojo, texto). Renglón vacío = separación de párrafo."""
    raw = open(ruta, 'rb').read()
    try: s = raw.decode('utf-8')
    except UnicodeDecodeError: s = raw.decode('latin-1')
    p = _P(); p.feed(s)
    out = []
    for l in p.lineas:
        segs = [(r, t) for r, t in l]
        # limpiar espacios en los bordes del renglón
        if segs:
            segs[0] = (segs[0][0], segs[0][1].lstrip()); segs[-1] = (segs[-1][0], segs[-1][1].rstrip())
            segs = [(r, t) for r, t in segs if t]
        out.append(segs)
    return out

def texto(segs): return ''.join(t for _, t in segs).strip()
def todo_rojo(segs): return bool(segs) and all(r for r, t in segs if t.strip())

def mostrar(ruta):
    for l in lineas(ruta):
        print(('R| ' if todo_rojo(l) else '  ') + ''.join(('«' + t + '»') if r else t for r, t in l))

if __name__ == '__main__':
    import sys; mostrar(sys.argv[1])
