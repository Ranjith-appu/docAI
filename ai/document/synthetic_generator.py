"""
High-Fidelity Synthetic Document Generator.
Generates realistic demonstration passports, visas, and presented selfies.
Complies with security rules by watermarking every document:
'SYNTHETIC / DEMO DATA - NOT AN OFFICIAL DOCUMENT'.
"""
import io
import math
from typing import Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont


def _draw_security_guilloche(draw: ImageDraw.ImageDraw, width: int, height: int, color=(210, 225, 240)):
    """Draw subtle security guilloche wave patterns across the document canvas."""
    for y in range(0, height, 24):
        points = []
        for x in range(0, width, 10):
            sine_val = math.sin(x * 0.05) * 8.0
            points.append((x, y + sine_val))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=1)


def _draw_synthetic_portrait(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, seed_char: str = "A"):
    """Draw a standardized biometric portrait avatar."""
    # Background for photo
    draw.rectangle([x, y, x + w, y + h], fill=(235, 240, 245), outline=(120, 140, 160), width=2)

    # Head and shoulders
    head_cx = x + w // 2
    head_cy = y + int(h * 0.42)
    head_r = int(w * 0.26)

    # Shoulders
    shoulder_y = head_cy + int(head_r * 1.1)
    draw.chord([x + int(w * 0.1), shoulder_y, x + int(w * 0.9), y + h + int(h * 0.3)], start=180, end=0, fill=(70, 95, 125))

    # Face circle
    skin_tone = (245, 218, 195) if ord(seed_char) % 2 == 0 else (210, 175, 145)
    draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], fill=skin_tone)

    # Hair
    draw.arc([head_cx - head_r, head_cy - head_r - 4, head_cx + head_r, head_cy], start=180, end=0, fill=(40, 30, 25), width=int(head_r * 0.35))

    # Eyes & Mouth
    eye_offset = int(head_r * 0.35)
    eye_y = head_cy - int(head_r * 0.1)
    draw.ellipse([head_cx - eye_offset - 3, eye_y - 3, head_cx - eye_offset + 3, eye_y + 3], fill=(30, 30, 40))
    draw.ellipse([head_cx + eye_offset - 3, eye_y - 3, head_cx + eye_offset + 3, eye_y + 3], fill=(30, 30, 40))

    # Mouth line
    mouth_y = head_cy + int(head_r * 0.45)
    draw.line([head_cx - int(head_r * 0.25), mouth_y, head_cx + int(head_r * 0.25), mouth_y], fill=(160, 80, 80), width=2)


def generate_synthetic_passport(
    full_name: str = "JOHN DOE",
    passport_number: str = "A12345678",
    nationality: str = "UTO",
    dob: str = "1992-05-14",
    expiry: str = "2029-08-20",
    is_tampered: bool = False
) -> bytes:
    """Generate a synthetic passport document as PNG bytes."""
    width, height = 750, 500
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # 1. Background Guilloche & Header Banner
    _draw_security_guilloche(draw, width, height)
    draw.rectangle([0, 0, width, 55], fill=(24, 43, 73))
    draw.text((30, 18), "PASSPORT / PASSEPORT", fill=(255, 255, 255))
    draw.text((width - 160, 18), f"TYPE P  |  {nationality}", fill=(200, 220, 245))

    # 2. Watermark
    watermark_text = "SYNTHETIC / DEMO DATA - NOT AN OFFICIAL DOCUMENT"
    draw.text((45, height - 30), watermark_text, fill=(210, 40, 40))

    # 3. Portrait Area
    photo_x, photo_y, photo_w, photo_h = 45, 85, 175, 225
    _draw_synthetic_portrait(draw, photo_x, photo_y, photo_w, photo_h, seed_char=full_name[0])

    if is_tampered:
        # Introduce slight visual edge artifact around photo box
        draw.rectangle([photo_x - 3, photo_y - 3, photo_x + photo_w + 3, photo_y + photo_h + 3], outline=(255, 0, 120), width=3)
        draw.text((photo_x, photo_y + photo_h + 8), "[MODIFIED PHOTO REGION]", fill=(220, 20, 60))

    # 4. Data Fields
    tx = 250
    fields = [
        ("Surname / Given Name", full_name),
        ("Passport No. / No de Passeport", passport_number),
        ("Nationality / Nationalité", nationality),
        ("Date of Birth / Date de Naissance", dob),
        ("Sex / Sexe", "M"),
        ("Date of Expiry / Date d'expiration", expiry),
    ]

    curr_y = 80
    for label, val in fields:
        draw.text((tx, curr_y), label.upper(), fill=(100, 116, 139))
        draw.text((tx, curr_y + 16), val, fill=(15, 23, 42))
        curr_y += 42

    # 5. ICAO Doc 9303 MRZ Lines
    clean_surname = full_name.split()[-1].upper()
    clean_given = full_name.split()[0].upper()
    mrz1 = f"P<{nationality}{clean_surname}<<{clean_given}".ljust(44, "<")
    mrz2 = f"{passport_number}4{nationality}9205141M2908202<<<<<<<<<<<<<<06"

    draw.rectangle([20, height - 100, width - 20, height - 40], fill=(240, 243, 246), outline=(203, 213, 225))
    draw.text((35, height - 92), mrz1, fill=(20, 20, 20))
    draw.text((35, height - 70), mrz2, fill=(20, 20, 20))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_synthetic_visa(
    full_name: str = "JOHN DOE",
    passport_number: str = "A12345678",
    visa_number: str = "V98765432",
    expiry: str = "2029-08-20"
) -> bytes:
    """Generate a synthetic entry visa document."""
    width, height = 750, 480
    img = Image.new("RGB", (width, height), color=(252, 251, 247))
    draw = ImageDraw.Draw(img)

    _draw_security_guilloche(draw, width, height, color=(235, 220, 200))
    draw.rectangle([0, 0, width, 50], fill=(139, 44, 44))
    draw.text((30, 15), "TRAVEL VISA / VISA DE VOYAGE", fill=(255, 255, 255))
    draw.text((width - 200, 15), f"VISA NO: {visa_number}", fill=(255, 230, 230))

    # Watermark
    draw.text((45, height - 25), "SYNTHETIC / DEMO DATA - NOT AN OFFICIAL DOCUMENT", fill=(180, 50, 50))

    tx = 50
    curr_y = 75
    fields = [
        ("Full Name", full_name),
        ("Passport Number", passport_number),
        ("Visa Class", "B1/B2 TOURIST / BUSINESS"),
        ("Number of Entries", "MULTIPLE"),
        ("Valid Until", expiry),
        ("Duration of Stay", "90 DAYS PER VISIT"),
    ]

    for label, val in fields:
        draw.text((tx, curr_y), label.upper(), fill=(120, 100, 90))
        draw.text((tx, curr_y + 16), val, fill=(30, 20, 15))
        curr_y += 45

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_synthetic_presented_face(full_name: str = "JOHN DOE", is_mismatch: bool = False) -> bytes:
    """Generate a synthetic presented live selfie for face matching verification."""
    width, height = 400, 400
    img = Image.new("RGB", (width, height), color=(235, 240, 245))
    draw = ImageDraw.Draw(img)

    seed = "Z" if is_mismatch else full_name[0]
    _draw_synthetic_portrait(draw, 50, 40, 300, 320, seed_char=seed)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
