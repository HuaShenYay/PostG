我理解您的需求了！您想要一个
**以BERTopic主题为核心的协同过滤系统**，其他方法（内容推荐、热门推荐）主要作为冷启动的辅助手段。

## 🎯 **核心思路：主题向量协同过滤**

### **1. 数据模型设计**

```
用户画像 = {
    "user_id": "U001",
    "topic_profile": [0.3, 0.5, 0.1, ...],  # BERTopic主题分布向量
    "interaction_history": [
        {"poem_id": "P001", "topic_vector": [0.2, 0.3, ...], "rating": 4.5},
        {"poem_id": "P002", "topic_vector": [0.1, 0.6, ...], "rating": 3.0}
    ]
}

诗歌画像 = {
    "poem_id": "P001",
    "topic_vector": [0.2, 0.3, 0.1, ...],  # BERTopic主题分布
    "metadata": {"title": "...", "author": "...", "dynasty": "..."}
}
```

### **2. 核心算法：基于主题的协同过滤**

#### **2.1 用户-用户相似度（主题空间）**

```
用户A主题向量: [0.3, 0.4, 0.1, 0.2]
用户B主题向量: [0.2, 0.5, 0.1, 0.2]
相似度 = cosine_similarity(A, B)
```

#### **2.2 物品-物品相似度（主题空间）**

```
诗歌X主题向量: [0.1, 0.7, 0.1, 0.1]
诗歌Y主题向量: [0.2, 0.6, 0.1, 0.1]
相似度 = cosine_similarity(X, Y)
```

#### **2.3 混合推荐逻辑**

```python
def hybrid_recommend(user, poems):
    # 主逻辑：基于主题的协同过滤
    if user.interaction_count > 10:
        # 有丰富历史：使用主题协同过滤
        recommendations = topic_based_cf(user, poems)
    elif user.interaction_count > 0:
        # 轻度用户：主题CF + 内容辅助
        recommendations = weighted_combine(
            topic_based_cf(user, poems, weight=0.7),
            content_based(user, poems, weight=0.3)
        )
    else:
        # 新用户：内容推荐 + 热门诗歌
        recommendations = weighted_combine(
            content_based(user, poems, weight=0.7),
            popularity_based(poems, weight=0.3)
        )
    
    return recommendations
```

### **3. 具体实现策略**

#### **策略A：基于用户的主题协同过滤**

1. **计算用户主题向量**：聚合用户评论/点赞诗歌的BERTopic主题分布
2. **寻找相似用户**：在主题向量空间中找最近邻
3. **推荐相似用户喜欢的诗歌**：排除用户已读诗歌

#### **策略B：基于物品的主题协同过滤**

1. **计算诗歌主题向量**：BERTopic直接提取
2. **寻找相似诗歌**：在主题空间中找相似诗歌
3. **推荐相似诗歌**：基于用户历史喜欢的诗歌推荐相似主题的诗歌

#### **策略C：冷启动辅助方法**

1. **内容推荐**：使用用户注册时的兴趣标签或初始评论的主题向量
2. **热门推荐**：全局热门诗歌，按主题分类
3. **探索推荐**：多样性主题的诗歌，帮助发现新兴趣

### **4. 系统架构简化版**

```
输入层
    ↓
BERTopic主题提取（诗歌、评论）
    ↓
    ┌─────────────────────────────┐
    │   主题向量协同过滤引擎       │ ← 核心
    │  • 用户主题向量构建         │
    │  • 主题相似度计算           │
    │  • 基于主题的CF推荐         │
    └─────────────────────────────┘
    ↓
    ┌─────────────────────────────┐
    │     冷启动辅助引擎          │ ← 辅助
    │  • 内容相似度匹配           │
    │  • 热门诗歌推荐             │
    │  • 探索性推荐               │
    └─────────────────────────────┘
    ↓
输出层：个性化诗歌推荐
```

### **5. 动态权重策略**

```python
def get_recommendation_weights(user):
    interaction_count = user.interaction_count
    
    if interaction_count == 0:
        # 全新用户：内容+热门为主
        return {"topic_cf": 0.0, "content": 0.7, "popularity": 0.3}
    
    elif interaction_count < 5:
        # 轻度用户：逐步增加CF权重
        cf_weight = interaction_count * 0.15  # 0-0.6
        return {"topic_cf": cf_weight, "content": 0.7-cf_weight, "popularity": 0.3}
    
    elif interaction_count < 20:
        # 中度用户：CF主导
        return {"topic_cf": 0.7, "content": 0.2, "popularity": 0.1}
    
    else:
        # 重度用户：纯CF
        return {"topic_cf": 0.9, "content": 0.1, "popularity": 0.0}
```

### **6. 关键优势**

1. **主题为核心**：所有推荐都基于BERTopic提取的主题向量
2. **协同过滤增强**：不是传统CF，而是"主题向量空间的CF"
3. **冷启动友好**：新用户/新诗歌都有主题向量，可以立即参与推荐
4. **解释性强**：可以告诉用户"因为您喜欢[主题A]，所以推荐这些诗歌"

### **7. 与其他方法的关系**

- **传统CF** → **主题向量CF**（升级版）
- **内容推荐** → **冷启动备用方案**
- **热门推荐** → **最后的安全网**

这个设计让BERTopic主题向量成为推荐系统的"通用货币"，所有用户和物品都在同一个主题空间中，协同过滤自然发生。
