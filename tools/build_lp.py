"""Genera X-lp.html para cada proveedor a partir de los PDF en lp/<proveedor>/.
Opcional lp/<proveedor>/meta.json: {"archivo.pdf": {"titulo": "...", "vigencia": "..."}}. El primero listado es la lista actual."""
import re, json, os, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
S = json.load(open(R + 'tools/split_summary.json'))
for p, (label, n_prod, n_acab, _) in S.items():
    h = open(R + p + '.html').read()
    a = h.find('    <nav class="prov-tabs">'); main_open = h[:a]
    main_open = main_open.replace(f'<span class="prov-current">{label}</span>', f'<span class="prov-current">{label} · Lista de precios</span>')
    main_open = re.sub(r'href="#([^"]+)" class="nav-pill"', lambda m: f'href="{p}.html#{m.group(1)}" class="nav-pill"', main_open)
    tabs = re.search(r'    <nav class="prov-tabs">.*?</nav>\n', h, re.S).group(0)
    tabs = tabs.replace('class="ptab active"', 'class="ptab"').replace(f'class="ptab" href="{p}-lp.html"', f'class="ptab active" href="{p}-lp.html"')
    d = R + 'lp/' + p + '/'
    pdfs = sorted([x for x in os.listdir(d) if x.lower().endswith('.pdf')], reverse=True) if os.path.isdir(d) else []
    meta = json.load(open(d + 'meta.json')) if os.path.exists(d + 'meta.json') else {}
    order = [k for k in meta if k in pdfs] + [x for x in pdfs if x not in meta]
    if order:
        body = '    <div class="lp-list">\n'
        for k, fn in enumerate(order):
            m = meta.get(fn, {}); tit = m.get('titulo', fn[:-4]); vig = m.get('vigencia', '')
            url = f'lp/{p}/{fn}'
            tg = m.get('tag', 'Vigente' if k == 0 else 'Anterior')
            tag = f'<span class="lp-tag{"" if k == 0 else " lp-old"}">{H.escape(tg)}</span>'
            body += (f'      <div class="lp-item" onclick="document.querySelector(\'.lp-view\').src=\'{url}#view=FitH\'">{tag}<span class="lp-tit">{H.escape(tit)}</span>'
                     f'<span class="lp-vig">{H.escape(vig)}</span>'
                     f'<a class="lp-btn" onclick="event.stopPropagation()" href="{url}" target="_blank" rel="noopener">Abrir</a>'
                     f'<a class="lp-btn lp-dl" onclick="event.stopPropagation()" href="{url}" download>Descargar</a></div>\n')
        body += '    </div>\n'
        body += f'    <iframe class="lp-view" src="lp/{p}/{order[0]}#view=FitH" title="Lista de precios {H.escape(label)}"></iframe>\n'
    else:
        body = (f'    <div class="empty-state"><b>Lista de precios pendiente de cargar</b>'
                f'La lista de precios vigente de {H.escape(label)} se publicará aquí en PDF.</div>\n')
    css = '''<style>
.lp-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.lp-item { cursor: pointer; display: flex; align-items: center; gap: 12px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 12px 16px; }
.lp-tag { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #fff;
  background: var(--dark-green); border-radius: 20px; padding: 3px 10px; }
.lp-tag.lp-old { background: var(--text-lo); }
.lp-tit { font-weight: 700; color: var(--petrol); flex: 1; }
.lp-vig { font-size: 0.8rem; color: var(--text-mid); }
.lp-btn { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none;
  color: #fff; background: var(--petrol); border-radius: 4px; padding: 7px 12px; }
.lp-btn.lp-dl { background: var(--bright-red); }
.lp-view { width: 100%; height: 78vh; border: 1px solid var(--border); border-radius: 6px; background: #fff; }
</style>
'''
    out = (main_open.replace('</head>', css + '</head>', 1) + tabs + body +
           f'    <p class="pie-vigencia">{H.escape(label)} — Lista de precios de uso interno Haworth by Papsa. Confirmar vigencia con el proveedor antes de cotizar.</p>\n'
           '  </main>\n</div>\n</body>\n</html>\n')
    open(R + p + '-lp.html', 'w').write(out)
print('ok', len(S))
