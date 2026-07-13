import cv2
import pytesseract
from PIL import Image
from ocrHelper import preprocess_image

image_path = "bin/pdf_converted_page_1.png"
img  = Image.open(image_path)
processed = preprocess_image(img)
cv2.imwrite("debug_preprocessed.png", processed)  # inspect this visually

text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 4 -l fra')
print(text)