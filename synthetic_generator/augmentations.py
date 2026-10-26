"""
Document Scan Degradation Pipeline using Augraphy:
Applies realistic scanner degradation to generated PDF certificates:
- Dirty roller lines & paper texture
- Photocopy noise & subtle ink bleed
- Geometric rotation / scanner feed skew
- Low-pass optical blur / contrast variance
"""
import io
import os
import random
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import fitz  # PyMuPDF

try:
    from augraphy import (
        AugraphyPipeline,
        DirtyRollers,
        BadPhotoCopy,
        Geometric,
        BleedThrough,
        LowLightNoise
    )
    HAVE_AUGRAPHY = True
except Exception:
    HAVE_AUGRAPHY = False

def create_augraphy_pipeline():
    """Builds a realistic office scanner degradation pipeline using Augraphy v8."""
    if not HAVE_AUGRAPHY:
        return None
    try:
        ink_phase = [
            BleedThrough(
                intensity_range=(0.05, 0.25),
                color_range=(0, 224),
                p=0.4
            )
        ]
        paper_phase = [
            DirtyRollers(
                line_width_range=(2, 6),
                scanline_type=0,
                p=0.5
            )
        ]
        post_phase = [
            BadPhotoCopy(
                noise_iteration=(1, 2),
                noise_size=(1, 2),
                p=0.4
            ),
            Geometric(
                rotate_range=(-1.5, 1.5),
                p=0.7
            )
        ]
        pipeline = AugraphyPipeline(ink_phase=ink_phase, paper_phase=paper_phase, post_phase=post_phase)
        return pipeline
    except Exception as e:
        print(f"Notice: Augraphy pipeline initialization note ({e}), using fallback.")
        return None

_pipeline = create_augraphy_pipeline()

def apply_pillow_scan_degradation(image: Image.Image) -> Image.Image:
    """Fast, reliable Pillow-based scan degradation fallback."""
    # 1. Subtle rotation skew (-1.2 to +1.2 degrees)
    angle = random.uniform(-1.5, 1.5)
    img = image.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor="white")
    
    # 2. Add subtle blur
    if random.random() < 0.7:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))
        
    # 3. Add grain/noise
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, random.uniform(3, 8), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    degraded = Image.fromarray(arr)
    
    # 4. Scanner contrast variance
    enhancer = ImageEnhance.Contrast(degraded)
    degraded = enhancer.enhance(random.uniform(0.92, 1.08))
    return degraded

def degrade_pdf_document(input_pdf_path: str, output_pdf_path: str) -> bool:
    """
    Renders input PDF page(s) to image, applies Augraphy scan degradation,
    and saves as a degraded scan-like PDF.
    """
    try:
        doc = fitz.open(input_pdf_path)
        degraded_images = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            # Render at 150 DPI for realistic document scan resolution
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Apply Augraphy if available
            augmented_img = None
            if _pipeline is not None:
                try:
                    img_np = np.array(img)
                    augmented_np = _pipeline(img_np)
                    if isinstance(augmented_np, np.ndarray):
                        augmented_img = Image.fromarray(augmented_np)
                except Exception as ex:
                    augmented_img = None

            if augmented_img is None:
                augmented_img = apply_pillow_scan_degradation(img)

            degraded_images.append(augmented_img)

        doc.close()

        if degraded_images:
            # Save degraded images as new PDF
            degraded_images[0].save(
                output_pdf_path,
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=degraded_images[1:] if len(degraded_images) > 1 else []
            )
            return True
    except Exception as e:
        print(f"Failed to degrade PDF {input_pdf_path}: {e}")
        # If degradation fails, copy original
        if input_pdf_path != output_pdf_path and os.path.exists(input_pdf_path):
            import shutil
            shutil.copy2(input_pdf_path, output_pdf_path)
        return False
    return False
