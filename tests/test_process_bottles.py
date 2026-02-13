"""Tests for process_bottles.py — covers core image processing functions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

# Reason: Ensure the project root is in sys.path so we can import the module directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Reason: rembg may call sys.exit(1) on import if onnxruntime is missing.
# We mock the entire rembg package so pure-function tests can run without it.
if "rembg" not in sys.modules:
    sys.modules["rembg"] = MagicMock()

import process_bottles as pb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_rgba(width: int, height: int, alpha: int = 255) -> Image.Image:
    """Create a solid-colour RGBA image with a given uniform alpha."""
    arr = np.full((height, width, 4), [128, 64, 32, alpha], dtype=np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def make_rgba_with_halo(width: int, height: int) -> Image.Image:
    """Create an RGBA image where the outer 2px border has low alpha (halo)."""
    arr = np.full((height, width, 4), [128, 64, 32, 255], dtype=np.uint8)
    # Reason: Simulate a halo by setting border pixels to low alpha
    arr[:2, :, 3] = 5
    arr[-2:, :, 3] = 5
    arr[:, :2, 3] = 5
    arr[:, -2:, 3] = 5
    return Image.fromarray(arr, mode="RGBA")


# ---------------------------------------------------------------------------
# needs_rotation
# ---------------------------------------------------------------------------

class TestNeedsRotation:
    def test_portrait_needs_rotation(self):
        """A portrait image (height > width) should need rotation."""
        img = make_rgba(100, 200)
        assert pb.needs_rotation(img) is True

    def test_landscape_no_rotation(self):
        """A landscape image (width > height) should NOT need rotation."""
        img = make_rgba(200, 100)
        assert pb.needs_rotation(img) is False

    def test_square_no_rotation(self):
        """A square image (width == height) should NOT need rotation."""
        img = make_rgba(100, 100)
        assert pb.needs_rotation(img) is False


# ---------------------------------------------------------------------------
# rotate_90
# ---------------------------------------------------------------------------

class TestRotate90:
    def test_clockwise_dimensions(self):
        """A 100x200 image rotated 90° clockwise becomes 200x100."""
        img = make_rgba(100, 200)
        rotated = pb.rotate_90(img)
        assert rotated.size == (200, 100)

    def test_counterclockwise(self, monkeypatch):
        """When ROTATE_CLOCKWISE is False, rotation goes counter-clockwise."""
        monkeypatch.setattr(pb, "ROTATE_CLOCKWISE", False)
        img = make_rgba(100, 200)
        rotated = pb.rotate_90(img)
        assert rotated.size == (200, 100)

    def test_preserves_mode(self):
        """Output should remain RGBA."""
        img = make_rgba(50, 50)
        rotated = pb.rotate_90(img)
        assert rotated.mode == "RGBA"


# ---------------------------------------------------------------------------
# clean_alpha
# ---------------------------------------------------------------------------

class TestCleanAlpha:
    def test_removes_low_alpha(self):
        """Pixels with alpha below ALPHA_THRESHOLD should become fully transparent."""
        arr = np.full((10, 10, 4), [100, 100, 100, 5], dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        cleaned = pb.clean_alpha(img)
        result_alpha = np.array(cleaned)[:, :, 3]
        assert np.all(result_alpha == 0)

    def test_keeps_opaque_pixels(self):
        """Fully opaque interior pixels should remain opaque (minus erosion border)."""
        img = make_rgba(20, 20, alpha=255)
        cleaned = pb.clean_alpha(img)
        result_alpha = np.array(cleaned)[:, :, 3]
        # Reason: Interior pixels (away from border) should stay 255
        assert result_alpha[10, 10] == 255

    def test_binarizes_alpha(self):
        """Semi-transparent pixels should be binarized: >CUTOFF→255, ≤CUTOFF→0."""
        # Reason: Create image with alpha=200 (above default CUTOFF=128)
        arr = np.full((10, 10, 4), [100, 100, 100, 200], dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        cleaned = pb.clean_alpha(img)
        result_alpha = np.array(cleaned)[:, :, 3]
        # Reason: All pixels had alpha=200 > 128, so after binarization they should be 255
        assert np.all((result_alpha == 0) | (result_alpha == 255))

    def test_binarizes_below_cutoff_to_zero(self):
        """Pixels with alpha at or below CUTOFF should become 0 after binarization."""
        # Reason: alpha=100 is below default CUTOFF=128 but above THRESHOLD=10
        arr = np.full((10, 10, 4), [100, 100, 100, 100], dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        cleaned = pb.clean_alpha(img)
        result_alpha = np.array(cleaned)[:, :, 3]
        assert np.all(result_alpha == 0)

    def test_converts_non_rgba(self):
        """If input is RGB, it should be converted to RGBA before processing."""
        img = Image.new("RGB", (10, 10), (128, 64, 32))
        cleaned = pb.clean_alpha(img)
        assert cleaned.mode == "RGBA"

    def test_halo_removal(self):
        """Border pixels with low alpha (halo) should be zeroed out."""
        img = make_rgba_with_halo(20, 20)
        cleaned = pb.clean_alpha(img)
        result_alpha = np.array(cleaned)[:, :, 3]
        # Reason: The 2px border had alpha=5 (< threshold=10), should be 0
        assert result_alpha[0, 0] == 0
        assert result_alpha[0, 5] == 0


# ---------------------------------------------------------------------------
# crop_to_alpha
# ---------------------------------------------------------------------------

class TestCropToAlpha:
    def test_crops_transparent_border(self):
        """Should crop away fully transparent border, leaving only opaque region."""
        arr = np.zeros((100, 100, 4), dtype=np.uint8)
        # Reason: Place a 20x20 opaque block at (30,40)
        arr[30:50, 40:60, :] = [255, 0, 0, 255]
        img = Image.fromarray(arr, mode="RGBA")
        cropped = pb.crop_to_alpha(img)
        assert cropped.size == (20, 20)

    def test_fully_opaque_unchanged(self):
        """A fully opaque image should not change size."""
        img = make_rgba(50, 80, alpha=255)
        cropped = pb.crop_to_alpha(img)
        assert cropped.size == (50, 80)

    def test_fully_transparent_returns_original(self):
        """A fully transparent image should return the original (no bbox)."""
        img = make_rgba(30, 30, alpha=0)
        cropped = pb.crop_to_alpha(img)
        assert cropped.size == (30, 30)


# ---------------------------------------------------------------------------
# save_webp_optimized
# ---------------------------------------------------------------------------

class TestSaveWebpOptimized:
    def test_saves_webp_file(self, tmp_path):
        """Should create a valid .webp file."""
        img = make_rgba(50, 50)
        out = tmp_path / "test.webp"
        pb.save_webp_optimized(img, out, max_bytes=None)
        assert out.exists()
        assert out.stat().st_size > 0
        # Verify it's a valid image
        reopened = Image.open(out)
        assert reopened.format == "WEBP"

    def test_respects_max_bytes(self, tmp_path):
        """When max_bytes is set, output should not exceed that limit."""
        # Reason: Use a large noisy image to ensure compression is needed
        arr = np.random.randint(0, 255, (200, 200, 4), dtype=np.uint8)
        arr[:, :, 3] = 255
        img = Image.fromarray(arr, mode="RGBA")
        out = tmp_path / "capped.webp"
        max_bytes = 50_000
        pb.save_webp_optimized(img, out, max_bytes=max_bytes)
        assert out.exists()
        # Reason: With MIN_QUALITY=60, it may still exceed for very noisy data,
        # but for 200x200 it should be within limits
        assert out.stat().st_size <= max_bytes

    def test_no_temp_file_left(self, tmp_path):
        """Temporary .tmp.webp file should not remain after saving."""
        img = make_rgba(50, 50)
        out = tmp_path / "clean.webp"
        pb.save_webp_optimized(img, out, max_bytes=10_000_000)
        tmp_file = out.with_suffix(".tmp.webp")
        assert not tmp_file.exists()


# ---------------------------------------------------------------------------
# list_images
# ---------------------------------------------------------------------------

class TestListImages:
    def test_finds_supported_formats(self, tmp_path):
        """Should find files with supported image extensions."""
        for ext in [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"]:
            (tmp_path / f"img{ext}").write_bytes(b"fake")
        (tmp_path / "readme.txt").write_bytes(b"not an image")
        found = list(pb.list_images(tmp_path))
        assert len(found) == 6

    def test_ignores_unsupported(self, tmp_path):
        """Should ignore non-image files."""
        (tmp_path / "data.csv").write_bytes(b"1,2,3")
        (tmp_path / "notes.txt").write_bytes(b"hello")
        found = list(pb.list_images(tmp_path))
        assert len(found) == 0

    def test_empty_folder(self, tmp_path):
        """Should return nothing for an empty folder."""
        found = list(pb.list_images(tmp_path))
        assert len(found) == 0


# ---------------------------------------------------------------------------
# process_image (integration-level, mocking rembg)
# ---------------------------------------------------------------------------

class TestProcessImage:
    def test_skips_existing(self, tmp_path, monkeypatch, capsys):
        """Should skip processing if output file already exists."""
        monkeypatch.setattr(pb, "OUT_DIR", tmp_path / "output")
        (tmp_path / "output").mkdir()

        # Create a fake input file
        input_img = Image.new("RGB", (10, 10), (255, 0, 0))
        in_path = tmp_path / "bottle.png"
        input_img.save(in_path)

        # Create existing output
        (tmp_path / "output" / "bottle.webp").write_bytes(b"existing")

        pb.process_image(in_path)
        captured = capsys.readouterr()
        assert "SKIP" in captured.out
