import pandas as pd
import jieba
from gensim import corpora, models
import os

# 1. 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, '../data/dataset.csv')
STOPWORDS_FILE = os.path.join(BASE_DIR, '../data/stopwords.txt')

def load_data():
    """加载CSV数据"""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"找不到数据文件: {DATA_FILE}")
    
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
    # jieba分词
    words = jieba.cut(text)
    # 过滤停用词和过短的词
    meaningful_words = [w for w in words if w not in stopwords and len(w) > 1]
    return meaningful_words # 返回列表，供 Gensim 使用

def train_lda_model(df=None):
    """
    训练LDA模型 (学术增强版：使用评估指标自动寻找最优 K 值)
    方案 B：Perplexity (困惑度) 评估法
    """
    if df is None:
        df = load_data()
    
    stopwords = load_stopwords()

    # 1. 预处理评论
    print("正在进行分词和预处理...")
    tokenized_texts = df['comment'].apply(lambda x: preprocess_text(str(x), stopwords)).tolist()
    
    # 2. 构建 Gensim 字典和语料库
    dictionary = corpora.Dictionary(tokenized_texts)
    dictionary.filter_extremes(no_below=1, no_above=1.0) 
    corpus = [dictionary.doc2bow(text) for text in tokenized_texts]

    if not corpus:
        print("语料库为空，无法训练。")
        return None, None, df, {}

    # 3. 寻找最优 K 值 (学术评估)
    # 遍历 K 从 2 到 10 (或根据数据量调整)
    k_range = range(2, 11)
    best_k = 5
    min_perplexity = float('inf')
    
    print(f"正在通过困惑度评估寻找最优主题数 K (范围: {list(k_range)})...")
    
    # 存储评估数据，方便后续打印（用户可用于论文绘图）
    eval_results = []

    for k in k_range:
        # 训练临时模型进行评估
        temp_lda = models.LdaModel(
            corpus=corpus, 
            num_topics=k, 
            id2word=dictionary, 
            passes=5, # 评估时减少迭代次数以提升速度
            random_state=42
        )
        # 计算困惑度 (值越小，模型拟合越好)
        perplexity = temp_lda.log_perplexity(corpus)
        eval_results.append((k, perplexity))
        print(f"  - K={k}, Log-Perplexity: {perplexity:.4f}")
        
        if perplexity < min_perplexity:
            min_perplexity = perplexity
            best_k = k

    print(f"\n[评估结论] 根据困惑度指标，选取最优主题数 K = {best_k}")

    # 4. 使用最优 K 值训练最终模型
    print(f"正在构建最终 LDA 模型 (K={best_k})...")
    lda = models.LdaModel(
        corpus=corpus, 
        num_topics=best_k, 
        id2word=dictionary, 
        passes=20, # 最终模型增加迭代次数，保证收敛
        random_state=42,
        alpha='auto',
        eta='auto'
    )
    
    # 5. 提取主题关键词
    topic_keywords = {}
    for topic_id in range(best_k):
        words = lda.show_topic(topic_id, topn=10)
        topic_keywords[topic_id] = [w[0] for w in words]
    
    return lda, dictionary, df, topic_keywords

if __name__ == "__main__":
    # 如果直接运行此脚本，则进行测试
    lda, dictionary, df, keywords = train_lda_model()
    if keywords:
        for tid, words in list(keywords.items())[:5]:
            print(f"主题 #{tid}: {' '.join(words)}")
