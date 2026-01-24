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
# 默认主题数 K (用户要求固定，我们可以通过预训练得出一个合理的固定值)
DEFAULT_K = 10 

def load_data():
    """加载CSV数据"""
    if not os.path.exists(DATA_FILE):
        # 如果 dataset.csv 不存在，尝试从数据库读取
        from models import Poem
        poems = Poem.query.all()
        if not poems:
            return pd.DataFrame(columns=['content'])
        return pd.DataFrame([p.content for p in poems], columns=['content'])
    
    df = pd.read_csv(DATA_FILE)
    print(f"成功加载数据，共 {len(df)} 条记录")
    return df

def load_stopwords():
    """加载停用词表"""
    stopwords = set()
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stopwords.add(line.strip())
    return stopwords

def preprocess_text(text, stopwords):
    """文本预处理：分词 + 去停用词"""
    if not isinstance(text, str):
        return []
    # jieba分词
    words = jieba.cut(text)
    # 过滤停用词和过短的词
    meaningful_words = [w for w in words if w not in stopwords and len(w) > 1]
    return meaningful_words 

def train_lda_on_poems(poems_content_list, num_topics=DEFAULT_K):
    """根据所有诗歌内容训练 LDA 模型"""
    stopwords = load_stopwords()
    tokenized_texts = [preprocess_text(content, stopwords) for content in poems_content_list]
    
    dictionary = corpora.Dictionary(tokenized_texts)
    dictionary.filter_extremes(no_below=2, no_above=0.8) 
    corpus = [dictionary.doc2bow(text) for text in tokenized_texts]

    if not corpus:
        return None, None, {}

    print(f"正在训练 LDA 模型 (K={num_topics})...")
    lda = models.LdaModel(
        corpus=corpus, 
        num_topics=num_topics, 
        id2word=dictionary, 
        passes=20, 
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
    if not text or not lda:
        return "未知"
    
    stopwords = load_stopwords()
    tokens = preprocess_text(text, stopwords)
    bow = dictionary.doc2bow(tokens)
    
    if not bow:
        return "未知"
    
    topics = lda.get_document_topics(bow)
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
    print("LDA 模型及字典已保存。")

def load_lda_model():
    """从本地加载模型"""
    model_dir = os.path.join(BASE_DIR, 'saved_models')
    lda_path = os.path.join(model_dir, 'lda.model')
    dict_path = os.path.join(model_dir, 'lda.dict')
    kw_path = os.path.join(model_dir, 'keywords.json')
    
    if os.path.exists(lda_path) and os.path.exists(dict_path):
        lda = models.LdaModel.load(lda_path)
        dictionary = corpora.Dictionary.load(dict_path)
        import json
        topic_keywords = {}
        if os.path.exists(kw_path):
            with open(kw_path, 'r', encoding='utf-8') as f:
                raw_kw = json.load(f)
                topic_keywords = {int(k): v for k, v in raw_kw.items()}
        return lda, dictionary, topic_keywords
    return None, None, None

if __name__ == "__main__":
    # 模拟训练
    df = load_data()
    if not df.empty:
        content_col = 'comment' if 'comment' in df.columns else df.columns[0]
        lda, dictionary, keywords = train_lda_on_poems(df[content_col].tolist())
        if lda:
            save_lda_model(lda, dictionary, keywords)
            test_text = "白日依山尽，黄河入海流。"
            topic = predict_topic(test_text, lda, dictionary, keywords)
            print(f"测试文本: {test_text}")
            print(f"预测主题: {topic}")
