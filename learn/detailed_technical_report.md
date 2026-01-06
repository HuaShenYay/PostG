# 基于主题模型的诗歌推荐系统——详细技术实现与进度报告

## 1. 技术栈概览 (Technical Stack)

本系统采用现代前后端分离架构，专注于高性能计算与极致的用户交互体验。

### 1.1 后端技术 (Backend)
- **核心框架**: Python Flask 3.0 (轻量级、高扩展性)
- **算法科学栈**: 
  - `Gensim`: 用于构建 LDA (Latent Dirichlet Allocation) 主题模型。
  - `Jieba`: 高性能中文分词引擎，用于诗歌及其评论的文本挖掘。
  - `Pandas`: 负责海量评分数据的清洗与矩阵运算。
- **持久化层**: SQLAlchemy ORM + MySQL/SQLite。
- **数据流**: 通过 RESTful API 输出 JSON 数据，支持跨域访问 (CORS)。

### 1.2 前端技术 (Frontend)
- **核心框架**: Vue 3 (Composition API) + Vite (构建工具)。
- **路由管理**: Vue-Router 4.x。
- **通信库**: Axios (用于异步获取推荐结果及提交评论)。
- **交互美学**: CSS 变量驱动的“新中式”主题，集成 CSS3 硬件加速动画。

---

## 2. 核心算法实现方法 (Implementation Methods)

### 2.1 语义提取：LDA 主题建模
系统并非粗放地通过关键词匹配，而是深度挖掘文本中潜在的“意境主题”：
1. **预处理分词**: 结合 `scu_stopwords.txt` 停用词库，对用户评论进行去噪处理。
2. **K 值寻优策略**: 
   - 算法自动遍历主题数范围（如 2-10）。
   - **困惑度评估 (Perplexity)**: 计算模型对语料库的拟合度，$Log\text{-}Perplexity$ 越小表示模型越优。
3. **向量化转化**: 将每首诗转化为一个高维的主题概率分布向量 $\vec{\theta}$。

### 2.2 推荐策略：LDA-CF 混合评分机制
为解决协同过滤的冷启动问题，我们构建了复合评分公式：
$$Final\_Score = (\vec{U}_{pref} \cdot \vec{P}_{topic}) \times \omega + (\frac{Rating}{5.0}) \times (1 - \omega)$$
- **$\vec{U}_{pref}$**: 用户审美偏好向量。
- **$\vec{P}_{topic}$**: 诗歌隐含主题向量。
- **$\omega$**: 语义权重（当前设定为 0.7），强调语义匹配的重要性。

### 2.3 系统实时刷新机制
通过 API 触发 `refresh_system_data()`，在用户提交新的评价后，后台会：
1. 更新数据库 `reviews` 表。
2. 重新加载全局 `Pandas DataFrame`。
3. 动态更新 LDA 模型的主题关键词缓存。

---

## 3. 实现进度清单 (Progress & Milestones)

| 阶段 | 模块 | 实现状态 | 具体内容描述 |
| :--- | :--- | :--- | :--- |
| **P0** | **数据层** | ✅ 已交付 | 完成诗歌数据集导入工具，支持评论与评分的多表关联。 |
| **P1** | **算法逻辑** | ✅ 已交付 | 实现 LDA 训练脚本，支持基于困惑度的自动调优。 |
| **P2** | **后端 API** | ✅ 已交付 | 完成登录鉴权、诗歌流接口、个性化推荐接口。 |
| **P3** | **前端 UI** | ✅ 已交付 | 完成首页瀑布流、雅评滑出层、登录/注册动态交互。 |
| **P4** | **优化与测试** | 🚧 进行中 | 正在进行 LDA 模型的参数微调与前端渲染性能优化。 |
| **P5** | **文档撰写** | 🚧 进行中 | 论文大纲已定，目前正在撰写第三章需求分析。 |

---

## 4. 关键代码实现片段 (Snippet)

### LDA 主题训练逻辑:
```python
# 通过困惑度寻找最优 K 值
for k in range(2, 11):
    temp_lda = models.LdaModel(corpus=corpus, num_topics=k, id2word=dictionary)
    perplexity = temp_lda.log_perplexity(corpus)
    if perplexity < min_perplexity:
        best_k = k
# 使用最优 K 值构建最终模型
lda = models.LdaModel(corpus=corpus, num_topics=best_k, id2word=dictionary, passes=20)
```

### 个性化推荐打分:
```python
# 混合打分：主题匹配度 (70%) + 用户历史评分 (30%)
hybrid_score = topic_prob * 0.7 + (row['rating'] / 5.0) * 0.3
```

---

## 5. 项目结论与展望

### 已实现价值:
- 成功打通了从**非结构化评论**到**结构化推荐**的转换路径。
- 系统界面极具美感，符合诗歌产品的文化定位。
- 算法具备解释性（能够告诉用户“因为您喜欢‘边塞风’而推荐”）。

### 后续方向:
- **长文本支持**: 增加对更长语料的 LDA 支持。
- **UI 响应式优化**: 针对移动端进行更深度的适配调整。
- **论文可视化**: 准备导出 pyLDAvis 格式的可交互主题分布图。

---
**日期**: 2026年1月5日  
**报告人**: 宋子杰
