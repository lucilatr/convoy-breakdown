#!/usr/bin/env python3
# Genera ep108_color_review.html clonando estructura de ep107_color_review.html
# Episodio 108 — "City Spy Chase!" (Los chicos juegan en Smalley's Garage a una
#   persecucion de espias por la ciudad: Von Steele escapa en su Durango por un
#   laberinto de barreras de hormigon; el escuadron lo acorrala y Charmaine lo
#   levanta con globos de desfile). Villano: Von Steele.
# Color final: desde la REFINERIA (endpoint /finals). Mapeo panel->imagen 1:1
#   (45 finales: 01,02,04..46; el breakdown tiene P03 -title card- sin color).
# Autos(SKU) + dialogos: desde trackerData de convoy_breakdown.html, indexado por 'label'.
import re, json, urllib.request

BK  = open('convoy_breakdown.html', encoding='utf-8').read()
TPL = open('ep107_color_review.html', encoding='utf-8').read()

# ---- 1. catalogo de vehiculos id -> {name, sku} ----
CAT = {}
for m in re.finditer(r"\{\s*id:'([^']+)',\s*name:'((?:[^'\\]|\\.)*)',\s*sku:'([^']+)',\s*badge:'vehicle'", BK):
    CAT[m.group(1)] = {'name': m.group(2), 'sku': m.group(3)}

# ---- 2. paneles EP108 desde trackerData ----
def unescape(s):
    return s.replace('\\"','"').replace("\\'","'").replace('\\n','\n').replace('\\\\','\\')

# El numero REAL de panel es el 'label' (primeros digitos). EP108 no tiene desfasaje.
tracker = {}
for line in BK.splitlines():
    mid = re.search(r"id:'ep108-p(\d+[a-z]?)'", line)
    if not mid: continue
    ml = re.search(r"label:'(\d+)", line)
    num = (ml.group(1) if ml else re.sub(r'[a-z]','',mid.group(1))).zfill(2)
    veh_ids = []
    mv = re.search(r"vehicles:\[([^\]]*)\]", line)
    if mv:
        veh_ids = [x.strip().strip("'\"") for x in mv.group(1).split(',') if x.strip()]
    vo = ''
    mvo = re.search(r'vo:"((?:\\.|[^"\\])*)"', line) or re.search(r"vo:'((?:\\.|[^'\\])*)'", line)
    if mvo: vo = unescape(mvo.group(1))
    mw = re.search(r"world:'(\w*)'", line); world = mw.group(1) if mw else ''
    me = re.search(r"env:'([^']*)'", line);  env = me.group(1) if me else ''
    vehicles = []
    for vid in veh_ids:
        v = CAT.get(vid)
        # los playsets/entornos (mountain-convoy, mountain-escape, smalleys-crusher)
        # no estan en el catalogo de vehiculos -> se omiten de la lista de autos.
        if v:
            vehicles.append({'name': v['name'], 'sku': v['sku']})
    tracker[num] = {'vehicles': vehicles, 'vo': vo, 'world': world, 'env': env}

# ---- 3. colores finales: ULTIMA version desde la REFINERIA (endpoint /finals) ----
url = 'https://refineria.onrender.com/api/projects/convoy/episodes/ep108/finals'
data = json.load(urllib.request.urlopen(url, timeout=90))
finals = data.get('finals', data if isinstance(data, list) else [])
COLOR = {}
for it in finals:
    b = it.get('board') or {}; fin = it.get('final')
    fn = b.get('filename','') or ''
    mm = re.search(r'_P(\d+)', fn)
    if not (mm and fin): continue
    num = mm.group(1).zfill(2)
    COLOR[num] = fin.get('imageUrl') if isinstance(fin, dict) else fin

nums = sorted(COLOR.keys(), key=lambda x:int(x))

# ---- 4. estructuras JS ----
WORLD = {'aw':'ADVENTURE WORLD','rw':'REAL WORLD'}
ENV = {'smalleys-garage':"SMALLEY'S GARAGE",'matchbox-city':'MATCHBOX CITY',
       'parade-route-maze':'PARADE ROUTE MAZE','city':'CITY','':''}
def scene_label(t):
    w = WORLD.get(t.get('world',''),'')
    e = ENV.get(t.get('env',''), (t.get('env','') or '').upper().replace('-',' '))
    return (w + (' · ' + e if e else '')) if w or e else ''

COLOR_URLS = {n: COLOR[n] for n in nums}
VEHICLES_IN_PANEL = {n: list(tracker.get(n,{}).get('vehicles',[])) for n in nums}
SCRIPT_DIALOGUES  = {n: tracker.get(n,{}).get('vo','') for n in nums}

# ── Ajustes de vehiculos por panel (pedido de la usuaria) ──
# Reemplazo total del set por panel, por id de vehiculo. Lista vacia = sin vehiculos.
# Primera pasada sin correcciones: se completan tras la revision de la usuaria.
VEH_SET = {}
for _n, _ids in VEH_SET.items():
    if _n in VEHICLES_IN_PANEL:
        VEHICLES_IN_PANEL[_n] = [{'name': CAT[i]['name'], 'sku': CAT[i]['sku']} for i in _ids if i in CAT]

# ── Altas/bajas por panel (revision de la usuaria) ──
SKU2NAME = {v['sku']: v['name'] for v in CAT.values()}
VEH_ADD = {}     # sumar estos SKU (dedupe por sku)
VEH_REMOVE = {}  # quitar estos SKU
for _n, _skus in VEH_REMOVE.items():
    if _n in VEHICLES_IN_PANEL:
        VEHICLES_IN_PANEL[_n] = [v for v in VEHICLES_IN_PANEL[_n] if v['sku'] not in _skus]
for _n, _skus in VEH_ADD.items():
    if _n in VEHICLES_IN_PANEL:
        have = {v['sku'] for v in VEHICLES_IN_PANEL[_n]}
        for s in _skus:
            if s not in have:
                VEHICLES_IN_PANEL[_n].append({'name': SKU2NAME.get(s, s), 'sku': s})
                have.add(s)

PANELS = [{'num':n,'label':n,'scene':scene_label(tracker.get(n,{})),
           'dialogue':SCRIPT_DIALOGUES.get(n,''),'chars':[]} for n in nums]

# ---- 5. reemplazos en el template ----
out = TPL
def repl_line(src, varname, value):
    pat = re.compile(r'^const '+varname+r' = .*?;\s*$', re.M)
    return pat.sub('const '+varname+' = '+json.dumps(value, ensure_ascii=False)+';', src, count=1)

out = repl_line(out, 'COLOR_URLS', COLOR_URLS)
out = repl_line(out, 'VEHICLES_IN_PANEL', VEHICLES_IN_PANEL)
out = repl_line(out, 'SCRIPT_DIALOGUES', SCRIPT_DIALOGUES)

# PANELS block: desde 'const PANELS = [' hasta 'const VILLAIN'
i0 = out.index('const PANELS = [')
i1 = out.index('const VILLAIN', i0)
out = out[:i0] + 'const PANELS = ' + json.dumps(PANELS, ensure_ascii=False, indent=2) + ';\n\n' + out[i1:]

# limpiar bloques de notas del episodio anterior
for name in ['ADDRESSED','ACTIONS','MATTEL_FEEDBACK']:
    out = re.sub(r'const '+name+r' = [\[{].*?\};', 'const '+name+' = {};', out, count=1, flags=re.S)

# ---- 6. lineup: vehiculos hero del EP108 (reveal P04 - Title Card composite) ----
# Sean=Land Rover 6x6, Aimee=Mustang Fastback, Crosby=Excavator,
# Ted=Triumph Scrambler, Charmaine=Rescue Helicopter. Villano Von Steele=Dodge Durango.
def vline(name, sku): return f'<div class="char-vehicle">{name} · #{sku}</div>'
LINEUP_VEH = {
 'Sean':      [('Land Rover 6x6','JKH28')],
 'Ted':       [('Triumph Scrambler','JKH31')],
 'Charmaine': [('Rescue Helicopter','JKH39')],
 'Aimee':     [('Mustang Fastback','JKH34')],
 'Crosby':    [('Excavator','JKH38')],
}
# quitar TODOS los char-vehicle (EP107) e insertar los del EP108 tras cada char-role
out = re.sub(r'\s*<div class="char-vehicle">[^<]*</div>', '', out)
for cname, vs in LINEUP_VEH.items():
    key = f'<div class="char-name">{cname}</div>'
    ci = out.find(key)
    if ci < 0: continue
    role_close = out.index('</div>', out.index('<div class="char-role"', ci)) + len('</div>')
    newv = ''.join('\n          ' + vline(n,s) for n,s in vs)
    out = out[:role_close] + newv + out[role_close:]

# ---- vestuario EP108 (MAZE): recorta 5 pins CUADRADOS de la hoja combinada ----
# Mismo orden L->R que la hoja: Charmaine, Crosby, Sean, Aimee, Ted.
try:
    from PIL import Image
    import os
    os.makedirs('wardrobe/108', exist_ok=True)
    sheet = Image.open('wardrobe/108/CONVOY-uniforms-MAZE.jpg').convert('RGB')
    W, H = sheet.size
    bg = sheet.getpixel((8, 8))
    Hc = int(H * 0.86)  # recorta el texto "CONVOY EP08 MAZE" de abajo
    ORDER = ['CHARMAINE', 'CROSBY', 'SEAN', 'AIMEE', 'TED']

    def is_fg(r, g, b):
        return abs(r-bg[0]) + abs(g-bg[1]) + abs(b-bg[2]) > 45

    # 1) segmentar por columnas: encontrar los 5 personajes por huecos de fondo
    sc = 6
    small = sheet.crop((0, 0, W, Hc)).resize((W//sc, Hc//sc))
    sw, sh = small.size; spx = small.load()
    coldens = []
    for x in range(sw):
        c = 0
        for y in range(sh):
            r, g, b = spx[x, y]
            if is_fg(r, g, b): c += 1
        coldens.append(c)
    thr = max(coldens) * 0.06
    runs = []; st = None
    for x in range(sw):
        if coldens[x] > thr and st is None: st = x
        elif coldens[x] <= thr and st is not None: runs.append((st, x)); st = None
    if st is not None: runs.append((st, sw))
    runs = [r for r in runs if (r[1]-r[0]) >= sw*0.03]
    runs.sort(key=lambda r: r[1]-r[0], reverse=True)
    runs = sorted(runs[:5])
    assert len(runs) == 5, 'segmentacion wardrobe: esperaba 5 personajes, hay %d' % len(runs)

    px = sheet.load()
    for (a, b), nm in zip(runs, ORDER):
        x0, x1 = a*sc, b*sc
        # 2) bbox vertical dentro de la franja del personaje
        miny, maxy = Hc, 0
        for y in range(0, Hc, 4):
            row = False
            for x in range(x0, x1, 4):
                r, g, bb = px[x, y]
                if is_fg(r, g, bb): row = True; break
            if row:
                if y < miny: miny = y
                if y > maxy: maxy = y
        pad = 45
        cx0 = max(0, x0-pad); cx1 = min(W, x1+pad)
        cy0 = max(0, miny-pad); cy1 = min(Hc, maxy+pad)
        ch = sheet.crop((cx0, cy0, cx1, cy1))
        cw, chh = ch.size
        side = max(cw, chh)
        cv = Image.new('RGB', (side, side), bg)
        cv.paste(ch, ((side-cw)//2, (side-chh)//2))
        cv.resize((1080, 1080), Image.LANCZOS).save('wardrobe/108/%s_EP108.png' % nm)
    print('[ok] pins de wardrobe/108 generados:', ', '.join(ORDER))
except ImportError:
    print('[warn] PIL no disponible: no se regeneraron los pins de wardrobe/108')

WARDROBE = {
    '107/SEAN_EP107.png':      '108/SEAN_EP108.png',
    '107/TED_EP107.png':       '108/TED_EP108.png',
    '107/CHARMAINE_EP107.png': '108/CHARMAINE_EP108.png',
    '107/AIMEE_EP107.png':     '108/AIMEE_EP108.png',
    '107/CROSBY_EP107.png':    '108/CROSBY_EP108.png',
}
for _old, _new in WARDROBE.items():
    out = out.replace('./wardrobe/' + _old, './wardrobe/' + _new)

# ---- 7. textos de episodio ----
reps = [
    ('CVY26_001_107','CVY26_001_108'),
    ('Episode 107 — Highway Heroes!','Episode 108 — City Spy Chase!'),
    ('107 — Highway Heroes!','108 — City Spy Chase!'),
    ('Episode 107 · Cast · Highway Heroes','Episode 108 · Cast · City Spy Chase'),
    ('CHARACTER LINEUP PAGE — EP107 (Highway Heroes)','CHARACTER LINEUP PAGE — EP108 (City Spy Chase)'),
    ('Episode 107','Episode 108'),
    ('Color Review · Highway Heroes!','Color Review · City Spy Chase!'),
    ('Highway Heroes! · 46 Panels','City Spy Chase! · %d Panels' % len(nums)),
    ('Highway Heroes!','City Spy Chase!'),
    ('Highway Heroes','City Spy Chase'),
    ('>46<', '>%d<' % len(nums)),
    ('46 Panels','%d Panels' % len(nums)),
]
for a_,b_ in reps:
    out = out.replace(a_, b_)

open('ep108_color_review.html','w',encoding='utf-8').write(out)

# ---- resumen ----
print('vehiculos catalogo:', len(CAT))
print('paneles con color:', len(nums), '->', ','.join(nums))
print('P03 (title card) sin color -> excluido')
missing_vo  = [n for n in nums if not SCRIPT_DIALOGUES[n]]
missing_veh = [n for n in nums if not VEHICLES_IN_PANEL[n]]
print('sin dialogo:', missing_vo)
print('sin autos:', missing_veh)
print('\n== autos por panel ==')
for n in nums:
    vs = ', '.join('%s #%s' % (v['name'], v['sku']) for v in VEHICLES_IN_PANEL[n]) or '—'
    print(n, ':', vs)
