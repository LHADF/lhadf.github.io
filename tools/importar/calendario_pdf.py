"""Lee el Calendario litúrgico ADF (PDF → texto con pdftotext -layout): celebraciones y notas al pie."""
import re, sys, json
MESES=['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE']
GRADOS=r'(Feria privilegiada|Feria|Memoria obligatoria|Memoria libre o Feria|Memoria libre|Fiesta|Solemnidad|Conmemoración|Domingo)'
def unir(a,b):
    if re.search(r'[A-Za-zÁÉÍÓÚáéíóúñ]-$',a): return a[:-1]+b      # guion de fin de renglón
    return (a+' '+b).strip()
def leer(txt):
    paginas=txt.split('\f'); mes=None; ents=[]; NOTAS=[]
    for np,pg in enumerate(paginas):
        mes0=mes
        L=[l.rstrip() for l in pg.split('\n')]
        notas={}; cur=None; cuerpo=[]
        # índice de la primera nota al pie de la página
        prim=next((i for i,l in enumerate(L) if re.match(r'^\d{1,2}\s{3,}\S',l)), None)
        # renglones sueltos justo antes de las notas, separados del cuerpo por un blanco: siguen la última nota de la página anterior
        sueltos=set()
        if prim is not None and NOTAS and NOTAS[-1]:
            j=prim-1
            while j>=0 and not L[j].strip(): j-=1
            bloque=[]
            while j>=0 and L[j].strip() and re.match(r'^\s{3,}\S',L[j]) and '|' not in L[j] and not re.match(r'^\s*'+GRADOS,L[j]): bloque.insert(0,j); j-=1
            if bloque and j>=0 and not L[j].strip():
                k=max(NOTAS[-1])
                for x in bloque: NOTAS[-1][k]=unir(NOTAS[-1][k],L[x].strip()); sueltos.add(x)
        for i,l in enumerate(L):
            if i in sueltos: continue
            s=l.strip()
            if s in MESES: mes=MESES.index(s)+1; cuerpo.append(('mes',mes)); continue
            m=re.match(r'^(\d{1,2})\s{3,}(\S.*)$', l)
            if m and mes: cur=int(m.group(1)); notas[cur]=m.group(2).strip(); continue
            if cur and re.match(r'^\s{3,}\S',l): notas[cur]=unir(notas[cur],s); continue
            if re.match(r'^\s*\d+\s*$',l) and not re.match(r'^\d\d$',l): continue
            cur=None; cuerpo.append(('l',l))
        NOTAS.append(notas)
        dia=None; e=None; m_act=mes0
        for t,l in cuerpo:
            if t=='mes': dia=None; m_act=l; continue
            if not m_act: continue
            m=re.match(r'^(\d\d)(?:\s+(\S.*))?$', l)
            if m: dia=int(m.group(1)); e={'fecha':f'{m_act:02d}-{dia:02d}','nombre':(m.group(2) or '').strip(),'pag':np}; ents.append(e); continue
            s=l.strip()
            if not s or dia is None: continue
            g=re.match(r'^'+GRADOS+r'\b(.*)$', s)
            if g and 'grado' not in e:
                e['grado']=g.group(1); resto=g.group(2); izq=resto.split('|')[0]
                e['cal_txt']=re.sub(r'\s+',' ',re.sub(r'\b\d+\b','',izq)).strip(' ,')
                e['refs']=[(sig,int(n)) for sig,n in re.findall(r'(?:([A-Z]{3})\s+)?(\d+)\b', izq)]
                e['color']=resto.split('|')[1].strip() if '|' in resto else ''
            elif g:   # otro grado para la misma celebración en otro calendario (p. ej. «Feria PGY»)
                izq=g.group(2).split('|')[0]
                e.setdefault('alt',[]).append({'grado':g.group(1),'cal_txt':re.sub(r'\s+',' ',re.sub(r'\b\d+\b','',izq)).strip(' ,'),'refs':[(sig,int(n)) for sig,n in re.findall(r'(?:([A-Z]{3})\s+)?(\d+)\b', izq)]})
            elif 'grado' not in e: e['nombre']=(e['nombre']+' '+s).strip()
            else: e={'fecha':e['fecha'],'nombre':s,'pag':np}; ents.append(e)
    for e in ents:
        e['notas']=[[sig or '', NOTAS[e['pag']].get(n,'??')] for sig,n in e.get('refs',[])]
        for a in e.get('alt',[]): a['notas']=[[sig or '', NOTAS[e['pag']].get(n,'??')] for sig,n in a.pop('refs')]
    return ents
if __name__=='__main__':
    E=leer(open(sys.argv[1],encoding='utf-8').read())
    json.dump(E,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
    print(len(E),'entradas;',sum(1 for e in E if e['notas']),'con nota;',sum(1 for e in E for n in e['notas'] if n[1]=='??'),'sin resolver;',sum(1 for e in E if 'grado' not in e),'sin grado')
