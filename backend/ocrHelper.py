from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
from PIL import Image
import unicodedata, re

MONTHS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08", "aout": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12", "decembre": "12",
}

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    img = np.array(pil_img.convert("L"))                 # grayscale
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(img)

def extract_text(file_path: str, ext: str) -> str:
    if ext == ".pdf":
        images = convert_from_path(file_path, dpi=300)
    else:
        images = [Image.open(file_path)]
    pages = [preprocess_image(img) for img in images]
    return "\n".join(pytesseract.image_to_string(p, lang="fra") for p in pages)

def clean_ocr_text(text: str) -> str:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")  # strip accents
    text = re.sub(r"[^a-z0-9\s./-]", " ", text)   
    text = re.sub(r"\s+", " ", text).strip()      
    return text

def extract_fields(clean_text: str) -> dict:
    fields = {}

    # Contract number: letters + optional dash + digits (e.g. ALZ-55120984)
    if m := re.search(r"contrat\s*:?\s*([a-z]{2,5}-?\d{4,})", clean_text):
        fields["numero_contrat"] = m.group(1).upper()

    # Numeric date: 09/04/2026
    if m := re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", clean_text):
        fields["date"] = m.group(1)
    # Numeric dates with year first: 2026-04-09 or 2026/04/09
    elif m := re.search(r"\b(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})\b", clean_text):
        fields["date"] = m.group(1)
    # Written date: 9 avril 2026
    elif m := re.search(r"\b(\d{1,2})\s+(" + "|".join(MONTHS_FR.keys()) + r")\s+(\d{4})\b", clean_text):
        day, month_name, year = m.groups()
        fields["date"] = f"{day.zfill(2)}/{MONTHS_FR[month_name]}/{year}"

    if m := re.search(r"n[o°]\s*permis\s*:?\s*(\w+)", clean_text):
        fields["numero_permis"] = m.group(1)

    if m := re.search(r"n[o°]\s*facture\s*:?\s*(\w+)", clean_text):
        fields["numero_facture"] = m.group(1)

    if m := re.search(r"immatricul\w*\s*[:\s]\s*([a-z]{2}-?\d{3}-?[a-z]{2})", clean_text):
        fields["immatriculation"] = m.group(1).upper()
    if m := re.search(r"montant\W*(\d+[.,]?\d*)", clean_text):
        fields["montant"] = m.group(1)

    return fields