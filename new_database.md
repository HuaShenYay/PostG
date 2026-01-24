poems表 id 唯一id title 诗歌名 author 作者 content 诗歌内容 dynasty 朝代
genre_type 诗歌类型 （从json文件获取/抽出合理的诗歌类型） rhythm_name 诗歌格律名
rhythm_type 诗歌格律类型 views 浏览量 review_count 评论量 created_at 创建时间
updated_at 更新时间 LDA_topic
LDA主题（使用LDA主题分析，这首诗歌属于哪个主题，不要把lda主题的id写进来，而是把主题名的文本写进来）
Real_topic 真实主题 （人工标注，用于论文对比组）

reviews表

id 唯一id user_id 用户id poem_id 诗歌id comment 评论内容 topic_names 主题名
（LDA分析这首评论属于哪个主题，不要把lda主题的id写进来，而是把主题名的文本写进来）
created_at 创建时间 updated_at 更新时间

users表 id 唯一id username 用户名 password_hash 密码 created_at 创建时间
total_reviews 评论总数 preference_topics 用户偏好主题
（分析关于该用户的所有评论，得出的具体的主题分布）
