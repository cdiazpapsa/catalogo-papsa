"""Separa cada catálogo en 3 vistas: Productos (X.html), Acabados (X-acabados.html), Lista de precios (X-lp.html).
Uso único sobre el estado actual del repo (idempotente: si X-acabados.html ya existe, no vuelve a partir X.html)."""
import re, json, glob, os, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FIN = re.compile(r'ACABADOS|_TELAS_|PINTURA|UPHOLSTERY')
SEC = re.compile(r'    <div class="section" id="([^"]+)"')

def parts(h):
    """Devuelve (pre, [(id, html)], post) de <main>."""
    ms = list(SEC.finditer(h))
    end = h.find('    <p class="pie-vigencia">')
    if end < 0: end = h.find('  </main>')
    secs = []
    for k, m in enumerate(ms):
        e = ms[k+1].start() if k+1 < len(ms) else end
        secs.append((m.group(1), h[m.start():e]))
    return h[:ms[0].start()], secs, h[end:]

def ncards(s): return len(re.findall(r'<div id="[^"]*" class="card', s))

def trim_imgs(h):
    a = h.find('<script id="imgdata"'); a = h.find('>', a) + 1; b = h.find('</script>', a)
    I = json.loads(h[a:b]); used = sorted({int(x) for x in re.findall(r'data-i="(\d+)"', h)})
    remap = {o: n for n, o in enumerate(used)}
    h2 = re.sub(r'data-i="(\d+)"', lambda m: f'data-i="{remap[int(m.group(1))]}"', h[:a]) + json.dumps([I[o] for o in used]) + h[b:]
    return h2

def tabs(p, active, n_prod, n_acab):
    t = [('', 'Catálogo de productos', n_prod), ('-acabados', 'Acabados', n_acab), ('-lp', 'Lista de precios', None)]
    out = '<nav class="prov-tabs">'
    for suf, lab, n in t:
        cls = 'ptab active' if suf == active else 'ptab'
        badge = f'<span class="ptab-n">{n}</span>' if n is not None else ''
        out += f'<a class="{cls}" href="{p}{suf}.html">{lab}{badge}</a>'
    return out + '</nav>\n'

TAB_CSS = '''
/* ── PESTAÑAS POR PROVEEDOR ── */
.prov-tabs { display: flex; gap: 6px; margin: 0 0 16px; border-bottom: 2px solid var(--border); flex-wrap: wrap; }
.ptab { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; margin-bottom: -2px;
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none;
  color: var(--text-mid); border-bottom: 3px solid transparent; }
.ptab:hover { color: var(--dark-blue); }
.ptab.active { color: var(--petrol); border-bottom-color: var(--bright-red); }
.ptab-n { font-size: 0.64rem; color: #fff; background: var(--text-lo); border-radius: 20px; padding: 2px 8px; }
.ptab.active .ptab-n { background: var(--petrol); }
.empty-state { background: var(--surface); border: 1px dashed var(--border); border-radius: 6px; padding: 48px 24px;
  text-align: center; color: var(--text-mid); font-size: 0.9rem; line-height: 1.5; }
.empty-state b { display: block; color: var(--petrol); font-size: 1rem; margin-bottom: 6px; }
'''

def main():
    pages = sorted(f for f in glob.glob(R + '*.html') if not re.search(r'(index|-acabados|-lp)\.html$', f))
    summary = {}
    for f in pages:
        p = os.path.basename(f)[:-5]
        h = open(f).read()
        if os.path.exists(R + p + '-acabados.html'):
            continue
        if TAB_CSS.strip()[:20] not in h:
            h = h.replace('</style>', TAB_CSS + '</style>', 1)
        pre, secs, post = parts(h)
        prod = [(i, s) for i, s in secs if not FIN.search(i)]
        acab = [(i, s) for i, s in secs if FIN.search(i)]
        n_prod = sum(ncards(s) for _, s in prod); n_acab = sum(ncards(s) for _, s in acab)
        label = re.search(r'<span class="prov-current">([^<]*)</span>', h).group(1)
        def nav_only(pre, keep):
            def f(m): return m.group(0) if m.group(1) in keep else ''
            return re.sub(r'\n    <a href="#([^"]+)" class="nav-pill"[^>]*>[^<]*</a>', f, pre)
        search_anchor = '    <div class="search-wrap">'
        # Productos
        pp = nav_only(pre, {i for i, _ in prod}).replace(search_anchor, '    ' + tabs(p, '', n_prod, n_acab) + search_anchor, 1)
        open(f, 'w').write(trim_imgs(pp + ''.join(s for _, s in prod) + post))
        # Acabados
        pa = nav_only(pre, {i for i, _ in acab}).replace(search_anchor, '    ' + tabs(p, '-acabados', n_prod, n_acab) + search_anchor, 1)
        pa = pa.replace(f'<span class="prov-current">{label}</span>', f'<span class="prov-current">{label} · Acabados</span>')
        pa = re.sub(r'placeholder="Buscar en [^"]*"', f'placeholder="Buscar acabados de {H.escape(label)} por clave, color o línea…"', pa)
        if acab:
            body = ''.join(s for _, s in acab)
        else:
            body = (f'    <div class="empty-state"><b>Acabados pendientes de cargar</b>'
                    f'Los acabados de {H.escape(label)} se publicarán aquí al cargar el muestrario o la lista vigente del proveedor.</div>\n\n')
            pa = pa.replace(pa[pa.find(search_anchor):], '', 0)
        open(R + p + '-acabados.html', 'w').write(trim_imgs(pa + body + post))
        summary[p] = (label, n_prod, n_acab, [i for i, _ in acab])
    if summary: json.dump(summary, open(R + 'tools/split_summary.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[1:3] for k, v in summary.items()}))

if __name__ == '__main__':
    main()
