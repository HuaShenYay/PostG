<template>
  <div class="home-container">
    <!-- 侧边栏 -->
    <el-drawer
      v-model="showSidebar"
      title="探索"
      direction="ltr"
      size="320px"
      :show-close="false"
    >
      <template #header>
        <h3 class="drawer-title">用户画像</h3>
      </template>
      
      <div v-if="userProfile" class="profile-section">
        <el-tag type="danger" effect="plain" class="interest-tag">
          偏好流派: {{ userProfile.top_interest.join(' / ') }}
        </el-tag>
        
        <div class="topic-bars">
          <div v-for="p in userProfile.preference" :key="p.topic_id" class="bar-item">
            <span class="bar-label">主题 {{ p.topic_id + 1 }}</span>
            <el-progress 
              :percentage="Math.round(p.score * 100)" 
              :stroke-width="6"
              :show-text="false"
              color="#1a1a1a"
            />
          </div>
        </div>
        
        <el-button @click="getRecommendations" class="sync-btn" plain>
          <el-icon><Refresh /></el-icon>
          同步画卷
        </el-button>
      </div>
      
      <el-divider />
      
      <h4 class="section-title">为您荐诗</h4>
      <div class="recommend-list">
        <div 
          v-for="rec in recommendations" 
          :key="rec.title" 
          class="rec-item"
          @click="jumpToPoem(rec.title)"
        >
          <div class="rec-title">{{ rec.title }}</div>
          <div class="rec-reason">{{ rec.reason }}</div>
        </div>
        <el-empty v-if="recommendations.length === 0" description="暂无推荐" :image-size="60" />
      </div>
    </el-drawer>

    <!-- 顶部导航 -->
    <el-header class="top-nav">
      <div class="nav-left">
        <el-button :icon="Menu" text @click="showSidebar = true" class="menu-btn" />
        <div class="site-branding">
          <span class="logo-text">诗云</span>
          <span class="edition">二零二五 · 典藏版</span>
        </div>
      </div>
      <div class="nav-right">
        <el-tag effect="plain" size="small">{{ currentUser }}</el-tag>
        <el-button type="danger" text @click="logout">
          <el-icon><SwitchButton /></el-icon>
          离席
        </el-button>
      </div>
    </el-header>

    <!-- 主舞台 -->
    <el-main class="main-stage">
      <div v-if="dailyPoem" class="poem-display">
        <el-card class="poem-card" shadow="never">
          <div class="poem-header">
            <h1 class="poem-title">{{ dailyPoem.title }}</h1>
            <el-tag type="danger" effect="plain" size="small">{{ dailyPoem.author }}</el-tag>
          </div>
          <el-divider />
          <div class="poem-content">{{ dailyPoem.content }}</div>
        </el-card>
        
        <div class="action-bar">
          <el-button-group>
            <el-button @click="toggleComments" :icon="ChatLineSquare">
              雅评 ({{ reviews.length }})
            </el-button>
            <el-button @click="getAnotherPoem" :icon="RefreshRight">
              易章
            </el-button>
          </el-button-group>
        </div>
      </div>
      
      <div v-else class="loading-state">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>研墨铺纸中...</p>
      </div>
    </el-main>

    <!-- 评论抽屉 -->
    <el-drawer
      v-model="showComments"
      title="诗友雅评"
      direction="rtl"
      size="400px"
    >
      <div class="comments-list">
        <div v-for="r in reviews" :key="r.id" class="comment-item">
          <div class="comment-header">
            <span class="comment-user">{{ r.user_id }}</span>
            <el-rate :model-value="r.rating" disabled size="small" />
          </div>
          <p class="comment-text">{{ r.comment }}</p>
        </div>
        <el-empty v-if="reviews.length === 0" description="寂寂无声，虚位以待" />
      </div>
      
      <template #footer>
        <div class="comment-form">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的感悟..."
          />
          <div class="form-actions">
            <el-rate v-model="newRating" />
            <el-button type="primary" @click="submitComment" :icon="EditPen">
              发表
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Menu, SwitchButton, Refresh, RefreshRight, 
  ChatLineSquare, Loading, EditPen 
} from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const currentUser = localStorage.getItem('user') || '访客'
const dailyPoem = ref(null)
const showComments = ref(false)
const showSidebar = ref(false)
const reviews = ref([])
const newComment = ref('')
const newRating = ref(5)
const userProfile = ref(null)
const recommendations = ref([])

const fetchUserProfile = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/user_preference/${currentUser}`)
    userProfile.value = res.data
  } catch(e) { console.error(e) }
}

const getRecommendations = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/recommend_personal/${currentUser}`)
    recommendations.value = res.data
    ElMessage.success('画卷已同步')
  } catch(e) { 
    ElMessage.error('同步失败')
  }
}

const getAnotherPoem = async () => {
  dailyPoem.value = null
  try {
    const res = await axios.get('http://127.0.0.1:5000/api/poems')
    const list = res.data
    dailyPoem.value = list[Math.floor(Math.random() * list.length)]
    fetchReviews(dailyPoem.value.id)
  } catch (e) { 
    ElMessage.error('获取诗歌失败')
  }
}

const fetchReviews = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}/reviews`)
    reviews.value = res.data
  } catch(e) { console.error(e) }
}

const toggleComments = () => { 
  showComments.value = !showComments.value 
}

const submitComment = async () => {
  if(!newComment.value) {
    ElMessage.warning('请填写评论内容')
    return
  }
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/poem/review', {
      username: currentUser,
      poem_id: dailyPoem.value.id,
      rating: newRating.value,
      comment: newComment.value
    })
    if(res.data.status === 'success') {
      ElMessage.success('雅评已收录')
      fetchReviews(dailyPoem.value.id)
      newComment.value = ''
    }
  } catch(e) { 
    ElMessage.error('发表失败')
  }
}

const logout = () => {
  localStorage.removeItem('user')
  ElMessage.info('已离席')
  router.push('/login')
}

const jumpToPoem = (title) => {
  ElMessage.info(`跳转至: ${title}`)
}

onMounted(() => {
  getAnotherPoem()
  fetchUserProfile()
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--stone-white);
}

/* 顶部导航 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  height: 70PX;
  border-bottom: 1px solid var(--line-gray);
  background: white;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.menu-btn {
  font-size: 20PX;
}

.site-branding {
  display: flex;
  flex-direction: column;
}

.logo-text {
  font-family: "Noto Serif SC", serif;
  font-size: 24PX;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.edition {
  font-size: 11PX;
  color: #aaa;
  margin-top: 2px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* 主舞台 */
.main-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.poem-display {
  width: 100%;
  max-width: 700px;
}

.poem-card {
  border: none;
  background: white;
  border-radius: 8px;
}

.poem-card :deep(.el-card__body) {
  padding: 40px;
}

.poem-header {
  display: flex;
  align-items: baseline;
  gap: 15px;
  flex-wrap: wrap;
}

.poem-title {
  font-family: "Noto Serif SC", serif;
  font-size: 32PX;
  font-weight: 700;
  margin: 0;
  color: var(--modern-black);
}

@media (max-width: 768px) {
  .poem-title { font-size: 24PX; }
}

.poem-content {
  font-family: "Noto Serif SC", serif;
  font-size: 18PX;
  line-height: 2;
  color: #333;
  white-space: pre-wrap;
}

.action-bar {
  margin-top: 30px;
  text-align: center;
}

.loading-state {
  text-align: center;
  color: #999;
}

.loading-state p {
  margin-top: 15px;
}

/* 侧边栏 */
.drawer-title {
  font-family: "Noto Serif SC", serif;
  font-size: 18PX;
  margin: 0;
}

.profile-section {
  margin-bottom: 20px;
}

.interest-tag {
  margin-bottom: 20px;
}

.topic-bars {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 25px;
}

.bar-item .bar-label {
  font-size: 12PX;
  color: #888;
  margin-bottom: 5px;
  display: block;
}

.sync-btn {
  width: 100%;
}

.section-title {
  font-size: 14PX;
  color: #666;
  margin-bottom: 15px;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rec-item {
  padding: 12px;
  border-radius: 6px;
  background: #f9f9f9;
  cursor: pointer;
  transition: background 0.3s;
}

.rec-item:hover {
  background: #f0f0f0;
}

.rec-title {
  font-weight: 600;
  font-size: 14PX;
  margin-bottom: 4px;
}

.rec-reason {
  font-size: 12PX;
  color: #999;
}

/* 评论 */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-user {
  font-weight: 600;
  font-size: 14PX;
}

.comment-text {
  font-size: 14PX;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
