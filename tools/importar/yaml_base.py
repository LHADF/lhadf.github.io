"""Escritura de la base en YAML legible: textos de varios renglones como bloques literales."""
import os
import yaml


class _Dumper(yaml.SafeDumper):
    pass


def _str(d, s):
    if '\n' in s:
        return d.represent_scalar('tag:yaml.org,2002:str', s, style='|')
    return d.represent_scalar('tag:yaml.org,2002:str', s)


_Dumper.add_representer(str, _str)


def escribir(ruta, datos, cabecera=''):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    cab = ''.join(f'# {l}\n' if l else '#\n' for l in cabecera.split('\n')) if cabecera else ''
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(cab)
        yaml.dump(datos, f, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=1000, default_flow_style=False)


def leer(ruta):
    with open(ruta, encoding='utf-8') as f:
        return yaml.safe_load(f)
