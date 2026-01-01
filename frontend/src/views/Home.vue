<template>
  <div class="home-container">

    <!-- 顶部导航 -->
    <el-header class="top-nav">
      <div class="nav-left">
        <div class="site-branding">
          <span class="logo-text">荐诗</span>
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

    <!-- 主舞台：启用纵向滚动 -->
    <el-main class="main-stage" ref="scrollContainer">
      <transition name="poem-fade" mode="out-in">
        <div v-if="dailyPoem" :key="dailyPoem.id" class="poem-wrapper">
          
          <!-- 智能推荐理由：作为滚动的起点 -->
          <div v-if="dailyPoem.recommend_reason" class="smart-rec-banner-inline">
             <el-icon><MagicStick /></el-icon>
             <span>{{ dailyPoem.recommend_reason }}</span>
          </div>

          <div class="poem-display-split" :class="{ 'with-reviews': showComments }">
            <!-- 雅评区域 -->
            <transition name="marginalia-slide">
              <div v-if="showComments" class="marginalia-reviews-integrated">
                <!-- ... (保持原有雅评内容) ... -->
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

            <!-- 核心展示区：内容居中，元数据在右 -->
            <div class="poem-main-body-horizontal">
              <div class="poem-content-center">
                <p class="content-text-horizontal">{{ formattedPoemContent }}</p>
              </div>

              <div class="poem-meta-right">
                <div class="meta-wrapper-vertical">
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
          <!-- ... -->
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>研墨铺纸中...</p>
        </div>
      </transition>
    </el-main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
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
const scrollContainer = ref(null) // 滚动容器引用

const formattedPoemContent = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.content) return ''
  // 核心清理：移除所有原始换行，完全由标点控制排版，确保对齐
  const cleanContent = dailyPoem.value.content.replace(/\s+/g, '').trim()
  return cleanContent.replace(/([，。！？；])/g, '$1\n')
})

const fetchUserProfile = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/user_preference/${currentUser}`)
    userProfile.value = res.data
  } catch(e) { console.error(e) }
}

const getAnotherPoem = async () => {
  const currentId = dailyPoem.value ? dailyPoem.value.id : ''
  dailyPoem.value = null
  
  // 滚动回顶部
  if (scrollContainer.value) {
    scrollContainer.value.$el.scrollTop = 0
  }

  try {
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
  padding: 0 40px; /* 减少水平内边距 */
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

/* 主舞台 - 全局滚动 */
.main-stage {
  flex: 1;
  overflow-y: auto;
  padding: 40px 40px 80px;
  scroll-behavior: smooth;
}

/* 智能推荐横幅 (改为流式布局) */
/* --- 主舞台整体布局优化 --- */
.main-stage {
  flex: 1;
  overflow-y: auto;
  padding: 60px 20px 100px;
  background-color: var(--stone-white);
  scroll-behavior: smooth;
}

/* 智能推荐横幅 (Zen风格) */
.smart-rec-banner-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 13px;
  color: var(--accent-red);
  letter-spacing: 0.1em;
  background: rgba(166, 27, 27, 0.03);
  padding: 12px 24px;
  border-radius: 2px;
  width: fit-content;
  margin: 0 auto 80px;
  border: 1px solid rgba(166, 27, 27, 0.1);
  animation: banner-slide-down 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes banner-slide-down {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.poem-wrapper {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  items-align: center;
  position: relative;
}

.poem-display-split {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  position: relative;
  min-height: 400px;
}

/* 核心内容区 */
.poem-main-body-horizontal {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 100px; /* 内容与落款的间距 */
  position: relative;
}

.poem-content-center {
  max-width: 600px;
  text-align: center;
}

.content-text-horizontal {
  font-family: "Noto Serif SC", serif;
  font-size: 20px;
  line-height: 2.2;
  color: #2c2c2c;
  letter-spacing: 0.15em;
  font-weight: 300;
  white-space: pre-wrap;
  display: inline-block;
  text-align: left;
}

/* 右侧落款 (垂直题识) */
.poem-meta-right {
  width: 60px;
  margin-top: 10px;
}

.meta-wrapper-vertical {
  writing-mode: vertical-rl;
  text-orientation: upright;
  display: flex;
  align-items: center;
  border-left: 1px solid rgba(166, 27, 27, 0.1);
  padding-left: 30px;
}

.poem-title-vertical {
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  font-weight: 500;
  color: var(--modern-black);
  margin: 0;
  letter-spacing: 0.4em;
}

.meta-divider {
  width: 1px;
  height: 30px;
  background: var(--accent-red);
  margin: 20px 0;
  opacity: 0.4;
}

.author-tag-vertical {
  font-size: 13px;
  letter-spacing: 0.6em;
  font-weight: 400;
  color: var(--accent-red);
  opacity: 0.9;
}

/* 底部操作 */
.action-bar-floating {
  margin-top: 100px;
  display: flex;
  gap: 50px;
  justify-content: center;
  padding-bottom: 50px;
}

.ghost-btn {
  border: none !important;
  background: transparent !important;
  font-size: 13px !important;
  letter-spacing: 0.25em;
  opacity: 0.5;
  color: var(--modern-black);
  transition: all 0.3s;
}

.ghost-btn:hover {
  opacity: 1;
  color: var(--accent-red) !important;
  transform: translateY(-2px);
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
  max-height: 40vh; /* 使用相对高度，防止溢出 */
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
