from annotated_types import doc
from pdf2image import convert_from_path
import fitz
import pytesseract
import cv2
import numpy as np
from PIL import Image
import unicodedata, re
from text_utils import clean_text as clean_ocr_text

MONTHS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08", "aout": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12", "decembre": "12",
}

def preprocess_image(img: Image.Image) -> np.ndarray:
    # Convert PIL Image -> OpenCV (numpy array, BGR color order)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    if max(h, w) < 2000:
        scale = 2000 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=15)

    bg = cv2.medianBlur(gray, 173)
    diff = 255 - cv2.absdiff(gray, bg)
    norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    thresh = cv2.adaptiveThreshold(
        norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 35, 11
    )

    coords = np.column_stack(np.where(thresh < 255))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) > 0.5:
        (h, w) = thresh.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        thresh = cv2.warpAffine(thresh, M, (w, h),
                                 flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return thresh

def extract_text(file_path: str, ext: str) -> str:
    if ext == ".pdf":
        doc = fitz.open(file_path)
        images = []
    
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
    
            # 300 DPI scaling
            zoom = 300 / 72
            matrix = fitz.Matrix(zoom, zoom)
    
            # Render page to a pixmap (Keep alpha=False unless you specifically need transparency)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
        
            # 1. Convert pixmap raw bytes into a 1D NumPy array
            img_buffer = np.frombuffer(pix.samples, dtype=np.uint8)
        
            # 2. Reshape the 1D array into an image matrix (Height x Width x Channels)
            # pix.n represents the number of color channels (usually 3 for RGB)
            img_np = img_buffer.reshape((pix.height, pix.width, pix.n))

            # 3. CRITICAL FOR OPENCV: PyMuPDF uses RGB, but OpenCV defaults to BGR
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            # Append the proper OpenCV-compatible image
            images.append(img_bgr)
            cv2.imwrite(f"pdf_converted_page_{page_num + 1}.png", img_bgr)
            print(f"Page {page_num + 1} converted successfully. Shape: {img_bgr.shape}")
    else:
        images = [Image.open(file_path)]
    pages = [preprocess_image(img) for img in images]
    custom_config = r'--oem 3 --psm 4 -l fra'
    return "\n".join(pytesseract.image_to_string(p, config=custom_config) for p in pages)


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