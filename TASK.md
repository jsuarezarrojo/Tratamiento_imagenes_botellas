# TASK — Registro de Tareas

## Tareas Completadas

- [x] **Eliminación de fondo** — Implementado con `rembg` (U²-Net). Convierte fondo a transparente. *(2026-02-12)*
- [x] **Rotación 90° horaria** — Embocadura queda a la derecha. *(2026-02-12)*
- [x] **Exportación WebP optimizada** — Calidad adaptativa para no superar el tamaño original. *(2026-02-12)*
- [x] **Limpieza de sombras/halos** — Umbralización alfa + erosión 3×3 sin OpenCV. *(2026-02-12)*
- [x] **Detección de duplicados** — Skip si ya existe el archivo en las carpetas de salida. *(2026-02-12)*
- [x] **Corrección EXIF** — Orientación automática antes de procesar. *(2026-02-12)*
- [x] **Documentación del proyecto** — README.md, PLANNING.md, TASK.md. *(2026-02-12)*
- [x] **Unificación carpeta output** — Una sola carpeta `output/` con imagen recortada (alineado con spec original). *(2026-02-12)*
- [x] **Fijar versiones en requirements.txt** — rembg==2.0.72, pillow==12.1.1, numpy==2.3.5. *(2026-02-12)*
- [x] **Crear .gitignore** — Excluye .venv/, input/, output/, __pycache__/, .u2net/. *(2026-02-12)*
- [x] **Tests unitarios** — 17 tests en `tests/test_process_bottles.py` con pytest. *(2026-02-12)*
- [x] **Binarización del canal alfa** — Elimina semi-transparencias que causaban fondo sucio en WebP lossy (`ALPHA_CUTOFF=128`). *(2026-02-13)*
- [x] **Detección automática de orientación** — Solo rota imágenes portrait; landscape se deja como está. Detección post-crop para manejar imágenes cuadradas. *(2026-02-13)*
- [x] **Soporte JPG y PNG** — Verificado que `ukan-2019.jpg` y `la-vina-mateu-tinto-g.png` se procesan correctamente. *(2026-02-13)*
- [x] **Ampliación tests** — 22 tests: añadidos `needs_rotation` (3 tests) y binarización alfa (2 tests). *(2026-02-13)*

## Tareas Pendientes

_(Sin tareas pendientes actualmente)_

## Discovered During Work

- *(Resuelto)* La discrepancia de carpetas `output_canvas/` y `output_crop/` vs `output/` se resolvió unificando a una sola carpeta `output/`.
- Existe una carpeta `output/` con un archivo previo (`carabibas_vendimia_seleccionada.webp`) que fue generado por una versión anterior del script.
- El fondo "sucio" en las imágenes procesadas era causado por semi-transparencias en el canal alfa (rembg deja valores 200-254 en vez de 255). Resuelto con binarización.
- Imágenes cuadradas (ej. `ukan-2019.jpg` 600×600) requerían detectar orientación después del crop, no antes.
