import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# High-priority manual overrides for common words to ensure utmost naturalness
HIGH_PRIORITY_ZH = {
    'vara': 'v. 是，存在，在',
    'är': 'v. 是，存在（现在式）',
    'var': 'v. 曾是，在（过去式）；adv. 哪里',
    'varit': 'v. 是，在（完成式）',
    'ha': 'v. 有，拥有',
    'har': 'v. 有，拥有（现在式）',
    'hade': 'v. 有，拥有（过去式）',
    'haft': 'v. 有，拥有（完成式）',
    'bli': 'v. 成为，变成，变得',
    'blir': 'v. 成为，变成（现在式）',
    'blev': 'v. 成为，变成（过去式）',
    'blivit': 'v. 成为，变成（完成式）',
    'få': 'v. 得到，获得；可以，允许',
    'får': 'v. 得到，可以（现在式）',
    'fick': 'v. 得到，可以（过去式）',
    'fått': 'v. 得到，可以（完成式）',
    'kunna': 'v. 能，能够，会',
    'kan': 'v. 能，可以，会（现在式）',
    'kunde': 'v. 能，可以，会（过去式）',
    'kunnat': 'v. 能，可以，会（完成式）',
    'vilja': 'v. 想要，愿意',
    'vill': 'v. 想要，愿意（现在式）',
    'ville': 'v. 想要，愿意（过去式）',
    'velat': 'v. 想要，愿意（完成式）',
    'skola': 'v. 将要，应当',
    'ska': 'v. 将要，应该（现在式）',
    'skulle': 'v. 将要，本想（过去式）',
    'måste': 'v. 必须，一定',
    'böra': 'v. 应当，应该',
    'bör': 'v. 应当，应该（现在式）',
    'borde': 'v. 应当，应该（过去式）',
    'säga': 'v. 说，讲',
    'säger': 'v. 说（现在式）',
    'sa': 'v. 说（过去式）',
    'sade': 'v. 说（过去式）',
    'sagt': 'v. 说（完成式）',
    'se': 'v. 看，看见',
    'ser': 'v. 看，看见（现在式）',
    'såg': 'v. 看，看见（过去式）',
    'sett': 'v. 看，看见（完成式）',
    'gå': 'v. 走，去，行走',
    'går': 'v. 走，去（现在式）',
    'gick': 'v. 走，去（过去式）',
    'gått': 'v. 走，去（完成式）',
    'komma': 'v. 来，到达',
    'kommer': 'v. 来，到达（现在式）',
    'kom': 'v. 来，到达（过去式）',
    'kommit': 'v. 来，到达（完成式）',
    'ta': 'v. 拿，取，带走，采取',
    'tar': 'v. 拿，取（现在式）',
    'tog': 'v. 拿，取（过去式）',
    'tagit': 'v. 拿，取（完成式）',
    'ge': 'v. 给，给予',
    'ger': 'v. 给，给予（现在式）',
    'gav': 'v. 给，给予（过去式）',
    'gett': 'v. 给，给予（完成式）',
    'givit': 'v. 给，给予（完成式）',
    'veta': 'v. 知道，了解',
    'vet': 'v. 知道，了解（现在式）',
    'visste': 'v. 知道，了解（过去式）',
    'vetat': 'v. 知道，了解（完成式）',
    'tro': 'v. 相信，认为，以为',
    'tror': 'v. 相信，认为（现在式）',
    'trodde': 'v. 相信，认为（过去式）',
    'trott': 'v. 相信，认为（完成式）',
    'tycka': 'v. 觉得，认为',
    'tycker': 'v. 觉得，认为（现在式）',
    'tyckte': 'v. 觉得，认为（过去式）',
    'tyckt': 'v. 觉得，认为（完成式）',
    'tänka': 'v. 想，思考，打算',
    'tänker': 'v. 想，思考（现在式）',
    'tänkte': 'v. 想，思考（过去式）',
    'tänkt': 'v. 想，思考（完成式）',
    'känna': 'v. 感觉，认识，感到',
    'känner': 'v. 感觉，感到（现在式）',
    'kände': 'v. 感觉，感到（过去式）',
    'känt': 'v. 感觉，感到（完成式）',
    'sitta': 'v. 坐，位于',
    'sitter': 'v. 坐（现在式）',
    'satt': 'v. 坐（过去式）',
    'suttit': 'v. 坐（完成式）',
    'stå': 'v. 站，站立，位于',
    'står': 'v. 站立（现在式）',
    'stod': 'v. 站立（过去式）',
    'stått': 'v. 站立（完成式）',
    'ligga': 'v. 躺，位于',
    'ligger': 'v. 躺，位于（现在式）',
    'låg': 'v. 躺，位于（过去式）',
    'legat': 'v. 躺，位于（完成式）',
    'minnas': 'v. 记得，回忆起',
    'minns': 'v. 记得，回忆起（现在式）',
    'mindes': 'v. 记得，回忆起（过去式）',
    'svara': 'v. 回答，答复，回应',
    'svarar': 'v. 回答，答复（现在式）',
    'svarade': 'v. 回答，答复（过去式）',
    'svarat': 'v. 回答，答复（完成式）',
    'fråga': 'v. 问，询问；n. 问题',
    'frågar': 'v. 询问（现在式）',
    'frågade': 'v. 询问（过去式）',
    'frågat': 'v. 询问（完成式）',
    'tala': 'v. 说话，谈论',
    'prata': 'v. 聊天，谈话',
    'berätta': 'v. 讲述，告诉',
    'lyssna': 'v. 倾听，听',
    'höra': 'v. 听见，听到',
    'hör': 'v. 听见（现在式）',
    'hörde': 'v. 听见（过去式）',
    'hört': 'v. 听见（完成式）',
    'titta': 'v. 看，注视',
    'hålla': 'v. 握住，保持，举行',
    'håller': 'v. 握住，保持（现在式）',
    'höll': 'v. 握住，保持（过去式）',
    'hållit': 'v. 握住，保持（完成式）',
    'låta': 'v. 让，使；听起来',
    'låter': 'v. 让，听起来（现在式）',
    'lät': 'v. 让，听起来（过去式）',
    'låtit': 'v. 让，听起来（完成式）',
    'äta': 'v. 吃',
    'dricka': 'v. 喝',
    'sova': 'v. 睡觉',
    'bo': 'v. 居住，住',
    'leva': 'v. 活着，生活',
    'dö': 'v. 死亡，死',
    'förstå': 'v. 理解，明白',
    'börja': 'v. 开始',
    'sluta': 'v. 结束，停止',
    'fortsätta': 'v. 继续',
    'hjälpa': 'v. 帮助',
    'behöva': 'v. 需要',
    'älska': 'v. 爱，热爱',
    'hoppas': 'v. 希望',
    'skriva': 'v. 写，写作',
    'läsa': 'v. 读，阅读，学习',
    'köpa': 'v. 购买，买',
    'sälja': 'v. 卖，出售',
    'öppna': 'v. 打开',
    'stänga': 'v. 关闭，关上',

    # Common nouns
    'stol': 'n. 椅子',
    'stolen': 'n. 椅子（定指）',
    'stolar': 'n. 椅子（复数）',
    'stolarna': 'n. 椅子（定指复数）',
    'bord': 'n. 桌子',
    'bordet': 'n. 桌子（定指）',
    'kök': 'n. 厨房',
    'köket': 'n. 厨房（定指）',
    'rum': 'n. 房间，空间',
    'rummet': 'n. 房间（定指）',
    'hus': 'n. 房子，房屋',
    'huset': 'n. 房子（定指）',
    'hem': 'n. 家；adv. 回家',
    'hemma': 'adv. 在家',
    'bok': 'n. 书，书籍',
    'boken': 'n. 书籍（定指）',
    'böcker': 'n. 书籍（复数）',
    'ord': 'n. 单词，词，言语',
    'svar': 'n. 答案，回复',
    'svaret': 'n. 答案，回复（定指）',
    'svaren': 'n. 答案（定指复数）',
    'fråga': 'n. 问题；v. 问',
    'frågan': 'n. 问题（定指）',
    'frågor': 'n. 问题（复数）',
    'ängel': 'n. 天使',
    'ängeln': 'n. 天使（定指）',
    'änglar': 'n. 天使（复数）',
    'änglarna': 'n. 天使们（定指复数）',
    'son': 'n. 儿子',
    'sonen': 'n. 儿子（定指）',
    'dotter': 'n. 女儿',
    'dottern': 'n. 女儿（定指）',
    'mor': 'n. 母亲，妈妈',
    'modern': 'n. 母亲（定指）',
    'far': 'n. 父亲，爸爸',
    'fadern': 'n. 父亲（定指）',
    'bror': 'n. 兄弟',
    'syster': 'n. 姐妹',
    'barn': 'n. 孩子，儿童',
    'barnet': 'n. 孩子（定指）',
    'barnen': 'n. 孩子们（定指复数）',
    'vän': 'n. 朋友',
    'vännen': 'n. 朋友（定指）',
    'vänner': 'n. 朋友们（复数）',
    'man': 'n. 男人，丈夫；pron. 人们',
    'kvinna': 'n. 女人，妇女',
    'kvinnan': 'n. 女人（定指）',
    'kvinnor': 'n. 女人们（复数）',
    'människa': 'n. 人，人类',
    'människor': 'n. 人们（复数）',
    'person': 'n. 人，个人',
    'hår': 'n. 头发，毛发',
    'håret': 'n. 头发（定指）',
    'öga': 'n. 眼睛',
    'ögat': 'n. 眼睛（定指）',
    'ögon': 'n. 眼睛（复数）',
    'ögonen': 'n. 眼睛（定指复数）',
    'hand': 'n. 手',
    'handen': 'n. 手（定指）',
    'händer': 'n. 双手（复数）',
    'ansikte': 'n. 面孔，脸',
    'ansiktet': 'n. 面孔（定指）',
    'kropp': 'n. 身体',
    'kroppen': 'n. 身体（定指）',
    'hjärta': 'n. 心脏，心灵',
    'hjärtat': 'n. 心灵（定指）',
    'själ': 'n. 灵魂',
    'själen': 'n. 灵魂（定指）',
    'liv': 'n. 生命，生活',
    'livet': 'n. 生命，生活（定指）',
    'död': 'n. 死亡',
    'döden': 'n. 死亡（定指）',
    'tid': 'n. 时间',
    'tiden': 'n. 时间（定指）',
    'år': 'n. 年，岁',
    'åren': 'n. 岁月，那些年（定指复数）',
    'dag': 'n. 天，白天',
    'dagen': 'n. 白天（定指）',
    'dagar': 'n. 日子（复数）',
    'natt': 'n. 夜晚',
    'natten': 'n. 夜晚（定指）',
    'morgon': 'n. 早晨，上午',
    'kväll': 'n. 傍晚，晚上',
    'kvällen': 'n. 傍晚（定指）',
    'känsla': 'n. 感觉，情绪，感情',
    'känslan': 'n. 感觉（定指）',
    'känslor': 'n. 感情，情绪（复数）',
    'känslorna': 'n. 情绪，情感（定指复数）',
    'tanke': 'n. 想法，念头，思想',
    'tanken': 'n. 想法（定指）',
    'tankar': 'n. 想法，思绪（复数）',
    'tröja': 'n. 毛衣，运动衫',
    'tröjan': 'n. 毛衣（定指）',
    'jeans': 'n. 牛仔裤',
    'sko': 'n. 鞋子',
    'skor': 'n. 鞋（复数）',
    'skorna': 'n. 鞋子（定指复数）',
    'kläder': 'n. 衣服，服装（复数）',

    # Common adjectives
    'stor': 'adj. 大的',
    'stort': 'adj. 大的（中性）',
    'stora': 'adj. 大的（复数/定指）',
    'liten': 'adj. 小的',
    'litet': 'adj. 小的（中性）',
    'små': 'adj. 小的（复数）',
    'bra': 'adj./adv. 好的，良好',
    'dålig': 'adj. 坏的，差的',
    'god': 'adj. 好的，美味的',
    'gott': 'adj. 好的（中性）',
    'goda': 'adj. 好的（复数）',
    'ond': 'adj. 邪恶的，痛苦的',
    'ny': 'adj. 新的',
    'nytt': 'adj. 新的（中性）',
    'nya': 'adj. 新的（复数）',
    'gammal': 'adj. 老的，古老的',
    'gammalt': 'adj. 老的（中性）',
    'gamla': 'adj. 老的（复数）',
    'ung': 'adj. 年轻的',
    'unga': 'adj. 年轻的（复数）',
    'lång': 'adj. 长的，高的',
    'långt': 'adj./adv. 长的；远地',
    'långa': 'adj. 长的（复数）',
    'kort': 'adj. 短的，简短的',
    'snabb': 'adj. 快速的',
    'snabbt': 'adv. 快速地',
    'långsam': 'adj. 缓慢的',
    'mörk': 'adj. 黑暗的，深色的',
    'mörkt': 'adj. 黑暗的（中性）',
    'mörka': 'adj. 黑暗的（复数）',
    'mörkare': 'adj. 更暗的，更深的（比较级）',
    'ljus': 'adj. 明亮的，浅色的；n. 光',
    'ljust': 'adj. 明亮的（中性）',
    'ljusa': 'adj. 明亮的（复数）',
    'vit': 'adj. 白色的',
    'vitt': 'adj. 白色的（中性）',
    'vita': 'adj. 白色的（复数）',
    'svart': 'adj. 黑色的',
    'svarta': 'adj. 黑色的（复数）',
    'röd': 'adj. 红色的',
    'blå': 'adj. 蓝色的',
    'grön': 'adj. 绿色的',
    'gul': 'adj. 黄色的',
    'smutsig': 'adj. 脏的，污秽的',
    'smutsigt': 'adj. 脏的（中性）',
    'smutsiga': 'adj. 脏的（复数）',
    'ren': 'adj. 干净的，纯洁的',
    'tovig': 'adj. 纠结的，乱蓬蓬的',
    'tovigt': 'adj. 乱蓬蓬的（中性）',
    'toviga': 'adj. 缠结的，蓬乱的（复数/定指）',
    'svår': 'adj. 困难的，严重的',
    'svårt': 'adj./adv. 困难地，沉重地',
    'lätt': 'adj. 容易的，轻的',
    'vacker': 'adj. 美丽的，漂亮的',
    'vackert': 'adj. 美丽的（中性）',
    'vackra': 'adj. 美丽的（复数）',
    'tacksam': 'adj. 感激的，感恩的',
    'tacksamt': 'adj. 感恩的（中性）',
    'tacksamma': 'adj. 感激的（复数）',
    'viktig': 'adj. 重要的',
    'viktigt': 'adj. 重要的（中性）',
    'viktiga': 'adj. 重要的（复数）',
    'sann': 'adj. 真实的，正确的',
    'sant': 'adj. 真的（中性）',
    'sanna': 'adj. 真实的（复数）',
    'ensam': 'adj. 孤独的，独自一人的',
    'ensamma': 'adj. 孤独的（复数）',
    'glad': 'adj. 高兴的，愉快的',
    'glada': 'adj. 高兴的（复数）',
    'ledsen': 'adj. 伤心的，难过的',
    'trött': 'adj. 疲劳的，累的',
    'hungrig': 'adj. 饥饿的',
    'törstig': 'adj. 口渴的',
    'sjuk': 'adj. 生病的',
    'frisk': 'adj. 健康的，新鲜的',

    # Function words
    'och': 'conj. 和，以及',
    'i': 'prep. 在...里面，在...中',
    'att': 'conj./inf. 引导从句；不定式标志“去...”',
    'en': 'art. 一个（通性冠词）',
    'ett': 'art. 一个（中性冠词）',
    'den': 'pron./art. 这，那；通性定冠词',
    'det': 'pron./art. 它，这，那；中性定冠词',
    'de': 'pron./art. 他们，那些；复数定冠词',
    'dem': 'pron. 他们（宾格）',
    'som': 'pron./conj. 正如，作为；关系代词“所...的”',
    'på': 'prep. 在...上面，在...上',
    'av': 'prep. 由...，从...，关于',
    'för': 'prep./conj. 为了；因为；对于',
    'med': 'prep. 和...一起，用，随着',
    'till': 'prep. 到...，向...，给',
    'om': 'prep./conj. 关于；如果，是否',
    'inte': 'adv. 不，没有',
    'så': 'adv./conj. 如此，这样；那么',
    'denna': 'pron. 这个（通性）',
    'detta': 'pron. 这个（中性）',
    'dessa': 'pron. 这些（复数）',
    'han': 'pron. 他',
    'honom': 'pron. 他（宾格）',
    'hans': 'pron. 他的',
    'hon': 'pron. 她',
    'henne': 'pron. 她（宾格）',
    'hennes': 'pron. 她的',
    'jag': 'pron. 我',
    'mig': 'pron. 我（宾格）',
    'min': 'pron. 我的（通性）',
    'mitt': 'pron. 我的（中性）',
    'mina': 'pron. 我的（复数）',
    'du': 'pron. 你',
    'dig': 'pron. 你（宾格）',
    'din': 'pron. 你的（通性）',
    'ditt': 'pron. 你的（中性）',
    'dina': 'pron. 你的（复数）',
    'vi': 'pron. 我们',
    'oss': 'pron. 我们（宾格）',
    'vår': 'pron. 我们的（通性）',
    'vårt': 'pron. 我们的（中性）',
    'våra': 'pron. 我们的（复数）',
    'ni': 'pron. 你们',
    'er': 'pron. 你们（宾格）；你们的',
    'ert': 'pron. 你们的（中性）',
    'era': 'pron. 你们的（复数）',
    'sig': 'pron. 自己（第三人称反身代词）',
    'sin': 'pron. 自己的（通性）',
    'sitt': 'pron. 自己的（中性）',
    'sina': 'pron. 自己的（复数）',
    'men': 'conj. 但是，可是',
    'eller': 'conj. 或者',
    'här': 'adv. 这里，在这儿',
    'där': 'adv. 那里，在那儿',
    'nu': 'adv. 现在，如今',
    'då': 'adv./conj. 那时，当时；那么',
    'när': 'adv./conj. 当...时，什么时候',
    'hur': 'adv. 怎样，如何',
    'vad': 'pron. 什么',
    'vem': 'pron. 谁',
    'varför': 'adv. 为什么',
    'mycket': 'adv./adj. 非常，许多',
    'många': 'adj. 许多，很多',
    'lite': 'adv./adj. 一点，少许',
    'mer': 'adj./adv. 更多，更',
    'mera': 'adj./adv. 更多',
    'mest': 'adj./adv. 最多，最',
    'mindre': 'adj./adv. 更少，较小',
    'minst': 'adj./adv. 最少，最小',
    'alltid': 'adv. 总是，一直',
    'aldrig': 'adv. 从不，决不',
    'ofta': 'adv. 经常，常常',
    'ibland': 'adv. 有时，偶尔',
    'kanske': 'adv. 也许，可能',
    'redan': 'adv. 已经',
    'ännu': 'adv. 仍然，还',
    'bara': 'adv. 仅仅，只',
    'också': 'adv. 也，同样',
    'heller': 'adv. 也不（用于否定句）',
    'nästan': 'adv. 几乎，差不多',
    'gärna': 'adv. 乐意地，欣然',
    'hellre': 'adv. 宁可，宁愿',
    'helst': 'adv. 最愿意，最好',
    'fram': 'adv. 向前，出来',
    'framför': 'prep. 在...前面',
    'bakom': 'prep. 在...后面',
    'under': 'prep. 在...下面；在...期间',
    'över': 'prep. 在...上方；超过',
    'mellan': 'prep. 在...之间',
    'genom': 'prep. 穿过，通过',
    'mot': 'prep. 朝着；反对，对抗',
    'hos': 'prep. 在...处，在...家',
    'vid': 'prep. 在...旁，在...时',
    'efter': 'prep. 在...之后',
    'före': 'prep. 在...之前',
    'sedan': 'adv./prep. 自从，然后',
    'utan': 'prep./conj. 没有；而是',
}

def clean_ecdict_translation(raw_tr):
    if not raw_tr:
        return ''
    # remove tech jargons like [计] xxx, [医] xxx
    lines = raw_tr.split('\\n')
    cleaned_lines = []
    for l in lines:
        l = l.strip()
        if not l or l.startswith('[') and l.endswith(']'):
            continue
        # remove bracketed jargon at start
        l = re.sub(r'\[[^\]]+\]\s*', '', l)
        cleaned_lines.append(l)
    return '； '.join(cleaned_lines)

def build_sv_zh():
    print("Loading ECDICT...")
    en_to_zh = {}
    with open('data/ecdict.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = row['word'].lower()
            en_to_zh[w] = clean_ecdict_translation(row['translation'])

    print(f"Loaded {len(en_to_zh)} English words.")

    print("Loading Folkets Lexikon...")
    with open('data/folkets_lexikon.json', 'r', encoding='utf-8') as f:
        folk = json.load(f)

    sv_dict = {}

    # 1. Add all manual high-priority words
    for k, v in HIGH_PRIORITY_ZH.items():
        sv_dict[k] = {
            'zh': v,
            'pos': v.split('.')[0] if '.' in v else '',
            'en': '',
            'phonetic': '',
            'audioUrl': ''
        }

    # 2. Process all Folkets words
    matches = 0
    for item in folk.get('words', []):
        raw_sv = item.get('swedish', '').lower()
        clean_sv = raw_sv.replace('|', '').strip()
        if not clean_sv:
            continue

        phonetic = item.get('phonetic', '')
        audio_url = item.get('audioUrl', '')
        pos = item.get('category', '')
        eng_raw = item.get('english', '').strip()

        # If already in HIGH_PRIORITY_ZH, attach phonetic and english
        if clean_sv in sv_dict:
            if phonetic and not sv_dict[clean_sv]['phonetic']:
                sv_dict[clean_sv]['phonetic'] = phonetic
            if audio_url and not sv_dict[clean_sv]['audioUrl']:
                sv_dict[clean_sv]['audioUrl'] = audio_url
            if eng_raw and not sv_dict[clean_sv]['en']:
                sv_dict[clean_sv]['en'] = eng_raw
            continue

        # Look up English definition in ECDICT
        zh_translations = []
        tokens = re.split(r'[,;/]\s*', eng_raw.lower())
        for tok in tokens:
            tok = re.sub(r'^\s*to\s+', '', tok).strip()
            if tok in en_to_zh and en_to_zh[tok]:
                zh_translations.append(en_to_zh[tok])
                break

        final_zh = ''
        if zh_translations:
            final_zh = zh_translations[0]
            matches += 1
        elif eng_raw:
            # Fallback to English only if no translation found, but marked clearly
            final_zh = f"（暂无中文，英文释义：{eng_raw}）"

        sv_dict[clean_sv] = {
            'zh': final_zh,
            'pos': pos,
            'en': eng_raw,
            'phonetic': phonetic,
            'audioUrl': audio_url
        }

    print(f"Matched {matches} Folkets words to Chinese definitions.")
    print(f"Total Swedish dictionary entries: {len(sv_dict)}")

    out_file = 'data/sv_zh_dict.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(sv_dict, f, ensure_ascii=False, indent=2)

    print(f"Saved to {out_file} (Size: {os.path.getsize(out_file)} bytes)")

    # Clean up ecdict.csv to save disk space
    if os.path.exists('data/ecdict.csv'):
        os.remove('data/ecdict.csv')
        print("Cleaned up temporary ecdict.csv")

if __name__ == '__main__':
    build_sv_zh()
