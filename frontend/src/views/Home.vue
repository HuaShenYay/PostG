<template>
  <div class="home-container">
    <!-- 顶部导航 (Floating) -->
    <nav class="top-nav glass-card">
      <div class="nav-brand">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      
      <!-- 推荐理由 - 居中显示 -->
      <div v-if="dailyPoem && dailyPoem.recommend_reason" class="nav-recommend">
        <n-icon><NSparkles /></n-icon>
        <span>{{ dailyPoem.recommend_reason }}</span>
      </div>
      
      <div class="nav-actions">
        <!-- 搜索 -->
        <div class="nav-btn-card" @click="openSearch" title="Search">
            <n-icon><NSearch /></n-icon>
            <span>搜索</span>
        </div>
        
        <!-- 观象 -->
        <div class="nav-btn-card" @click="goToAnalysis" title="Analysis">
             <n-icon><NDataLine /></n-icon>
             <span>观象</span>
        </div>

        <div class="divider-vertical"></div>

        <!-- User Profile -->
        <div class="user-area">
             <div v-if="currentUser !== '访客'" class="user-greeting" @click="logout" title="Logout">
                <span class="user-name">{{ currentUser }}</span>
                <span class="logout-hint">离席</span>
             </div>
             <div v-else class="login-prompt" @click="$router.push('/login')">
                Login
             </div>
        </div>
      </div>
    </nav>

    <!-- Main Stage -->
    <main class="main-stage">
      <transition name="poem-fade" mode="out-in">
        <div v-if="dailyPoem" :key="dailyPoem.id" class="content-wrapper">
            
            <!-- LEFT PANEL: Reviews/Comments -->
            <section class="panel-left glass-card">
                <div class="panel-header">
                    <h3><n-icon><NSend /></n-icon> 雅评</h3>
                </div>
                <div class="reviews-container">
                    <div v-if="reviews.length === 0" class="empty-state-mini">
                        <n-empty description="暂无雅评" />
                    </div>
                    <div v-else class="review-scroll">
                        <div v-for="(r, index) in reviews" :key="r.id" class="review-minimal">
                            <div class="review-header">
                                <span class="r-user">{{ r.user_id }}</span>
                                <n-rate readonly :value="r.rating" size="small" />
                            </div>
                            <p class="r-content">{{ r.comment }}</p>
                        </div>
                    </div>
                    
                    <!-- Simple Input - Fixed at Bottom -->
                    <div class="quick-comment" v-if="currentUser !== '访客'">
                        <n-input v-model:value="newComment" placeholder="留下雅言..." size="small" round />
                        <n-button circle size="small" type="primary" @click="submitComment" :disabled="!newComment">
                            <template #icon><n-icon><NSend /></n-icon></template>
                        </n-button>
                    </div>
                    <div v-else class="quick-comment login-hint">
                        <span>请先登录后发表评论</span>
                    </div>
                </div>
            </section>

            <!-- CENTER STAGE: The Poem -->
            <section class="center-stage">
                <div class="poem-card glass-card">
                    <!-- Poem Header - Horizontal Layout -->
                    <div class="poem-header-horizontal">
                        <h1 class="poem-title">{{ dailyPoem.title }}</h1>
                        <div class="author-info">
                            <span class="author-name">{{ dailyPoem.author }}</span>
                        </div>
                    </div>

                    <!-- Poem Content - Horizontal Reading with Vertical Layout -->
                    <div class="poem-body">
                         <div class="poem-verses-horizontal">
                            <div v-for="(line, index) in poemLines" :key="index" class="verse-line">
                                <span class="verse-text" :style="{ fontSize: poemFontSize }">{{ line }}</span>
                            </div>
                         </div>
                    </div>

                    <!-- Action Footer -->
                    <div class="poem-footer">
                        <div class="action-btn-circle" @click="getAnotherPoem" title="Next Poem">
                            <n-icon size="20"><NRefresh /></n-icon>
                        </div>
                    </div>
                </div>
            </section>

             <!-- RIGHT PANEL: Annotations/Helper -->
             <aside class="panel-right glass-card">
                 <div class="panel-header">
                     <h3><n-icon><NCompass /></n-icon> 注译</h3>
                 </div>
                 <div class="annotations-container">
                    <!-- Real Annotations -->
                    <div v-if="allusions && allusions.length > 0" class="helper-block">
                        <h4>注释</h4>
                        <div v-for="(note, idx) in allusions" :key="idx" style="margin-bottom: 12px;">
                             <span style="font-weight: 600; color: var(--text-primary);">{{ note.text }}</span>
                             <span style="margin: 0 4px; color: var(--text-tertiary);">:</span>
                             <span style="color: var(--text-secondary);">{{ note.explanation }}</span>
                             <div v-if="note.source" style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">{{ note.source }}</div>
                        </div>
                    </div>

                    <div v-if="poemHelper.author_bio" class="helper-block">
                        <h4>作者</h4>
                        <p>{{ poemHelper.author_bio }}</p>
                    </div>
                     <div v-if="poemHelper.appreciation" class="helper-block">
                        <h4>赏析</h4>
                        <p>{{ poemHelper.appreciation }}</p>
                    </div>
                    <div v-if="(!allusions || allusions.length === 0) && !poemHelper.author_bio && !poemHelper.appreciation" class="empty-state-mini">
                        <p>暂无鉴赏信息</p>
                    </div>
                 </div>
             </aside>

        </div>
        <div v-else class="loading-screen">
             <n-spin size="large" />
             <span class="loading-text">研墨...</span>
        </div>
      </transition>
    </main>

    <!-- Search Modal -->
    <n-modal v-model:show="searchVisible" class="custom-modal" :mask-closable="true" :closable="true">
        <n-card class="search-panel glass-card" :bordered="false">
            <div class="search-header">
                <h3>寻觅诗词</h3>
            </div>
            <n-input 
                v-model:value="searchQuery" 
                placeholder="输入标题、作者或诗句..." 
                size="large" 
                @keyup.enter="handleSearch" 
                class="search-bar-zen"
                clearable
            >
                 <template #prefix><n-icon><NSearch /></n-icon></template>
                 <template #suffix>
                     <n-button text @click="handleSearch" :disabled="!searchQuery.trim()">
                         <n-icon><NSearch /></n-icon>
                     </n-button>
                 </template>
            </n-input>
            <div v-if="searchLoading" class="search-loading">
                <n-spin size="medium" />
                <span>寻觅中...</span>
            </div>
            <div v-else-if="searchResults.length" class="search-results-list">
                 <div v-for="(item, index) in searchResults" :key="item.id" class="result-item" @click="selectPoemFromSearch(item)">
                     <div class="result-content">
                         <span class="r-title">{{ item.title }}</span>
                         <span class="r-author">{{ item.author }}</span>
                     </div>
                     <n-icon class="result-arrow"><NArrowRight /></n-icon>
                 </div>
            </div>
            <div v-else-if="searchQuery && !searchLoading" class="search-empty">
                <n-empty description="未找到相关诗词" />
            </div>
        </n-card>
    </n-modal>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
// 导入 Naive UI 组件和图标
import { 
  NModal, 
  NCard,
  NInput, 
  NButton, 
  NIcon, 
  NEmpty, 
  NRate,
  NTabs,
  NTabPane,
  NSpin
} from 'naive-ui'
import { 
  Search as NSearch, 
  ChevronForward as NArrowRight, 
  Close as NClose, 
  Refresh as NRefresh, 
  Compass as NCompass, 
  Sparkles as NSparkles,
  TrendingUp as NDataLine,
  Menu as NMenu,
  Send as NSend
} from '@vicons/ionicons5'

const router = useRouter()
const goToAnalysis = () => router.push('/analysis')
const currentUser = localStorage.getItem('user') || '访客'
const dailyPoem = ref(null)
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
// showSidePanel removed

// Computed: Split poem content into lines for vertical display
const poemLines = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.content) return []
  const cleanContent = dailyPoem.value.content.replace(/\s+/g, '').trim()
  return cleanContent.split(/([，。！？；])/).reduce((acc, part, i, arr) => {
    if (i % 2 === 0 && part) {
      acc.push(part + (arr[i + 1] || ''))
    }
    return acc
  }, []).filter(Boolean)
})

const formattedPoemContent = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.content) return ''
  const cleanContent = dailyPoem.value.content.replace(/\s+/g, '').trim()
  return cleanContent.replace(/([，。！？；])/g, '$1\n')
})

// 根据诗歌总字符数动态计算字体大小（无极适配）
const poemFontSize = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.content) return '20px'
  
  const totalChars = dailyPoem.value.content.replace(/\s+/g, '').length
  const maxChars = 150
  const ratio = Math.min(1, maxChars / totalChars)
  
  const baseSize = 24 * ratio
  const minSize = 16
  const maxSize = 24
  
  const finalSize = Math.max(minSize, Math.min(maxSize, baseSize))
  return `${finalSize}px`
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
    scrollContainer.value.scrollTop = 0
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
    const res = await axios.get(`http://127.0.0.1:5000/api/search_poems?q=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = res.data
    console.log('搜索结果:', res.data)
  } catch (e) {
    console.error('搜索失败:', e)
    searchResults.value = []
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
    scrollContainer.value.scrollTop = 0
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

// toggleSidePanel removed

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
/* ==================== CONTAINER ==================== */
.home-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--gradient-bg);
  position: relative;
}

/* ==================== NAVIGATION ==================== */
.top-nav {
  position: sticky;
  top: 20px;
  z-index: 1000;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  height: var(--header-height);
  margin: 20px 40px 0;
  max-width: calc(100% - 80px);
}

.nav-brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-brand:hover {
  color: var(--cinnabar-red);
}

.logo-text {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.3em;
  color: var(--ink-black);
  transition: color 0.2s ease;
}

.nav-brand:hover .logo-text {
  color: var(--cinnabar-red);
}

.edition-badge {
  font-size: 10px;
  font-weight: 300;
  letter-spacing: 0.15em;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.nav-recommend {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(207, 63, 53, 0.08);
  border-radius: 24px;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: "Noto Serif SC", serif;
  letter-spacing: 0.05em;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.nav-recommend:hover {
  background: rgba(207, 63, 53, 0.12);
}

.nav-recommend .n-icon {
  color: var(--cinnabar-red);
  font-size: 14px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-btn-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.02);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.05em;
}

.nav-btn-card:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--ink-black);
}

.nav-btn-card .n-icon {
  font-size: 16px;
  transition: all 0.2s ease;
}

.nav-btn-card:hover .n-icon {
  color: var(--cinnabar-red);
}

.nav-btn-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  transition: var(--transition-fast);
  color: var(--text-secondary);
}

.nav-btn-icon:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--ink-black);
}

.divider-vertical {
  width: 1px;
  height: 20px;
  background: rgba(0, 0, 0, 0.1);
}

.user-area {
  display: flex;
  align-items: center;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.2s ease;
}

.user-greeting:hover {
  background: rgba(0, 0, 0, 0.04);
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  letter-spacing: 0.05em;
}

.logout-hint {
  font-size: 11px;
  color: var(--cinnabar-red);
  opacity: 0.7;
  letter-spacing: 0.1em;
}

.login-prompt {
  font-size: 13px;
  color: var(--cinnabar-red);
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.2s ease;
}

.login-prompt:hover {
  background: rgba(207, 63, 53, 0.1);
}

/* ==================== MAIN STAGE ==================== */
.main-stage {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px 20px;
  min-height: calc(100vh - var(--header-height) - 40px);
  width: 100%;
}

.content-wrapper {
  width: 100%;
  max-width: 1600px;
  display: flex;
  gap: 24px;
  align-items: stretch;
  justify-content: center;
}

/* ==================== PANELS (LEFT/RIGHT) ==================== */
.panel-left, .panel-right {
  width: 320px;
  flex-shrink: 0;
  max-height: calc(100vh - var(--header-height) - 80px);
  overflow-y: hidden;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.panel-left {
  position: relative;
}

.panel-header {
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.panel-header h3 {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.panel-header h3:hover {
  color: var(--cinnabar-red);
}

.panel-header h3 .n-icon {
  transition: all 0.2s ease;
}

.panel-header h3:hover .n-icon {
  color: var(--cinnabar-red);
}

/* ==================== CENTER STAGE: POEM CARD ==================== */
.center-stage {
  flex: 1;
  min-width: 0;
  max-width: 700px;
  display: flex;
  justify-content: center;
  padding-top: 20px;
  padding-bottom: 40px;
}

.poem-card {
  width: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  overflow: hidden;
  
  background: var(--paper-white);
  
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    
  border-radius: var(--radius-sub);
  transition: opacity 0.2s ease;
  opacity: 0;
  animation: simpleFadeIn 0.3s ease forwards;
}

@keyframes simpleFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Poem Header - Horizontal Layout */
.poem-header-horizontal {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.poem-title {
  font-family: "Noto Serif SC", serif;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0.15em;
  color: var(--ink-black);
  margin: 0 0 10px 0;
  line-height: 1.4;
  text-align: center;
  transition: all 0.2s ease;
}

.poem-card:hover .poem-title {
  color: var(--cinnabar-red);
}

.author-info {
  padding: 6px 20px;
  background: var(--cinnabar-red);
  border-radius: 16px;
  color: white;
  transition: all 0.2s ease;
}

.author-info:hover {
  background: rgba(207, 63, 53, 0.8);
}

.author-name {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  font-weight: 500;
  color: white;
  letter-spacing: 0.1em;
}

/* Poem Body - Horizontal Reading with Vertical Layout */
.poem-body {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 16px 24px;
  overflow-y: auto;
  min-height: 0;
}

.poem-verses-horizontal {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 600px;
}

.verse-line {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.verse-text {
  font-family: "Noto Serif SC", serif;
  font-size: 20px;
  line-height: 1.6;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  text-align: center;
  transition: all 0.2s ease;
}

/* Poem Footer */
.poem-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.action-btn-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}

.action-btn-circle .n-icon {
  transition: all 0.2s ease;
}

.action-btn-circle:hover {
  background: var(--cinnabar-red);
  color: white;
}

.action-btn-circle:hover .n-icon {
  color: white;
}

/* ==================== REVIEWS & HELPERS ==================== */
.reviews-container,
.annotations-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - var(--header-height) - 100px);
  overflow: hidden;
}

.review-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 4px 16px 0;
  min-height: 0;
  max-height: calc(100vh - var(--header-height) - 180px);
}

.empty-state-mini {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  min-height: calc(100vh - var(--header-height) - 230px);
  max-height: calc(100vh - var(--header-height) - 180px);
  overflow-y: auto;
  transition: all 0.2s ease;
}

.empty-state-mini:hover {
  color: var(--text-secondary);
}

.review-minimal {
  padding: 14px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  transition: background-color 0.2s ease;
}


.review-minimal:hover {
  background: rgba(0, 0, 0, 0.04);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.r-user {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.review-minimal:hover .r-user {
  color: var(--cinnabar-red);
}

.r-content {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.review-minimal:hover .r-content {
  color: var(--text-primary);
}

.quick-comment {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 0 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  flex-grow: 0;
  height: auto;
  min-height: 50px;
  background: var(--paper-white);
  position: sticky;
  bottom: 0;
  z-index: 10;
  transition: all 0.2s ease;
}

.quick-comment:hover {
  background: rgba(255, 255, 255, 0.95);
}

.quick-comment.login-hint {
  justify-content: center;
  font-size: 13px;
  color: var(--text-tertiary);
  transition: all 0.2s ease;
}

.quick-comment.login-hint:hover {
  color: var(--text-secondary);
}

.helper-block {
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  margin-bottom: 8px;
  transition: background-color 0.2s ease;
}


.helper-block:hover {
  background: rgba(0, 0, 0, 0.04);
}

.helper-block h4 {
  font-family: "Noto Serif SC", serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0 0 8px 0;
  letter-spacing: 0.1em;
  transition: all 0.2s ease;
}

.helper-block:hover h4 {
  color: var(--cinnabar-red);
}

.helper-block p {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
  text-align: justify;
  transition: all 0.2s ease;
}

.helper-block:hover p {
  color: var(--text-primary);
}

/* ==================== SEARCH MODAL ==================== */
.custom-modal {
  --n-border-radius: 24px;
}

.search-panel {
  padding: 32px;
  min-width: 600px;
  max-width: 90vw;
  animation: simpleFadeIn 0.2s ease;
}

.search-header {
  margin-bottom: 24px;
  text-align: center;
}

.search-header h3 {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}


.search-bar-zen :deep(.n-input__wrapper) {
  border-radius: 24px;
  padding: 12px 20px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  background: var(--paper-white);
}

.search-bar-zen :deep(.n-input__wrapper):focus-within {
  border-color: var(--cinnabar-red);
  box-shadow: 0 0 0 3px rgba(207, 63, 53, 0.1);
  transform: scale(1.01);
}

.search-bar-zen :deep(.n-input__wrapper:hover) {
  border-color: rgba(207, 63, 53, 0.3);
}

.search-results-list {
  margin-top: 30px;
  max-height: 50vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-arrow {
  color: var(--text-tertiary);
  transition: all 0.2s ease;
}

.result-item:hover .result-arrow {
  color: var(--cinnabar-red);
}


.result-item:hover {
  background: rgba(207, 63, 53, 0.05);
}

.r-title {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.r-author {
  font-size: 13px;
  color: var(--cinnabar-red);
  letter-spacing: 0.1em;
  transition: all 0.2s ease;
}

.result-item:hover .r-author {
  color: var(--cinnabar-red);
}

.search-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
  padding: 40px;
  color: var(--text-tertiary);
  font-family: "Noto Serif SC", serif;
}

.search-empty {
  text-align: center;
  padding: 60px 20px;
  font-size: 16px;
  color: var(--text-tertiary);
  font-family: "Noto Serif SC", serif;
}

.search-empty :deep(.n-empty) {
  --n-icon-color: var(--text-tertiary);
}

.search-empty :deep(.n-empty__description) {
  font-family: "Noto Serif SC", serif;
  color: var(--text-tertiary);
}

/* ==================== LOADING ==================== */
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  min-height: 400px;
  animation: fadeInUp 0.3s ease;
}

.loading-text {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  color: var(--text-tertiary);
  letter-spacing: 0.3em;
  animation: pulse 2s ease-in-out infinite;
}

/* ==================== TRANSITIONS ==================== */
.poem-fade-enter-active {
  transition: all 0.3s ease;
}

.poem-fade-leave-active {
  transition: all 0.2s ease;
}

.poem-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.poem-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 1200px) {
  .content-wrapper {
    flex-direction: column;
    align-items: center;
  }

  .panel-left, .panel-right {
    width: 100%;
    max-width: 800px;
    position: static;
    max-height: calc(100vh - var(--header-height) - 80px);
  }
  
  .center-stage {
    order: -1; /* Keep poem on top for mobile/tablet */
    width: 100%;
  }
}

@media (max-width: 768px) {
  .top-nav {
    margin: 10px 10px 0;
    max-width: calc(100% - 20px);
    padding: 0 12px;
  }

  .nav-recommend {
    display: none;
  }

  .nav-btn-card {
    padding: 6px 12px;
    font-size: 12px;
  }

  .nav-btn-card span {
    display: none;
  }

  .nav-btn-card .n-icon {
    font-size: 18px;
  }

  .poem-header-vertical {
    position: static;
    writing-mode: horizontal-tb;
    text-orientation: initial;
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
    margin-bottom: 30px;
  }

  .poem-title {
    writing-mode: horizontal-tb;
    text-orientation: initial;
  }

  .author-seal {
    writing-mode: horizontal-tb;
    text-orientation: initial;
  }

  .poem-verses-vertical {
    writing-mode: horizontal-tb;
    text-orientation: initial;
    flex-direction: column;
  }

  .verse-line {
    writing-mode: horizontal-tb;
    text-orientation: initial;
  }

  .poem-body {
    padding: 20px;
  }

  .search-panel {
    min-width: auto;
    padding: 24px;
  }
}
</style>
