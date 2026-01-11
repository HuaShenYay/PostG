<template>
  <div class="home-container">
    <!-- 顶部导航 -->
    <n-layout-header class="top-nav glass-card">
      <div class="nav-left">
        <div class="site-branding">
          <span class="logo-text">荐诗</span>
          <span class="edition">二零二五 · 典藏版</span>
        </div>
      </div>
      <div class="nav-right">
        <!-- 搜诗入口 -->
        <div class="search-entry" @click="openSearch">
          <n-icon><NSearch /></n-icon>
          <span>搜诗</span>
        </div>

        <!-- 观象入口 -->
        <div class="search-entry" @click="goToAnalysis">
          <n-icon><NDataLine /></n-icon>
          <span>观象</span>
        </div>

        <!-- 用户画像：移至顶部，保持观看契合主题 -->
        <transition name="fade">
          <div v-if="userProfile" class="header-preference-tag">
            <n-icon class="aura-icon"><NCompass /></n-icon>
            <span class="aura-text">{{ userProfile.top_interest.join(' · ') }}</span>
          </div>
        </transition>

        <div class="user-meta-link">
          <span class="user-name-tag">{{ currentUser }}</span>
          <div class="meta-dot"></div>
          <span class="logout-link" @click="logout">离席</span>
        </div>
      </div>
    </n-layout-header>

    <!-- 全屏搜索蒙层 -->
    <n-modal
      v-model:show="searchVisible"
      preset="card"
      :style="{ width: '90%', maxWidth: '800px' }"
      @close="closeSearch"
      title=""
    >
      <div class="search-modal">
        <div class="search-input-wrapper">
            <n-input
              v-model:value="searchQuery"
              placeholder="输入题目、作者或诗句..."
              class="zen-search-input"
              :prefix-icon="NSearch"
              clearable
              @input="handleSearch"
              @keyup.enter="handleSearch"
            />
            <n-icon class="close-search-icon" @click="closeSearch"><NClose /></n-icon>
          </div>
        
        <div class="search-results-area" :loading="searchLoading">
          <div v-if="searchResults.length > 0" class="results-grid">
            <div 
              v-for="item in searchResults" 
              :key="item.id" 
              class="search-result-card glass-card-hover"
              @click="selectPoemFromSearch(item)"
            >
              <div class="card-title">{{ item.title }}</div>
              <div class="card-author">{{ item.author }}</div>
              <div class="card-snippet">{{ item.content.slice(0, 30) }}...</div>
            </div>
          </div>
          <n-empty v-else-if="searchQuery && !searchLoading" description="未觅得相关诗章" />
          <div v-else-if="!searchQuery" class="search-tip">欲寻何诗？</div>
        </div>
      </div>
    </n-modal>

    <!-- 主舞台：启用纵向滚动 -->
    <n-layout-content class="main-stage" ref="scrollContainer">
      <transition name="poem-fade" mode="out-in">
        <div v-if="dailyPoem" :key="dailyPoem.id" class="poem-wrapper">
          
          <!-- 智能推荐理由：作为滚动的起点 -->
          <div v-if="dailyPoem.recommend_reason" class="smart-rec-banner-inline">
             <n-icon><NMagicStick /></n-icon>
             <span>{{ dailyPoem.recommend_reason }}</span>
          </div>

          <div class="poem-display-split">
            <!-- 核心内容区 -->
            <div class="poem-main-content">
              <!-- 左侧诗句 -->
              <div class="poem-verses">
                <p class="content-text-horizontal">{{ formattedPoemContent }}</p>
              </div>
              
              <!-- 右侧标题和作者 -->
              <div class="poem-meta">
                <h1 class="poem-title-vertical">{{ dailyPoem.title }}</h1>
                <div class="meta-divider"></div>
                <span class="author-tag-vertical theme-color">{{ dailyPoem.author }}</span>
              </div>
            </div>
            
            <!-- 右侧模块容器 -->
            <div class="module-container">
              <!-- 诗解模块展开/收起按钮 -->
            <div 
              v-if="!showPoemHelper" 
              class="expand-helper-btn" 
              @click="togglePoemHelper"
            >
              <n-icon><NDocument /></n-icon>
              <span>原文诗解</span>
            </div>
            
            <!-- 诗歌辅助理解模块 - 右侧，可折叠 -->
            <transition name="slide">
              <div v-if="showPoemHelper" class="allusions-side-panel">
                <div class="watermark-title">诗解</div>
                <div class="module-header">
                   <span class="module-title">辅助理解</span>
                   <n-button 
                     circle 
                     quaternary 
                     @click="togglePoemHelper" 
                     class="module-close-btn"
                   >
                     <template #icon><n-icon><NClose /></n-icon></template>
                   </n-button>
                </div>
                  <div class="module-content">
                    <!-- 作者简介 -->
                    <div class="poem-helper-section">
                      <h3 class="helper-title">作者简介</h3>
                      <div class="helper-content">
                        <div v-if="poemHelper.author_bio" class="author-bio">
                          {{ poemHelper.author_bio }}
                        </div>
                        <n-empty v-else description="暂无作者简介" :image-size="30" />
                      </div>
                    </div>
                    
                    <!-- 诗歌背景 -->
                    <div class="poem-helper-section">
                      <h3 class="helper-title">诗歌背景</h3>
                      <div class="helper-content">
                        <div v-if="poemHelper.background" class="poem-background">
                          {{ poemHelper.background }}
                        </div>
                        <n-empty v-else description="暂无诗歌背景" :image-size="30" />
                      </div>
                    </div>
                    
                    <!-- 用典注释 -->
                    <div class="poem-helper-section">
                      <h3 class="helper-title">用典注释</h3>
                      <div class="helper-content">
                        <div v-if="allusions && allusions.length > 0" class="allusions-list">
                          <div v-for="(allusion, index) in allusions" :key="index" class="allusion-item">
                            <div class="allusion-title">
                              <span class="allusion-text">{{ allusion.text }}</span>
                              <span class="allusion-source">{{ allusion.source }}</span>
                            </div>
                            <div class="allusion-explanation">{{ allusion.explanation }}</div>
                          </div>
                        </div>
                        <n-empty v-else description="暂无用典注释" :image-size="30" />
                      </div>
                    </div>
                    
                    <!-- 诗歌赏析 -->
                    <div class="poem-helper-section">
                      <h3 class="helper-title">诗歌赏析</h3>
                      <div class="helper-content">
                        <div v-if="poemHelper.appreciation" class="poem-appreciation">
                          {{ poemHelper.appreciation }}
                        </div>
                        <n-empty v-else description="暂无诗歌赏析" :image-size="30" />
                      </div>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </div>
          
          <!-- 雅评模块 -->
          <div class="module-container">
            <transition name="slide-up">
              <div v-if="showComments" class="reviews-module">
                <div class="watermark-title">雅评</div>
                <div class="module-header">
                   <span class="module-title">{{ reviews.length }} 条雅赏</span>
                   <n-button 
                     circle 
                     quaternary 
                     @click="toggleComments" 
                     class="module-close-btn"
                   >
                     <template #icon><n-icon><NClose /></n-icon></template>
                   </n-button>
                </div>
                <div class="module-content">
                  <div v-if="reviews.length > 0" class="reviews-list">
                    <div v-for="(r, _) in reviews" :key="r.id" class="review-item">
                      <div class="item-header">
                        <span class="user-name">{{ r.user_id }}</span>
                        <div class="item-line"></div>
                        <span class="user-rating">{{ r.rating }}.0</span>
                      </div>
                      <p class="user-comment">{{ r.comment }}</p>
                    </div>
                  </div>
                  <n-empty v-else description="虚位以待" :image-size="40" />
                  
                  <!-- 评论输入区 -->
                  <div class="comment-input-area">
                    <n-input
                      v-model:value="newComment"
                      placeholder="在此处留墨..."
                      :bordered="false"
                      @keyup.enter="submitComment"
                    />
                    <div class="input-actions">
                      <n-rate v-model:value="newRating" size="small" />
                      <n-button 
                        type="primary" 
                        quaternary 
                        @click="submitComment"
                        :disabled="!newComment"
                      >
                        落笔
                      </n-button>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
          
          <!-- 操作栏 -->
          <div class="action-bar">
            <n-button @click="toggleComments" quaternary class="action-btn">
              雅评 ({{ reviews.length }})
            </n-button>
            <n-button @click="getAnotherPoem" quaternary class="action-btn">
              易章
            </n-button>
          </div>
        </div>

        <div v-else class="loading-state">
          <n-icon class="is-loading" :size="32"><NLoading /></n-icon>
          <p>研墨铺纸中...</p>
        </div>
      </transition>
    </n-layout-content>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
// 导入 Naive UI 组件和图标
import { 
  NLayoutHeader, 
  NLayoutContent, 
  NModal, 
  NInput, 
  NButton, 
  NIcon, 
  NEmpty, 
  NRate
} from 'naive-ui'
import { 
  Search as NSearch, 
  Close as NClose, 
  Document as NDocument, 
  Refresh as NLoading, 
  Compass as NCompass, 
  Sparkles as NMagicStick, 
  TrendingUp as NDataLine 
} from '@vicons/ionicons5'

const router = useRouter()
const goToAnalysis = () => router.push('/analysis')
const currentUser = localStorage.getItem('user') || '访客'
const dailyPoem = ref(null)
const showComments = ref(false)
const showPoemHelper = ref(false) // 控制诗歌辅助理解模块的显示/隐藏
const reviews = ref([])
const newComment = ref('')
const newRating = ref(5)
const userProfile = ref(null)
const scrollContainer = ref(null)
const skipCount = ref(0)
const allusions = ref([])
const poemHelper = ref({
  author_bio: '',
  background: '',
  appreciation: ''
})

// 搜索功能相关状态
const searchVisible = ref(false)
const searchQuery = ref('')
const searchLoading = ref(false)
const searchResults = ref([])

const formattedPoemContent = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.content) return ''
  // 核心清理：移除所有原始换行，完全由标点控制排版，确保对齐
  const cleanContent = dailyPoem.value.content.replace(/\s+/g, '').trim()
  return cleanContent.replace(/([，。！？；])/g, '$1\n')
})

const fetchUserProfile = async () => {
  if (currentUser === '访客') {
    userProfile.value = null
    return
  }
  
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/user_preference/${currentUser}`)
    userProfile.value = res.data
  } catch(e) { 
    console.error('获取用户画像失败:', e)
    userProfile.value = null
  }
}

const getAnotherPoem = async () => {
  const currentId = dailyPoem.value ? dailyPoem.value.id : ''
  dailyPoem.value = null
  
  // 滚动回顶部
  if (scrollContainer.value) {
    scrollContainer.value.$el.scrollTop = 0
  }

  try {
    skipCount.value++
    const res = await axios.get(`http://127.0.0.1:5000/api/recommend_one/${currentUser}?current_id=${currentId}&skip_count=${skipCount.value}`)
    dailyPoem.value = res.data
    fetchReviews(dailyPoem.value.id)
    fetchAllusions(dailyPoem.value.id)
    fetchPoemHelper(dailyPoem.value.id)
  } catch (e) { 
    console.error('获取诗歌失败:', e)
  }
}

const fetchReviews = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}/reviews`)
    reviews.value = res.data
  } catch(e) { console.error('获取评论失败:', e) }
}

const fetchAllusions = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}/allusions`)
    allusions.value = res.data
  } catch(e) {
    console.error('获取用典注释失败:', e)
    allusions.value = []
  }
}

const fetchPoemHelper = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}/helper`)
    poemHelper.value = res.data
  } catch(e) {
    console.error('获取诗歌辅助信息失败:', e)
    poemHelper.value = {
      author_bio: '',
      background: '',
      appreciation: ''
    }
  }
}

const toggleComments = () => { 
  showComments.value = !showComments.value 
}

const togglePoemHelper = () => {
  showPoemHelper.value = !showPoemHelper.value
}

// 搜索控制逻辑
const openSearch = () => {
  searchVisible.value = true
  searchQuery.value = ''
  searchResults.value = []
}

const closeSearch = () => {
  searchVisible.value = false
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/search_poems?q=${searchQuery.value}`)
    searchResults.value = res.data
  } catch (e) {
    console.error('搜索失败:', e)
  } finally {
    searchLoading.value = false
  }
}

const selectPoemFromSearch = (poem) => {
  dailyPoem.value = poem
  fetchReviews(poem.id)
  fetchAllusions(poem.id)
  fetchPoemHelper(poem.id)
  closeSearch()
  if (scrollContainer.value) {
    scrollContainer.value.$el.scrollTop = 0
  }
}

const submitComment = async () => {
  if(!newComment.value) {
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
      fetchReviews(dailyPoem.value.id)
      newComment.value = ''
    }
  } catch(e) {
    console.error('发表评论失败:', e)
  }
}

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
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
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  background-attachment: fixed;
}

/* 顶部导航 - 更加现代通透 */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  height: var(--header-height);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  z-index: 100;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

@media (max-width: 768px) {
  .top-nav { padding: 0 20px; }
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 40px;
}

.site-branding {
  display: flex;
  flex-direction: column;
}

.logo-text {
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.2em;
}

.edition {
  font-size: 10px;
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
  font-size: 13px;
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
  font-size: 13px;
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
  padding: 6px 16px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 20px;
  margin-right: 20px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: var(--transition-smooth);
  cursor: pointer;
}

.header-preference-tag:hover {
  background: rgba(166, 27, 27, 0.05);
  border-color: rgba(166, 27, 27, 0.1);
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

/* 搜索入口 */
.search-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 16px;
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.03);
  transition: var(--transition-smooth);
  margin-right: 10px;
}

.search-entry:hover {
  background: rgba(0, 0, 0, 0.06);
}

.search-entry .n-icon {
  font-size: 16px;
  color: var(--modern-black);
  opacity: 0.6;
}

.search-entry span {
  font-size: 12px;
  color: var(--modern-black);
  opacity: 0.6;
  letter-spacing: 0.1em;
}

/* 搜索蒙层 */
.search-modal {
  padding: 40px 20px;
}

.search-input-wrapper {
  position: relative;
  margin-bottom: 40px;
}

.zen-search-input :deep(.n-input__wrapper) {
  background: transparent;
  box-shadow: none;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 0;
  padding: 10px 0;
}

.zen-search-input :deep(.n-input__input-el) {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  letter-spacing: 0.1em;
}

.close-search-icon {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  font-size: 24px;
  cursor: pointer;
  opacity: 0.3;
  transition: var(--transition-smooth);
}

.close-search-icon:hover {
  opacity: 1;
}

.search-results-area {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px 0;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.search-result-card {
  padding: 25px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(15px);
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
}

.search-result-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  border-color: rgba(220, 53, 69, 0.3);
}

.card-title {
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  margin-bottom: 8px;
  color: var(--modern-black);
}

.card-author {
  font-size: 12px;
  color: var(--accent-red);
  margin-bottom: 12px;
  letter-spacing: 0.1em;
}

.card-snippet {
  font-size: 13px;
  color: #888;
  line-height: 1.6;
}

.search-tip {
  text-align: center;
  font-size: 18px;
  color: #ccc;
  font-family: "Noto Serif SC", serif;
  margin-top: 100px;
}

/* 主舞台整体布局优化 */
.main-stage {
  flex: 1;
  overflow-y: auto;
  padding: 40px 40px 80px;
  scroll-behavior: smooth;
  background: transparent;
}

/* 智能推荐横幅 (现代风格) */
.smart-rec-banner-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 14px;
  color: #6c757d;
  letter-spacing: 0.08em;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(15px);
  padding: 16px 32px;
  border-radius: 40px;
  width: fit-content;
  margin: 0 auto 40px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.smart-rec-banner-inline:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
}

.poem-wrapper {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.poem-display-split {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  position: relative;
  min-height: 400px;
  gap: 40px;
}

/* 核心内容区：左侧诗句，右侧标题作者 */
.poem-main-content {
  display: flex;
  align-items: flex-start;
  gap: 60px;
  flex: 1;
  max-width: 700px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

/* 左侧诗句 */
.poem-verses {
  flex: 1;
  text-align: center;
  padding: 0 20px;
}

.content-text-horizontal {
  font-family: "Noto Serif SC", serif;
  font-size: 26px;
  line-height: 2.8;
  color: #212529;
  letter-spacing: 0.12em;
  font-weight: 400;
  white-space: pre-wrap;
  display: inline-block;
  text-align: left;
  margin: 0;
  background: linear-gradient(135deg, #212529 0%, #495057 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 右侧标题和作者 */
.poem-meta {
  width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  writing-mode: vertical-rl;
  text-orientation: upright;
  padding-left: 30px;
  border-left: 2px solid linear-gradient(180deg, rgba(166, 27, 27, 0.3) 0%, rgba(166, 27, 27, 0.1) 100%);
  margin-top: 20px;
}

.poem-title-vertical {
  font-family: "Noto Serif SC", serif;
  font-size: 36px;
  font-weight: 600;
  color: var(--modern-black);
  margin: 0;
  letter-spacing: 0.6em;
  line-height: 1.8;
  background: linear-gradient(135deg, #dc3545 0%, #6f42c1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.meta-divider {
  width: 2px;
  height: 50px;
  background: linear-gradient(180deg, rgba(166, 27, 27, 0.6) 0%, rgba(166, 27, 27, 0.2) 100%);
  margin: 25px 0;
  border-radius: 1px;
}

.author-tag-vertical {
  font-size: 16px;
  letter-spacing: 0.9em;
  font-weight: 500;
  color: var(--accent-red);
  opacity: 0.9;
  background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 展开/收起按钮 */
.expand-helper-btn {
  width: 130px;
  height: auto;
  background: linear-gradient(135deg, rgba(220, 53, 69, 0.1) 0%, rgba(111, 66, 193, 0.1) 100%);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 12px;
  border: 1px solid rgba(220, 53, 69, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  writing-mode: vertical-rl;
  text-orientation: upright;
  padding: 25px 12px;
  box-shadow: 0 8px 25px rgba(220, 53, 69, 0.15);
  margin-top: 40px;
}

.expand-helper-btn:hover {
  background: linear-gradient(135deg, rgba(220, 53, 69, 0.15) 0%, rgba(111, 66, 193, 0.15) 100%);
  transform: translateX(8px) translateY(-2px);
  box-shadow: 0 12px 35px rgba(220, 53, 69, 0.25);
}

.expand-helper-btn .n-icon {
  font-size: 20px;
  color: #dc3545;
  opacity: 1;
}

.expand-helper-btn span {
  font-size: 13px;
  color: #dc3545;
  opacity: 1;
  letter-spacing: 3px;
  font-weight: 600;
}

/* 模块容器 - 用于控制动画 */
.module-container {
  overflow: hidden;
  flex-shrink: 0;
}

/* 模块通用样式 */
.allusions-side-panel, .reviews-module {
  width: 340px;
  display: flex;
  flex-direction: column;
  position: relative;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.allusions-side-panel:hover, .reviews-module:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.15);
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.module-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--accent-red);
  letter-spacing: 0.1em;
}

.module-close-btn {
  opacity: 0.5;
}

.module-close-btn:hover {
  opacity: 1;
}

.module-content {
  padding: 20px;
  overflow-y: auto;
  max-height: 500px;
}

/* 诗解模块样式 */
.allusions-side-panel {
  margin-top: 20px;
}

.poem-helper-section {
  margin-bottom: 30px;
}

.helper-title {
  font-size: 13px;
  letter-spacing: 0.2em;
  color: var(--accent-red);
  font-weight: 500;
  margin: 0 0 15px 0;
  opacity: 0.9;
  border-bottom: 1px solid rgba(166, 27, 27, 0.1);
  padding-bottom: 8px;
}

.helper-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 作者简介样式 */
.author-bio {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  font-weight: 300;
}

/* 诗歌背景样式 */
.poem-background {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  font-weight: 300;
}

/* 诗歌赏析样式 */
.poem-appreciation {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  font-weight: 300;
}

/* 用典注释项样式 */
.allusion-item {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border-left: 2px solid rgba(166, 27, 27, 0.2);
}

.allusion-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.allusion-text {
  font-family: "Noto Serif SC", serif;
  font-size: 15px;
  font-weight: 500;
  color: var(--modern-black);
  letter-spacing: 0.1em;
}

.allusion-source {
  font-size: 11px;
  color: var(--accent-red);
  opacity: 0.8;
  letter-spacing: 0.1em;
  font-weight: 400;
  white-space: nowrap;
}

.allusion-explanation {
  font-size: 13px;
  line-height: 1.6;
  color: #555;
  font-weight: 300;
}

/* 雅评模块样式 */
.reviews-module {
  width: 100%;
  max-width: 850px;
  margin-top: 30px;
  align-self: center;
}

.reviews-list {
  margin-bottom: 40px;
}

.review-item {
  margin-bottom: 35px;
  padding-bottom: 25px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.review-item:hover {
  transform: translateX(8px);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #dc3545;
  letter-spacing: 0.1em;
  background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.item-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(220, 53, 69, 0.3) 0%, rgba(111, 66, 193, 0.3) 100%);
}

.user-rating {
  font-size: 12px;
  color: #adb5bd;
  font-weight: 500;
}

.user-comment {
  font-size: 16px;
  line-height: 1.8;
  color: #495057;
  font-weight: 300;
  margin: 0;
  background: linear-gradient(135deg, #212529 0%, #6c757d 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 评论输入区 */
.comment-input-area {
  margin-top: 35px;
  padding-top: 25px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  padding: 20px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.04);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18px;
}

/* 操作栏 */
.action-bar {
  margin-top: 50px;
  display: flex;
  gap: 40px;
  justify-content: center;
  padding-bottom: 30px;
}

.action-btn {
  font-size: 15px;
  letter-spacing: 0.15em;
  color: var(--modern-black);
  opacity: 0.8;
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(15px);
  padding: 12px 28px;
  border-radius: 30px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.action-btn:hover {
  opacity: 1;
  color: #dc3545;
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(220, 53, 69, 0.15);
  border-color: rgba(220, 53, 69, 0.2);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 20px;
  color: #6c757d;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.is-loading {
  color: #dc3545;
  animation: spin 1s infinite linear;
  font-size: 40px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 水印背景 */
.watermark-title {
  position: absolute;
  top: -20px;
  right: -10px;
  font-family: "Noto Serif SC", serif;
  font-size: 140px;
  color: rgba(220, 53, 69, 0.015); 
  font-weight: 900;
  pointer-events: none;
  user-select: none;
  z-index: 0;
  line-height: 1;
  transform: rotate(15deg);
  backdrop-filter: blur(5px);
}

/* 主题色 */
.theme-color {
  color: var(--accent-red);
}

/* 动画效果 - 使用 Naive UI 内置动画 */
.poem-fade-enter-active,
.poem-fade-leave-active {
  transition: all 0.5s ease;
}

.poem-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.poem-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 侧边栏滑入/滑出动画 - 更平滑的过渡 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
  width: 0;
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(30px);
  width: 0;
}

/* 底部模块滑入/滑出动画 - 更平滑的过渡 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  opacity: 1;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
  max-height: 0;
  overflow: hidden;
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
  max-height: 0;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .poem-display-split {
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }
  
  .allusions-side-panel, .reviews-module {
    width: 100%;
    max-width: 600px;
  }
  
  .poem-main-content {
    flex-direction: column;
    align-items: center;
    gap: 40px;
  }
  
  .poem-meta {
    writing-mode: horizontal-tb;
    text-orientation: initial;
    width: 100%;
    flex-direction: row;
    justify-content: center;
    align-items: center;
    padding: 20px 0;
    border-left: none;
    border-top: 1px solid rgba(166, 27, 27, 0.1);
  }
  
  .poem-title-vertical {
    font-size: 28px;
    writing-mode: horizontal-tb;
    text-orientation: initial;
  }
  
  .meta-divider {
    width: 30px;
    height: 1px;
    margin: 0 20px;
  }
  
  .author-tag-vertical {
    writing-mode: horizontal-tb;
    text-orientation: initial;
  }
  
  .expand-helper-btn {
    writing-mode: horizontal-tb;
    text-orientation: initial;
    width: 100%;
    height: 50px;
    border-radius: 8px;
    border: 1px solid rgba(166, 27, 27, 0.15);
    margin-top: 20px;
    padding: 10px 20px;
  }
}

@media (max-width: 768px) {
  .main-stage {
    padding: 40px 20px 80px;
  }
  
  .content-text-horizontal {
    font-size: 20px;
    line-height: 2.2;
  }
  
  .poem-title-vertical {
    font-size: 24px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 20px;
    align-items: center;
  }
}
</style>