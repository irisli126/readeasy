import os
import sys
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from bottle import Bottle, request, response, static_file, run
import pymupdf

from dictionary import SwedishDictionary

app = Bottle()

# Support PyInstaller frozen bundle vs script
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BUNDLE_DIR

WEB_DIR = os.path.join(BUNDLE_DIR, 'web')
DATA_DIR = os.path.join(EXE_DIR, 'data') if os.path.exists(os.path.join(EXE_DIR, 'data')) else os.path.join(BUNDLE_DIR, 'data')
STATE_FILE = os.path.join(EXE_DIR, 'readeasy_state.json')
VOCAB_FILE = os.path.join(DATA_DIR, 'vocab.json')
TRANS_CACHE_FILE = os.path.join(DATA_DIR, 'translations_cache.json')

# PDF Path: check next to exe first, then bundle
PDF_PATH = os.path.join(EXE_DIR, 'Änglarnas svar.pdf')
if not os.path.exists(PDF_PATH):
    PDF_PATH = os.path.join(BUNDLE_DIR, 'Änglarnas svar.pdf')

# Initialize Dictionary
swedish_dict = SwedishDictionary(data_dir=DATA_DIR)

# Load Book Processed Data
book_pages = []
processed_path = os.path.join(DATA_DIR, 'book_processed.json')
if os.path.exists(processed_path):
    with open(processed_path, 'r', encoding='utf-8') as f:
        book_pages = json.load(f)

# Load Translations Cache
trans_cache = {}
if os.path.exists(TRANS_CACHE_FILE):
    try:
        with open(TRANS_CACHE_FILE, 'r', encoding='utf-8') as f:
            trans_cache = json.load(f)
    except Exception:
        trans_cache = {}

# Load Vocab
vocab_list = []
if os.path.exists(VOCAB_FILE):
    try:
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            vocab_list = json.load(f)
    except Exception:
        vocab_list = []

# Open PDF Document for rendering
pdf_doc = None
if os.path.exists(PDF_PATH):
    try:
        pdf_doc = pymupdf.open(PDF_PATH)
    except Exception as e:
        print("Failed to open PDF:", e)

def save_translations_cache():
    try:
        with open(TRANS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(trans_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_vocab_file():
    try:
        with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
            json.dump(vocab_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def translate_single_text(text):
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
    except Exception:
        pass
    return text

def prefetch_page_translation(page_num):
    p_str = str(page_num)
    if p_str in trans_cache:
        return
    if page_num < 1 or page_num > len(book_pages):
        return
    page = book_pages[page_num - 1]
    paras = page.get('paragraphs', [])
    if not paras:
        return
    
    translated = []
    for p in paras:
        if len(p) <= 2:
            translated.append(p)
        else:
            translated.append(translate_single_text(p))
            time.sleep(0.1)
    trans_cache[p_str] = translated
    save_translations_cache()

# Generate TOC
def get_table_of_contents():
    toc = []
    known_clean = {
        'PROLOG': 'PROLOG (序幕)',
        'MARCUS': 'MARCUS (马库斯)',
        'IRIS': 'IRIS (艾丽丝)',
        'HANNA': 'HANNA (汉娜)',
        'MADELEINE': 'MADELEINE (玛德琳)',
        'ANDREAS': 'ANDREAS (安德烈亚斯)',
        'RACHEL': 'RACHEL (蕾切尔)',
        'VLADEK': 'VLADEK (弗拉德克)',
        'EPILOG': 'EPILOG (尾声)'
    }
    for p in book_pages:
        paras = p.get('paragraphs', [])
        if not paras:
            continue
        for para in paras[:2]:
            p_strip = para.strip().replace('"', '').replace('»', '')
            for k, label in known_clean.items():
                if p_strip.startswith(k):
                    toc.append({'page': p['page_num'], 'title': label})
                    break
    # Deduplicate by title
    seen = set()
    cleaned_toc = []
    for item in toc:
        if item['title'] not in seen:
            seen.add(item['title'])
            cleaned_toc.append(item)
    return cleaned_toc

# ================= API ROUTES =================

@app.route('/')
def serve_index():
    return static_file('index.html', root=WEB_DIR)

@app.route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root=WEB_DIR)

@app.route('/api/book_info')
def api_book_info():
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except Exception:
            state = {}

    # Default to page 6 (Chapter 1) if first time opening
    if not state.get('current_page'):
        state['current_page'] = 6
        state['mode'] = 'bilingual'
        state['theme'] = 'sepia'
        state['font_size'] = 18

    return {
        'book_title': 'Änglarnas svar',
        'total_pages': len(book_pages),
        'toc': get_table_of_contents(),
        'state': state
    }

@app.route('/api/page')
def api_get_page():
    page_num = int(request.query.get('num', 1))
    mode = request.query.get('mode', 'bilingual')

    if page_num < 1 or page_num > len(book_pages):
        return {'error': 'Invalid page number'}

    page_data = book_pages[page_num - 1]
    p_str = str(page_num)

    translations = trans_cache.get(p_str, [])
    paras = page_data.get('paragraphs', [])

    # If in bilingual mode and translations are missing, translate on the fly
    if mode == 'bilingual' and (not translations or len(translations) < len(paras)):
        translated_list = []
        for p in paras:
            if len(p) <= 2:
                translated_list.append(p)
            else:
                translated_list.append(translate_single_text(p))
                time.sleep(0.05)
        translations = translated_list
        trans_cache[p_str] = translations
        save_translations_cache()

    # Trigger background prefetch for next page
    if page_num < len(book_pages):
        t = threading.Thread(target=prefetch_page_translation, args=(page_num + 1,))
        t.daemon = True
        t.start()

    return {
        'page_num': page_num,
        'img_width': page_data.get('img_width', 1240),
        'img_height': page_data.get('img_height', 1755),
        'paragraphs': paras,
        'translations': translations,
        'lines': page_data.get('lines', [])
    }

@app.route('/api/page_image')
def api_page_image():
    page_num = int(request.query.get('num', 1))
    if not pdf_doc or page_num < 1 or page_num > len(pdf_doc):
        response.status = 404
        return "Image not found"

    pix = pdf_doc[page_num - 1].get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    response.content_type = 'image/png'
    return img_bytes

@app.route('/api/lookup')
def api_lookup():
    word = request.query.get('word', '').strip()
    if not word:
        return {'word': '', 'zh': ''}
    res = swedish_dict.lookup(word)
    return res

@app.route('/api/save_state', method='POST')
def api_save_state():
    try:
        data = request.json or {}
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/api/vocab')
def api_get_vocab():
    return json.dumps(vocab_list, ensure_ascii=False)

@app.route('/api/vocab/add', method='POST')
def api_add_vocab():
    item = request.json or {}
    w = item.get('word', '').lower()
    if not w:
        return {'status': 'ignored'}
    # avoid duplicates
    for ex in vocab_list:
        if ex.get('word', '').lower() == w:
            return {'status': 'exists'}
    vocab_list.insert(0, item)
    save_vocab_file()
    return {'status': 'ok'}

@app.route('/api/vocab/remove', method='POST')
def api_remove_vocab():
    data = request.json or {}
    w = data.get('word', '').lower()
    global vocab_list
    vocab_list = [x for x in vocab_list if x.get('word', '').lower() != w]
    save_vocab_file()
    return {'status': 'ok'}

@app.route('/api/search')
def api_search():
    q = request.query.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return {'results': []}

    results = []
    for p in book_pages:
        p_num = p['page_num']
        for para in p.get('paragraphs', []):
            lower_p = para.lower()
            if q in lower_p:
                idx = lower_p.find(q)
                start = max(0, idx - 40)
                end = min(len(para), idx + len(q) + 50)
                snippet = para[start:end]
                if start > 0:
                    snippet = '...' + snippet
                if end < len(para):
                    snippet = snippet + '...'
                # highlight keyword
                highlighted = re.sub(f'({re.escape(q)})', r'<mark>\1</mark>', snippet, flags=re.IGNORECASE)
                results.append({
                    'page': p_num,
                    'snippet': highlighted
                })
                if len(results) >= 50:
                    break
        if len(results) >= 50:
            break

    return {'results': results}

def run_server(port=23456):
    print(f"Server starting on http://127.0.0.1:{port}...")
    run(app, host='127.0.0.1', port=port, quiet=True)

if __name__ == '__main__':
    run_server()
