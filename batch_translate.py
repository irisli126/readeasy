import json
import os
import time
import urllib.parse
import urllib.request

def translate_text_mymemory(text):
    if not text.strip():
        return ""
    try:
        url = f'https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=sv|zh-CN'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tr = data.get('responseData', {}).get('translatedText', '')
            if tr and 'MYMEMORY WARNING' not in tr and 'QUERY LENGTH' not in tr:
                return tr
    except Exception as e:
        pass
    return text

def pretranslate_initial_pages(num_pages=15):
    cache_path = os.path.abspath('data/translations_cache.json')
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    with open('data/book_processed.json', 'r', encoding='utf-8') as f:
        pages = json.load(f)

    print(f"Starting pre-translation for first {num_pages} pages...")
    for p_idx in range(min(num_pages, len(pages))):
        page = pages[p_idx]
        p_num = str(page['page_num'])
        if p_num in cache and len(cache[p_num]) == len(page['paragraphs']):
            print(f"Page {p_num} already translated ({len(cache[p_num])} paragraphs).")
            continue

        translated_paras = []
        for p in page['paragraphs']:
            if len(p) <= 2:
                translated_paras.append(p)
                continue
            tr = translate_text_mymemory(p)
            translated_paras.append(tr)
            time.sleep(0.15) # slight pause to avoid rate limit

        cache[p_num] = translated_paras
        print(f"Translated Page {p_num}/{num_pages} ({len(translated_paras)} paragraphs)")

        # Save periodically
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    print("Initial pages pre-translated successfully!")

if __name__ == '__main__':
    pretranslate_initial_pages(30)
