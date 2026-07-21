# Cómo armar un Color Review de CONVOY (para Claude Code)

Este doc explica cómo generar el documento de **Color Review** de un episodio.
Está pensado para que **cualquier** Claude Code parado en este repo lo pueda hacer,
sin depender de memorias locales de una cuenta puntual.

> Si sos una persona: no necesitás correr nada a mano. Abrí Claude Code en este
> repo y pedí, por ejemplo: **"armá el color review del EP104"**. Claude lee este
> doc y hace el resto. Solo hace falta: Python 3 + internet + este repo clonado.

---

## Qué es el Color Review

Un **HTML autocontenido** por episodio (`epNNN_color_review.html`) que se le manda
al cliente (Mattel) para revisar color. Se genera con un builder de Python por
episodio: `build_epNNN_color_review.py`, que **clona la estructura/estética** del
HTML del episodio anterior (template) y le inyecta los datos del episodio nuevo.

Ejemplos ya hechos: `build_ep102_color_review.py`, `build_ep103_color_review.py`
y sus salidas `ep10X_color_review.html`.

---

## Fuentes de datos (de dónde sale cada cosa)

1. **Color final → de la REFINERÍA, por API pública HTTP** (no del MCP, no de PDFs):
   `https://refineria.onrender.com/api/projects/convoy/episodes/epNNN/finals`
   El builder mapea `board.filename` → busca `_P<NN>` → número de panel → `final.imageUrl`.
   ⚠️ La refinería a veces tiene finales **mal asignados o corridos**; hay que corregir
   el mapeo panel→imagen a mano (ver "Correcciones por episodio").

2. **Autos (nombre + SKU) y diálogos (VO) → de `convoy_breakdown.html`**
   (el `trackerData`, entradas con `id:'epNNN-pXX'`). El catálogo de vehículos son
   las entradas `badge:'vehicle'`. Los playsets (ej. Mountain Convoy) son
   `badge:'playset'` y hay que resolverlos aparte / a mano.

3. **Retratos de personajes**: `MATCHBOX-<NOMBRE>-turn1.jpg`. Sirven para todos los
   episodios; entre episodios solo cambian los vehículos del lineup y el wardrobe.

Si el usuario pasa un **PDF "para el orden"**, es SOLO referencia del orden de los
paneles (1..N). NO tomar de ahí color, ni rough layout, ni comentarios.

---

## Gotcha clave: indexar por `label`, NO por `id`

En el breakdown el `id` (`epNNN-pXX`) puede estar **desfasado** del número real de
panel. El número REAL es el campo `label`. Ej. EP103: `id06` → `label '04A–E'`
(hero reveal) = panel **04**. Parsear los dígitos iniciales del `label` para la clave
del panel. (El EP102 no tenía desfasaje; el EP103 sí — ver su builder.)

---

## Receta para un episodio nuevo (EP10N)

1. **Copiá el builder más reciente**: `cp build_ep103_color_review.py build_ep10N_color_review.py`.
2. **Cambiá el episodio en todos lados**: el `ep103-p` del regex, la URL `/episodes/ep10N/finals`,
   el template a clonar (`TPL = open('ep10(N-1)_color_review.html')`), y el nombre de salida.
3. **Actualizá el bloque de textos** (`reps = [...]`): título del episodio, "Episode 10N",
   nombre del capítulo, cantidad de paneles, etc.
4. **Limpiá las notas del episodio previo**: los consts `ADDRESSED`, `ACTIONS`,
   `MATTEL_FEEDBACK` → `{}` (no se renderizan pero arrastran data del episodio anterior).
5. **Actualizá el lineup**: vehículo por personaje del EP10N (`LINEUP_VEH`) y el wardrobe
   (`WARDROBE`) — reemplazá los pins del episodio previo por los de este.
   ⚠️ Para saber qué vehículo maneja cada personaje, consultá el **GUION** del episodio,
   NO los tags del repo (los `vehicles:[...]` del breakdown suelen estar mal etiquetados).
6. **Corré** `python3 build_ep10N_color_review.py` y **leé el resumen** que imprime:
   paneles con color, "sin diálogo", "sin autos", y la lista de autos por panel.
7. **Aplicá las correcciones por episodio** (abajo) hasta que la lista quede bien.
8. **Abrí el HTML** y revisá visualmente antes de publicar.

---

## Correcciones por episodio (la parte que necesita criterio)

Cada episodio necesita ajustes manuales; por eso NO alcanza con "correr el .py".
Los ejemplos están en `build_ep103_color_review.py`. Bloques típicos:

- **Corrimiento de color**: si la refinería tiene los finales corridos, remapear
  `COLOR[dst] = COLOR[src]` (ej. EP103 corrió 27→28…30→31 y liberó el 31).
- **Colores manuales**: paneles cuyo final todavía no está en `/finals` o que la
  usuaria reemplazó por una imagen propia (subida a R2). Se setean directo: `COLOR['20'] = '<url>'`.
- **Altas/bajas de vehículos por panel**: `VEH_ADD` (sumar), `VEH_REMOVE` (por SKU),
  `VEH_SET`/`VEHICLES_IN_PANEL[n]=[]` (reemplazar/vaciar). Todo por pedido de la usuaria.
- **Relleno de diálogos faltantes**: `DIALOGUE_FILL` con el VO tomado del **guion**
  del episodio, solo para los paneles que vienen vacíos del breakdown.
- **Nombres de vehículos**: usar el nombre **canónico** (ej. "Excavator"), nunca el
  apodo. Los apodos van en notas del panel, no en el nombre del auto.

---

## Publicar

La salida es `epNNN_color_review.html` (autocontenido). Cuando está aprobada, se suele
guardar una copia `epNNN_color_review_PUBLISHED.html` como la versión enviada al cliente.
Commit + push del builder y del HTML.

---

## Checklist rápido

- [ ] Color desde `/finals` de la refinería (corregir corrimientos/mal asignados)
- [ ] Autos + diálogos desde `convoy_breakdown.html`, indexando por `label`
- [ ] Vehículo por personaje según el GUION (no los tags del repo)
- [ ] Notas del episodio previo limpiadas (`ADDRESSED`/`ACTIONS`/`MATTEL_FEEDBACK` = `{}`)
- [ ] Lineup + wardrobe actualizados al episodio
- [ ] Resumen del script revisado (sin diálogo / sin autos) y correcciones aplicadas
- [ ] HTML abierto y revisado a ojo antes de publicar
