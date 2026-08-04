#!/usr/bin/env python3
# Genera ep106_color_review.html clonando estructura de ep105_color_review.html
# Episodio 106 — "Volcano Treasure!" (The Matchbox Crew Volcano Treasure). Cast de aventura, sin villano.
# Color final: desde la REFINERIA (endpoint /finals). Mapeo panel->imagen 1:1
#   (44 finales: 01,02,04..45; el breakdown tiene P03 -title card- sin color).
# Autos(SKU) + dialogos: desde trackerData de convoy_breakdown.html, indexado por 'label'.
import re, json, urllib.request

BK  = open('convoy_breakdown.html', encoding='utf-8').read()
TPL = open('ep105_color_review.html', encoding='utf-8').read()

# ---- 1. catalogo de vehiculos id -> {name, sku} ----
CAT = {}
for m in re.finditer(r"\{\s*id:'([^']+)',\s*name:'((?:[^'\\]|\\.)*)',\s*sku:'([^']+)',\s*badge:'vehicle'", BK):
    CAT[m.group(1)] = {'name': m.group(2), 'sku': m.group(3)}

# ---- 2. paneles EP106 desde trackerData ----
def unescape(s):
    return s.replace('\\"','"').replace("\\'","'").replace('\\n','\n').replace('\\\\','\\')

# El numero REAL de panel es el 'label' (primeros digitos).
tracker = {}
for line in BK.splitlines():
    mid = re.search(r"id:'ep106-p(\d+)'", line)
    if not mid: continue
    ml = re.search(r"label:'(\d+)", line)
    num = (ml.group(1) if ml else mid.group(1)).zfill(2)
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
        vehicles.append({'name': v['name'], 'sku': v['sku']} if v else {'name': vid, 'sku': '??'})
    tracker[num] = {'vehicles': vehicles, 'vo': vo, 'world': world, 'env': env}

# ---- 3. colores finales: ULTIMA version desde la REFINERIA (endpoint /finals) ----
url = 'https://refineria.onrender.com/api/projects/convoy/episodes/ep106/finals'
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
ENV = {'smalleys-garage':"SMALLEY'S GARAGE",'treasure-mountain':'TREASURE MOUNTAIN',
       'construction-site':'CONSTRUCTION SITE','city':'CITY','':''}
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

# Paneles 04, 07 y 08: mismo convoy de 5 (pedido de la usuaria). "Land Rover 6x6
# Distressed" (BL250) no esta en el catalogo del breakdown (ahi solo esta "Land Rover
# 6x6" JKH28), por eso van como literales.
def _convoy5():
    return [
        {'name': 'Polaris RZR',               'sku': 'BL251'},
        {'name': 'Land Rover 6x6 Distressed', 'sku': 'BL250'},
        {'name': 'Triumph Scrambler',         'sku': 'JKH31'},
        {'name': 'Ford F-150',                'sku': 'JKH36'},
        {'name': 'Toyota Tacoma',             'sku': 'JMB54'},
    ]
for _p in ('04', '07', '08'):
    if _p in VEHICLES_IN_PANEL:
        VEHICLES_IN_PANEL[_p] = _convoy5()

# Panel 14 (transformacion): las 9 formas (pedido de la usuaria). BL250 unificado como
# "Land Rover 6x6 Distressed"; JKH34 va como "Mustang Fastback Distressed" en este panel.
VEHICLES_IN_PANEL['14'] = [
    {'name': 'Land Rover 6x6 Distressed', 'sku': 'BL250'},
    {'name': 'Ford F-150',                'sku': 'JKH36'},
    {'name': 'Toyota Tacoma',             'sku': 'JMB54'},
    {'name': 'Chevy Stock Car',           'sku': 'JKH33'},
    {'name': 'Mustang Fastback','sku': 'JKH34'},
    {'name': 'Polaris RZR',               'sku': 'BL251'},
    {'name': '1971 Dodge Challenger',     'sku': 'JKH42'},
    {'name': 'Triumph Scrambler',         'sku': 'JKH31'},
    {'name': 'Porsche 911',               'sku': 'BL252'},
]

# Panel 15 (pedido de la usuaria): los 4 autos de carrera. JKH34 = "Mustang Fastback Distressed".
VEHICLES_IN_PANEL['15'] = [
    {'name': '1971 Dodge Challenger',      'sku': 'JKH42'},
    {'name': 'Mustang Fastback','sku': 'JKH34'},
    {'name': 'Porsche 911',                'sku': 'BL252'},
    {'name': 'Chevy Stock Car',            'sku': 'JKH33'},
]

# Panel 18 (pedido de la usuaria): los 5 autos de carrera que levantan los chicos.
VEHICLES_IN_PANEL['18'] = [
    {'name': 'Triumph Scrambler',          'sku': 'JKH31'},
    {'name': 'Porsche 911',                'sku': 'BL252'},
    {'name': '1971 Dodge Challenger',      'sku': 'JKH42'},
    {'name': 'Chevy Stock Car',            'sku': 'JKH33'},
    {'name': 'Mustang Fastback','sku': 'JKH34'},
]

# Panel 38 (pedido de la usuaria): sumar Chevy Stock Car (Aimee) al composite del drift.
VEHICLES_IN_PANEL['38'] = [
    {'name': 'Porsche 911',       'sku': 'BL252'},
    {'name': 'Mustang Fastback',  'sku': 'JKH34'},
    {'name': 'Triumph Scrambler', 'sku': 'JKH31'},
    {'name': 'Chevy Stock Car',   'sku': 'JKH33'},
]

# Panel 43 (pedido de la usuaria): en el podio estan ademas el helicopter, la moto, el 911 y el fastback.
VEHICLES_IN_PANEL['43'] = [
    {'name': 'Chevy Stock Car',   'sku': 'JKH33'},
    {'name': 'Rescue Helicopter', 'sku': 'JKH39'},
    {'name': 'Triumph Scrambler', 'sku': 'JKH31'},
    {'name': 'Porsche 911',       'sku': 'BL252'},
    {'name': 'Mustang Fastback',  'sku': 'JKH34'},
]

# Panel 44 (pedido de la usuaria): helicopter, Mustang Fastback y la moto.
VEHICLES_IN_PANEL['44'] = [
    {'name': 'Rescue Helicopter', 'sku': 'JKH39'},
    {'name': 'Mustang Fastback',  'sku': 'JKH34'},
    {'name': 'Triumph Scrambler', 'sku': 'JKH31'},
]

# Reemplazo global (pedido de la usuaria): Land Rover 6x6 (JKH28) -> Land Rover 6x6
# Distressed (BL250) en todos los paneles donde aparezca.
for _vs in VEHICLES_IN_PANEL.values():
    for _v in _vs:
        if _v['sku'] == 'JKH28':
            _v['name'] = 'Land Rover 6x6 Distressed'
            _v['sku']  = 'BL250'

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

# ---- 6. lineup: vehiculos de aventura del EP106 (segun guion: convoy del volcan) ----
# EP106 no tiene villano. Convoy (p09): Tacoma(Charmaine), Rover6x6(Sean), F150(Crosby),
# RZR(Aimee), Scrambler(Ted).
def vline(name, sku): return f'<div class="char-vehicle">{name} · #{sku}</div>'
# En el P14 los vehiculos del convoy se TRANSFORMAN en autos de carrera; cada
# personaje maneja 2 formas (climb -> race). Charmaine ademas pilotea el helicoptero
# en el rescate del climax.
LINEUP_VEH = {
 'Sean':      [('Land Rover 6x6','JKH28'), ('Mustang Fastback','JKH34')],
 'Ted':       [('Triumph Scrambler','JKH31')],
 'Charmaine': [('Toyota Tacoma','JMB54'), ('1971 Dodge Challenger','JKH42'), ('Rescue Helicopter','JKH39')],
 'Aimee':     [('Polaris RZR','BL251'), ('Chevy Stock Car','JKH33')],
 'Crosby':    [('Ford F-150','JKH36'), ('Porsche 911','BL252')],
}
# quitar TODOS los char-vehicle (EP105) e insertar los del EP106 tras cada char-role
out = re.sub(r'\s*<div class="char-vehicle">[^<]*</div>', '', out)
for cname, vs in LINEUP_VEH.items():
    key = f'<div class="char-name">{cname}</div>'
    ci = out.find(key)
    if ci < 0: continue
    role_close = out.index('</div>', out.index('<div class="char-role"', ci)) + len('</div>')
    newv = ''.join('\n          ' + vline(n,s) for n,s in vs)
    out = out[:role_close] + newv + out[role_close:]

# ---- vestuario EP106 (volcano): recorta 5 pins CUADRADOS de la hoja combinada ----
try:
    from PIL import Image
    import os
    os.makedirs('wardrobe/106', exist_ok=True)
    sheet = Image.open('wardrobe/CONVOY-106-uniforms-VOLCANO.jpg').convert('RGB')
    W, H = sheet.size
    bg = sheet.getpixel((8, 8))
    Hc = int(H * 0.86)  # recorta el texto "CONVOY EP06 VOLCANO" de abajo
    # orden L->R en la hoja: Charmaine, Crosby, Sean, Aimee, Ted
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
        cv.resize((1080, 1080), Image.LANCZOS).save('wardrobe/106/%s_EP106.png' % nm)
    print('[ok] pins de wardrobe/106 generados:', ', '.join(ORDER))
except ImportError:
    print('[warn] PIL no disponible: no se regeneraron los pins de wardrobe/106')

WARDROBE = {
    '105/SEAN_EP105.png':      '106/SEAN_EP106.png',
    '105/TED_EP105.png':       '106/TED_EP106.png',
    '105/CHARMAINE_EP105.png': '106/CHARMAINE_EP106.png',
    '105/AIMEE_EP105.png':     '106/AIMEE_EP106.png',
    '105/CROSBY_EP105.png':    '106/CROSBY_EP106.png',
}
for _old, _new in WARDROBE.items():
    out = out.replace('./wardrobe/' + _old, './wardrobe/' + _new)

# ---- 7. textos de episodio ----
reps = [
    ('CVY26_001_105','CVY26_001_106'),
    ('Episode 105 — Booby Trap Building!','Episode 106 — Volcano Treasure!'),
    ('105 — Booby Trap Building!','106 — Volcano Treasure!'),
    ('Episode 105 · Cast · Booby Trap Building','Episode 106 · Cast · Volcano Treasure'),
    ('CHARACTER LINEUP PAGE — EP105 (Booby Trap Building)','CHARACTER LINEUP PAGE — EP106 (Volcano Treasure)'),
    ('Episode 105','Episode 106'),
    ('Color Review · Booby Trap Building!','Color Review · Volcano Treasure!'),
    ('Booby Trap Building! · 44 Panels','Volcano Treasure! · %d Panels' % len(nums)),
    ('Booby Trap Building!','Volcano Treasure!'),
    ('Booby Trap Building','Volcano Treasure'),
    ('>44<', '>%d<' % len(nums)),
    ('44 Panels','%d Panels' % len(nums)),
]
for a_,b_ in reps:
    out = out.replace(a_, b_)

open('ep106_color_review.html','w',encoding='utf-8').write(out)

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
