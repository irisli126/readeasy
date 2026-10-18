import re
import json
import os
import urllib.request
import urllib.parse

class SwedishDictionary:
    def __init__(self, data_dir='data'):
        self.data_dir = os.path.abspath(data_dir)
        self.sv_zh_dict = {}
        self.cache_file = os.path.join(self.data_dir, 'dict_cache.json')
        self.cache = {}
        self._load_sv_zh()
        self._load_cache()

    def _load_sv_zh(self):
        dict_path = os.path.join(self.data_dir, 'sv_zh_dict.json')
        if os.path.exists(dict_path):
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    self.sv_zh_dict = json.load(f)
                print(f"Loaded {len(self.sv_zh_dict)} Swedish-Chinese dictionary entries.")
            except Exception as e:
                print("Error loading sv_zh_dict.json:", e)

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def lemmatize_word(self, word):
        w = word.lower().strip()
        candidates = [w]

        # 1. Genitive -s: "sonens" -> "sonen", "Marcus" -> "Marcus"
        if w.endswith('s') and len(w) > 3 and not w.endswith(('ss', 'as', 'is', 'us', 'os', 'es')):
            stem_s = w[:-1]
            candidates.append(stem_s)

        # 2. Definite plural: -arna, -erna, -orna, -na
        for suff in ['arna', 'erna', 'orna', 'ena', 'na']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'a', base + 'e', base + 'o'])

        # 3. Definite singular: -en, -et
        for suff in ['en', 'et']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'e', base + 'a'])

        # 4. Plural endings: -ar, -er, -or
        for suff in ['ar', 'er', 'or']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'a', base + 'e', base + 'o'])

        # 5. Verb past: -ade, -te, -de
        if w.endswith('ade') and len(w) > 4:
            base = w[:-3]
            candidates.extend([base + 'a', base])
        elif (w.endswith('te') or w.endswith('de')) and len(w) > 3:
            base = w[:-2]
            candidates.extend([base + 'a', base])

        # 6. Verb present: -ar, -er, -r
        if w.endswith('ar') and len(w) > 3:
            candidates.append(w[:-2] + 'a')
        elif w.endswith('er') and len(w) > 3:
            candidates.append(w[:-2] + 'a')
            candidates.append(w[:-2])
        elif w.endswith('r') and len(w) > 2:
            candidates.append(w[:-1])

        # 7. Adjective neuter: -t, plural: -a
        if w.endswith('t') and len(w) > 3:
            candidates.append(w[:-1])
        if w.endswith('a') and len(w) > 3:
            candidates.append(w[:-1])
            candidates.append(w[:-1] + 'e')

        # 8. Comparative / Superlative: -are, -ast
        if w.endswith('are') and len(w) > 4:
            candidates.append(w[:-3])
        if w.endswith('ast') and len(w) > 4:
            candidates.append(w[:-3])

        # Deduplicate while preserving order
        seen = set()
        res = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                res.append(c)
        return res

    def lookup(self, raw_query):
        query = raw_query.strip()
        if not query:
            return None

        # Clean punctuation from edges
        clean_word = re.sub(r'^[^\wåäöÅÄÖ]+|[^\wåäöÅÄÖ]+$', '', query).lower()
        if not clean_word:
            clean_word = query.lower()

        # Check local cache first
        if clean_word in self.cache:
            return self.cache[clean_word]

        # Multi-word phrase or sentence
        if ' ' in clean_word or len(clean_word.split()) > 1:
            tr = self._translate_online(clean_word)
            res = {
                'query': query,
                'word': clean_word,
                'lemma': '',
                'pos': '短语 / 句子',
                'phonetic': '',
                'audioUrl': '',
                'zh': tr or '（网络不可用，无法翻译整句）',
                'en': ''
            }
            if tr:
                self.cache[clean_word] = res
                self._save_cache()
            return res

        # Single word lookup
        candidates = self.lemmatize_word(clean_word)

        # 1. Search in offline Swedish-Chinese dictionary
        hit_entry = None
        hit_lemma = clean_word

        for cand in candidates:
            if cand in self.sv_zh_dict:
                entry = self.sv_zh_dict[cand]
                # Check if it has genuine Chinese definition
                if entry.get('zh') and not entry['zh'].startswith('（暂无中文'):
                    hit_entry = entry
                    hit_lemma = cand
                    break

        # If not found with genuine Chinese, check if there's any entry at all
        if not hit_entry:
            for cand in candidates:
                if cand in self.sv_zh_dict:
                    hit_entry = self.sv_zh_dict[cand]
                    hit_lemma = cand
                    break

        if hit_entry and hit_entry.get('zh') and not hit_entry['zh'].startswith('（暂无中文'):
            res = {
                'query': query,
                'word': clean_word,
                'lemma': hit_lemma if hit_lemma != clean_word else '',
                'pos': hit_entry.get('pos', '单词'),
                'phonetic': hit_entry.get('phonetic', ''),
                'audioUrl': hit_entry.get('audioUrl', ''),
                'zh': hit_entry.get('zh', ''),
                'en': hit_entry.get('en', '')
            }
            self.cache[clean_word] = res
            self._save_cache()
            return res

        # 2. Try online translation if not found in offline dictionary
        online_zh = self._translate_online(clean_word)
        if not online_zh and hit_lemma != clean_word:
            online_zh = self._translate_online(hit_lemma)

        en_def = hit_entry.get('en', '') if hit_entry else ''
        phonetic = hit_entry.get('phonetic', '') if hit_entry else ''
        audio_url = hit_entry.get('audioUrl', '') if hit_entry else ''
        pos = hit_entry.get('pos', '单词') if hit_entry else '单词'

        # CRITICAL: If no Chinese found, do NOT show English as Chinese!
        zh_def = online_zh if online_zh else ('未收录中文释义' if not en_def else '（暂无直接中文释义）')

        res = {
            'query': query,
            'word': clean_word,
            'lemma': hit_lemma if hit_lemma != clean_word else '',
            'pos': pos,
            'phonetic': phonetic,
            'audioUrl': audio_url,
            'zh': zh_def,
            'en': en_def
        }

        self.cache[clean_word] = res
        self._save_cache()
        return res

    def _translate_online(self, text):
        # Fallback to MyMemory or Youdao
        try:
            url = f'https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=sv|zh-CN'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                tr = data.get('responseData', {}).get('translatedText', '')
                if tr and 'MYMEMORY WARNING' not in tr and 'QUERY LENGTH' not in tr and not tr.isascii():
                    return tr
        except Exception:
            pass
        return None

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    d = SwedishDictionary()
    test_words = ['svarade', 'stolen', 'känslor', 'håret', 'mindes', 'toviga', 'jeansen', 'gymnastikskorna']
    for tw in test_words:
        res = d.lookup(tw)
        print(f"[{tw}] -> lemma: {res['lemma']} | ZH: {res['zh']} | EN: {res['en']} | PHONETIC: {res['phonetic']}")
