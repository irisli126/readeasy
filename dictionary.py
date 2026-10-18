import re
import json
import os
import urllib.request
import urllib.parse
from functools import lru_cache

# Irregular verbs: inflected -> (lemma, part_of_speech, zh_meaning)
IRREGULAR_VERBS = {
    'är': ('vara', 'verb', '是，存在'),
    'var': ('vara', 'verb', '是，在（过去式）'),
    'varit': ('vara', 'verb', '是，在（完成式）'),
    'ha': ('ha', 'verb', '有，拥有'),
    'har': ('ha', 'verb', '有，拥有（现在式）'),
    'hade': ('ha', 'verb', '有，拥有（过去式）'),
    'haft': ('ha', 'verb', '有，拥有（完成式）'),
    'sa': ('säga', 'verb', '说（过去式）'),
    'sade': ('säga', 'verb', '说（过去式）'),
    'säger': ('säga', 'verb', '说（现在式）'),
    'sagt': ('säga', 'verb', '说（完成式）'),
    'såg': ('se', 'verb', '看，看见（过去式）'),
    'ser': ('se', 'verb', '看，看见（现在式）'),
    'sett': ('se', 'verb', '看，看见（完成式）'),
    'gick': ('gå', 'verb', '走，去（过去式）'),
    'går': ('gå', 'verb', '走，去（现在式）'),
    'gått': ('gå', 'verb', '走，去（完成式）'),
    'kom': ('komma', 'verb', '来，到达（过去式）'),
    'kommer': ('komma', 'verb', '来，将要（现在式）'),
    'kommit': ('komma', 'verb', '来，到达（完成式）'),
    'mindes': ('minnas', 'verb', '记得，回忆起（过去式）'),
    'minns': ('minnas', 'verb', '记得，回忆起（现在式）'),
    'tog': ('ta', 'verb', '拿，取，采取（过去式）'),
    'tar': ('ta', 'verb', '拿，取，采取（现在式）'),
    'tagit': ('ta', 'verb', '拿，取，采取（完成式）'),
    'fick': ('få', 'verb', '得到，获得，可以（过去式）'),
    'får': ('få', 'verb', '得到，获得，可以（现在式）'),
    'fått': ('få', 'verb', '得到，获得，可以（完成式）'),
    'gav': ('ge', 'verb', '给，给予（过去式）'),
    'ger': ('ge', 'verb', '给，给予（现在式）'),
    'givit': ('ge', 'verb', '给，给予（完成式）'),
    'gett': ('ge', 'verb', '给，给予（完成式）'),
    'vet': ('veta', 'verb', '知道（现在式）'),
    'visste': ('veta', 'verb', '知道（过去式）'),
    'vetat': ('veta', 'verb', '知道（完成式）'),
    'vill': ('vilja', 'verb', '想要，愿意（现在式）'),
    'ville': ('vilja', 'verb', '想要，愿意（过去式）'),
    'velat': ('vilja', 'verb', '想要，愿意（完成式）'),
    'kan': ('kunna', 'verb', '能够，可以，会（现在式）'),
    'kunde': ('kunna', 'verb', '能够，可以，会（过去式）'),
    'kunnat': ('kunna', 'verb', '能够，可以，会（完成式）'),
    'ska': ('skola', 'verb', '将要，应该（现在式）'),
    'skall': ('skola', 'verb', '将要，应该（现在式）'),
    'skulle': ('skola', 'verb', '将会，原本打算（过去式）'),
    'måste': ('måste', 'verb', '必须，一定'),
    'borde': ('böra', 'verb', '应该，应当'),
    'bör': ('böra', 'verb', '应该，应当（现在式）'),
    'satt': ('sitta', 'verb', '坐，位于（过去式/完成式）'),
    'sitter': ('sitta', 'verb', '坐，位于（现在式）'),
    'stod': ('stå', 'verb', '站立，立着（过去式）'),
    'står': ('stå', 'verb', '站立，立着（现在式）'),
    'stått': ('stå', 'verb', '站立，立着（完成式）'),
    'låg': ('ligga', 'verb', '躺，位于（过去式）'),
    'ligger': ('ligga', 'verb', '躺，位于（现在式）'),
    'legat': ('ligga', 'verb', '躺，位于（完成式）'),
    'blev': ('bli', 'verb', '变成，变得（过去式）'),
    'blir': ('bli', 'verb', '变成，变得（现在式）'),
    'blivit': ('bli', 'verb', '变成，变得（完成式）'),
    'fann': ('finna', 'verb', '找到，发觉（过去式）'),
    'finner': ('finna', 'verb', '找到，发觉（现在式）'),
    'funnit': ('finna', 'verb', '找到，发觉（完成式）'),
    'fanns': ('finnas', 'verb', '有，存在（过去式）'),
    'finns': ('finnas', 'verb', '有，存在（现在式）'),
    'funnits': ('finnas', 'verb', '有，存在（完成式）'),
    'höll': ('hålla', 'verb', '握住，保持（过去式）'),
    'håller': ('hålla', 'verb', '握住，保持（现在式）'),
    'hållit': ('hålla', 'verb', '握住，保持（完成式）'),
    'lät': ('låta', 'verb', '让，听起来（过去式）'),
    'låter': ('låta', 'verb', '让，听起来（现在式）'),
    'låtit': ('låta', 'verb', '让，听起来（完成式）'),
    'skrev': ('skriva', 'verb', '写（过去式）'),
    'skriver': ('skriva', 'verb', '写（现在式）'),
    'skrivit': ('skriva', 'verb', '写（完成式）'),
    'åt': ('äta', 'verb', '吃（过去式）'),
    'äter': ('äta', 'verb', '吃（现在式）'),
    'ätit': ('äta', 'verb', '吃（完成式）'),
    'drack': ('dricka', 'verb', '喝（过去式）'),
    'dricker': ('dricka', 'verb', '喝（现在式）'),
    'druckit': ('dricka', 'verb', '喝（完成式）'),
    'dog': ('dö', 'verb', '死，死去（过去式）'),
    'dör': ('dö', 'verb', '死，死去（现在式）'),
    'dött': ('dö', 'verb', '死，死去（完成式）'),
    'bar': ('bära', 'verb', '背，穿，携带（过去式）'),
    'bär': ('bära', 'verb', '背，穿，携带（现在式）'),
    'burit': ('bära', 'verb', '背，穿，携带（完成式）'),
    'valde': ('välja', 'verb', '选择（过去式）'),
    'väljer': ('välja', 'verb', '选择（现在式）'),
    'valt': ('välja', 'verb', '选择（完成式）'),
    'körde': ('köra', 'verb', '驾驶，开动（过去式）'),
    'kör': ('köra', 'verb', '驾驶，开动（现在式）'),
    'kört': ('köra', 'verb', '驾驶，开动（完成式）'),
    'tänkte': ('tänka', 'verb', '想，思考（过去式）'),
    'tänker': ('tänka', 'verb', '想，思考（现在式）'),
    'tänkt': ('tänka', 'verb', '想，思考（完成式）'),
    'trodde': ('tro', 'verb', '相信，认为（过去式）'),
    'tror': ('tro', 'verb', '相信，认为（现在式）'),
    'trott': ('tro', 'verb', '相信，认为（完成式）'),
    'tyckte': ('tycka', 'verb', '觉得，认为（过去式）'),
    'tycker': ('tycka', 'verb', '觉得，认为（现在式）'),
    'tyckt': ('tycka', 'verb', '觉得，认为（完成式）'),
    'kände': ('känna', 'verb', '感觉，认识（过去式）'),
    'känner': ('känna', 'verb', '感觉，认识（现在式）'),
    'känt': ('känna', 'verb', '感觉，认识（完成式）'),
    'förstod': ('förstå', 'verb', '明白，理解（过去式）'),
    'förstår': ('förstå', 'verb', '明白，理解（现在式）'),
    'förstått': ('förstå', 'verb', '明白，理解（完成式）'),
}

# Core vocabulary: lemma -> (part_of_speech, zh_definition)
CORE_VOCAB = {
    'och': ('konj', '和，以及'),
    'i': ('prep', '在...里面，在...中'),
    'att': ('konj/inf', '为了；去，引导词'),
    'en': ('art', '一个（通性单数定冠词）'),
    'ett': ('art', '一个（中性单数定冠词）'),
    'den': ('pron/art', '这，那；定冠词'),
    'det': ('pron/art', '它，这；中性定冠词'),
    'de': ('pron/art', '他们，那些；复数定冠词'),
    'dem': ('pron', '他们（宾格）'),
    'som': ('pron/konj', '正如，作为；引导从句的关系代词'),
    'på': ('prep', '在...上面，在...上'),
    'är': ('verb', '是，存在'),
    'av': ('prep', '由...，从...，关于'),
    'för': ('prep/konj', '为了；因为；对于'),
    'med': ('prep', '和...一起，用，随着'),
    'till': ('prep', '到...，向...，给'),
    'om': ('prep/konj', '关于；如果，是否'),
    'har': ('verb', '有，拥有'),
    'inte': ('adv', '不，没有'),
    'så': ('adv/konj', '如此，这样；那么'),
    'denna': ('pron', '这个（通性）'),
    'detta': ('pron', '这个（中性）'),
    'dessa': ('pron', '这些（复数）'),
    'han': ('pron', '他'),
    'honom': ('pron', '他（宾格）'),
    'hans': ('pron', '他的'),
    'hon': ('pron', '她'),
    'henne': ('pron', '她（宾格）'),
    'hennes': ('pron', '她的'),
    'jag': ('pron', '我'),
    'mig': ('pron', '我（宾格）'),
    'min': ('pron', '我的（通性）'),
    'mitt': ('pron', '我的（中性）'),
    'mina': ('pron', '我的（复数）'),
    'du': ('pron', '你'),
    'dig': ('pron', '你（宾格）'),
    'din': ('pron', '你的（通性）'),
    'ditt': ('pron', '你的（中性）'),
    'dina': ('pron', '你的（复数）'),
    'vi': ('pron', '我们'),
    'oss': ('pron', '我们（宾格）'),
    'vår': ('pron', '我们的（通性）'),
    'vårt': ('pron', '我们的（中性）'),
    'våra': ('pron', '我们的（复数）'),
    'ni': ('pron', '你们'),
    'er': ('pron', '你们（宾格）；你们的'),
    'ert': ('pron', '你们的（中性）'),
    'era': ('pron', '你们的（复数）'),
    'sig': ('pron', '自己（反身代词）'),
    'sin': ('pron', '自己的（通性）'),
    'sitt': ('pron', '自己的（中性）'),
    'sina': ('pron', '自己的（复数）'),
    'men': ('konj', '但是，可是'),
    'vara': ('verb', '是，存在'),
    'bli': ('verb', '成为，变成'),
    'få': ('verb', '得到，收到；可以'),
    'kunna': ('verb', '能够，会'),
    'skola': ('verb', '将要，应该'),
    'vilja': ('verb', '想要，愿意'),
    'måste': ('verb', '必须，一定'),
    'skulle': ('verb', '将会，原本'),
    'kunde': ('verb', '能够，曾会'),
    'ville': ('verb', '曾想，想要'),
    'ha': ('verb', '有，拥有'),
    'här': ('adv', '这里，在这儿'),
    'där': ('adv', '那里，在那儿'),
    'nu': ('adv', '现在，如今'),
    'då': ('adv/konj', '那时，当时；那么'),
    'när': ('adv/konj', '当...时，什么时候'),
    'hur': ('adv', '怎样，如何'),
    'vad': ('pron', '什么'),
    'vem': ('pron', '谁'),
    'var': ('adv', '哪里；曾是'),
    'vart': ('adv', '去哪里'),
    'varför': ('adv', '为什么'),
    'all': ('pron/adj', '所有的，全部（通性）'),
    'allt': ('pron/adj', '一切，全部（中性）'),
    'alla': ('pron/adj', '所有人，所有（复数）'),
    'mycket': ('adv/adj', '非常，许多'),
    'många': ('adj', '许多，很多'),
    'lite': ('adv/adj', '一点，少许'),
    'få': ('adj', '少数的'),
    'mer': ('adj/adv', '更多，更'),
    'mera': ('adj/adv', '更多'),
    'mest': ('adj/adv', '最多，最'),
    'mindre': ('adj/adv', '更少，较小'),
    'minst': ('adj/adv', '最少，最小'),
    'bra': ('adj/adv', '好的，良好'),
    'god': ('adj', '好的，美味的'),
    'gott': ('adj', '好的（中性）'),
    'goda': ('adj', '好的（复数）'),
    'dålig': ('adj', '坏的，差的'),
    'stor': ('adj', '大的'),
    'stort': ('adj', '大的（中性）'),
    'stora': ('adj', '大的（复数）'),
    'liten': ('adj', '小的（通性）'),
    'litet': ('adj', '小的（中性）'),
    'små': ('adj', '小的（复数）'),
    'ung': ('adj', '年轻的'),
    'gammal': ('adj', '老的，古老的'),
    'gamla': ('adj', '老的（复数）'),
    'ny': ('adj', '新的（通性）'),
    'nytt': ('adj', '新的（中性）'),
    'nya': ('adj', '新的（复数）'),
    'lång': ('adj', '长的，高的'),
    'långt': ('adj/adv', '远的，长地'),
    'långa': ('adj', '长的（复数）'),
    'kort': ('adj', '短的，简短的'),
    'korta': ('adj', '短的（复数）'),
    'snabb': ('adj', '快的，迅速的'),
    'snabbt': ('adv', '快速地'),
    'långsam': ('adj', '慢的'),
    'tid': ('subst', '时间'),
    'tiden': ('subst', '时间（定指）'),
    'år': ('subst', '年，岁'),
    'åren': ('subst', '那些年（定指复数）'),
    'dag': ('subst', '白天，天，日'),
    'dagen': ('subst', '白天（定指）'),
    'dagar': ('subst', '天，日子（复数）'),
    'natt': ('subst', '夜晚'),
    'natten': ('subst', '夜晚（定指）'),
    'nätter': ('subst', '夜晚（复数）'),
    'morgon': ('subst', '早晨，上午'),
    'kväll': ('subst', '晚上，傍晚'),
    'kvällen': ('subst', '傍晚（定指）'),
    'människa': ('subst', '人，人类'),
    'människor': ('subst', '人们（复数）'),
    'person': ('subst', '人，个人'),
    'man': ('subst/pron', '男人；泛指“人们”'),
    'kvinna': ('subst', '女人，妇女'),
    'kvinnor': ('subst', '女人们（复数）'),
    'barn': ('subst', '孩子，儿童'),
    'barnet': ('subst', '那个孩子（定指）'),
    'barnen': ('subst', '孩子们（定指复数）'),
    'son': ('subst', '儿子'),
    'sonen': ('subst', '儿子（定指）'),
    'dotter': ('subst', '女儿'),
    'dottern': ('subst', '女儿（定指）'),
    'mor': ('subst', '母亲，妈妈'),
    'modern': ('subst', '母亲（定指）'),
    'far': ('subst', '父亲，爸爸'),
    'fadern': ('subst', '父亲（定指）'),
    'föräldrar': ('subst', '父母（复数）'),
    'bror': ('subst', '兄弟'),
    'syster': ('subst', '姐妹'),
    'vän': ('subst', '朋友'),
    'vännen': ('subst', '朋友（定指）'),
    'vänner': ('subst', '朋友们（复数）'),
    'liv': ('subst', '生命，生活'),
    'livet': ('subst', '生命，生活（定指）'),
    'hem': ('subst/adv', '家；回家'),
    'hemma': ('adv', '在家里'),
    'rum': ('subst', '房间，空间'),
    'rummet': ('subst', '房间（定指）'),
    'hus': ('subst', '房子，房屋'),
    'huset': ('subst', '房子（定指）'),
    'kök': ('subst', '厨房'),
    'köket': ('subst', '厨房（定指）'),
    'bord': ('subst', '桌子'),
    'bordet': ('subst', '桌子（定指）'),
    'stol': ('subst', '椅子'),
    'stolen': ('subst', '椅子（定指）'),
    'stolar': ('subst', '椅子（复数）'),
    'bok': ('subst', '书，书籍'),
    'boken': ('subst', '书（定指）'),
    'böcker': ('subst', '书（复数）'),
    'ord': ('subst', '单词，话语'),
    'ordet': ('subst', '单词，话语（定指）'),
    'svar': ('subst', '答案，回复'),
    'svaret': ('subst', '答案，回复（定指）'),
    'fråga': ('subst/verb', '问题；询问'),
    'frågan': ('subst', '问题（定指）'),
    'frågor': ('subst', '问题（复数）'),
    'ängel': ('subst', '天使'),
    'ängeln': ('subst', '天使（定指）'),
    'änglar': ('subst', '天使们（复数）'),
    'änglarna': ('subst', '天使们（定指复数）'),
    'svara': ('verb', '回答，答复'),
    'svarar': ('verb', '回答（现在式）'),
    'svarade': ('verb', '回答（过去式）'),
    'svarat': ('verb', '回答（完成式）'),
    'fråga': ('verb', '询问，问'),
    'frågar': ('verb', '问（现在式）'),
    'frågade': ('verb', '问（过去式）'),
    'tala': ('verb', '说话，谈论'),
    'talar': ('verb', '说话（现在式）'),
    'talade': ('verb', '说话（过去式）'),
    'prata': ('verb', '聊天，谈话'),
    'pratar': ('verb', '聊天（现在式）'),
    'pratade': ('verb', '聊天（过去式）'),
    'berätta': ('verb', '讲述，告诉'),
    'berättar': ('verb', '讲述（现在式）'),
    'berättade': ('verb', '讲述（过去式）'),
    'lyssna': ('verb', '聆听，听'),
    'lyssnar': ('verb', '聆听（现在式）'),
    'lyssnade': ('verb', '聆听（过去式）'),
    'höra': ('verb', '听见，听到'),
    'hör': ('verb', '听见（现在式）'),
    'hörde': ('verb', '听见（过去式）'),
    'titta': ('verb', '看，注视'),
    'tittar': ('verb', '看（现在式）'),
    'tittade': ('verb', '看（过去式）'),
    'känna': ('verb', '感觉，认识'),
    'känner': ('verb', '感觉（现在式）'),
    'kände': ('verb', '感觉（过去式）'),
    'känsla': ('subst', '感觉，感情'),
    'känslan': ('subst', '感觉（定指）'),
    'känslor': ('subst', '感情，感觉（复数）'),
    'känslorna': ('subst', '感情，感觉（定指复数）'),
    'hår': ('subst', '头发，毛发'),
    'håret': ('subst', '头发（定指）'),
    'hand': ('subst', '手'),
    'handen': ('subst', '手（定指）'),
    'händer': ('subst', '双手（复数）'),
    'öga': ('subst', '眼睛'),
    'ögat': ('subst', '眼睛（定指）'),
    'ögon': ('subst', '眼睛（复数）'),
    'ögonen': ('subst', '眼睛（定指复数）'),
    'ansikte': ('subst', '脸，面孔'),
    'ansiktet': ('subst', '面孔（定指）'),
    'kropp': ('subst', '身体'),
    'kroppen': ('subst', '身体（定指）'),
    'tanke': ('subst', '想法，念头'),
    'tanken': ('subst', '想法（定指）'),
    'tankar': ('subst', '想法，思绪（复数）'),
    'tro': ('verb/subst', '相信，信仰'),
    'hopp': ('subst', '希望'),
    'kärlek': ('subst', '爱，爱情'),
    'kärleken': ('subst', '爱（定指）'),
    'rädsla': ('subst', '害怕，恐惧'),
    'sanning': ('subst', '真相，真理'),
    'sanningen': ('subst', '真相（定指）'),
}

class SwedishDictionary:
    def __init__(self, data_dir='data'):
        self.data_dir = os.path.abspath(data_dir)
        self.cache_file = os.path.join(self.data_dir, 'dict_cache.json')
        self.cache = {}
        self.folkets_words = {}
        self._load_cache()
        self._load_folkets()

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

    def _load_folkets(self):
        folkets_path = os.path.join(self.data_dir, 'folkets_lexikon.json')
        if os.path.exists(folkets_path):
            try:
                with open(folkets_path, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    for item in d.get('words', []):
                        raw_w = item.get('swedish', '').lower()
                        clean_w = raw_w.replace('|', '')
                        if clean_w and clean_w not in self.folkets_words:
                            self.folkets_words[clean_w] = item
            except Exception as e:
                print('Error loading folkets:', e)

    def lemmatize_word(self, word):
        w = word.lower().strip()
        candidates = [w]

        # 1. Check irregular verbs
        if w in IRREGULAR_VERBS:
            lemma, pos, zh = IRREGULAR_VERBS[w]
            candidates.append(lemma)
            return candidates

        # 2. Check genitive -s: "sonens" -> "sonen", "Marcus" -> "Marcus"
        if w.endswith('s') and len(w) > 3 and not w.endswith(('ss', 'as', 'is', 'us', 'os')):
            stem_s = w[:-1]
            candidates.append(stem_s)

        # 3. Definite plural: -arna, -erna, -orna, -na
        for suff in ['arna', 'erna', 'orna', 'ena']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'a', base + 'e'])

        # 4. Definite singular: -en, -et
        for suff in ['en', 'et']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'e', base + 'a'])

        # 5. Plural endings: -ar, -er, -or
        for suff in ['ar', 'er', 'or']:
            if w.endswith(suff) and len(w) > len(suff) + 1:
                base = w[:-len(suff)]
                candidates.extend([base, base + 'a', base + 'e'])

        # 6. Verb past: -ade, -te, -de
        if w.endswith('ade') and len(w) > 4:
            base = w[:-3]
            candidates.extend([base + 'a', base])
        elif (w.endswith('te') or w.endswith('de')) and len(w) > 3:
            base = w[:-2]
            candidates.extend([base + 'a', base])

        # 7. Verb present: -ar, -er
        if w.endswith('ar') and len(w) > 3:
            candidates.append(w[:-2] + 'a')
        elif w.endswith('er') and len(w) > 3:
            candidates.append(w[:-2] + 'a')
            candidates.append(w[:-2])

        # 8. Adjective neuter: -t, plural: -a
        if w.endswith('t') and len(w) > 3:
            candidates.append(w[:-1])
        if w.endswith('a') and len(w) > 3:
            candidates.append(w[:-1])

        # deduplicate while preserving order
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

        # Check cache first
        if clean_word in self.cache:
            return self.cache[clean_word]

        # Multi-word sentence or phrase
        if ' ' in clean_word or len(clean_word.split()) > 1:
            tr = self._translate_online(clean_word)
            res = {
                'query': query,
                'word': clean_word,
                'lemma': clean_word,
                'pos': '短语/句子',
                'phonetic': '',
                'audioUrl': '',
                'zh': tr or '（无释义）',
                'en': ''
            }
            if tr:
                self.cache[clean_word] = res
                self._save_cache()
            return res

        # Single word lookup
        candidates = self.lemmatize_word(clean_word)

        # 1. Check irregular verbs
        if clean_word in IRREGULAR_VERBS:
            lemma, pos, zh = IRREGULAR_VERBS[clean_word]
            folk = self.folkets_words.get(lemma, {}) or self.folkets_words.get(clean_word, {})
            res = {
                'query': query,
                'word': clean_word,
                'lemma': lemma,
                'pos': pos,
                'phonetic': folk.get('phonetic', ''),
                'audioUrl': folk.get('audioUrl', ''),
                'zh': zh,
                'en': folk.get('english', '')
            }
            self.cache[clean_word] = res
            self._save_cache()
            return res

        # 2. Check CORE_VOCAB for word or any candidate lemma
        for cand in candidates:
            if cand in CORE_VOCAB:
                pos, zh = CORE_VOCAB[cand]
                folk = self.folkets_words.get(cand, {}) or self.folkets_words.get(clean_word, {})
                res = {
                    'query': query,
                    'word': clean_word,
                    'lemma': cand if cand != clean_word else '',
                    'pos': pos,
                    'phonetic': folk.get('phonetic', ''),
                    'audioUrl': folk.get('audioUrl', ''),
                    'zh': zh,
                    'en': folk.get('english', '')
                }
                self.cache[clean_word] = res
                self._save_cache()
                return res

        # 3. Check Folkets Lexikon
        folk = None
        hit_lemma = clean_word
        for cand in candidates:
            if cand in self.folkets_words:
                folk = self.folkets_words[cand]
                hit_lemma = cand
                break

        # 4. If we have Folkets entry, or if we need online translation
        online_zh = self._translate_online(clean_word)
        if not online_zh and hit_lemma != clean_word:
            online_zh = self._translate_online(hit_lemma)

        en_def = folk.get('english', '') if folk else ''
        phonetic = folk.get('phonetic', '') if folk else ''
        audio_url = folk.get('audioUrl', '') if folk else ''

        zh_def = online_zh or en_def or '未找到释义'

        res = {
            'query': query,
            'word': clean_word,
            'lemma': hit_lemma if hit_lemma != clean_word else '',
            'pos': folk.get('category', '单词') if folk else '单词',
            'phonetic': phonetic,
            'audioUrl': audio_url,
            'zh': zh_def,
            'en': en_def
        }

        self.cache[clean_word] = res
        self._save_cache()
        return res

    def _translate_online(self, text):
        # 1. MyMemory translator
        try:
            url = f'https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=sv|zh-CN'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                tr = data.get('responseData', {}).get('translatedText', '')
                # Filter out MyMemory error strings
                if tr and 'MYMEMORY WARNING' not in tr and 'QUERY LENGTH' not in tr:
                    return tr
        except Exception:
            pass
        return None

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    d = SwedishDictionary()
    test_words = ['svarade', 'stolen', 'känslor', 'håret', 'mindes', 'Marcus betraktade sonen']
    for tw in test_words:
        res = d.lookup(tw)
        print(f"[{tw}] -> {res['word']} (lemma: {res['lemma']}) | ZH: {res['zh']} | EN: {res['en']} | PHONETIC: {res['phonetic']}")
