import pandas as pd
import jieba
import jieba.posseg as pseg
from gensim import corpora, models
from collections import Counter
import os

# 1. 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, '../data/dataset.csv')
STOPWORDS_FILE = os.path.join(BASE_DIR, '../data/scu_stopwords.txt')
# 默认主题数 K
DEFAULT_K = 60 

def load_data():
    """加载CSV数据"""
    if not os.path.exists(DATA_FILE):
        from models import Poem
        poems = Poem.query.all()
        if not poems:
            return pd.DataFrame(columns=['content'])
        return pd.DataFrame([p.content for p in poems], columns=['content'])
    
    try:
        df = pd.read_csv(DATA_FILE)
        return df
    except:
        return pd.DataFrame(columns=['content'])

def load_stopwords():
    """加载停用词表 - 包含基础停用词和诗歌评论专用停用词"""
    stopwords = set()
    
    # 1. 加载基础停用词
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stopwords.add(line.strip())
    
    # 2. 加载诗歌评论专用停用词
    poetry_stopwords_file = os.path.join(BASE_DIR, '../data/poetry_stopwords.txt')
    if os.path.exists(poetry_stopwords_file):
        with open(poetry_stopwords_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    stopwords.add(line)
    
    # 3. 扩展古典诗词常见的功能性"噪声"词
    extra_stops = {
        '千里', '万里', '不知', '不得', '不可', '何处', '今日', '此时', '不见', 
        '一个', '如此', '便是', '还是', '这样', '这个', '那里', '这里', '而且',
        '甚至', '怎么', '如果', '但是', '因此', '因为', '所以', '虽然', '可是',
        # 诗歌评论专用
        '这首', '诗', '词', '句', '意境', '韵味', '写', '写得', '作', '作诗',
        '点赞', '收藏', '转发', '分享', '支持', '给力', '牛', '厉害', '佩服',
        '感觉', '认为', '觉得', '喜欢', '爱', '赞', '好诗', '不错', '推荐',
        '优秀', '精彩', '太好了', '真好', '一切', '都是', '令人', '真是', '哈哈',
        '今天', '昨天', '明天', '现在', '以前', '以后', '一首', '几首', '多首',
        '什么', '怎么', '为什么', '如何', '哪里', '而且', '并且', '但是', '不过'
    }
    
    return stopwords.union(extra_stops)

def preprocess_text(text, stopwords):
    """高级文本预处理：分词 + POS 过滤 + 去停用词"""
    if not isinstance(text, str) or not text:
        return []
    
    # 使用 POS 过滤：只保留名词(n)、动词(v)、形容词(a)、地名(ns)、人名(nr)、成语(i)、习用语(l)
    target_pos = {'n', 'v', 'a', 'ns', 'nr', 'nz', 'i', 'l', 'ad', 'an'}
    words = pseg.cut(text)
    
    meaningful_words = []
    for word, pos in words:
        if pos in target_pos and len(word) > 1:
            if word not in stopwords:
                meaningful_words.append(word)
                
    return meaningful_words 

def train_lda_on_poems(poems_content_list, num_topics=DEFAULT_K):
    """根据所有诗歌内容训练 LDA 模型，并加入 TF-IDF 降噪"""
    stopwords = load_stopwords()
    print("[LDA] Preprocessing text with POS filtering...")
    tokenized_texts = []
    total = len(poems_content_list)
    for i, content in enumerate(poems_content_list):
        tokenized_texts.append(preprocess_text(content, stopwords))
        if (i + 1) % 500 == 0:
            print(f"  - Preprocessing: {i + 1}/{total} ({(i + 1)/total*100:.1f}%)")
            
    tokenized_texts = [t for t in tokenized_texts if len(t) > 3] # 过滤过短样本

    dictionary = corpora.Dictionary(tokenized_texts)
    # 更加严格的词频过滤
    dictionary.filter_extremes(no_below=5, no_above=0.4) 
    
    corpus = [dictionary.doc2bow(text) for text in tokenized_texts]

    if not corpus:
        return None, None, {}

    # 使用 TF-IDF 对词袋进行加权，进一步降低背景噪音词的权重
    print("[LDA] Applying TF-IDF weighting for noise reduction...")
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]

    print(f"[LDA] Training high-precision LDA model (K={num_topics})...")
    lda = models.LdaModel(
        corpus=corpus_tfidf, # 使用 TF-IDF 权重
        num_topics=num_topics, 
        id2word=dictionary, 
        passes=30, 
        random_state=42,
        alpha='auto',
        eta='auto'
    )
    
    # 提取主题关键词并生成主题名
    topic_keywords = {}
    for topic_id in range(num_topics):
        words = lda.show_topic(topic_id, topn=3)
        topic_keywords[topic_id] = "-".join([w[0] for w in words])
    
    return lda, dictionary, topic_keywords

def predict_topic(text, lda, dictionary, topic_keywords):
    """预测文本所属的主题名"""
    if not text or lda is None:
        return "未知"
    
    stopwords = load_stopwords()
    tokens = preprocess_text(text, stopwords)
    bow = dictionary.doc2bow(tokens)
    
    if not bow:
        return "未知"
    
    topics = lda.get_document_topics(bow)
    if not topics:
        return "未知"
        
    # 获取概率最高的主题
    best_topic_id = max(topics, key=lambda x: x[1])[0]
    return topic_keywords.get(best_topic_id, f"主题-{best_topic_id}")

def save_lda_model(lda, dictionary, topic_keywords):
    """保存模型到本地"""
    model_dir = os.path.join(BASE_DIR, 'saved_models')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    lda.save(os.path.join(model_dir, 'lda.model'))
    dictionary.save(os.path.join(model_dir, 'lda.dict'))
    import json
    with open(os.path.join(model_dir, 'keywords.json'), 'w', encoding='utf-8') as f:
        json.dump(topic_keywords, f, ensure_ascii=False)
    print("LDA 优化模型已保存。")

def load_lda_model():
    """从本地加载模型"""
    model_dir = os.path.join(BASE_DIR, 'saved_models')
    lda_path = os.path.join(model_dir, 'lda.model')
    dict_path = os.path.join(model_dir, 'lda.dict')
    kw_path = os.path.join(model_dir, 'keywords.json')
    
    if os.path.exists(lda_path) and os.path.exists(dict_path):
        lda = models.LdaModel.load(lda_path)
        dictionary = corpora.Dictionary.load(dict_path)
        topic_keywords = {}
        if os.path.exists(kw_path):
            import json
            with open(kw_path, 'r', encoding='utf-8') as f:
                raw_kw = json.load(f)
                topic_keywords = {int(k): v for k, v in raw_kw.items()}
        return lda, dictionary, topic_keywords
    return None, None, None

if __name__ == "__main__":
    # 测试
    df = load_data()
    if not df.empty:
        content_col = 'comment' if 'comment' in df.columns else df.columns[0]
        lda, dictionary, keywords = train_lda_on_poems(df[content_col].tolist())
        if lda:
            save_lda_model(lda, dictionary, keywords)
