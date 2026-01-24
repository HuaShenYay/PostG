import os
import jieba
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
import pandas as pd

# 配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'saved_models', 'bertopic_model')
STOPWORDS_FILE = os.path.join(BASE_DIR, '..', 'data', 'scu_stopwords.txt')
POETRY_STOPWORDS_FILE = os.path.join(BASE_DIR, '..', 'data', 'poetry_stopwords.txt')

# 核心停用词库 (避免显示 "是-不-在-的")
DEFAULT_STOPWORDS = {
    '的', '了', '和', '是', '不', '在', '之', '于', '也', '与', '而', '则', '其', '为', '以',
    '到', '从', '就', '并', '且', '又', '或', '都', '即', '此', '彼', '若', '如', '但', '即便',
    '虽然', '但是', '可是', '然而', '所以', '因此', '因为', '于是', '既然', '那么', '如何',
    '什么', '哪个', '谁', '哪里', '怎么', '如此', '极其', '非常', '特别', '更加', '再', '更',
    '还', '已经', '将', '要', '向', '对', '把', '被', '让', '使', '给', '由', '由于', '因',
    '为了', '关于', '对于', '哪怕', '哪怕是', '即便如此', '个', '位', '只', '支', '头', '面'
}

def load_stopwords():
    """加载停用词，合并文件与硬编码库"""
    stopwords = set(DEFAULT_STOPWORDS)
    
    def read_file(filepath):
        encodings = ['utf-8', 'gbk', 'utf-16']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return [line.strip() for line in f]
            except UnicodeDecodeError:
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
    return list(stopwords.union(extra))

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

def get_individual_keywords(text, top_k=4):
    """单独针对单首诗歌提取关键词 (解决‘全是标点/噪音’问题)"""
    if not text:
        return "未知"
    # 使用 TF-IDF 提取这首诗里最重要的词
    keywords = jieba.analyse.extract_tags(text, topK=top_k)
    if not keywords:
        # Fallback to simple scan if TF-IDF fails
        words = tokenize_zh(text)
        keywords = words[:top_k]
        
    return "-".join(keywords) if keywords else "未分类"

def train_bertopic_model(docs):
    """训练 BERTopic 模型"""
    print("[BERTopic] Loading embedding model (multilingual-MiniLM)...")
    embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
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
    """加载模型"""
    if os.path.exists(MODEL_DIR):
        try:
            print("[BERTopic] Loading embedding model...")
            embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            print("[BERTopic] Loading BERTopic model...")
            model = BERTopic.load(MODEL_DIR, embedding_model=embedding_model)
            print("[BERTopic] Model loaded successfully.")
            return model
        except Exception as e:
            print(f"[BERTopic] Failed to load model: {e}")
            return None
    return None

def get_document_vector(text, model):
    """获取文档的向量表示"""
    if not model or not text:
        return None
    if hasattr(model.embedding_model, 'embed'):
        embeddings = model.embedding_model.embed([text])
        return embeddings[0]
    return model.embedding_model.encode(text)

def batch_get_vectors(texts, model):
    """批量获取文档向量"""
    if not model or not texts:
        return []
    if hasattr(model.embedding_model, 'embed'):
        return model.embedding_model.embed(texts)
    return model.embedding_model.encode(texts)

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
    topics, _ = model.transform([text])
    topic_id = topics[0]
    
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
