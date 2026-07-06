#!/usr/bin/env python3
# Genera ep102_color_review.html clonando la estetica/estructura de ep101_color_review.html
# Datos: colores desde refineria /finals ; autos(SKU) + dialogos desde trackerData de convoy_breakdown.html
import re, json, urllib.request

BK = open('convoy_breakdown.html', encoding='utf-8').read()
TPL = open('ep101_color_review.html', encoding='utf-8').read()

# ---- 1. catalogo de vehiculos id -> {name, sku} ----
CAT = {}
for m in re.finditer(r"\{\s*id:'([^']+)',\s*name:'((?:[^'\\]|\\.)*)',\s*sku:'([^']+)',\s*badge:'vehicle'", BK):
    CAT[m.group(1)] = {'name': m.group(2), 'sku': m.group(3)}

# ---- 2. paneles EP102 desde trackerData ----
def unescape(s):
    return s.replace('\\"','"').replace("\\'","'").replace('\\n','\n').replace('\\\\','\\')

tracker = {}
for line in BK.splitlines():
    mid = re.search(r"id:'ep102-p(\d+)'", line)
    if not mid: continue
    num = mid.group(1).zfill(2)
    veh_ids = []
    mv = re.search(r"vehicles:\[([^\]]*)\]", line)
    if mv:
        veh_ids = [x.strip().strip("'\"") for x in mv.group(1).split(',') if x.strip()]
    vo = ''
    mvo = re.search(r'vo:"((?:\\.|[^"\\])*)"', line)
    if mvo: vo = unescape(mvo.group(1))
    world = (re.search(r"world:'(\w*)'", line) or [None,''])[1] if re.search(r"world:'(\w*)'", line) else ''
    mw = re.search(r"world:'(\w*)'", line); world = mw.group(1) if mw else ''
    me = re.search(r"env:'([^']*)'", line);  env = me.group(1) if me else ''
    vehicles = []
    for vid in veh_ids:
        v = CAT.get(vid)
        vehicles.append({'name': v['name'], 'sku': v['sku']} if v else {'name': vid, 'sku': '??'})
    tracker[num] = {'vehicles': vehicles, 'vo': vo, 'world': world, 'env': env}

# ---- 3. colores desde refineria ----
url = 'https://refineria.onrender.com/api/projects/convoy/episodes/ep102/finals'
data = json.load(urllib.request.urlopen(url, timeout=60))
finals = data.get('finals', data if isinstance(data, list) else [])
COLOR = {}
for it in finals:
    b = it.get('board') or {}; fin = it.get('final')
    fn = b.get('filename','') or ''
    mm = re.search(r'_P(\d+)', fn)
    if not (mm and fin): continue
    num = mm.group(1).zfill(2)
    gurl = fin.get('imageUrl') if isinstance(fin, dict) else fin
    COLOR[num] = gurl

nums = sorted(COLOR.keys(), key=lambda x:int(x))

# ---- 4. armar estructuras JS ----
WORLD = {'aw':'ADVENTURE WORLD','rw':'REAL WORLD'}
ENV = {'jungle':'JUNGLE','smalleys-garage':"SMALLEY'S GARAGE",'mountain-escape':'MOUNTAIN ESCAPE','':''}
def scene_label(t):
    w = WORLD.get(t.get('world',''),''); e = ENV.get(t.get('env',''), (t.get('env','') or '').upper().replace('-',' '))
    return (w + (' · ' + e if e else '')) if w or e else ''

COLOR_URLS = {n: COLOR[n] for n in nums}
VEHICLES_IN_PANEL = {n: list(tracker.get(n,{}).get('vehicles',[])) for n in nums}

# ── Correcciones manuales de autos por panel (revision del usuario) ──
# VEH_ADD suma autos ; VEH_SET reemplaza toda la lista del panel.
VEH_ADD = {
    '04': [{'name':'Super Hercules','sku':'JKH51'}, {'name':'Polaris RZR','sku':'BL251'}],
}
VEH_SET = {
    '13': [],
    '24': [],
}
for n, extra in VEH_ADD.items():
    if n in VEHICLES_IN_PANEL:
        have = {v['sku'] for v in VEHICLES_IN_PANEL[n]}
        VEHICLES_IN_PANEL[n] += [v for v in extra if v['sku'] not in have]
for n, lst in VEH_SET.items():
    if n in VEHICLES_IN_PANEL:
        VEHICLES_IN_PANEL[n] = lst
SCRIPT_DIALOGUES = {n: tracker.get(n,{}).get('vo','') for n in nums}
PANELS = [{'num':n,'label':n,'scene':scene_label(tracker.get(n,{})),
           'dialogue':tracker.get(n,{}).get('vo',''),'chars':[]} for n in nums]

# ---- 5. reemplazos en el template ----
out = TPL
def repl_line(src, varname, value):
    pat = re.compile(r'^const '+varname+r' = .*?;\s*$', re.M)
    return pat.sub('const '+varname+' = '+json.dumps(value, ensure_ascii=False)+';', src, count=1)

out = repl_line(out, 'COLOR_URLS', COLOR_URLS)
out = repl_line(out, 'VEHICLES_IN_PANEL', VEHICLES_IN_PANEL)
out = repl_line(out, 'SCRIPT_DIALOGUES', SCRIPT_DIALOGUES)

# PANELS block: desde 'const PANELS = [' hasta '];' antes de 'const VILLAIN'
i0 = out.index('const PANELS = [')
i1 = out.index('const VILLAIN', i0)
panels_js = 'const PANELS = ' + json.dumps(PANELS, ensure_ascii=False, indent=2) + ';\n\n'
out = out[:i0] + panels_js + out[i1:]

# reemplazar la pagina Character Lineup de EP101 por la de EP102 (jungla)
LINEUP_102 = open('_ep102_lineup.html', encoding='utf-8').read() if __import__('os').path.exists('_ep102_lineup.html') else None
a = out.index('<div class="page lineup-page">')
cstart = out.rfind('<!--', 0, a)
b = out.index('</div><!-- /lineup-page -->') + len('</div><!-- /lineup-page -->')
if LINEUP_102:
    out = out[:cstart] + LINEUP_102.strip() + out[b:]
else:
    out = out[:cstart] + out[b:]  # fallback: sin lineup si no esta el snippet

# textos de episodio
reps = [
    ('CVY26_001_101','CVY26_001_102'),
    ('Bridge Chase!','Jungle Race!'),
    ('Episode 101','Episode 102'),
    ('101 — Jungle Race!','102 — Jungle Race!'),
    ('45 Panels','%d Panels' % len(nums)),
    ('44 <span style="font-size:9px;opacity:0.5;font-weight:400;">(P03 pending design)</span>','%d' % len(nums)),
    ('Episode 101 · Cast','Episode 102 · Cast'),
]
for a_,b_ in reps:
    out = out.replace(a_, b_)

open('ep102_color_review.html','w',encoding='utf-8').write(out)

# ---- resumen ----
print('vehiculos catalogo:', len(CAT))
print('paneles con color:', len(nums), '->', ','.join(nums))
missing_vo = [n for n in nums if not SCRIPT_DIALOGUES[n]]
missing_veh = [n for n in nums if not VEHICLES_IN_PANEL[n]]
print('sin dialogo:', missing_vo)
print('sin autos:', missing_veh)
print('\n== autos por panel (para revisar) ==')
for n in nums:
    vs = ', '.join('%s #%s' % (v['name'], v['sku']) for v in VEHICLES_IN_PANEL[n]) or '—'
    print(n, ':', vs)
