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

## Tareas Pendientes

_(Sin tareas pendientes actualmente)_

## Discovered During Work

- *(Resuelto)* La discrepancia de carpetas `output_canvas/` y `output_crop/` vs `output/` se resolvió unificando a una sola carpeta `output/`.
- Existe una carpeta `output/` con un archivo previo (`carabibas_vendimia_seleccionada.webp`) que fue generado por una versión anterior del script.
