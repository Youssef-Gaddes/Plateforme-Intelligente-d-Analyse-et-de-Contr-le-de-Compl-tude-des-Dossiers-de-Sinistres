# ml/batch_ocr.py
import os
import csv
import sys
# Add the directory containing the file to the system path

from ocrHelper import extract_text

REAL_IMAGES_DIR = "ml/real_images"
OUTPUT_CSV = "ml/data/real_ocr_output.csv"

def main():
    rows = []
    for label in os.listdir(REAL_IMAGES_DIR):
        label_dir = os.path.join(REAL_IMAGES_DIR, label)
        if not os.path.isdir(label_dir):
            continue
        for filename in sorted(os.listdir(label_dir)):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".pdf"):
                continue
            file_path = os.path.join(label_dir, filename)
            print(f"Processing {file_path} ...")
            try:
                raw_text = extract_text(file_path, ext)
                print(raw_text)
            except Exception as e:
                print(f"  FAILED: {e}")
                continue
            rows.append((filename, label, raw_text))

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label", "raw_text"])
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")
    print("Current working directory:", os.getcwd())
    print("REAL_IMAGES_DIR exists:", os.path.exists(REAL_IMAGES_DIR))
    print("Contents:", os.listdir(REAL_IMAGES_DIR))
    counts = {}
    for _, label, _ in rows:
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")

if __name__ == "__main__":
    main()