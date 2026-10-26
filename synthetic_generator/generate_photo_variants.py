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
    """Creates a high-contrast representative campus photo if no input folder is provided."""
    colors = {
        "Computer Center & AI Lab": ((20, 30, 50), (14, 165, 233)),
        "Central Digital Library": ((50, 35, 20), (245, 158, 11)),
        "Advanced Material Testing Lab": ((30, 45, 35), (16, 185, 129)),
        "Smart Classroom & Lecture Hall": ((40, 30, 45), (168, 85, 247)),
        "Barrier-Free Entrance & Ramps": ((35, 40, 45), (100, 116, 139))
    }
    bg_color, accent_color = colors.get(category_name, ((30, 30, 40), (200, 200, 200)))
    
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Floor perspective
    draw.polygon([(0, int(height * 0.7)), (width, int(height * 0.7)), (width, height), (0, height)], fill=(bg_color[0]+15, bg_color[1]+15, bg_color[2]+15))
    
    # Grid lines / workstations representation
    for i in range(5):
        x = int(width * (0.15 + i * 0.18))
        draw.rectangle([x, int(height * 0.45), x + 120, int(height * 0.65)], outline=accent_color, width=3)
        draw.rectangle([x + 20, int(height * 0.48), x + 100, int(height * 0.60)], fill=(accent_color[0]//3, accent_color[1]//3, accent_color[2]//3))

    # Header title banner
    draw.rectangle([0, 0, width, 80], fill=(15, 23, 42))
    draw.text((40, 28), f"AICTE TECHNICAL CAMPUS INFRASTRUCTURE: {category_name.upper()}", fill=(240, 240, 240))
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
