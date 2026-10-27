"""
PRAMAAN-X Infrastructure Photo Variants Generator (Prompt 2.2):
Generates realistic infrastructure photo variants for Photo Reuse Radar & Forensic evaluation:
(a) Original assigned to Institution A (genuine EXIF: timestamp, camera model, GPS coordinates)
(b) Exact duplicate assigned to Institution B (verbatim byte-for-byte duplicate)
(c) Cropped / brightness-shifted / rotated near-duplicate assigned to Institution C (testing perceptual hash pHash)
(d) Version with EXIF metadata stripped (testing provenance inspection)

Uses Pillow and piexif. Logs all variants into ground_truth.csv.
"""
import os
import io
import csv
import math
import argparse
from datetime import datetime, timezone
import imagehash
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import piexif

from synthetic_generator.defects import GroundTruthLogger

def decimal_to_dms_rational(deg_float: float):
    """Converts decimal degrees float to EXIF rational DMS tuple ((d,1), (m,1), (s*100, 100))."""
    abs_deg = abs(deg_float)
    d = int(abs_deg)
    rem_m = (abs_deg - d) * 60
    m = int(rem_m)
    s = (rem_m - m) * 60
    s_hundredths = int(round(s * 100))
    return ((d, 1), (m, 1), (s_hundredths, 100))

def build_genuine_exif(lat: float, lon: float, timestamp_str: str = "2024:08:15 14:32:10") -> bytes:
    """Builds authentic iPhone camera EXIF byte sequence with GPS tags."""
    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    
    lat_dms = decimal_to_dms_rational(lat)
    lon_dms = decimal_to_dms_rational(lon)

    zeroth_ifd = {
        piexif.ImageIFD.Make: "Apple",
        piexif.ImageIFD.Model: "iPhone 14 Pro",
        piexif.ImageIFD.Software: "17.4.1",
        piexif.ImageIFD.DateTime: timestamp_str,
    }

    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: timestamp_str,
        piexif.ExifIFD.DateTimeDigitized: timestamp_str,
        piexif.ExifIFD.LensMake: "Apple",
        piexif.ExifIFD.LensModel: "iPhone 14 Pro back triple camera 6.86mm f/1.78",
        piexif.ExifIFD.FocalLength: (686, 100),
        piexif.ExifIFD.ISOSpeedRatings: 64,
    }

    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: lat_ref,
        piexif.GPSIFD.GPSLatitude: lat_dms,
        piexif.GPSIFD.GPSLongitudeRef: lon_ref,
        piexif.GPSIFD.GPSLongitude: lon_dms,
        piexif.GPSIFD.GPSAltitudeRef: 0,
        piexif.GPSIFD.GPSAltitude: (920, 1),
        piexif.GPSIFD.GPSDateStamp: timestamp_str.split(" ")[0].replace(":", "-"),
    }

    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd, "1st": {}, "thumbnail": None}
    return piexif.dump(exif_dict)

def create_synthetic_campus_photo(category_name: str, width: int = 1200, height: int = 800) -> Image.Image:
    """Creates a high-contrast representative campus photo tailored with distinct infrastructure geometry."""
    if "Computer" in category_name:
        # Computer Center: Rows of dual monitors with desk surfaces
        img = Image.new("RGB", (width, height), color=(18, 25, 45))
        draw = ImageDraw.Draw(img)
        # Carpet floor
        draw.rectangle([0, int(height * 0.65), width, height], fill=(12, 18, 32))
        # Tables
        for row in range(2):
            y_base = int(height * (0.50 + row * 0.22))
            draw.rectangle([60, y_base, width - 60, y_base + 35], fill=(45, 55, 75))
            for col in range(6):
                x = 90 + col * 175
                # Dual monitors
                draw.rectangle([x, y_base - 70, x + 65, y_base - 5], fill=(8, 14, 25), outline=(14, 165, 233), width=2)
                draw.rectangle([x + 72, y_base - 70, x + 137, y_base - 5], fill=(8, 14, 25), outline=(14, 165, 233), width=2)
                draw.rectangle([x + 20, y_base - 5, x + 45, y_base], fill=(70, 80, 100))
                draw.rectangle([x + 92, y_base - 5, x + 117, y_base], fill=(70, 80, 100))
        draw.rectangle([0, 0, width, 70], fill=(10, 16, 28))
        draw.text((40, 24), f"CENTRAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(220, 240, 255))
        return img

    elif "Library" in category_name:
        # Digital Library: Multiple tall vertical bookshelves filled with multicolored books
        img = Image.new("RGB", (width, height), color=(40, 28, 18))
        draw = ImageDraw.Draw(img)
        # Parquet floor
        draw.rectangle([0, int(height * 0.72), width, height], fill=(30, 20, 12))
        # Tall bookshelves
        book_colors = [(220, 60, 50), (40, 120, 200), (40, 160, 90), (220, 170, 40), (160, 80, 200), (230, 230, 230)]
        for bay in range(4):
            x_bay = 80 + bay * 265
            draw.rectangle([x_bay, 100, x_bay + 230, int(height * 0.72)], fill=(65, 45, 30), outline=(20, 15, 10), width=4)
            for shelf in range(5):
                y_shelf = 130 + shelf * 85
                draw.line([(x_bay, y_shelf), (x_bay + 230, y_shelf)], fill=(20, 12, 8), width=5)
                # Books on shelf
                x_book = x_bay + 8
                while x_book < x_bay + 215:
                    bw = 14 + (x_book % 12)
                    bh = 55 + (x_book % 20)
                    bc = book_colors[(x_book // 17) % len(book_colors)]
                    draw.rectangle([x_book, y_shelf - bh, min(x_book + bw, x_bay + 222), y_shelf], fill=bc, outline=(15, 10, 8))
                    x_book += bw + 3
        draw.rectangle([0, 0, width, 70], fill=(25, 18, 12))
        draw.text((40, 24), f"CENTRAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(255, 235, 210))
        return img

    elif "Material" in category_name:
        # Materials Testing Lab: Heavy testing column (UTM), safety hazard stripes, pressure gauges
        img = Image.new("RGB", (width, height), color=(30, 35, 38))
        draw = ImageDraw.Draw(img)
        # Polished concrete floor
        draw.rectangle([0, int(height * 0.60), width, height], fill=(22, 26, 28))
        # Hazard stripe border
        for s in range(0, width, 40):
            draw.polygon([(s, int(height * 0.60)), (s + 20, int(height * 0.60)), (s + 40, int(height * 0.64)), (s + 20, int(height * 0.64))], fill=(245, 158, 11))
        # Universal Testing Machine in center
        cx = width // 2
        draw.rectangle([cx - 260, 120, cx + 260, int(height * 0.60)], fill=(45, 55, 60), outline=(15, 20, 22), width=5)
        # Heavy steel twin columns
        draw.rectangle([cx - 210, 140, cx - 150, int(height * 0.55)], fill=(120, 130, 135), outline=(40, 45, 50), width=3)
        draw.rectangle([cx + 150, 140, cx + 210, int(height * 0.55)], fill=(120, 130, 135), outline=(40, 45, 50), width=3)
        # Crosshead
        draw.rectangle([cx - 150, 260, cx + 150, 330], fill=(16, 185, 129), outline=(10, 100, 70), width=3)
        # Hydraulic circular dial
        draw.ellipse([cx - 60, 150, cx + 60, 270], fill=(240, 245, 250), outline=(20, 25, 30), width=4)
        draw.line([(cx, 210), (cx + 35, 180)], fill=(220, 38, 38), width=3)
        draw.rectangle([0, 0, width, 70], fill=(18, 22, 24))
        draw.text((40, 24), f"CENTRAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(210, 245, 225))
        return img

    elif "Smart" in category_name:
        # Smart Classroom: Tiered amphitheater curved seating rows + huge interactive smartboard
        img = Image.new("RGB", (width, height), color=(35, 25, 40))
        draw = ImageDraw.Draw(img)
        # Tiered wooden benches
        for tier in range(4):
            y_t = int(height * (0.50 + tier * 0.12))
            draw.arc([100 - tier * 40, y_t, width - 100 + tier * 40, y_t + 350], start=190, end=350, fill=(168, 85, 247), width=18)
            draw.arc([100 - tier * 40, y_t + 15, width - 100 + tier * 40, y_t + 365], start=190, end=350, fill=(100, 60, 130), width=10)
        # Huge central interactive smartboard display screen
        draw.rectangle([width // 2 - 280, 110, width // 2 + 280, 340], fill=(15, 10, 22), outline=(192, 132, 252), width=6)
        draw.rectangle([width // 2 - 250, 130, width // 2 + 250, 320], fill=(24, 18, 35))
        # Presentation chart on smartboard
        draw.line([(width // 2 - 220, 290), (width // 2 - 140, 220), (width // 2 - 60, 250), (width // 2 + 40, 170), (width // 2 + 200, 150)], fill=(52, 211, 153), width=4)
        draw.rectangle([0, 0, width, 70], fill=(22, 14, 28))
        draw.text((40, 24), f"CENTRAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(240, 220, 255))
        return img

    else:
        # Entrance Ramp: Diagonal barrier-free access ramp with stainless handrails and wheelchair icon
        img = Image.new("RGB", (width, height), color=(30, 35, 42))
        draw = ImageDraw.Draw(img)
        # Sky/facade upper half
        draw.rectangle([0, 70, width, 280], fill=(45, 55, 65))
        # Zig-zag ramp concrete surface
        draw.polygon([(0, height), (0, 480), (width * 0.65, 360), (width, 360), (width, height)], fill=(148, 163, 184))
        # Stainless steel handrail bars
        draw.line([(0, 410), (width * 0.65, 290)], fill=(226, 232, 240), width=6)
        draw.line([(0, 440), (width * 0.65, 320)], fill=(203, 213, 225), width=4)
        for post_x in range(40, int(width * 0.65), 75):
            post_y = int(480 - (post_x / (width * 0.65)) * 120)
            draw.line([(post_x, post_y), (post_x, post_y - 70)], fill=(226, 232, 240), width=4)
        # Yellow tactile warning pavers
        for px in range(0, 180, 25):
            draw.rectangle([px, height - 60, px + 18, height - 10], fill=(234, 179, 8))
        # Wheelchair disability symbol
        cx, cy = int(width * 0.80), int(height * 0.55)
        draw.ellipse([cx - 15, cy - 45, cx + 15, cy - 15], outline=(59, 130, 246), width=4)
        draw.arc([cx - 30, cy - 10, cx + 30, cy + 50], start=40, end=240, fill=(59, 130, 246), width=5)
        draw.rectangle([0, 0, width, 70], fill=(18, 22, 28))
        draw.text((40, 24), f"CENTRAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(230, 235, 245))
        return img

def main():
    parser = argparse.ArgumentParser(description="PRAMAAN-X Infrastructure Photo Variants Generator (Prompt 2.2)")
    parser.add_argument("--input-photos-dir", type=str, default=None, help="Optional input directory with real classroom/lab/library photos")
    parser.add_argument("--output-dir", type=str, default="generated_data/photos", help="Output directory for generated photo variants")
    parser.add_argument("--ground-truth", type=str, default="generated_data/ground_truth.csv", help="Ground truth CSV path")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    gt_logger = GroundTruthLogger(args.ground_truth)

    print("=" * 70)
    print("PRAMAAN-X Infrastructure Photo Variants Generator (Prompt 2.2)")
    print(f"Output Directory: {args.output_dir}")
    print(f"Ground Truth CSV: {args.ground_truth}")
    print("=" * 70)

    # Base photo categories
    categories = [
        ("Computer Center & AI Lab", "computer_lab"),
        ("Central Digital Library", "central_library"),
        ("Advanced Material Testing Lab", "materials_lab"),
        ("Smart Classroom & Lecture Hall", "smart_classroom"),
        ("Barrier-Free Entrance & Ramps", "entrance_ramp")
    ]

    # Institutions mapping
    inst_a = {"id": "INST_001", "name": "Apex Institute of Technology & Science", "lat": 12.9416, "lon": 77.5655}
    inst_b = {"id": "INST_002", "name": "Royal College of Engineering", "lat": 12.2842, "lon": 76.6413}
    inst_c = {"id": "INST_003", "name": "National Academy of Technical Studies", "lat": 18.5293, "lon": 73.8565}
    inst_d = {"id": "INST_004", "name": "Zenith Institute of Engineering", "lat": 13.0033, "lon": 74.7922}

    total_variants_generated = 0

    for title, slug in categories:
        print(f"\nProcessing Infrastructure Category: {title}")

        # Check if real photo provided in input dir
        base_img = None
        if args.input_photos_dir and os.path.exists(args.input_photos_dir):
            for candidate in os.listdir(args.input_photos_dir):
                if slug in candidate.lower() and candidate.lower().endswith(('.jpg', '.jpeg', '.png')):
                    base_img = Image.open(os.path.join(args.input_photos_dir, candidate)).convert("RGB")
                    break

        if base_img is None:
            base_img = create_synthetic_campus_photo(title)

        # Compute baseline perceptual hash
        base_phash = str(imagehash.phash(base_img))

        # --------------------------------------------------------------------
        # (a) Original assigned to Institution A (Genuine EXIF + GPS)
        # --------------------------------------------------------------------
        path_a = os.path.join(args.output_dir, f"{inst_a['id']}_{slug}_original.jpg")
        exif_a = build_genuine_exif(inst_a["lat"], inst_a["lon"], timestamp_str="2024:09:10 11:15:30")
        base_img.save(path_a, "JPEG", quality=95, exif=exif_a)
        total_variants_generated += 1

        print(f"  [Variant A] Genuine Original: {os.path.basename(path_a)}")
        print(f"              GPS: {inst_a['lat']}, {inst_a['lon']} | pHash: {base_phash}")

        # --------------------------------------------------------------------
        # (b) Exact duplicate assigned to Institution B
        # --------------------------------------------------------------------
        path_b = os.path.join(args.output_dir, f"{inst_b['id']}_{slug}_exact_duplicate.jpg")
        base_img.save(path_b, "JPEG", quality=95, exif=exif_a) # Exact verbatim copy
        total_variants_generated += 1

        phash_b = str(imagehash.phash(Image.open(path_b)))
        gt_logger.log_defect(
            institution_id=inst_b["id"],
            institution_name=inst_b["name"],
            document_id=f"PHOTO_{slug}_B",
            document_type="Campus Infrastructure Photo",
            defect_type="reused_photo",
            details=(
                f"Exact duplicate photo reuse: Image for '{title}' submitted by {inst_b['name']} "
                f"is a byte-for-byte exact clone of the photograph submitted by {inst_a['name']} "
                f"(Perceptual hash match: {phash_b}, Hamming distance = 0)."
            ),
            severity="CRITICAL",
            expected_regulatory_flag="PHOTO_REUSE_RADAR_MATCH"
        )
        print(f"  [Variant B] Exact Duplicate:  {os.path.basename(path_b)} (LOGGED DEFECT)")

        # --------------------------------------------------------------------
        # (c) Cropped / brightness-shifted / rotated near-duplicate to Institution C
        # --------------------------------------------------------------------
        w, h = base_img.size
        # Crop 6% from each edge
        cropped = base_img.crop((int(w * 0.06), int(h * 0.06), int(w * 0.94), int(h * 0.94)))
        # Rotate 1.5 degrees
        rotated = cropped.rotate(1.5, resample=Image.BICUBIC, expand=False)
        # Shift brightness +15%
        brightened = ImageEnhance.Brightness(rotated).enhance(1.15)

        path_c = os.path.join(args.output_dir, f"{inst_c['id']}_{slug}_near_duplicate.jpg")
        brightened.save(path_c, "JPEG", quality=90)
        total_variants_generated += 1

        phash_c = str(imagehash.phash(brightened))
        dist = imagehash.hex_to_hash(base_phash) - imagehash.hex_to_hash(phash_c)
        similarity = round((1.0 - (dist / 64.0)) * 100, 1)

        gt_logger.log_defect(
            institution_id=inst_c["id"],
            institution_name=inst_c["name"],
            document_id=f"PHOTO_{slug}_C",
            document_type="Campus Infrastructure Photo",
            defect_type="reused_photo",
            details=(
                f"Cropped / manipulated near-duplicate reuse: Image for '{title}' submitted by {inst_c['name']} "
                f"matches {inst_a['name']} with {similarity}% visual similarity "
                f"(pHash: {phash_c}, Hamming distance = {dist} bits)."
            ),
            severity="CRITICAL",
            expected_regulatory_flag="PHOTO_REUSE_RADAR_MATCH"
        )
        print(f"  [Variant C] Near-Duplicate:   {os.path.basename(path_c)} (Similarity {similarity}%, Hamming {dist}) (LOGGED DEFECT)")

        # --------------------------------------------------------------------
        # (d) Version with EXIF stripped to Institution D
        # --------------------------------------------------------------------
        path_d = os.path.join(args.output_dir, f"{inst_d['id']}_{slug}_exif_stripped.jpg")
        # Save fresh copy without passing any EXIF bytes
        image_no_exif = base_img.copy()
        image_no_exif.save(path_d, "JPEG", quality=92)
        total_variants_generated += 1

        gt_logger.log_defect(
            institution_id=inst_d["id"],
            institution_name=inst_d["name"],
            document_id=f"PHOTO_{slug}_D",
            document_type="Campus Infrastructure Photo",
            defect_type="missing_exif_metadata",
            details=(
                f"EXIF metadata completely stripped on '{title}' photo. Camera make, timestamp, "
                f"and GPS geo-tag coordinates missing from statutory upload."
            ),
            severity="WARNING",
            expected_regulatory_flag="STRIPPED_EXIF_PROVENANCE"
        )
        print(f"  [Variant D] EXIF Stripped:    {os.path.basename(path_d)} (LOGGED DEFECT)")

    print("\n" + "=" * 70)
    print(f"PHOTO VARIANTS GENERATION COMPLETE: {total_variants_generated} Images Generated")
    print(f"Ground Truth CSV updated at: {args.ground_truth}")
    print("=" * 70)

if __name__ == "__main__":
    main()
