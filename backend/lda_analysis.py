import pandas as pd
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
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
    return " ".join(meaningful_words)

def train_lda_model(n_topics=3):
    """训练LDA模型"""
    # 1. 加载数据
    df = load_data()
    stopwords = load_stopwords()

    # 2. 预处理评论
    print("正在进行分词和预处理...")
    df['processed_comment'] = df['comment'].apply(lambda x: preprocess_text(str(x), stopwords))
    
    # 3. 构建词频矩阵 (Document-Term Matrix)
    # max_df=0.95: 如果一个词在95%的文档里都出现，那它太常见了（比如“诗歌”），去掉
    # min_df=2: 如果一个词只出现过1次，去掉
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2)
    tf = tf_vectorizer.fit_transform(df['processed_comment'])

    # 4. 训练LDA模型
    print(f"开始训练LDA模型，尝试提取 {n_topics} 个主题...")
    lda = LatentDirichletAllocation(n_components=n_topics, max_iter=50,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0)
    lda.fit(tf)

    # 5. 展示主题词
    print("\n=== 主题挖掘结果 ===")
    feature_names = tf_vectorizer.get_feature_names_out()
    
    # 存储主题关键词，方便后续使用
    topic_keywords = {}
    
    for topic_idx, topic in enumerate(lda.components_):
        # 获取每个主题下权重最高的10个词
        top_features_ind = topic.argsort()[:-11:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        topic_keywords[topic_idx] = top_features
        print(f"主题 #{topic_idx}: {' '.join(top_features)}")
    
    return lda, tf_vectorizer, df, topic_keywords

if __name__ == "__main__":
    # 如果直接运行此脚本，则进行测试
    train_lda_model()
