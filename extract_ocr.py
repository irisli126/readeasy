import asyncio
import os
import sys
import json
import time
import pymupdf
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.storage import StorageFile

async def run_ocr():
    pdf_path = os.path.abspath('Änglarnas svar.pdf')
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    print(f"Total pages to OCR: {total_pages}")

    lang = Language('sv-SE')
    engine = OcrEngine.try_create_from_language(lang)
    if not engine:
        print("Failed to initialize Windows OCR for sv-SE")
        return

    temp_dir = os.path.abspath('temp_ocr_frames')
    os.makedirs(temp_dir, exist_ok=True)

    results = []
    t0 = time.time()

    for idx in range(total_pages):
        page = doc[idx]
        # render at 150 dpi for high OCR quality and fast processing
        pix = page.get_pixmap(dpi=150)
        img_path = os.path.join(temp_dir, f"p_{idx}.png")
        pix.save(img_path)

        storage_file = await StorageFile.get_file_from_path_async(img_path)
        stream = await storage_file.open_async(0)
        decoder = await BitmapDecoder.create_async(stream)
        bmp = await decoder.get_software_bitmap_async()
        ocr_res = await engine.recognize_async(bmp)

        lines_data = []
        for line in ocr_res.lines:
            words = []
            for w in line.words:
                words.append({
                    "text": w.text,
                    "box": [w.bounding_rect.x, w.bounding_rect.y, w.bounding_rect.width, w.bounding_rect.height]
                })
            lines_data.append({
                "text": line.text,
                "words": words
            })

        page_data = {
            "page_num": idx + 1,
            "img_width": pix.width,
            "img_height": pix.height,
            "lines": lines_data
        }
        results.append(page_data)

        # Cleanup image file to save disk space
        try:
            os.remove(img_path)
        except Exception:
            pass

        if (idx + 1) % 10 == 0 or (idx + 1) == total_pages:
            elapsed = time.time() - t0
            avg_per_page = elapsed / (idx + 1)
            remaining = avg_per_page * (total_pages - (idx + 1))
            print(f"Progress: {idx + 1}/{total_pages} pages ({((idx+1)/total_pages)*100:.1f}%) | Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")

    os.makedirs('data', exist_ok=True)
    out_json = os.path.abspath('data/book_ocr.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"OCR successfully completed! Saved to {out_json}")
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass

if __name__ == '__main__':
    asyncio.run(run_ocr())
