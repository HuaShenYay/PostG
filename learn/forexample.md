中图分类号: TP391.1 文献标志码: A

# 基于 LDA 主题模型的协同过滤推荐算法

张 宇, 吴 静(浙江理工大学 计算机科学与技术学院, 杭州 310018)

摘 要: 传统的协同过滤推荐算法直接根据用户对物品的评分进行推荐 忽略了评论文本中隐含的重要信息 当用户对物品的评论较少时 由于数据的稀疏性会造成推荐效果的不准确和单一 本文提出了一种基于 LDA 主题模型的协同过滤推荐算法LDA-CF( Latent Dirichlet Allocation model-LDA-Collaborative Filtering),在传统的协同过滤算法基础上,通过 LDA 模型对评论文本中的主题进行分类 从各个主题层面挖掘用户的情感偏好 计算用户之间的相似度 进而向目标用户推荐商品 对京东平台牙膏的评论数据集的实验结果表明,该算法不仅可以缓解由于评分数据较少造成的稀疏性问题,推荐的精确度也有所提高。

关键词: 协同过滤 推荐算法 LDA 评论文本

# Collaborative filtering recommendation algorithm based on LDA topic model 

ZHANG Yu, WU Jing 

(School of Computer Science and Technology, Zhejiang Sci-Tech University, Hangzhou 310018, China) 

Abstract: Traditional collaborative filtering recommendation algorithms tend to recommend items directly according to users′ scores, ignoring the important information implied in the comment text. Moreover, when users have few comments on items, the sparsity of the data will lead to the inaccuracy and singleness of the recommendation effect. Therefore, this paper proposes a collaborative filtering recommendation algorithm based on LDA topic model. Based on the traditional collaborative filtering algorithm, the algorithm classifies the topics in the review text through the LDA model, mines the emotional preferences of users from each topic level, calculates the similarity between users, and then recommends products to target users. The experimental results based on the review data set of toothpaste on JD platform show that the algorithm can not only alleviate the sparsity problem caused by few score data, but also improve the recommendation accuracy compared with the traditional collaborative filtering algorithm. 

Key words: collaborative filtering; recommendation algorithm; LDA; comment text 

# 0 引 言

随着互联网的飞速发展 海量数据的产生使得用户找到自己需要的内容十分艰难 为解决这一难题提出了推荐算法[1] 常见的推荐算法分为基于内容的推荐算法 基于协同过滤的推荐算法以及混合推荐算法[2]。 传统的推荐算法往往只分析用户对商品的共同评分 根据用户的历史行为记录进行推荐 如果用户之间共同评分的商品较少,推荐的性能就会受到数据稀疏性的影响,从而影响推荐的精度[3]。

传统的推荐算法是通过对商品的评分计算用户之间的相似度 而评分只能反映用户对商品的总体满意程度 不能准确反映用户对商品各个属性的满意度 以牙膏评论为例 用户 和 对同一款牙膏满意度打分均为 分 用户 认为该款牙膏的使用效果好而价格昂贵 用户 认为这款牙膏的价格合适而使用效果不明显 用户 和用户 对同一款牙膏的评分相同,但是他们喜爱偏好却不同。 由此可见 从用户对商品的文本评论中可以挖掘出更有价值的信息 对这些文本评论加以利用 可以准确分析出用户的喜爱偏好 从而提高推荐的准确度

本文对评论文本采用 主题模型进行分析 深刻挖掘用户对商品各个方面的喜爱程度 每个商品都包含各个方面的主题,如:牙膏包括价格、使用效果、味道等 通过对各主题的分析来预测用户对商品的总体评分 从而找到与目标用户最相似的用户进行推荐

# 1 相关工作

# 1.1 LDA 主题模型

LDA 主题模型由 Blei 等于 2003 年提出,LDA 模型是一种主题概率生成模型 构建 文档 主题 词层的贝叶斯结构 文档是词汇的集合 每篇文档都会有一个或者多个主题 每个主题会以一定概率选择某个词 词会以一定的概率生成某个主题[4-7] 近年来 很多研究者将 模型和推荐系统相结合等[8]充分利用评论文本信息 通过 模型观察由丰富文档组成的本地上下文 这些文档可能直接或间接地影响目标文档的主题分布 等[9] 提出评级模型 认为用户行为不是独立的 还受相似用户的影响 相似用户给出的评分高 则目标用户也有可能喜爱该商品;Huang 等[10] 对 LDA 主题模型扩展了文本特征的数量 基于支持向量机 随机森林等算法构建文本分类器 并通过十倍交叉和混淆矩阵验证情感分类方法的有效性

# 1.2 推荐系统

推荐系统的探索源于 世纪 年代初 综合了诸多领域的知识 如信息检索 预测结果 数据存储以及市场分析等[11-13] 推荐系统是非常有用的工具 随着用户 服务和在线数据的规模迅速扩大 可以在用户购买产品之前提供适当的建议[14] 一个高效的有价值的推荐系统 要解决在推荐过程中的推荐精准度问题冷启动问题以及大规模的计算与存储等问题[15]等[16]研究发现 在推荐算法中引入社会关系和历史行为等 可以更好地为推荐系统服务 由于社交网络中存在同伴影响或共同兴趣等隐性因素 具有相似隐性因素的用户更有可能成为目标推荐的相似对象。 随着研究的不断深入 陆续产生了基于关联规则挖掘的推荐系统 基于贝叶斯分类的推荐系统 个性化推荐服务等[17] 。

# 2 推荐模型

# 2.1 数据预处理

获取用户对商品的评论文本 按照如下步骤对评论文本进行预处理 首先 对评论文本去除同一用户短时期内的重复商品评论 其次 由于较短的评论文本所包含的信息较少 为保证推荐结果的准确性 去除评论文本字数少于 个的商品评论 最后 去除评论文本中完全没有用或者没有意义的词 如助词 拟声词 虚词等 使用 分词进行中文分词 得到数据集

# 2.2 构建 LDA 主题模型

将一个评论文本视为 模型中的一个文档进行分析,所有的评论文本视为文档集合。

LDA 模型的生成过程: 从狄利克雷分布 $\alpha$ 中取样生成文档 $p$ 的主题分布 ${ \theta _ { p } } ^ { [ 1 8 ] }$ 从主题的多项式分布 $\theta _ { { p } }$ 中取样,生成文档 $p$ 第 $q$ 个词的主题 $Z _ { p , q }$ ;从狄利克雷分布 $\beta$ 中取样,生成主题 $Z _ { p , q }$ 对应的词语分布 $\varphi _ { p , q }$ ;从词语的多项式分布 $\varphi _ { p , q }$ 中采样,最终生成词语 $\boldsymbol { W } _ { p , q }$ 。 其中,参数 $\alpha$ 和参数 $\beta$ 根据 Gibbs 采样方法进行参数估计[19] 最佳主题数目 $K$ 的值根据困惑度的大小来确定 困惑度越小 主题数目 $K$ 越合适

# 2.3 商品评分计算

在主题-词汇矩阵中 主题下只有部分词汇具有情感极性 采用知网情感词典判断每个主题下包含的词汇是否为正面情感词 负面情感词和中性词[20-21],若主题每包含一个正面情感词,则将该主题的情感得分加 每包含一个负面情感词 则将该主题的情感得分减 中性词不计入情感得分 依次类推直至统计完所有词汇 得到每个主题对应的情感得分。

在文档-主题矩阵中,每个文档所包含各个主题的概率不同, 每个文档的评分也不同,用户 $u _ { i }$ 对商品 $x _ { h }$ 的评分 $s _ { u _ { i } , x _ { h } } ^ { ' }$ , 计算公式(1):

$$
s _ { u _ { i } , x _ { h } } ^ { ' } = \sum _ { k = 0 } ^ { K } g _ { u _ { i } , x _ { h } } ^ { k } \times p _ { u _ { i } , x _ { h } } ^ { k }
$$

其中 $1 \leqslant i \leqslant N , N$ 表示用户总数 $1 \leqslant h \leqslant H$ ,$H$ 表示商品总数; $k ( k = 0 , 1 , 2 , 3 , \cdots , K )$ 表示文档 -主题矩阵中文档的第 $k$ 个主题 $K$ 表示文档所包含的主题数目; ${ { g } _ { u _ { i } , x _ { h } } ^ { k } }$ 表示用户 $u _ { i }$ 对商品 $x _ { h }$ 的评论文本在第 $k$ 个主题上的情感得分; $p _ { u _ { i } , x _ { h } } ^ { k }$ 表示用户 $\overline { { u } } _ { i }$ 对商品 $x _ { h }$ 的评论文本包含主题 $k$ 的概率

通过最大最小标准化公式使得用户对商品的评分在[1,5]之间,标准化后的用户 $u _ { i }$ 对商品 $x _ { h }$ 的评分 $s _ { u _ { i } , x _ { h } }$ , 计算公式(2):

$$
s _ { u _ { i } , x _ { h } } = \frac { s _ { u _ { i } , x _ { h } } ^ { ' } - s _ { u _ { i } , \mathrm { m i n } } ^ { ' } } { s _ { u _ { i } , \mathrm { m a x } } ^ { ' } - s _ { u _ { i } , \mathrm { m i n } } ^ { ' } } \times 5
$$

其中, $s _ { u _ { i } , \mathrm { m i n } } ^ { ' }$ 表示用户 $u _ { i }$ 对已购买商品的评分最小值, $s _ { u _ { i } , \operatorname* { m a x } } ^ { ' }$ 表示用户 $u _ { i }$ 对已购买商品的评分最大值。

计算结果四舍五入取整 不足 分的记为 分情感值范围为 1-5 分,5 分为完全满意,1 分为完全不满意 分数越高表示用户对商品越满意 空缺值表示用户未对该商品进行打分 最后得到用户对商品的评分矩阵。

根据用户对所有商品的评分,计算用户 $u _ { i }$ 对全部已评价商品评分的均值 $\bar { s } _ { u _ { i } }$ , 计算公式(3):

$$
\bar { s } _ { u _ { i } } = \frac { 1 } { H } \sum _ { h \ : = 1 } ^ { H } \ : s _ { u _ { i } , x _ { h } }
$$

# 2.4 用户相似度计算

使用余弦相似度方法计算两个用户之间的相似度。 $s i m \big ( u _ { i } , u _ { j } \big )$ 表示用户 $u _ { i }$ 和用户 $u _ { j }$ 的相似度,计算公式(4):

$$
 , \ ( u _ { i } , u _ { j } ) = \frac { \displaystyle \sum _ { h = 1 } ^ { H } s _ { u _ { i } , x _ { h } } \times s _ { u _ { j } , x _ { h } } } { \sqrt { \displaystyle \sum _ { h = 1 } ^ { H } \ ( s _ { u _ { i } , x _ { h } } ) ^ { 2 } } \ \times \sqrt { \displaystyle \sum _ { h = 1 } ^ { H } \ ( s _ { u _ { j } , x _ { h } } ) ^ { 2 } } }
$$

其中, $s _ { u _ { i } , x _ { h } }$ 表示用户 ui 对商品 xh 的评分, su x表示用户 $u _ { j }$ 对商品 $x _ { h }$ 的评分。

按照相似度数值排序 数值越大说明两个用户之间的相似度越高 按照相似度大小对所有用户降序排列 即越靠前的用户同目标用户之间的相似度越高 得到目标用户的相似用户群

# 2.5 生成推荐商品

根据 Top - $N$ 策略从相似用户群中选取排名前$N$ 个用户作为最近邻用户 根据最近邻用户预测目标用户对待推荐商品的评分 根据预测结果 生成向目标用户推荐的商品。 ${ { g } _ { u _ { o } , x _ { h } } }$ 表示目标用户 $u _ { o }$ 对待推荐商品 $x _ { h }$ 的预测评分,公式(5):

$$
g _ { u _ { o } , x _ { h } } = \frac { \displaystyle \sum _ { u _ { m } \in M } ( s i m ( u _ { o } , u _ { m } ) \times ( s _ { u _ { m } , x _ { h } } - \bar { s } _ { u _ { m } } ) \ : ) } { \displaystyle \sum _ { u _ { m } \in M } s i m ( u _ { o } , u _ { m } ) }
$$

其中, $M$ 表示相似用户群中对待推荐商品 $x _ { h }$ 进行了评分的所有用户的集合; $s i m ( u _ { o } , u _ { m } )$ 表示目标用户 $u _ { o }$ 和用户 $\boldsymbol { u } _ { m }$ 的相似度; $s _ { u _ { m } , x _ { h } }$ 表示用户 $\boldsymbol { u } _ { m }$ 对待推荐商品 $x _ { h }$ 的评分; $\bar { s } _ { u _ { m } }$ 表示用户 $u _ { m }$ 对其全部已评价商品评分的均值。

# 3 实验与分析

# 3.1 实验数据集

本文实验使用的初始数据集为京东 个排名较高的牙膏品牌的评论文本 数据集共包括个用户的 103 850 条商品评论。 对数据进行预处理 可用数据集数包括 个用户的 条商品评论 每条评论文本平均字数为 个 按 $8 : 2$ 的比例将数据集随机地分为训练集和测试集

# 3.2 对比实验与评估指标

为验证推荐方法的准确性 将 - 算法与以下两种传统的推荐算法进行比较:

(1) CB( Content-Based Recommendations CB):基于内容的推荐算法。

(2) CF( Collaborative Filtering):传统的协同过

滤推荐算法

本文采用的评价指标

平均绝对值误差 $( M A E )$ 反映推荐算法预测评分与实际评分的相似程度 公式

$$
\ M A E = \frac { \displaystyle \sum _ { ( i , j ) \in E ^ { U } } \left| \boldsymbol { u } _ { i , j } - \boldsymbol { u } _ { i , j } ^ { ' } \right| } { \left| E ^ { U } \right| }
$$

其中, $u _ { i , j }$ 表示用户 $i$ 对商品 $j$ 的实际评分; $u _ { i , j } ^ { ' }$ 表示用户 $i$ 对商品 $j$ 的预测评分 $\mid E ^ { U } \mid$ 表示预测评分总数。

(2) F1 - Score: 综合了分类模型的精确率 $P$ 和召回率 $R$ ,公式(7) \~ 公式(9):

$$
P = { \frac { T P } { T P + F P } }
$$

$$
R = \frac { T N } { T N + F N }
$$

$$
F 1 _ { \bf \Phi } - S c o r e = \frac { 2 P R } { P \ + \ R }
$$

其中 $T P$ 表示将文本正向样本预测为正向样本 $F N$ 表示将文本正向样本预测为负向样本 TN表示将文本负向样本预测为负向样本 $F P$ 表示将文本负向样本预测为正向样本

# 3.3 实验结果与分析

采用 主题模型对用户的评论数据进行分析,通过 Gibbs 采样的方法对参数进行估计,设置先验参数 $\alpha = 5 0 / T$ 和 先验参数$\beta = 0 . 0 1$ 依据困惑度的方法来确立最佳主题数 $K$ ,通过模型训练 得出文档 - 主题矩阵和主题 - 词汇矩阵 主题数目 $K$ 和困惑度的关系如图 所示 可以看出当主题数 $K = 7$ 时 主题模型的困惑度最小。

![](images/b369fff136d80adcf822c6e513a4ee62d8a3137b2e13f9c77eacad8863c2e156.jpg)



图 1 主题数目 $\pmb { K }$ 和困惑度的关系



Fig. 1 Relationship between the number of topics $\pmb { K }$ and the degree 


# of confusion 

主题模型得到的部分用户评论数据的主题-词汇概率分布见表

主题模型得到的部分用户评论数据的文档-主题概率分布见表2。


表1 部分用户评论数据的主题-词汇概率分布



Table 1 Topic-word probability distribution of partial user review data 



表2 部分用户评论数据的文档-主题概率分布




<table><tr><td>主题</td><td>词汇</td><td>概率</td></tr><tr><td>主题1</td><td>不错,快递,物流速度快,方便快捷</td><td>0.428,0.040,0.031,0.027</td></tr><tr><td>主题2</td><td>品牌,信赖,牌子,老字号</td><td>0.354,0.121,0.087,0.401</td></tr><tr><td>主题3</td><td>回购,质量,实惠,物超所值</td><td>0.272,0.120,0.085,0.046</td></tr><tr><td>主题4</td><td>包装,精美，物流完好，完好无损</td><td>0.149,0.090,0.074,0.067</td></tr><tr><td>主题5</td><td>第一次，别人，朋友,好用</td><td>0.186,0.103,0.081,0.063</td></tr><tr><td>主题6</td><td>味道,薄荷,清新,好闻</td><td>0,243,0.076,0.071,0.061</td></tr><tr><td>主题7</td><td>活动,凑单,赠品,划算</td><td>0.223,0.103,0.090,0.082</td></tr></table>




Table 2 Document-topic probability distribution of partial user review data 




<table><tr><td>文档</td><td>主题</td><td>概率</td></tr><tr><td>文档1</td><td>[7,3,5,6,4,2,1]</td><td>0.355,0.270,0.196,0.072,0.006,0.005,0.004</td></tr><tr><td>文档2</td><td>[5,7,1,6,3,4,2]</td><td>0.287,0.137,0.074,0.063,0.005,0.004,0.003</td></tr><tr><td>文档3</td><td>[3,7,6,5,4,2,1]</td><td>0.201,0.153,0.009,0.009,0.006,0.005,0.003</td></tr><tr><td>文档4</td><td>[4,2,7,6,5,3,1]</td><td>0.535,0.419,0.006,0.005,0.004,0.002,0.001</td></tr><tr><td>文档5</td><td>[6,2,1,5,4,3,7]</td><td>0.304,0.296,0.170,0.087,0.066,0.056,0.005</td></tr></table>




- 在各项指标上均有所提高 推荐较为准确


算法先通过 主题模型得出用户评论的文档 主题概率分布和主题 词汇概率分布得出用户的评分 算法与传统的协同过滤算法和基于内容的推荐算法推荐效果如图 所示可见相比其他两种方法 - 算法的 MAE 值较小 在评分预测的准确性优于其他两种算法

![](images/c7d00381384e8ca7afa93dbc077afb88a54fcd930db7d8f0a72fd97a1929ed14.jpg)



图 2 不同模型的 MAE 值对比



Fig. 2 Comparison of MAE values of different models 


利用余弦相似度的方法得出目标用户的待推荐商品,将本文的 LDA-CF 算法与基于内容的推荐算法(CB)和传统的协同过滤推荐算法(CF)进行对比实验,实验结果见表 3,可见在同等条件和数据下,


表3 评论数据集评测结果对比



Table 3 Comparison of evaluation results of review data sets 




<table><tr><td>模型</td><td>准确率</td><td>召回率</td><td>F1- Score值</td></tr><tr><td>CB</td><td>0.867</td><td>0.847</td><td>0.857</td></tr><tr><td>CF</td><td>0.875</td><td>0.889</td><td>0.882</td></tr><tr><td>LDA-CF</td><td>0.895</td><td>0.914</td><td>0.904</td></tr></table>



# 4 结束语

本文提出一种基于 主题模型的协同过滤推荐算法 使用 模型获取评论文本的信息 并将文本主题与评论文本相融合 利用协同过滤算法得出用户对商品的评分 与传统的推荐算法相比本文提出的 算法能够充分利用评论文本包含的信息 更加深刻地分析挖掘用户在商品各个主题下的喜爱偏好 从而提高了推荐的准确性 在后续的研究中,将会尝试提高文本主题提取的精度,从而更加精准的分析出评论文本包含的主题信息,进一步提高推荐算法的精准度

# 参考文献

[1] NASSARN,JAFARA,RAHHAL Y. A novel deep multi - criteria collaborative filtering model for recommendation system [ J ] . 

Knowledge-Based Systems - .  
[2] Prasad RVVSV. A Categorical Review of Recommender Systems[ J] . International Journal of Distributed and Parallel Systems,2012,3(5):108-119.  
[ 3 ] YU Chengyuan, HUANG Linpeng. CluCF: A clustering CFalgorithm to address data sparsity problem J . Service OrientedComputing and Applications - .  
SAFI IE M A UTAMI E FATTA H A. Latent DirichletAllocation ( LDA) model and kNN algorithm to classify researchproject selection [ J] . IOP Conference Series: Materials Scienceand Engineering,2018,333(1):49-70.  
[5] 王李冬,魏宝刚,袁杰. 基于概率主题模型的文档聚类[J]. 电子学报 - .  
[6] Venugopalan Manju, Gupta Deepa. An enhanced guided LDAmodel augmented with BERT based semantic strength for aspectterm extraction in sentiment analysis [ J ] . Knowledge - BasedSystems,2022,5(1):108-668.  
[7] ZHENG Wei, GE Bin, WANG Chishe. Building a TIN - LDAModel for Mining Microblog Users ' Interest [ J ] . IEEE Access,2019,7(1):21795-21806.  
[8] LIU Yang, XU Songhua. A local context-aware LDA model fortopic modeling in a document network [ J ] . Journal of theAssociation for Information Science and Technology, 2017, 68(6):1429-1448.  
[9] ZHOU Xiuze, WU Shunxiang. Rating LDA model for collaborativefiltering[J]. Knowledge-Based Systems,2016,110(5):135-143.  
[10] HUANG Yanrong, WANG Rui, HUANG Bin, et al. Sentimentclassification of crowdsourcing participants′ reviews text based onLDA topic model[J]. IEEE ACCESS,2021,9(7):1921-1937.  
黄勃 严非凡 张昊 等. 推荐系统研究进展与应用 J . 武汉大学学报 ( 理 学 版), 2021, 67 ( 6 ): 503 - 516. DOI: 10. 14188 / j.

# (上接第 189 页)


表3 实验结果



Table 3 Experimental results 




<table><tr><td>模型</td><td>精确度</td><td>召回率</td><td>F1 - score</td></tr><tr><td>本模型</td><td>90.54</td><td>92.87</td><td>91.69</td></tr><tr><td>BiLSTM</td><td>90.16</td><td>92.84</td><td>91.03</td></tr><tr><td>RNN</td><td>87.17</td><td>86.59</td><td>86.59</td></tr><tr><td>CNN</td><td>85.15</td><td>84.13</td><td>84.71</td></tr><tr><td>LSTM</td><td>88.46</td><td>88.07</td><td>86.06</td></tr></table>



# 4 结束语

本文针对影评提出了基于星级权重和双向长短期记忆网络的神经网络模型 能够解决单一特征无法充分利用文章上下文信息的问题 改善影评情感偏向不明显的情况 从而能提高了分类准确率。

. . .  
CHEN Rui HUA Qingyi CHANG Yanshuo et al. A survey ofcollaborative filtering - based recommender systems: fromtraditional methods to hybrid methods based on social networksJ . IEEE Access - .  
Devdatta Godbole Manish Narnaware. A survey on personalizedservice recommendation systems J . International Journal ofEngineering Research and Technology - .  
[14 ] Nachiket Sadashiv Bhosale, Sachin S Pande. A survey onrecommendation system for big data applications[ J] . Data Miningand Knowledge Engineering,2015,7(1):42-44.  
罗婷予 Miguel Baptista Nunes. 从用户视角理解智能推荐系统[J]. 数字图书馆论坛,2019,3(10):30-36.  
LEE Yan - Li ZHOU Tao YANG Kexin et al. Personalizedrecommender systems based on social relationships and historicalbehaviors[ J]. Applied Mathematics and Computation, 2023, 43- .  
[17] Gabroveanu Mihai. Recommendation system based on associationrules for distributed E - learning management systems[ J] . ACTAUniversitatis Cibiniensis - .  
万志成 郑静. 基于狄利克雷过程高斯混合模型的变分推断J . 杭州电子科技大学学报 自然科学版 -.  
[19]凤维明,尹一通. 分布式采样理论综述[J]. 软件学报,2022,33(10):3673-3699.  
LIU W Y XIAO B S WANG T et al. Building Chinesesentiment lexicon based on howNet [ J ] . Advanced MaterialsResearch - - .  
[21]LIU L, LEI M, WANG H. Combining domain-specific sentimentlexicon with hownet for Chinese sentiment analysis[ J] .Journal ofComputers,2013,8(4):878-883.

# 参考文献

[1] 陈晓东. 基于情感词典的中文微博情感倾向分析研究[D]. 武汉 华中科技大学 .  
尹宝才 王文通 王立春. 深度学习研究综述 J . 北京工业大学学报,2015,41(1):48-59.  
庞亮 兰艳艳 徐君 等. 深度文本匹配综述 J . 计算机学报2017,40(4) :985-1003.  
[4] 唐明,朱磊,邹显春. 基于 Word2Vec 的一种文档向量表示[J].计算机科学 - .  
黄磊 杜昌顺. 基于递归神经网络的文本分类研究 J . 北京化工大学学报 自然科学版 - .  
[6] TAI K S,SOCHER R,MANNING C D. Improved semantic representationsfrom tree-structured long short-term memory networks[ J] . arXivpreprint arXiv:1503.00075, 2015.  
BAZIOTIS C PELEKIS N DOULKERIDIS C. Datastories at semeval-2017 task 4: Deep lstm with attention for message-level and topic-based sentiment analysis[ C] / / Proceedings of the $1 1 ^ { \mathrm { t h } }$ InternationalWorkshop on Semantic Evaluation (SemEval-2017). 2017: 747-754.