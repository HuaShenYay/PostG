<template>
  <div class="home-container">

    <!-- 顶部导航 -->
    <el-header class="top-nav">
      <div class="nav-left">
        <div class="site-branding">
          <span class="logo-text">诗云</span>
          <span class="edition">二零二五 · 典藏版</span>
        </div>
      </div>
      <div class="nav-right">
        <!-- 用户画像：移至顶部，保持观看契合主题 -->
        <transition name="fade">
          <div v-if="userProfile" class="header-preference-tag">
            <el-icon class="aura-icon"><Compass /></el-icon>
            <span class="aura-text">{{ userProfile.top_interest.join(' · ') }}</span>
          </div>
        </transition>

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
        <div v-if="dailyPoem" :key="dailyPoem.id" class="poem-wrapper">
          <div v-if="dailyPoem.recommend_reason" class="smart-rec-banner">
             <el-icon><MagicStick /></el-icon>
             <span>{{ dailyPoem.recommend_reason }}</span>
          </div>
          <div class="poem-display-split" :class="{ 'with-reviews': showComments }">
            <!-- 雅评区域：作为页面的“边注”融入 -->
            <transition name="marginalia-slide">
              <div v-if="showComments" class="marginalia-reviews-integrated">
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

            <!-- 诗文内容与元数据 -->
            <div class="poem-main-body">
              <div class="poem-content-side">
                <p class="content-text">{{ dailyPoem.content }}</p>
              </div>

              <div class="poem-meta-side">
                <div class="meta-wrapper">
                  <h1 class="poem-title-vertical">{{ dailyPoem.title }}</h1>
                  <div class="meta-divider"></div>
                  <span class="author-tag-vertical theme-color">{{ dailyPoem.author }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 操作栏 -->
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
const reviews = ref([])
const newComment = ref('')
const newRating = ref(5)
const userProfile = ref(null)

const fetchUserProfile = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/user_preference/${currentUser}`)
    userProfile.value = res.data
  } catch(e) { console.error(e) }
}

const getAnotherPoem = async () => {
  const currentId = dailyPoem.value ? dailyPoem.value.id : ''
  dailyPoem.value = null
  try {
    // 调用智能换诗接口，并传入当前ID以去重
    const res = await axios.get(`http://127.0.0.1:5000/api/recommend_one/${currentUser}?current_id=${currentId}`)
    dailyPoem.value = res.data
    fetchReviews(dailyPoem.value.id)
  } catch (e) { 
    ElMessage.error('寻诗失败')
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

const jumpToPoem = async (title) => {
  dailyPoem.value = null
  try {
    // 这里我们简单处理，从已有的 poems 列表中找，或者去后端查
    // 后端目前没有直接按 title 查的接口，但我们可以先模糊匹配或者查全部
    const res = await axios.get('http://127.0.0.1:5000/api/poems')
    const target = res.data.find(p => p.title === title)
    if (target) {
      dailyPoem.value = target
      fetchReviews(target.id)
      showSidebar.value = false
      ElMessage.success(`已为您呈上《${title}》`)
    }
  } catch(e) {
    ElMessage.error('寻诗失败')
  }
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

/* 顶部画像标签：替代侧边栏 */
.header-preference-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 15px;
  margin-right: 20px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.aura-icon {
  font-size: 14px;
  color: var(--accent-red);
  opacity: 0.6;
}

.aura-text {
  font-size: 12px;
  letter-spacing: 0.1em;
  color: #888;
  font-weight: 300;
}

/* 主题库样式 */
.system-topics-gallery {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 0 5px;
}

.topic-capsule {
  background: rgba(0,0,0,0.02);
  border-radius: 4px;
  padding: 12px;
  border-left: 2px solid var(--accent-red);
}

.topic-id {
  font-size: 10px;
  color: var(--accent-red);
  font-weight: bold;
  display: block;
  margin-bottom: 4px;
}

.topic-keywords {
  font-size: 13px;
  color: #666;
  letter-spacing: 1px;
}

/* 智能推荐横幅 */
.smart-rec-banner {
  position: absolute;
  top: -40px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--accent-red);
  background: rgba(166, 27, 27, 0.05);
  padding: 6px 15px;
  border-radius: 20px;
  opacity: 0.8;
  animation: fade-in 1s;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 0.8; transform: translateY(0); }
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
.poem-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.poem-display-split {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-start;
  gap: 120PX;
  width: 100%;
  max-width: 1100px;
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
}

.poem-main-body {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 120PX;
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 当有雅评时，整体布局略微左移或压缩 */
.poem-display-split.with-reviews {
  gap: 60PX;
}

@media (max-width: 1200px) {
  .poem-display-split.with-reviews .poem-main-body {
    transform: scale(0.9);
  }
}

@media (max-width: 900px) {
  .poem-display-split {
    flex-direction: column-reverse;
    align-items: center;
    gap: 40px;
  }
  .poem-main-body {
    flex-direction: column-reverse;
    align-items: center;
    gap: 40px;
  }
}

/* 左侧：内容容器 */
.poem-content-side {
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
  margin-top: 120px;
  display: flex;
  gap: 40px;
  width: 100%;
  justify-content: center;
}

@media (max-width: 900px) {
  .action-bar-floating {
    margin-top: 60px;
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
  transform: translateY(20px);
}
.poem-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 雅评：集成在页面内的版本 */
.marginalia-reviews-integrated {
  width: 350px;
  display: flex;
  flex-direction: column;
  margin-right: 40px;
  position: relative;
  /* 竖线优化：使用更具主题感的淡红色，并带有一点渐变感 */
  border-right: 1px solid rgba(166, 27, 27, 0.08); 
  padding-right: 40px;
  animation: slide-in 1s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 评分图标优化：深度覆盖 Element Plus 样式 */
.marginalia-input-zone :deep(.el-rate) {
  --el-rate-fill-color: var(--accent-red); /* 使用主题红 */
  --el-rate-void-color: rgba(0, 0, 0, 0.05);
  opacity: 0.8;
}

.marginalia-input-zone :deep(.el-rate__item) {
  cursor: pointer;
  transition: transform 0.3s;
}

.marginalia-input-zone :deep(.el-rate__item:hover) {
  transform: scale(1.2);
}

@keyframes slide-in {
  from { opacity: 0; transform: translateX(-30px); }
  to { opacity: 1; transform: translateX(0); }
}

/* 水印背景 */
.watermark-title {
  position: absolute;
  top: -60px;
  left: -20px;
  font-family: "Noto Serif SC", serif;
  font-size: 120PX;
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
  margin-bottom: 40px;
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
  max-height: 480px;
  overflow-y: auto;
  padding-right: 15px;
  mask-image: linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
  scrollbar-width: none;
}

.marginalia-scroll::-webkit-scrollbar {
  display: none;
}

.marginalia-item {
  margin-bottom: 40px;
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
}

.u-content-modern {
  font-size: 14PX;
  line-height: 1.8;
  color: #555;
  font-weight: 300;
  margin: 0;
}

.marginalia-input-zone {
  margin-top: 30px;
  padding-top: 20px;
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
}

.submit-ink:hover {
  opacity: 1;
}

/* 动画过渡 */
.marginalia-slide-enter-active, .marginalia-slide-leave-active {
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}
.marginalia-slide-enter-from, .marginalia-slide-leave-to {
  width: 0;
  opacity: 0;
  margin-right: 0;
  padding-right: 0;
}
</style>
