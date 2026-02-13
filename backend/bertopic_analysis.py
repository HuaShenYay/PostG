import os
import jieba
import pandas as pd
BERTopic = None
CountVectorizer = None
SentenceTransformer = None
util = None
torch = None

def _lazy_load_bertopic():
    global BERTopic, CountVectorizer
    if BERTopic is None:
        from bertopic import BERTopic as _BERTopic
        from sklearn.feature_extraction.text import CountVectorizer as _CountVectorizer
        BERTopic = _BERTopic
        CountVectorizer = _CountVectorizer

def _lazy_load_sentence_transformers():
    global SentenceTransformer, util, torch
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as _SentenceTransformer, util as _util
        import torch as _torch
        SentenceTransformer = _SentenceTransformer
        util = _util
        torch = _torch
import csv
import codecs

# 配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'saved_models', 'bertopic_model')
STOPWORDS_FILE = os.path.join(BASE_DIR, '..', 'data', 'scu_stopwords.txt')
POETRY_STOPWORDS_FILE = os.path.join(BASE_DIR, '..', 'data', 'poetry_stopwords.txt')
EMOTION_LEXICON_FILE = os.path.join(BASE_DIR, '..', 'data', 'emotion_lexicon.csv')
DICT_CSV_FILE = os.path.join(BASE_DIR, '..', 'data', 'dict.csv')

# 核心停用词库 (避免显示 "是-不-在-的")
DEFAULT_STOPWORDS = {
    '的', '了', '和', '是', '不', '在', '之', '于', '也', '与', '而', '则', '其', '为', '以',
    '到', '从', '就', '并', '且', '又', '或', '都', '即', '此', '彼', '若', '如', '但', '即便',
    '虽然', '但是', '可是', '然而', '所以', '因此', '因为', '于是', '既然', '那么', '如何',
    '什么', '哪个', '谁', '哪里', '怎么', '如此', '极其', '非常', '特别', '更加', '再', '更',
    '还', '已经', '将', '要', '向', '对', '把', '被', '让', '使', '给', '由', '由于', '因',
    '为了', '关于', '对于', '哪怕', '哪怕是', '即便如此', '个', '位', '只', '支', '头', '面'
}

# 全局停用词缓存
_cached_stopwords = None
_cached_emotion_lexicon = None
_cached_dict_csv_lexicon = None

def load_stopwords():
    """加载停用词，合并文件与硬编码库 (带缓存)"""
    global _cached_stopwords
    if _cached_stopwords is not None:
        return _cached_stopwords
        
    stopwords = set(DEFAULT_STOPWORDS)
    
    def read_file(filepath):
        encodings = ['utf-8', 'gbk'] # 优先 utf-8
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return [line.strip() for line in f]
            except (UnicodeDecodeError, Exception):
                continue
        return []

    if os.path.exists(STOPWORDS_FILE):
        stopwords.update(read_file(STOPWORDS_FILE))
    
    if os.path.exists(POETRY_STOPWORDS_FILE):
        for line in read_file(POETRY_STOPWORDS_FILE):
            line = line.strip()
            if line and not line.startswith('#'):
                stopwords.add(line)
                    
    # Hardcoded extras for ancient poetry context
    extra = {'千里', '万里', '不知', '不得', '不可', '何处', '一个', '如此', '便是'}
    _cached_stopwords = list(stopwords.union(extra))
    return _cached_stopwords

import re
import jieba.analyse

def tokenize_zh(text):
    """Jieba tokenizer with robust filtering"""
    # 1. Regex to keep only Chinese
    chinese_only = re.sub(r'[^\u4e00-\u9fa5]', '', text)
    if not chinese_only:
        return []
    
    # 2. Tokenize and filter single-char particles and stopwords
    words = jieba.lcut(chinese_only)
    stopwords = load_stopwords()
    
    # Keep words that are: 1) Not in stopwords 2) Length > 1
    # This prevents "的", "不" even if stopword file is incomplete
    return [w for w in words if w not in stopwords and len(w) > 1]

class RealTopicGenerator:
    """模拟用户评论主题生成器"""
    
    FAMOUS_AUTHORS = {
        '李白', '杜甫', '白居易', '苏轼', '王维', '李商隐', '杜牧', '孟浩然', '李清照', 
        '辛弃疾', '陆游', '王昌龄', '王之涣', '刘禹锡', '柳宗元', '欧阳修', '范仲淹',
        '曹操', '陶渊明', '屈原'
    }

    THEME_MAPPING = {
        "思乡": ["月", "故乡", "乡", "家", "梦", "书", "信", "归", "客", "旅", "愁", "亲"],
        "爱情": ["相思", "红豆", "眉", "心", "情", "爱", "恋", "君", "伊", "鸳鸯", "同心"],
        "边塞": ["烽火", "沙场", "剑", "弓", "马", "塞", "边", "旗", "鼓", "征", "战", "雪", "关"],
        "山水": ["山", "水", "云", "林", "松", "竹", "江", "湖", "月", "风", "花", "鸟", "田园", "隐"],
        "离别": ["送", "别", "离", "去", "酒", "柳", "亭", "舟", "帆", "路", "远"],
        "怀古": ["古", "今", "昔", "旧", "兴", "亡", "宫", "台", "陵", "史", "名", "利"],
        "壮志": ["志", "气", "剑", "胆", "豪", "杰", "雄", "功", "业", "国", "天"],
        "悲秋": ["秋", "落", "叶", "风", "霜", "寒", "凉", "萧", "瑟", "残"]
    }

    EMOTION_TAGS = {
        "joy": ["欢快", "愉悦", "美好", "治愈"],
        "anger": ["愤怒", "激昂", "热血", "不平"],
        "sorrow": ["感人", "悲伤", "心碎", "破防", "意难平"],
        "fear": ["紧张", "压抑", "惊悚"],
        "love": ["深情", "浪漫", "唯美"],
        "zen": ["宁静", "淡泊", "超脱", "治愈"]
    }

    @classmethod
    def generate(cls, text, author=None):
        """生成模拟评论标签 (格式: 核心主题,情感评价,关键意象)"""
        if not text:
            return "未知"
            
        tags = []
        
        # 1. 核心主题 (基于关键词匹配)
        text_set = set(jieba.cut(text))
        theme_scores = {k: 0 for k in cls.THEME_MAPPING}
        
        for theme, keywords in cls.THEME_MAPPING.items():
            for kw in keywords:
                if kw in text_set:
                    theme_scores[theme] += 1
        
        best_theme = max(theme_scores.items(), key=lambda x: x[1])
        if best_theme[1] > 0:
            tags.append(best_theme[0])
            
        # 2. 情感评价 (基于情感分析)
        emotions = get_poem_emotions(text) # Returns dict with scores 0-10
        
        # 特殊规则：王维/孟浩然 优先禅意
        if author in {'王维', '孟浩然', '王梵志', '寒山'}:
            emotions['zen'] += 3.0
            
        # 找出显著的情感 (score > 4)
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        top_emo, score = sorted_emotions[0]
        
        if score >= 4:
            import random
            # 从对应情感标签中随机选一个，增加多样性
            emo_tag = random.choice(cls.EMOTION_TAGS.get(top_emo, ["感人"]))
            if emo_tag not in tags:
                tags.append(emo_tag)

        # 3. 关键意象 (使用 TF-IDF)
        keywords = jieba.analyse.extract_tags(text, topK=3)
        for kw in keywords:
            if len(kw) > 1 and kw not in tags: # 避免单字和重复
                tags.append(kw)
                
        # 4. 作者/经典标签
        if author and author in cls.FAMOUS_AUTHORS:
            tags.append("经典")
            tags.append("必背")
        
        # 5. 补充通用标签
        if not tags:
            tags.append("诗歌")
            
        # 去重并保持顺序
        seen = set()
        final_tags = []
        for t in tags:
            if t not in seen:
                final_tags.append(t)
                seen.add(t)
                
        return ",".join(final_tags[:5]) # 最多返回5个标签

def generate_real_topic(text, author=None):
    """(兼容接口) 生成真实主题"""
    return RealTopicGenerator.generate(text, author)

def get_individual_keywords(text, top_k=4):
    """单独针对单首诗歌提取关键词"""
    if not text:
        return "未知"
    keywords = jieba.analyse.extract_tags(text, topK=top_k)
    return "-".join(keywords) if keywords else "未分类"

def get_poem_imagery(text, top_k=20):
    """提取诗歌意象关键词 (带权重)"""
    if not text:
        return []
    
    # 使用 TF-IDF 提取带权重的关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
    
    # 格式化为 [{name: word, value: weight}, ...]
    result = [{"name": k, "value": int(w * 100)} for k, w in keywords]
    return result

# 全局语义颜色分析器实例
_semantic_color_analyzer = None

class SemanticColorAnalyzer:
    """基于语义嵌入的颜色分析器 (轻量级/高性能)"""
    def __init__(self):
        try:
            _lazy_load_sentence_transformers()
            # 复用 BERT 模型 (paraphrase-multilingual-MiniLM-L12-v2)
            # 这是一个非常轻量且效果好的多语言模型
            self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        except Exception as e:
            print(f"[ColorAnalyzer] Error loading model: {e}")
            self.model = None
            return

        # 定义丰富的语义颜色映射 (中国传统色 + 意象/情感词)
        self.color_profiles = {
            '#FF2121': ['热烈', '红色', '火焰', '愤怒', '喜庆', '朱砂', '血', '丹心', '红豆', '相思', '燃烧'], # 丹红
            '#FFB11B': ['光明', '黄色', '皇权', '黄金', '收获', '阳光', '菊花', '富贵', '辉煌', '温暖'], # 帝释黄
            '#177CB0': ['宁静', '蓝色', '天空', '大海', '寒冷', '宽广', '哀愁', '泪', '清澈', '深邃', '碧空'], # 靛蓝
            '#45B787': ['生机', '绿色', '春天', '希望', '自然', '森林', '竹林', '柳树', '新生', '清新'], # 竹青
            '#E9E7EF': ['纯洁', '白色', '雪', '空灵', '孤独', '月光', '霜', '素雅', '缟素', '虚无'], # 鱼肚白 (偏冷)
            '#131124': ['压抑', '黑色', '夜晚', '死亡', '神秘', '深渊', '乌鸦', '沉重', '绝望', '阴暗'], # 墨色
            '#8D4BBB': ['高贵', '紫色', '梦幻', '紫罗兰', '紫烟', '神秘', '优雅', '仙气', '华丽'], # 葡萄紫
            '#F07C82': ['浪漫', '粉色', '爱情', '花朵', '桃花', '温柔', '晚霞', '少女', '春心'], # 盈盈粉
            '#88ADA6': ['平淡', '青色', '水墨', '烟雨', '江南', '雅致', '悠远', '古朴', '淡泊'], # 游鞠色
            '#5D4037': ['稳重', '褐色', '大地', '山峦', '古老', '沧桑', '枯萎', '泥土', '怀旧']  # 赭石
        }
        
        self.profile_embeddings = {}
        self._precompute()

    def _precompute(self):
        """预计算颜色意象的嵌入向量"""
        if not self.model:
            return
        
        print("[ColorAnalyzer] Pre-computing color profile embeddings...")
        for color, keywords in self.color_profiles.items():
            # 编码该颜色的所有关键词
            # 我们将每个关键词单独编码，以便在匹配时寻找最大相似度
            embs = self.model.encode(keywords, convert_to_tensor=True)
            self.profile_embeddings[color] = embs

    def analyze(self, text, top_k=6):
        if not self.model or not text:
            return []
            
        # 编码输入文本
        text_emb = self.model.encode(text, convert_to_tensor=True)
        
        scores = []
        for color, concept_embs in self.profile_embeddings.items():
            # 计算文本与该颜色下所有概念的余弦相似度
            # concept_embs: [N, D], text_emb: [D]
            cos_scores = util.cos_sim(text_emb, concept_embs)[0]
            
            # 取最大值：只要文本与该颜色下的某一个概念非常相似，就认为该颜色匹配
            # 例如 "烽火" 与 "火焰" 相似，就会激活红色，即使它不完全像 "喜庆"
            best_score = torch.max(cos_scores).item()
            scores.append((color, best_score))
            
        # 按分数降序排列
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 过滤掉分数太低的 (可选)
        valid_scores = [s for s in scores if s[1] > 0.15]
        if not valid_scores:
            valid_scores = scores # 如果都低，就硬着头皮返回
            
        return [c for c, s in valid_scores[:top_k]]

def get_poem_colors(text, sentiment=0.5):
    """根据诗歌内容提取代表颜色 (关键词匹配 + 情感色板)"""
    if not text:
        return []

    # [DELETED] Remove semantic analysis initialization
    # global _semantic_color_analyzer
    # semantic_colors = []
    # try: ... except ...

    # 1. 基础单字颜色映射表 (中国传统色)
    SINGLE_CHAR_MAP = {
        # Reds
        '朱': '#FF2121', '红': '#D93A49', '赤': '#C3272B', '丹': '#E45A41', '绛': '#8C4356', 
        '血': '#8E2961', '胭脂': '#9D2933', '茜': '#CB3A56', '彤': '#F35336', '霞': '#F07C82',
        '花': '#F07C82', '桃': '#F58F98', '粉': '#FFA488', '海': '#22A2C3', '石': '#69504C',

        # Yellows/Golds
        '黄': '#FFD400', '金': '#EACD76', '琥': '#CA6924', '杏': '#F28E16', '菊': '#D3A237',
        '橙': '#FA8C35', '橘': '#FA8C35', '日': '#F2BE45', '阳': '#F2BE45', '辉': '#F2BE45',
        '铜': '#B69968', '土': '#8F5B3C',

        # Greens
        '绿': '#45B787', '翠': '#0AA344', '碧': '#1BD1A5', '青': '#00E09E', '苍': '#7397AB',
        '柳': '#8A988E', '苔': '#69836A', '草': '#86C166', '松': '#375830', '竹': '#789262',
        '葱': '#5DA39D', '艾': '#A4CAB6', '玉': '#2EDFA3',

        # Blues
        '蓝': '#44CEF6', '靛': '#177CB0', '天': '#2E9FDB', '空': '#5CB3CC',
        '水': '#88ADA6', '江': '#4B5CC4', '湖': '#22A2C3', '波': '#22A2C3', '烟': '#6D8346',

        # Purples
        '紫': '#8D4BBB', '薇': '#815463', '茄': '#815476', '檀': '#B36D61', '黛': '#4A4266',

        # Whites/Silvers
        '白': '#FFFFFF', '素': '#E2E1E4', '雪': '#FFFFFE', '霜': '#E9E7EF', '银': '#E9E7EF',
        '云': '#F2F2F2', '月': '#D6ECF0', '梨': '#F1F2F4', '缟': '#F2ECDE',

        # Blacks/Darks
        '黑': '#131124', '墨': '#50616D', '玄': '#622A1D', '乌': '#131124', '暗': '#3C3C3C',
        '夜': '#202020', '影': '#50616D', '昏': '#50616D', '鸦': '#131124', '漆': '#161823'
    }

    # 2. 双字特定意象映射 (优先级更高)
    BIGRAM_MAP = {
        '杨柳': '#8A988E', '黄鹂': '#F2BE45', '白鹭': '#FFFFFF', '青天': '#2E9FDB',
        '明月': '#FFFBF0', '残阳': '#B25D25', '夕阳': '#FF8C31', '落日': '#FF8C31',
        '朝霞': '#F07C82', '晚霞': '#9D2933', '红豆': '#D93A49', '芭蕉': '#69836A',
        '梧桐': '#B36D61', '芙蓉': '#F03752', '丁香': '#B19693', '杜鹃': '#F03752',
        '牡丹': '#F03752', '芍药': '#EB3C70', '桂花': '#D3A237', '荷花': '#F07C82',
        '莲花': '#F07C82', '梅花': '#F03752', '桃花': '#F58F98', '杏花': '#F28E16',
        '梨花': '#F1F2F4', '菊花': '#D3A237', '兰花': '#7B90D2', '松柏': '#375830',
        '苍苔': '#69836A', '白云': '#F2F2F2', '青山': '#405E3F', '流水': '#88ADA6',
        '寒山': '#5D4037', '秋水': '#88ADA6', '春水': '#86C166', '暮雨': '#8A988E',
        '细雨': '#F2F2F2', '风雪': '#FFFFFF', '冰雪': '#FFFFFF', '白发': '#E9E7EF',
        '朱门': '#D93A49', '青衫': '#003371', '白衣': '#F2F2F2', '红袖': '#F07C82',
        '黄金': '#EACD76', '白玉': '#F1F8E9', '青砖': '#637159', '绿瓦': '#0AA344',
        '黄昏': '#F9906F', '清晨': '#C6E6E8', '深夜': '#131124', '星河': '#D6ECF0',
        '锦瑟': '#A61B29', '紫烟': '#8552a1', '碧空': '#45B787', '玉盘': '#F0F0F4'
    }

    # 3. 混合策略：优先使用语义颜色，不足部分用关键词补齐
    final_colors = []
    
    # 3.1 [DELETED] Remove semantic analysis part as per user request to avoid heavy libraries
    # if semantic_colors:
    #     final_colors.extend(semantic_colors)
        
    # 3.2 扫描文本中的关键词 (作为细节补充)
    keyword_colors = []
    i = 0
    n = len(text)
    while i < n:
        matched = False
        # 优先尝试匹配双字
        if i + 1 < n:
            bigram = text[i:i+2]
            if bigram in BIGRAM_MAP:
                keyword_colors.append(BIGRAM_MAP[bigram])
                i += 2
                matched = True
                continue
        
        # 匹配单字
        if not matched:
            char = text[i]
            if char in SINGLE_CHAR_MAP:
                keyword_colors.append(SINGLE_CHAR_MAP[char])
            i += 1
            
    # 3.3 合并关键词颜色 (去重，但保持顺序)
    for c in keyword_colors:
        if c not in final_colors:
            final_colors.append(c)
    
    # 3. 如果颜色太少 (< 6)，根据情感倾向补充色系
    target_count = 6
    if len(final_colors) < target_count:
        needed = target_count - len(final_colors)
        
        # 定义色系板 (更加协调的中国色)
        if sentiment > 0.6: # 积极/暖/明亮 -> 橙黄粉红
            fillers = ['#F9906F', '#F2BE45', '#F07C82', '#FFA488', '#F2F2F2']
        elif sentiment < 0.4: # 消极/冷/忧郁 -> 蓝灰紫青
            fillers = ['#177CB0', '#50616D', '#4A4266', '#8A988E', '#E9E7EF']
        else: # 中性/自然/淡雅 -> 绿白青米
            fillers = ['#69836A', '#F1F8E9', '#45B787', '#E2E1E4', '#D6ECF0']
            
        import random
        # 补充颜色
        for _ in range(needed):
            final_colors.append(random.choice(fillers))
            
    # 截取前N个
    return final_colors[:10]

def get_poem_emotions(text):
    """
    根据关键词分析诗歌情感分布 (返回雷达图数据)
    简单字典匹配，不依赖重型模型
    """
    if not text:
        return {"joy": 0, "anger": 0, "sorrow": 0, "fear": 0, "love": 0, "zen": 0}

    def load_emotion_lexicon():
        global _cached_emotion_lexicon
        if _cached_emotion_lexicon is not None:
            return _cached_emotion_lexicon
        lex = {}
        if os.path.exists(EMOTION_LEXICON_FILE):
            try:
                with open(EMOTION_LEXICON_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row or len(row) < 2:
                            continue
                        word = row[0].strip()
                        cat = row[1].strip().lower()
                        weight = 1.0
                        if len(row) >= 3:
                            try:
                                weight = float(row[2])
                            except Exception:
                                weight = 1.0
                        emo_map = {
                            'joy': 'joy',
                            'anger': 'anger',
                            'sadness': 'sorrow',
                            'fear': 'fear',
                            'love': 'love',
                            'trust': 'zen',
                            'calm': 'zen',
                            'serenity': 'zen',
                            'anticipation': 'joy',
                            'surprise': 'fear',
                            'disgust': 'anger'
                        }
                        mapped = emo_map.get(cat)
                        if mapped:
                            lex[word] = (mapped, weight)
            except Exception:
                lex = {}
        _cached_emotion_lexicon = lex
        return lex

    external_lexicon = load_emotion_lexicon()
    
    def load_dict_csv_lexicon():
        global _cached_dict_csv_lexicon
        if _cached_dict_csv_lexicon is not None:
            return _cached_dict_csv_lexicon
        lex = {}
        if os.path.exists(DICT_CSV_FILE):
            try:
                with codecs.open(DICT_CSV_FILE, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    word_idx = 0
                    emo_idx = 4
                    strength_idx = 5
                    aux_emo_idx = 8
                    aux_strength_idx = 9
                    if header:
                        def find_idx(name, default):
                            try:
                                return header.index(name)
                            except ValueError:
                                return default
                        word_idx = find_idx('词语', word_idx)
                        emo_idx = find_idx('情感分类', emo_idx)
                        strength_idx = find_idx('强度', strength_idx)
                        aux_emo_idx = find_idx('辅助情感分类', aux_emo_idx)
                        aux_strength_idx = find_idx('强度', aux_strength_idx)
                    def map_code(code):
                        m = {
                            'PA':'joy','PH':'joy','PK':'joy','PC':'joy',
                            'PB':'love','PF':'love','PD':'love',
                            'PE':'zen','PG':'zen',
                            'NB':'sorrow','NJ':'sorrow','NH':'sorrow',
                            'NC':'fear','NI':'fear',
                            'NA':'anger','ND':'anger','NE':'anger','NN':'anger','NK':'anger'
                        }
                        return m.get(code.strip().upper())
                    for row in reader:
                        if not row or len(row) <= max(word_idx, emo_idx):
                            continue
                        w = row[word_idx].strip()
                        code = row[emo_idx].strip() if len(row) > emo_idx else ''
                        cat = map_code(code)
                        try:
                            weight = float(row[strength_idx]) if len(row) > strength_idx else 1.0
                        except Exception:
                            weight = 1.0
                        if w and cat:
                            lex[w] = (cat, max(0.5, weight))
                        if len(row) > aux_emo_idx:
                            aux_code = row[aux_emo_idx].strip()
                            aux_cat = map_code(aux_code)
                            if aux_cat and len(row) > aux_strength_idx:
                                try:
                                    aux_weight = float(row[aux_strength_idx])
                                except Exception:
                                    aux_weight = 1.0
                                if w not in lex:
                                    lex[w] = (aux_cat, max(0.5, aux_weight))
                    _cached_dict_csv_lexicon = lex
            except Exception:
                _cached_dict_csv_lexicon = {}
        else:
            _cached_dict_csv_lexicon = {}
        return _cached_dict_csv_lexicon
    
    dict_csv_lexicon = load_dict_csv_lexicon()

    EMOTION_KEYWORDS = {
        'joy': {'喜', '笑', '欢', '乐', '欣', '悦', '畅', '春', '酒', '歌', '舞', '晴', '明', '好', '美', '香', '花', '月', '金', '玉', '庆', '幸', '傲', '瑞', '福', '安', '康', '醉', '乐', '丰', '和'},
        'anger': {'怒', '愤', '恨', '怨', '仇', '敌', '战', '烽', '剑', '血', '杀', '吼', '狂', '急', '烈', '斗', '斥', '骂', '雷', '火', '戈', '兵', '暴', '狠', '戾', '恶'},
        'sorrow': {'悲', '哀', '愁', '苦', '泪', '哭', '伤', '痛', '残', '断', '寒', '孤', '独', '凄', '惨', '逝', '死', '墓', '荒', '凉', '落', '老', '病', '别', '离', '殇', '寂', '怅', '忧'},
        'fear': {'惧', '恐', '惊', '怕', '畏', '颤', '危', '险', '鬼', '魂', '魄', '夜', '黑', '暗', '深', '渊', '逃', '慌', '怖', '乱'},
        'love': {'爱', '情', '思', '念', '恋', '相', '心', '意', '梦', '缘', '君', '伊', '佳', '偶', '鸳', '鸯', '眉', '眼', '红', '豆', '惜', '怜', '慕', '柔', '欢'},
        'zen': {'静', '闲', '空', '无', '禅', '佛', '寺', '钟', '云', '山', '林', '幽', '远', '淡', '清', '悟', '道', '松', '鹤', '隐', '寂', '素', '净', '澹'}
    }
    
    EMOTION_PHRASES = {
        'joy': {'喜悦': 1.6, '欢乐': 1.6, '欢喜': 1.5, '春风': 1.5, '良辰': 1.4, '美景': 1.4, '花开': 1.4, '彩云': 1.3, '清欢': 1.3},
        'anger': {'愤怒': 1.8, '怒火': 1.7, '怨恨': 1.6, '杀气': 1.6, '战火': 1.6, '烽烟': 1.5, '怒吼': 1.5, '暴怒': 1.7},
        'sorrow': {'悲伤': 1.7, '哀愁': 1.6, '离愁': 1.6, '别绪': 1.5, '泪下': 1.5, '断肠': 1.7, '凄凉': 1.6, '愁思': 1.5, '孤寂': 1.5},
        'fear': {'恐惧': 1.7, '惊惧': 1.6, '心惊': 1.5, '夜半': 1.3, '鬼神': 1.4, '阴风': 1.4},
        'love': {'相思': 1.7, '情深': 1.6, '思君': 1.6, '柔情': 1.5, '怜惜': 1.5, '红豆': 1.6, '恋人': 1.4},
        'zen': {'清净': 1.6, '空灵': 1.6, '无为': 1.5, '禅意': 1.6, '山林': 1.4, '松风': 1.4, '明月': 1.3}
    }

    scores = {k: 0.0 for k in EMOTION_KEYWORDS.keys()}
    total_matches = 0

    if dict_csv_lexicon:
        for word in jieba.lcut(text):
            info = dict_csv_lexicon.get(word)
            if info:
                cat, weight = info
                scores[cat] += weight
                total_matches += weight
    elif external_lexicon:
        for word in jieba.lcut(text):
            info = external_lexicon.get(word)
            if info:
                cat, weight = info
                scores[cat] += weight
                total_matches += weight
    else:
        for word in jieba.lcut(text):
            for emotion, keywords in EMOTION_PHRASES.items():
                if word in keywords:
                    weight = keywords[word]
                    scores[emotion] += weight
                    total_matches += weight

    for char in text:
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if char in keywords:
                scores[emotion] += 1.0
                total_matches += 1.0
    
    # 归一化 (防止除零)
    if total_matches > 0:
        for k in scores:
            scores[k] = round((scores[k] / total_matches) * 10, 2) # Scale to 0-10
    else:
        # 如果没有匹配到关键词，给一个默认的平庸分布
        scores = {"joy": 2, "anger": 1, "sorrow": 2, "fear": 1, "love": 2, "zen": 2}
        
    return scores

def train_bertopic_model(docs):
    """训练 BERTopic 模型 (支持 GPU 加速)"""
    _lazy_load_sentence_transformers()
    _lazy_load_bertopic()
    # 硬件加速检测
    device = "cpu"
    try:
        import torch_directml
        device = torch_directml.device()
        print(f"[BERTopic] Using DirectML GPU acceleration: {device}")
    except ImportError:
        print("[BERTopic] Hardware acceleration (DirectML) not found, using CPU.")

    print("[BERTopic] Loading embedding model (multilingual-MiniLM)...")
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
    
    print("[BERTopic] Configuring vectorizer...")
    # BERTopic using the robust tokenizer
    vectorizer_model = CountVectorizer(tokenizer=tokenize_zh)
    
    print(f"[BERTopic] Training on {len(docs)} documents...")
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        language="multilingual",
        calculate_probabilities=False,
        verbose=True,
        nr_topics="auto"
    )
    
    topics, probs = topic_model.fit_transform(docs)
    return topic_model, topics, probs

def save_bertopic_model(model):
    """保存模型"""
    if not os.path.exists(os.path.dirname(MODEL_DIR)):
        os.makedirs(os.path.dirname(MODEL_DIR))
    model.save(MODEL_DIR, serialization="safetensors", save_ctfidf=True)
    print(f"[BERTopic] Model saved to {MODEL_DIR}")

def load_bertopic_model():
    """加载模型 (支持 GPU 加速)"""
    _lazy_load_bertopic()
    # 硬件加速检测
    device = "cpu"
    try:
        import torch_directml
        device = torch_directml.device()
    except ImportError:
        pass

    if os.path.exists(MODEL_DIR):
        try:
            print(f"[BERTopic] Loading embedding model on {device}...")
            _lazy_load_sentence_transformers()
            embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
            print("[BERTopic] Loading BERTopic model...")
            model = BERTopic.load(MODEL_DIR, embedding_model=embedding_model)
            print("[BERTopic] Model loaded successfully.")
            return model
        except Exception as e:
            print(f"[BERTopic] Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return None
    return None

def get_document_vector(text, model):
    """获取文档的向量表示"""
    if not model or not text:
        return None
    try:
        if hasattr(model.embedding_model, 'embed'):
            embeddings = model.embedding_model.embed([text])
            return embeddings[0]
        return model.embedding_model.encode(text)
    except Exception:
        return None

def batch_get_vectors(texts, model):
    """批量获取文档向量"""
    if not model or not texts:
        return []
    try:
        if hasattr(model.embedding_model, 'embed'):
            return model.embedding_model.embed(texts)
        return model.embedding_model.encode(texts)
    except Exception:
        return []

def get_topic_info(model, topic_id):
    """获取主题关键词 (全局统计用)"""
    if topic_id == -1:
        return "未分类"
    keywords = model.get_topic(topic_id)
    if keywords:
        return "-".join([k[0] for k in keywords[:4]])
    return f"Topic {topic_id}"

def predict_topic(text, model):
    """预测单条文本的主题 (逻辑修正: 结果返回该诗的独立关键词)"""
    if not model or not text:
        return -1, "未知"
    
    # 1. 全局预测 (用于推荐引擎的 Topic ID)
    try:
        topics, _ = model.transform([text])
        topic_id = topics[0]
    except Exception:
        return -1, get_individual_keywords(text)
    
    # 2. 独立提取 (用于前端显示的标签)
    # 不再展示 generic 聚类标签，而是针对这首诗提取最重要的词
    topic_name = get_individual_keywords(text)
    
    return topic_id, topic_name

def get_all_topics(model):
    """获取所有全局主题描述"""
    if not model:
        return {}
    topic_dict = {}
    topics = model.get_topics()
    for tid, words in topics.items():
        if tid == -1: continue
        name = "-".join([w[0] for w in words[:4]])
        topic_dict[tid] = name
    return topic_dict

if __name__ == "__main__":
    # Test stub
    pass
