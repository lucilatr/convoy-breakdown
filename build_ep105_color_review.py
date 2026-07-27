#!/usr/bin/env python3
# Genera ep105_color_review.html clonando estructura de ep104_color_review.html
# Episodio 105 — "Booby Trap Building!" (Skyscraper). Cast de construcción, sin villano.
# Color final: desde la REFINERIA (endpoint /finals). Mapeo panel->imagen 1:1
#   (44 finales: 01,02,04..45; el breakdown tiene P03 -title card- sin color).
# Autos(SKU) + dialogos: desde trackerData de convoy_breakdown.html, indexado por 'label'.
import re, json, urllib.request

BK  = open('convoy_breakdown.html', encoding='utf-8').read()
TPL = open('ep104_color_review.html', encoding='utf-8').read()

# ---- 1. catalogo de vehiculos id -> {name, sku} ----
CAT = {}
for m in re.finditer(r"\{\s*id:'([^']+)',\s*name:'((?:[^'\\]|\\.)*)',\s*sku:'([^']+)',\s*badge:'vehicle'", BK):
    CAT[m.group(1)] = {'name': m.group(2), 'sku': m.group(3)}

# ---- 2. paneles EP105 desde trackerData ----
def unescape(s):
    return s.replace('\\"','"').replace("\\'","'").replace('\\n','\n').replace('\\\\','\\')

# El numero REAL de panel es el 'label' (primeros digitos).
tracker = {}
for line in BK.splitlines():
    mid = re.search(r"id:'ep105-p(\d+)'", line)
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
url = 'https://refineria.onrender.com/api/projects/convoy/episodes/ep105/finals'
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
ENV = {'smalleys-garage':"SMALLEY'S GARAGE",'construction-site':'CONSTRUCTION SITE',
       'underground-cavern':'UNDERGROUND CAVERN','city':'CITY','':''}
def scene_label(t):
    w = WORLD.get(t.get('world',''),'')
    e = ENV.get(t.get('env',''), (t.get('env','') or '').upper().replace('-',' '))
    return (w + (' · ' + e if e else '')) if w or e else ''

COLOR_URLS = {n: COLOR[n] for n in nums}
VEHICLES_IN_PANEL = {n: list(tracker.get(n,{}).get('vehicles',[])) for n in nums}
SCRIPT_DIALOGUES  = {n: tracker.get(n,{}).get('vo','') for n in nums}

# ── Ajustes de vehiculos por panel (pedido de la usuaria) ──
# Reemplazo total del set por panel, por id de vehiculo. Lista vacia = sin vehiculos.
VEH_SET = {
 '05': [],
 '06': ['excavator','rover-6x6','bulldozer','turf-hauler','rescue-heli'],  # = los del P04
 '07': ['rover-6x6','bulldozer','turf-hauler','rescue-heli'],              # saca excavator
 '12': ['excavator','turf-hauler','rover-6x6'],                            # saca bulldozer + heli
 '15': [],                                                                 # saca heli
 '16': [],                                                                 # saca heli
 '18': ['rover-6x6','excavator','bulldozer','turf-hauler'],
 '20': ['turf-hauler','rover-6x6'],
 '22': [],                                                                 # saca excavator
 '24': ['excavator','rover-6x6','turf-hauler'],                           # saca bulldozer
 '26': [],                                                                 # saca heli
 '27': [],                                                                 # saca excavator
 '28': [],                                                                 # saca los dos
 '31': [],                                                                 # saca excavator
 '33': ['excavator'],                                                      # saca heli
 '34': ['excavator','rover-6x6','bulldozer'],                             # suma bulldozer
 '35': ['excavator','rover-6x6','bulldozer'],                             # saca turf-hauler
 '42': ['excavator','bulldozer'],
}
for _n, _ids in VEH_SET.items():
    if _n in VEHICLES_IN_PANEL:
        VEHICLES_IN_PANEL[_n] = [{'name': CAT[i]['name'], 'sku': CAT[i]['sku']} for i in _ids if i in CAT]

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

# ---- 6. lineup: vehiculos de construccion del EP105 (segun guion V4) ----
# EP105 no tiene villano (el template EP104 ya no trae la tarjeta de Von Steele).
def vline(name, sku): return f'<div class="char-vehicle">{name} · #{sku}</div>'
LINEUP_VEH = {
 'Sean':      [('Land Rover 6x6','JKH28')],
 'Ted':       [('Turf Hauler','HFB90')],
 'Charmaine': [('Rescue Helicopter','JKH39')],
 'Aimee':     [('Bulldozer','JFB96')],
 'Crosby':    [('Excavator','JKH38')],
}
# quitar TODOS los char-vehicle (EP104) e insertar los del EP105 tras cada char-role
out = re.sub(r'\s*<div class="char-vehicle">[^<]*</div>', '', out)
for cname, vs in LINEUP_VEH.items():
    key = f'<div class="char-name">{cname}</div>'
    ci = out.find(key)
    if ci < 0: continue
    role_close = out.index('</div>', out.index('<div class="char-role"', ci)) + len('</div>')
    newv = ''.join('\n          ' + vline(n,s) for n,s in vs)
    out = out[:role_close] + newv + out[role_close:]

# vestuario EP105 (construccion): pins CUADRADOS 1080x1080 desde los PNG individuales.
try:
    from PIL import Image
    import os
    os.makedirs('wardrobe/105', exist_ok=True)
    _srcs = {
        'SEAN':      'wardrobe/sean_construction_wardrobe.png',
        'TED':       'wardrobe/ted_construction_wardrobe.png',
        'CHARMAINE': 'wardrobe/charmine_construction_wardrobe.png',
        'AIMEE':     'wardrobe/aimee_construction_wardrobe.png',
        'CROSBY':    'wardrobe/crosby_construction_wardrobe.png',
    }
    for _nm, _p in _srcs.items():
        if not os.path.exists(_p): print('[warn] falta', _p); continue
        _src = Image.open(_p).convert('RGB')
        _bg = _src.getpixel((8, 8))                    # gris de fondo de la hoja
        _W, _H = _src.size
        _side = max(_W, _H)
        _cv = Image.new('RGB', (_side, _side), _bg)
        _cv.paste(_src, ((_side-_W)//2, (_side-_H)//2))
        _cv.resize((1080,1080), Image.LANCZOS).save('wardrobe/105/%s_EP105.png' % _nm)
except ImportError:
    print('[warn] PIL no disponible: no se regeneraron los pins de wardrobe/105')

WARDROBE = {
    '104/SEAN_EP104.png':      '105/SEAN_EP105.png',
    '104/TED_EP104.png':       '105/TED_EP105.png',
    '104/CHARMAINE_EP104.png': '105/CHARMAINE_EP105.png',
    '104/AIMEE_EP104.png':     '105/AIMEE_EP105.png',
    '104/CROSBY_EP104.png':    '105/CROSBY_EP105.png',
}
for _old, _new in WARDROBE.items():
    out = out.replace('./wardrobe/' + _old, './wardrobe/' + _new)

# ---- 7. textos de episodio ----
reps = [
    ('CVY26_001_104','CVY26_001_105'),
    ('Episode 104 — Dog Race!','Episode 105 — Booby Trap Building!'),
    ('104 — Dog Race!','105 — Booby Trap Building!'),
    ('Episode 104 · Cast · Dog Race','Episode 105 · Cast · Booby Trap Building'),
    ('CHARACTER LINEUP PAGE — EP104 (Dog Race)','CHARACTER LINEUP PAGE — EP105 (Booby Trap Building)'),
    ('Episode 104','Episode 105'),
    ('Color Review · Dog Race!','Color Review · Booby Trap Building!'),
    ('Dog Race! · 44 Panels','Booby Trap Building! · %d Panels' % len(nums)),
    ('Dog Race!','Booby Trap Building!'),
    ('>44<', '>%d<' % len(nums)),
    ('44 Panels','%d Panels' % len(nums)),
]
for a_,b_ in reps:
    out = out.replace(a_, b_)

open('ep105_color_review.html','w',encoding='utf-8').write(out)

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
