import json
import re
import os
import sys

def clean_paragraph_text(text):
    # join hyphens at line wraps: "köks- stolen" -> "köksstolen"
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    # clean extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def group_lines_into_paragraphs(lines):
    if not lines:
        return []

    # Calculate average line width for standard lines
    widths = []
    line_heights = []
    for i in range(len(lines)):
        w_list = lines[i]['words']
        if len(w_list) >= 4:
            w = (w_list[-1]['box'][0] + w_list[-1]['box'][2]) - w_list[0]['box'][0]
            widths.append(w)
        if i > 0 and lines[i]['words'] and lines[i-1]['words']:
            dy = lines[i]['words'][0]['box'][1] - lines[i-1]['words'][0]['box'][1]
            if dy > 0:
                line_heights.append(dy)

    max_w = max(widths) if widths else 800
    avg_h = (sum(line_heights) / len(line_heights)) if line_heights else 45

    paragraphs = []
    curr_words = []

    for i, line in enumerate(lines):
        txt = line['text'].strip()
        if not txt:
            continue

        # Ignore bottom page numbers
        if txt.isdigit() and len(txt) <= 3 and i >= len(lines) - 2:
            continue

        words = line['words']
        if not words:
            continue

        starts_new = False

        if not curr_words:
            starts_new = True
        elif txt.isupper() and len(txt) < 30: # e.g. "MARCUS"
            starts_new = True
        elif txt.startswith('"') or txt.startswith('–') or txt.startswith('»'): # dialogue opening
            starts_new = True
        elif curr_words:
            last_word = curr_words[-1]
            last_ends_punct = bool(re.search(r'[\.\!\?][\"\'\”]?$', last_word))
            prev_line = lines[i-1]
            prev_words = prev_line['words']
            if prev_words:
                prev_line_w = (prev_words[-1]['box'][0] + prev_words[-1]['box'][2]) - prev_words[0]['box'][0]
                prev_line_txt = prev_line['text'].strip()
                dy = words[0]['box'][1] - prev_words[0]['box'][1]

                # If previous line had punctuation and ended well before the right margin
                if last_ends_punct and prev_line_w < max_w * 0.88:
                    starts_new = True
                # Or if there is a distinct vertical paragraph break
                elif dy > avg_h * 1.4:
                    starts_new = True

        if starts_new and curr_words:
            p_text = clean_paragraph_text(' '.join(curr_words))
            if p_text:
                paragraphs.append(p_text)
            curr_words = []

        for w in words:
            curr_words.append(w['text'])

    if curr_words:
        p_text = clean_paragraph_text(' '.join(curr_words))
        if p_text:
            paragraphs.append(p_text)

    return paragraphs

def process_all_pages():
    with open('data/book_ocr.json', 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)

    processed_pages = []
    for page in ocr_data:
        paras = group_lines_into_paragraphs(page['lines'])
        processed_pages.append({
            "page_num": page['page_num'],
            "img_width": page['img_width'],
            "img_height": page['img_height'],
            "paragraphs": paras,
            "lines": page['lines']
        })

    with open('data/book_processed.json', 'w', encoding='utf-8') as f:
        json.dump(processed_pages, f, ensure_ascii=False, indent=2)

    print(f"Processed {len(processed_pages)} pages into data/book_processed.json")

    # Show sample from page 6
    p6 = processed_pages[5]
    print(f"\n--- Sample from Page 6 (has {len(p6['paragraphs'])} paragraphs) ---")
    for i, p in enumerate(p6['paragraphs']):
        print(f"[{i}]: {p}\n")

if __name__ == '__main__':
    process_all_pages()
