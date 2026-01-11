<template>
  <div class="home-container">
    <!-- 顶部导航 (Floating) -->
    <nav class="top-nav glass-card anim-enter" style="animation-delay: 0.1s">
      <div class="nav-brand">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      
      <div class="nav-actions">
        <!-- 搜索 -->
        <div class="nav-btn-icon" @click="openSearch" title="Search">
            <n-icon><NSearch /></n-icon>
        </div>
        
        <!-- 观象 -->
        <div class="nav-btn-icon" @click="goToAnalysis" title="Analysis">
             <n-icon><NDataLine /></n-icon>
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
            <section class="panel-left glass-card anim-enter" style="animation-delay: 0.3s">
                <div class="panel-header">
                    <h3><n-icon><NSend /></n-icon> 雅评</h3>
                </div>
                <div class="reviews-container">
                    <n-empty v-if="reviews.length === 0" description="暂无雅评" class="empty-state-mini" />
                    <div v-else class="review-scroll">
                        <div v-for="r in reviews" :key="r.id" class="review-minimal">
                            <div class="review-header">
                                <span class="r-user">{{ r.user_id }}</span>
                                <n-rate readonly :value="r.rating" size="small" />
                            </div>
                            <p class="r-content">{{ r.comment }}</p>
                        </div>
                    </div>
                    
                    <!-- Simple Input -->
                    <div class="quick-comment">
                        <n-input v-model:value="newComment" placeholder="留下雅言..." size="small" round />
                        <n-button circle size="small" type="primary" @click="submitComment" :disabled="!newComment">
                            <template #icon><n-icon><NSend /></n-icon></template>
                        </n-button>
                    </div>
                </div>
            </section>

            <!-- CENTER STAGE: The Poem -->
            <section class="center-stage anim-enter" style="animation-delay: 0.2s">
                <div class="poem-card glass-card">
                    <!-- Poem Meta (Title & Author) - Vertical -->
                    <div class="poem-header-vertical">
                        <h1 class="poem-title">{{ dailyPoem.title }}</h1>
                        <div class="author-seal">
                            <span class="author-name">{{ dailyPoem.author }}</span>
                        </div>
                    </div>

                    <!-- Poem Content - Vertical Flow -->
                    <div class="poem-body">
                         <div class="poem-verses-vertical">
                            <p v-for="(line, index) in poemLines" :key="index" class="verse-line">
                                {{ line }}
                            </p>
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
             <aside class="panel-right glass-card anim-enter" style="animation-delay: 0.4s">
                 <div class="panel-header">
                     <h3><n-icon><NCompass /></n-icon> 注译</h3>
                 </div>
                 <div class="annotations-container">
                    <div v-if="poemHelper.author_bio" class="helper-block">
                        <h4>作者</h4>
                        <p>{{ poemHelper.author_bio }}</p>
                    </div>
                     <div v-if="poemHelper.appreciation" class="helper-block">
                        <h4>赏析</h4>
                        <p>{{ poemHelper.appreciation }}</p>
                    </div>
                    <div v-if="!poemHelper.author_bio && !poemHelper.appreciation" class="empty-state-mini">
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
    <n-modal v-model:show="searchVisible" class="custom-modal">
        <div class="search-panel glass-card">
            <n-input v-model:value="searchQuery" placeholder="寻觅诗词..." size="large" @keyup.enter="handleSearch" class="search-bar-zen">
                 <template #prefix><n-icon><NSearch /></n-icon></template>
            </n-input>
            <div class="search-results-list" v-if="searchResults.length">
                 <div v-for="item in searchResults" :key="item.id" class="result-item" @click="selectPoemFromSearch(item)">
                     <span class="r-title">{{ item.title }}</span>
                     <span class="r-author">{{ item.author }}</span>
                 </div>
            </div>
            <div v-else-if="searchQuery && !searchLoading" class="search-empty">...</div>
        </div>
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
  Close as NClose, 
  Refresh as NRefresh, 
  Compass as NCompass, 
  Sparkles as NMagicStick, 
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
  top: 0;
  z-index: 1000;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 clamp(20px, 5vw, 60px);
  height: var(--header-height);
}

.nav-brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.logo-text {
  font-family: "Noto Serif SC", serif;
  font-size: clamp(20px, 3vw, 28px);
  font-weight: 600;
  letter-spacing: 0.3em;
  color: var(--ink-black);
}

.edition-badge {
  font-size: 10px;
  font-weight: 300;
  letter-spacing: 0.15em;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
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
  transform: scale(1.1);
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
  transition: var(--transition-fast);
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
  transition: var(--transition-fast);
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
  padding: 40px 20px;
  min-height: calc(100vh - var(--header-height));
  width: 100%;
}

.content-wrapper {
  width: 100%;
  max-width: 1600px;
  display: flex;
  gap: 24px;
  align-items: flex-start;
  justify-content: center;
}

/* ==================== PANELS (LEFT/RIGHT) ==================== */
.panel-left, .panel-right {
  width: 340px;
  flex-shrink: 0;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  padding: 24px;
  position: sticky;
  top: 90px;
}

.panel-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.panel-header h3 {
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ==================== CENTER STAGE: POEM CARD ==================== */
.center-stage {
  flex: 1;
  min-width: 0;
  max-width: 800px;
  display: flex;
  justify-content: center;
}

.poem-card {
  width: 100%;
  padding: clamp(50px, 8vw, 80px);
  display: flex;
  flex-direction: column;
  gap: 50px;
  position: relative;
  min-height: 700px;
  
  /* Paper Texture & Depth */
  background: var(--paper-white);
  background-image: 
    linear-gradient(to right, rgba(0,0,0,0.02) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0,0,0,0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  
  box-shadow: 
    0 1px 2px rgba(0,0,0,0.05), 
    0 20px 50px rgba(0,0,0,0.05),
    0 0 0 1px rgba(0,0,0,0.02);
    
  border-radius: 4px;
}

.poem-card::before {
  content: '';
  position: absolute;
  inset: 0;
  box-shadow: inset 0 0 80px rgba(255,255,255,0.8);
  pointer-events: none;
  border-radius: inherit;
}

/* Poem Header - Vertical Title & Author */
.poem-header-vertical {
  position: absolute;
  right: 50px;
  top: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  writing-mode: vertical-rl;
  text-orientation: upright;
  gap: 20px;
}

.poem-title {
  font-family: "Noto Serif SC", serif;
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 600;
  letter-spacing: 0.2em;
  color: var(--ink-black);
  margin: 0;
  line-height: 1.6;
}

.author-seal {
  padding: 12px 6px;
  background: var(--cinnabar-red); /* Simplified background */
  border-radius: 6px;
  color: white;
  writing-mode: vertical-rl;
  text-orientation: upright;
}

.author-name {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  font-weight: 500;
  color: white;
  letter-spacing: 0.1em;
}

/* Poem Body - Vertical Verses */
.poem-body {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 100px 20px 20px;
}

.poem-verses-vertical {
  display: flex;
  flex-direction: row-reverse;
  gap: clamp(36px, 5vw, 60px); /* Increased gap for better static read */
  writing-mode: vertical-rl;
  text-orientation: upright;
}

.verse-line {
  font-family: "Noto Serif SC", serif;
  font-size: clamp(22px, 2.8vw, 28px);
  line-height: 2;
  letter-spacing: 0.2em;
  color: var(--text-primary);
  margin: 0;
  /* Removed transition and hover effect */
}

/* Poem Footer */
.poem-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.action-btn-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.3s;
  color: var(--text-secondary);
}

.action-btn-circle:hover {
  background: var(--cinnabar-red);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 8px 20px rgba(207, 63, 53, 0.3);
}

/* ==================== REVIEWS & HELPERS ==================== */
.reviews-container,
.annotations-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.review-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;
}

.review-minimal {
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  border-left: 3px solid var(--cinnabar-red);
  transition: transform 0.2s;
}

.review-minimal:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: translateX(2px);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.r-user {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.r-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

.quick-comment {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.helper-block {
  padding: 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  margin-bottom: 8px;
}

.helper-block h4 {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0 0 10px 0;
  letter-spacing: 0.1em;
}

.helper-block p {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin: 0;
  text-align: justify;
}

.empty-state-mini {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}

/* ==================== SEARCH MODAL ==================== */
.search-panel {
  padding: 40px;
  min-width: 600px;
  max-width: 90vw;
}

.search-bar-zen :deep(.n-input__wrapper) {
  border-radius: 24px;
  padding: 12px 20px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  transition: var(--transition-fast);
}

.search-bar-zen :deep(.n-input__wrapper):focus-within {
  border-color: var(--cinnabar-red);
  box-shadow: 0 0 0 3px rgba(207, 63, 53, 0.1);
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
  transition: var(--transition-fast);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-item:hover {
  background: rgba(207, 63, 53, 0.05);
  transform: translateX(8px);
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
}

.search-empty {
  text-align: center;
  padding: 60px 20px;
  font-size: 16px;
  color: var(--text-tertiary);
  font-family: "Noto Serif SC", serif;
}

/* ==================== LOADING ==================== */
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  min-height: 400px;
}

.loading-text {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  color: var(--text-tertiary);
  letter-spacing: 0.3em;
}

/* ==================== TRANSITIONS ==================== */
.poem-fade-enter-active,
.poem-fade-leave-active {
  transition: opacity 0.6s var(--ease-smooth), transform 0.6s var(--ease-smooth);
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
    max-height: none;
  }
  
  .center-stage {
    order: -1; /* Keep poem on top for mobile/tablet */
    width: 100%;
  }
}

@media (max-width: 768px) {
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
    padding: 30px 20px;
  }
}
</style>
