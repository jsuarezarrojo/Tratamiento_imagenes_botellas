# PLANNING — Tratamiento de Imágenes de Botellas

## Objetivo

Automatizar el procesamiento de fotografías de botellas para uso web: eliminar fondo, rotar y exportar en WebP optimizado.

## Arquitectura

- **Backend puro en Python** — Sin frontend, sin API. Script de línea de comandos.
- **Procesamiento por lotes** — Itera sobre todas las imágenes en `input/` y genera resultados en la carpeta `output/`.
- **Modelo de IA para segmentación** — `rembg` (U²-Net) para eliminación de fondo.

## Stack Tecnológico

| Componente       | Tecnología         |
|------------------|--------------------|
| Lenguaje         | Python 3.10+       |
| Segmentación     | rembg (U²-Net)     |
| Imágenes         | Pillow             |
| Procesamiento    | NumPy              |

## Estructura de Archivos

```
input/              → Imágenes originales
output/             → Resultado procesado (.webp recortado al contorno)
tests/              → Tests unitarios (pytest)
process_bottles.py  → Script principal (único módulo)
requirements.txt    → Dependencias (versiones fijadas)
.gitignore          → Exclusiones de Git
```

## Decisiones de Diseño

### 1. Una sola carpeta de salida
Se genera una única variante por imagen: recortada al bounding box del canal alfa (mínimo tamaño, ideal para web). Esto alinea la implementación con la especificación original que indicaba una sola carpeta `output/`.

### 1b. Binarización del canal alfa
Después de la erosión, el canal alfa se binariza (>128 → 255, ≤128 → 0). Esto elimina las semi-transparencias que causan "fondo sucio" al comprimir en WebP lossy, ya que la compresión degrada el alfa de 255 a ~250.

### 1c. Detección automática de orientación
La rotación se decide **después del recorte** (crop), no antes. Esto permite detectar correctamente la forma real de la botella incluso en imágenes cuadradas. Solo se rotan las imágenes portrait (h > w); las landscape se dejan como están.

### 2. Erosión sin OpenCV
Se implementó erosión 3×3 con NumPy puro (`np.minimum.reduce`) para evitar la dependencia pesada de OpenCV. Suficiente para eliminar el reborde de 1px que deja el matting.

### 3. Optimización de tamaño WebP
Algoritmo iterativo que reduce la calidad desde 88 hasta 60 (en pasos de 4) hasta que el archivo no supere el tamaño del original. Esto garantiza que la conversión nunca aumente el peso del fichero.

### 4. Detección de duplicados por nombre
Antes de procesar, se comprueba si ya existe un archivo con el mismo nombre (stem + `.webp`) en la carpeta de salida. Esto permite re-ejecutar el script de forma segura sin reprocesar.

### 5. Corrección EXIF
Se aplica `exif_transpose()` al inicio para que la orientación sea correcta independientemente de los metadatos de la cámara.

## Convenciones

- **Naming**: snake_case para funciones y variables, UPPER_CASE para constantes de configuración.
- **Estilo**: Script monolítico (un solo archivo) dado el alcance reducido del proyecto.
- **Idioma del código**: Comentarios y mensajes en español.

## Testing

- Framework: **pytest**
- 22 tests unitarios cubriendo todas las funciones puras.
- `rembg` se mockea en tests para evitar dependencia de `onnxruntime` en CI.

## Limitaciones Conocidas

- El modelo U²-Net puede no funcionar bien con botellas muy transparentes o de cristal claro.
- La erosión de 1px puede recortar detalles finos en etiquetas con bordes delgados.
- No hay paralelismo; las imágenes se procesan secuencialmente.
- La primera ejecución descarga el modelo (~176 MB).
