import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from rembg import remove


INPUT_DIR = Path("input")
OUT_DIR = Path("output")

# Fondo/recorte
ALPHA_THRESHOLD = 10    # umbral bajo para eliminar halos débiles antes de erosión
ALPHA_CUTOFF = 128      # umbral de binarización: >CUTOFF → 255 (opaco), ≤CUTOFF → 0 (transparente)
ERODE_PX = 1            # 1 suele ir bien para quitar reborde

# Rotación: botella "de pie" => boca a la derecha con clockwise
ROTATE_CLOCKWISE = True

# WEBP (optimización)
WEBP_METHOD = 6
START_QUALITY = 88
MIN_QUALITY = 60
STEP = 4

# Si quieres forzar que NO pese más que el original (útil para web):
CAP_TO_INPUT_SIZE = True


def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def list_images(folder: Path):
    exts = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def needs_rotation(img: Image.Image) -> bool:
    """Detecta si la imagen necesita rotación (es portrait / vertical)."""
    w, h = img.size
    return h > w


def rotate_90(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_270 if ROTATE_CLOCKWISE else Image.Transpose.ROTATE_90)


def clean_alpha(img_rgba: Image.Image) -> Image.Image:
    """Quita sombras/halos del matting: erosión + binarización del canal alfa."""
    if img_rgba.mode != "RGBA":
        img_rgba = img_rgba.convert("RGBA")

    arr = np.array(img_rgba).astype(np.uint8)
    alpha = arr[:, :, 3].astype(np.uint8)

    # Reason: Primero eliminamos halos muy débiles antes de erosionar
    alpha = np.where(alpha < ALPHA_THRESHOLD, 0, alpha).astype(np.uint8)

    # erosión 3x3 simple (sin OpenCV)
    if ERODE_PX > 0:
        a = alpha
        for _ in range(ERODE_PX):
            padded = np.pad(a, ((1, 1), (1, 1)), mode="edge")
            neigh = [
                padded[0:-2, 0:-2], padded[0:-2, 1:-1], padded[0:-2, 2:],
                padded[1:-1, 0:-2], padded[1:-1, 1:-1], padded[1:-1, 2:],
                padded[2:, 0:-2],   padded[2:, 1:-1],   padded[2:, 2:],
            ]
            a = np.minimum.reduce(neigh).astype(np.uint8)
        alpha = a

    # Reason: Binarizar alfa elimina semi-transparencias que causan fondo sucio
    # en WebP lossy (la compresión degrada el canal alfa de 255 a ~250)
    alpha = np.where(alpha > ALPHA_CUTOFF, 255, 0).astype(np.uint8)

    arr[:, :, 3] = alpha
    return Image.fromarray(arr, mode="RGBA")


def crop_to_alpha(img_rgba: Image.Image) -> Image.Image:
    alpha = img_rgba.split()[-1]
    bbox = alpha.getbbox()
    return img_rgba.crop(bbox) if bbox else img_rgba


def save_webp_optimized(img_rgba: Image.Image, out_path: Path, max_bytes: int | None):
    """
    Guarda WEBP optimizando:
    - method=6 para mejor compresión
    - prueba calidades hasta cumplir max_bytes (si se pide)
    """
    tmp = out_path.with_suffix(".tmp.webp")

    def attempt(q: int) -> int:
        img_rgba.save(
            tmp,
            format="WEBP",
            quality=q,
            method=WEBP_METHOD,
        )
        return tmp.stat().st_size

    if max_bytes is None:
        img_rgba.save(out_path, format="WEBP", quality=START_QUALITY, method=WEBP_METHOD)
        return

    q = START_QUALITY
    size = attempt(q)
    while size > max_bytes and q > MIN_QUALITY:
        q -= STEP
        size = attempt(q)

    tmp.replace(out_path)


def process_image(in_path: Path):
    in_bytes = in_path.stat().st_size
    base_name = in_path.stem + ".webp"
    out_path = OUT_DIR / base_name

    # Si ya existe en output, lo damos por procesado
    if out_path.exists():
        print(f"SKIP (ya existe): {in_path.name}")
        return

    # 1) Cargar y corregir EXIF
    img = Image.open(in_path)
    img = ImageOps.exif_transpose(img)

    # 2) Eliminar fondo
    nobg = remove(img)
    if isinstance(nobg, (bytes, bytearray)):
        nobg = Image.open(io.BytesIO(nobg))
    img_rgba = nobg.convert("RGBA")

    # 3) Limpieza de bordes (sombras/halo)
    img_rgba = clean_alpha(img_rgba)

    # 4) Recorte al contorno (revela la forma real de la botella)
    cropped = crop_to_alpha(img_rgba)

    # 5) Rotación (solo si la botella recortada es portrait/vertical)
    if needs_rotation(cropped):
        cropped = rotate_90(cropped)
    else:
        print(f"  (sin rotar, ya es landscape): {in_path.name}")

    # 6) Guardado WebP optimizado
    max_bytes = in_bytes if CAP_TO_INPUT_SIZE else None
    save_webp_optimized(cropped, out_path, max_bytes)
    print(f"OK: {in_path.name} -> {out_path.name}")


def main():
    ensure_dirs()
    for p in list_images(INPUT_DIR):
        try:
            process_image(p)
        except Exception as e:
            print(f"ERROR en {p.name}: {e}")


if __name__ == "__main__":
    main()
