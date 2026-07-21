# CONVOY — notas para Claude Code

Proyecto de animación Mattel/Matchbox (serie CONVOY, CVY26_001). La app principal
es `convoy_breakdown.html` (single-file). Los documentos que se le mandan al cliente
se generan con builders de Python (`build_*.py`).

## Color Review

Cuando alguien pida **"armá / hacé el color review del EP10N"**, seguí la guía:
👉 **[COLOR_REVIEW_HOWTO.md](./COLOR_REVIEW_HOWTO.md)**

Resumen: clonar el builder del episodio anterior (`build_epNNN_color_review.py`),
color desde la API pública de la refinería, autos+diálogos desde `convoy_breakdown.html`,
y aplicar las correcciones manuales por episodio. Necesita solo Python 3 + internet + el repo.
