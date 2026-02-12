# Tratamiento de Imágenes de Botellas

Herramienta de procesamiento por lotes de imágenes de botellas para uso web. Elimina fondos, rota las imágenes y las exporta en formato WebP optimizado.

## Descripción

Este proyecto automatiza el tratamiento de fotografías de botellas con las siguientes operaciones:

1. **Eliminación de fondo** — Convierte el fondo en transparente usando IA (modelo U²-Net vía `rembg`), dejando únicamente la botella.
2. **Limpieza de bordes** — Elimina sombras, halos y semitransparencias residuales del proceso de matting.
3. **Rotación 90°** — Gira la imagen en sentido horario para que la embocadura quede a la derecha.
4. **Exportación WebP** — Guarda en formato `.webp` con compresión optimizada, garantizando que el archivo resultante no pese más que el original.
5. **Detección de duplicados** — Comprueba por nombre si la imagen ya fue procesada, evitando reprocesar.

## Estructura del Proyecto

```
Tratamiento_imagenes_botellas/
├── input/                  # Carpeta con las imágenes originales a procesar
├── output/                 # Resultado: imágenes procesadas (.webp)
├── tests/                  # Tests unitarios (pytest)
│   ├── __init__.py
│   └── test_process_bottles.py
├── process_bottles.py      # Script principal de procesamiento
├── requirements.txt        # Dependencias Python (versiones fijadas)
├── .gitignore              # Exclusiones de Git
└── README.md               # Este archivo
```

### Carpetas de entrada/salida

| Carpeta    | Descripción                                                                          |
|------------|--------------------------------------------------------------------------------------|
| `input/`   | Imágenes originales de botellas (JPG, PNG, WebP, TIFF)                               |
| `output/`  | Botellas sin fondo, rotadas 90° y recortadas al contorno, en formato WebP transparente |

> Las imágenes procesadas conservan el nombre original pero con extensión `.webp`.

## Requisitos

- **Python 3.10+**
- Dependencias listadas en `requirements.txt`

### Dependencias principales

| Paquete  | Uso                                                        |
|----------|------------------------------------------------------------|
| `rembg`  | Eliminación de fondo mediante modelo U²-Net                |
| `Pillow` | Manipulación de imágenes (rotación, recorte, exportación)  |
| `NumPy`  | Procesamiento de canal alfa (limpieza de halos/sombras)    |

## Instalación

```bash
# 1. Clonar o descargar el proyecto
cd Tratamiento_imagenes_botellas

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

> **Nota:** La primera ejecución descargará automáticamente el modelo U²-Net (~176 MB).

## Uso

1. Colocar las imágenes de botellas en la carpeta `input/`.
2. Ejecutar el script:

```bash
python process_bottles.py
```

3. Las imágenes procesadas aparecerán en `output/`.

### Ejemplo de salida en consola

```
OK: lias_1023x.webp -> lias_1023x.webp
SKIP (ya existe): lias_1023x.webp
```

## Parámetros de Configuración

Los parámetros se definen como constantes al inicio de `process_bottles.py`:

| Parámetro           | Valor por defecto | Descripción                                                      |
|---------------------|-------------------|------------------------------------------------------------------|
| `ALPHA_THRESHOLD`   | `10`              | Umbral para eliminar semitransparencias débiles (halo/sombra)    |
| `ERODE_PX`          | `1`               | Píxeles de erosión del borde alfa (elimina reborde residual)     |
| `ROTATE_CLOCKWISE`  | `True`            | Dirección de rotación (`True` = horario, embocadura a la derecha)|
| `WEBP_METHOD`       | `6`               | Método de compresión WebP (6 = máxima compresión, más lento)     |
| `START_QUALITY`     | `88`              | Calidad WebP inicial                                             |
| `MIN_QUALITY`       | `60`              | Calidad mínima aceptable al optimizar tamaño                    |
| `STEP`              | `4`               | Decremento de calidad en cada iteración de optimización          |
| `CAP_TO_INPUT_SIZE` | `True`            | Si `True`, el archivo de salida no superará el tamaño del original|

## Pipeline de Procesamiento

```
Imagen original (input/)
    │
    ▼
[1] Corrección EXIF (orientación automática)
    │
    ▼
[2] Eliminación de fondo (rembg / U²-Net) → RGBA
    │
    ▼
[3] Limpieza de canal alfa
    ├── Umbralización (elimina semitransparencias < ALPHA_THRESHOLD)
    └── Erosión 3×3 (elimina reborde de 1px)
    │
    ▼
[4] Rotación 90° en sentido horario
    │
    ▼
[5] Recorte al contorno + guardado ──→ output/ (.webp)
    │
    ▼
Optimización WebP: reduce calidad iterativamente hasta que
el archivo no supere el tamaño del original
```

## Formatos de Imagen Soportados

**Entrada:** `.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, `.tiff`

**Salida:** `.webp` (con transparencia alfa)

## Notas Técnicas

- **Sin dependencia de OpenCV**: La erosión del canal alfa se implementa con NumPy puro usando un kernel 3×3 de mínimos, evitando la pesada dependencia de `cv2`.
- **Optimización de tamaño**: El algoritmo reduce la calidad WebP iterativamente (de `START_QUALITY` a `MIN_QUALITY` en pasos de `STEP`) hasta que el archivo resultante no supere el tamaño del original.
- **Corrección EXIF**: Se aplica `ImageOps.exif_transpose()` antes de procesar para respetar la orientación real de la foto independientemente de los metadatos EXIF.
- **Detección de duplicados**: Si ya existe un archivo con el mismo nombre en la carpeta `output/`, se omite el procesamiento.

## Tests

El proyecto incluye 17 tests unitarios con pytest:

```bash
# Instalar pytest (si no está instalado)
pip install pytest

# Ejecutar tests
python -m pytest tests/ -v
```

Los tests cubren: `rotate_90`, `clean_alpha`, `crop_to_alpha`, `save_webp_optimized`, `list_images` y `process_image` (skip de duplicados).

## Licencia

Uso interno.
