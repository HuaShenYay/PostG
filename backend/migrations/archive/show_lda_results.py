# show_lda_results.py
from lda_analysis import load_lda_model

# 加载已保存的模型
lda_model, dictionary, topic_keywords = load_lda_model()

if lda_model:
    print("=== LDA模型结果 ===")
    print(f"主题数量: {lda_model.num_topics}")
    
    # 显示所有主题的关键词
    print("\n各主题关键词:")
    for topic_id, keywords in topic_keywords.items():
        print(f"主题 #{topic_id}: {' '.join(keywords)}")
    
    # 显示每个主题的完整分布（带权重）
    print("\n各主题详细分布:")
    for topic_id in range(lda_model.num_topics):
        topic_terms = lda_model.show_topic(topic_id, topn=15)
        terms_str = ", ".join([f"{term}: {weight:.4f}" for term, weight in topic_terms])
        print(f"主题 #{topic_id}: {terms_str}")
else:
    print("未找到已训练的LDA模型")