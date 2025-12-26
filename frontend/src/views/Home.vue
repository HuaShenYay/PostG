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
        <div class="user-meta-link">
          <span class="user-name-tag">{{ currentUser }}</span>
          <div class="meta-dot"></div>
          <span class="logout-link" @click="logout">离席</span>
        </div>
      </div>
    </el-header>

    <!-- 主舞台 -->
    <el-main class="main-stage">
      <transition name="poem-fade" mode="out-in">
        <div v-if="dailyPoem" :key="dailyPoem.id" class="poem-display-split">
          <!-- 左侧：诗文内容 -->
          <div class="poem-content-side">
            <p class="content-text">{{ dailyPoem.content }}</p>
          </div>

          <!-- 右侧：诗题与诗人 (错落排列) -->
          <div class="poem-meta-side">
            <div class="meta-wrapper">
              <h1 class="poem-title-vertical">{{ dailyPoem.title }}</h1>
              <div class="meta-divider"></div>
              <span class="author-tag-vertical theme-color">{{ dailyPoem.author }}</span>
            </div>
          </div>
          
          <!-- 操作栏：改为侧边浮动或底部跟随 -->
          <div class="action-bar-floating">
            <el-button @click="toggleComments" class="ghost-btn">
              雅评 ({{ reviews.length }})
            </el-button>
            <el-button @click="getAnotherPoem" class="ghost-btn">
              易章
            </el-button>
          </div>
        </div>
        
        <div v-else class="loading-state">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>研墨铺纸中...</p>
        </div>
      </transition>
    </el-main>

    <!-- 雅评区域：彻底去盒子化，作为页面的“边注”融入 -->
    <transition name="editorial-fade">
      <div v-if="showComments" class="marginalia-reviews">
        <!-- 背景水印感标题 -->
        <div class="watermark-title">雅评</div>
        
        <div class="marginalia-header">
           <span class="editorial-count">卷之九 / {{ reviews.length }} 条雅赏</span>
           <el-button :icon="Close" circle text @click="showComments = false" class="marginalia-close" />
        </div>
        
        <div class="marginalia-scroll">
          <div v-for="(r, index) in reviews" :key="r.id" class="marginalia-item" :style="{ transitionDelay: index * 100 + 'ms' }">
            <div class="item-header">
              <span class="u-name theme-color">{{ r.user_id }}</span>
              <div class="item-line"></div>
              <span class="u-rating">{{ r.rating }}.0</span>
            </div>
            <p class="u-content-modern">{{ r.comment }}</p>
          </div>
          <el-empty v-if="reviews.length === 0" description="虚位以待" :image-size="40" />
        </div>

        <div class="marginalia-input-zone">
          <el-input
            v-model="newComment"
            placeholder="在此处留墨..."
            class="bare-input"
            @keyup.enter="submitComment"
          />
          <div class="input-actions-minimal">
            <el-rate v-model="newRating" size="small" />
            <span class="submit-ink" @click="submitComment">落笔</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Menu, SwitchButton, Refresh, RefreshRight, 
  ChatLineSquare, Loading, EditPen, Close, Check 
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
  background-color: var(--stone-white);
}

/* 顶部导航 - 更加通透 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 60px;
  height: var(--header-height);
  background: transparent;
  z-index: 100;
}

@media (max-width: 768px) {
  .top-nav { padding: 0 20px; }
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 40px;
}

.menu-btn {
  font-size: 24PX;
  color: var(--modern-black);
}

.site-branding {
  display: flex;
  flex-direction: column;
}

.logo-text {
  font-family: "Noto Serif SC", serif;
  font-size: 28PX;
  font-weight: 700;
  letter-spacing: 0.2em;
}

.edition {
  font-size: 10PX;
  color: #bbb;
  margin-top: 6px;
  text-transform: uppercase;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 30px;
}

.user-meta-link {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name-tag {
  font-size: 13PX;
  letter-spacing: 0.1em;
  color: var(--modern-black);
  font-weight: 300;
}

.meta-dot {
  width: 3px;
  height: 3px;
  background-color: var(--accent-red);
  border-radius: 50%;
  opacity: 0.4;
}

.logout-link {
  font-size: 13PX;
  letter-spacing: 0.2em;
  color: var(--accent-red);
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.3s;
  font-weight: 400;
}

.logout-link:hover {
  opacity: 1;
  text-decoration: underline;
  text-underline-offset: 4px;
}

/* 主舞台 - 大面积留白 */
.main-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 40px 100px;
}

.poem-display {
  width: 100%;
  max-width: 800px;
  text-align: center;
}

.poem-card {
  border: none;
  background: transparent;
  box-shadow: none;
}

.poem-card :deep(.el-card__body) {
  padding: 0;
}

/* 错落并排布局 (现代新中式) */
.poem-display-split {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-start;
  gap: 120PX; /* 诗文与标题的间距 */
  width: 100%;
  max-width: 1100px;
  position: relative;
}

@media (max-width: 900px) {
  .poem-display-split {
    flex-direction: column-reverse;
    align-items: center;
    gap: 40px;
  }
}

/* 左侧：内容容器 */
.poem-content-side {
  flex: 1;
  text-align: right; /* 内容右对齐，靠近标题 */
  margin-top: 60PX; /* 与右侧形成高度差(错落) */
}

.content-text {
  font-family: "Noto Serif SC", serif;
  font-size: 20PX;
  line-height: 2.2;
  color: #333;
  white-space: pre-wrap;
  font-weight: 300;
  letter-spacing: 0.05em;
  display: inline-block;
  text-align: left; /* 文字内部左对齐 */
}

/* 右侧：元数据容器 (垂直排版) */
.poem-meta-side {
  width: 120px;
  display: flex;
  justify-content: center;
}

.meta-wrapper {
  writing-mode: vertical-rl; /* 关键：垂直排列 */
  text-orientation: upright;
  display: flex;
  align-items: center;
}

.poem-title-vertical {
  font-family: "Noto Serif SC", serif;
  font-size: 36PX;
  font-weight: 500;
  margin: 0;
  letter-spacing: 0.3em;
  color: var(--modern-black);
}

.meta-divider {
  width: 1px;
  height: 60px;
  background: var(--accent-red);
  margin: 20px 0;
  opacity: 0.3;
}

.author-tag-vertical {
  font-size: 14PX;
  letter-spacing: 0.5em;
  font-weight: 400;
}

/* 操作栏：底部悬浮 */
.action-bar-floating {
  position: absolute;
  bottom: -100PX;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 40px;
  width: 100%;
  justify-content: center;
}

@media (max-width: 900px) {
  .action-bar-floating {
    position: static;
    transform: none;
    margin-top: 40px;
  }
}

.ghost-btn {
  border: none !important;
  background: transparent !important;
  font-size: 12PX !important;
  letter-spacing: 0.2em;
  opacity: 0.4;
  color: var(--modern-black);
}

.ghost-btn:hover {
  opacity: 1;
  color: var(--accent-red) !important;
}

.theme-color {
  color: var(--accent-red) !important;
}

.theme-bg {
  background-color: var(--accent-red) !important;
  border-color: var(--accent-red) !important;
}

/* 切换动画 */
.poem-fade-enter-active, .poem-fade-leave-active {
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
.poem-fade-enter-from {
  opacity: 0;
  transform: translateX(30px); /* 侧向滑入 */
}
.poem-fade-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 雅评：彻底融入背景的“边注”派 */
.marginalia-reviews {
  position: fixed;
  top: 180PX;
  left: 60px;
  width: 400px;
  bottom: 80px;
  z-index: 900;
  display: flex;
  flex-direction: column;
  background: transparent; /* 彻底透明 */
}

/* 水印背景 */
.watermark-title {
  position: absolute;
  top: -80px;
  left: -20px;
  font-family: "Noto Serif SC", serif;
  font-size: 140PX;
  color: rgba(0, 0, 0, 0.02); /* 极淡的水印 */
  font-weight: 900;
  pointer-events: none;
  user-select: none;
  z-index: -1;
}

.marginalia-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 50px;
}

.editorial-count {
  font-size: 10PX;
  letter-spacing: 0.3em;
  color: #bbb;
  text-transform: uppercase;
}

.marginalia-close {
  opacity: 0.2;
}

.marginalia-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 20px;
  mask-image: linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
  /* 彻底隐藏滚动条 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.marginalia-scroll::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.marginalia-item {
  margin-bottom: 50px;
  opacity: 1; /* 默认设为 1，确保动画结束后不消失 */
  transform: translateX(0);
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 仅在进入动画开始时设为透明 */
.editorial-fade-enter-from .marginalia-item {
  opacity: 0;
  transform: translateX(-10px);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 12px;
}

.item-line {
  flex: 1;
  height: 0.5px;
  background: rgba(0, 0, 0, 0.04);
}

.u-name {
  font-size: 12PX;
  font-weight: 500;
  letter-spacing: 0.1em;
}

.u-rating {
  font-size: 10PX;
  color: #ccc;
  font-family: 'Inter', sans-serif;
}

.u-content-modern {
  font-size: 15PX;
  line-height: 1.8;
  color: #555;
  font-weight: 300;
  margin: 0;
}

.marginalia-input-zone {
  margin-top: 50px;
  padding-top: 30px;
}

.bare-input :deep(.el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border-bottom: 0.5px solid rgba(0,0,0,0.05) !important;
  padding: 0 !important;
}

.input-actions-minimal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.submit-ink {
  font-size: 12PX;
  letter-spacing: 0.3em;
  color: var(--accent-red);
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.submit-ink:hover {
  opacity: 1;
}

/* 彻底融入的渐变 */
.editorial-fade-enter-active, .editorial-fade-leave-active {
  transition: opacity 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.editorial-fade-enter-from, .editorial-fade-leave-to {
  opacity: 0;
}
</style>
