<template>
  <div class="home-container">
    <!-- 顶部导航 (Floating) -->
    <nav class="top-nav glass-card">
      <div class="nav-brand">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      
      <div class="nav-actions">
        <!-- 搜索 -->
        <div class="nav-btn-card" @click="router.push('/search')" title="Search">
            <n-icon><NSearch /></n-icon>
            <span>搜索</span>
        </div>
        
        <!-- 个人万象 -->
        <div class="nav-btn-card" @click="goToPersonalAnalysis" title="Personal Analysis">
             <n-icon><NPersonOutline /></n-icon>
             <span>个人万象</span>
        </div>
        
        <!-- 全站万象 -->
        <div class="nav-btn-card" @click="goToGlobalAnalysis" title="Global Analysis">
             <n-icon><NGlobeOutline /></n-icon>
             <span>全站万象</span>
        </div>

        <div class="divider-vertical"></div>

        <!-- User Profile -->
        <div class="user-area">
             <div v-if="currentUser !== '访客'" class="user-greeting" @click="$router.push('/profile')" title="个人信息">
                <n-icon class="user-icon"><NPersonOutline /></n-icon>
                <span class="user-name">{{ currentUser }}</span>
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
        <div v-if="dailyPoem" :key="dailyPoem.id" class="unified-card glass-card">
            <!-- 三个功能区域 -->
            <div class="unified-header">
                <!-- 左侧：雅评 -->
                <div class="unified-section left-section">
                    <div class="section-header">
                        <h3><n-icon><NSend /></n-icon> 雅评</h3>
                    </div>
                    <div class="section-content reviews-content">
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
                        
                        <!-- 评论输入框 -->
                        <div class="quick-comment" v-if="currentUser !== '访客'">
                            <n-input v-model:value="newComment" placeholder="留下雅言..." size="small" round />
                            <n-button circle size="small" @click="submitComment" :disabled="!newComment" class="submit-btn">
                                <template #icon><n-icon><NSend /></n-icon></template>
                            </n-button>
                        </div>
                        <div v-else class="quick-comment login-hint">
                            <span>请先登录后发表评论</span>
                        </div>
                    </div>
                </div>

                <!-- 中间：诗歌内容 -->
                <div class="unified-section center-section">
                    <div class="section-header">
                        <h3><n-icon><NCompass /></n-icon> 诗词</h3>
                    </div>
                    <div class="section-content poem-content">
                        <!-- 诗歌标题和作者 -->
                        <div class="poem-header-horizontal">
                                <h1 class="poem-title">{{ dailyPoem.title }}</h1>
                            <div class="author-section">
                                <div class="author-info">
                                    <span class="author-name">{{ dailyPoem.author }}</span>
                                </div>
                                <!-- 推荐理由 - 并排放置 -->
                                <div v-if="dailyPoem && dailyPoem.recommend_reason" class="recommend-reason">
                                    <n-icon><NSparkles /></n-icon>
                                    <span>{{ dailyPoem.recommend_reason }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- 诗歌正文 -->
                        <div class="poem-body">
                            <div class="poem-verses-horizontal">
                                <div v-for="(line, index) in poemLines" :key="index" class="verse-line">
                                    <span class="verse-text" :style="{ fontSize: poemFontSize }">{{ line }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- 操作按钮 -->
                        <div class="poem-footer">
                            <div class="action-btn-circle" @click="getAnotherPoem" title="Next Poem">
                                <n-icon size="20"><NRefresh /></n-icon>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 右侧：诗韵可视化 -->
                <div class="unified-section right-section">
                    <div class="section-header">
                        <h3><n-icon><NDataLine /></n-icon> 诗韵</h3>
                    </div>
                    <div class="section-content viz-content">
                            <!-- 1. 文体特征 (Moved to Top) -->
                            <div class="viz-card" v-if="dailyPoem">
                                <div class="viz-title">文体特征</div>
                                <div class="feature-tags">
                                    <n-tag :bordered="false" type="error" size="small">{{ dailyPoem.rhythm_type }}</n-tag>
                                    <n-tag v-if="dailyPoem.dynasty" :bordered="false" type="warning" size="small">{{ dailyPoem.dynasty }}</n-tag>
                                    <n-tag v-if="dailyPoem.rhythm_name && dailyPoem.rhythm_name !== '未知'" :bordered="false" type="info" size="small">{{ dailyPoem.rhythm_name }}</n-tag>
                                </div>
                            </div>

                            <!-- 2. 意境画像 (ECharts Radar) -->
                            <div class="viz-card">
                                <div class="viz-title">意境画像 (Atmosphere Profile)</div>
                                <div ref="sentimentRef" style="height: 180px;"></div>
                            </div>

                            <!-- 3. 音律心跳 (ECharts Line) -->
                            <div class="viz-card">
                                <div class="viz-title">音律心跳 (Rhythmic Wave)</div>
                                <div ref="heartbeatRef" style="height: 80px;"></div>
                            </div>

                            <!-- 4. 韵脚序列 (Compact) -->
                            <div class="viz-card" v-if="poemAnalysis.rhymes && poemAnalysis.rhymes.length">
                                <div class="viz-title">韵脚序列 (Rhyme Seq)</div>
                                <div class="rhyme-flow-compact">
                                    <span v-for="r in poemAnalysis.rhymes" :key="r.line" 
                                          class="rhyme-capsule" :class="{ 'gold-border': r.line % 2 === 0 }">
                                        {{ r.char }}<small>/{{ r.rhyme }}/</small>
                                    </span>
                                </div>
                            </div>
                    </div>
                </div>
            </div>
        </div>
        <div v-else class="loading-screen">
             <n-spin size="large" />
             <span class="loading-text">研墨...</span>
        </div>
      </transition>
    </main>


  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'
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
  NSpin,
  NProgress,
  NTag
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
  Send as NSend,
  PersonOutline as NPersonOutline,
  GlobeOutline as NGlobeOutline
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()

// 导航函数
const goToPersonalAnalysis = () => router.push('/personal-analysis')
const goToGlobalAnalysis = () => router.push('/global-analysis')
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
const poemAnalysis = ref({ 
  matrix: [], 
  rhymes: [], 
  chart_data: { 
    tonal_sequence: [], 
    char_labels: [], 
    sentiment: [], 
    colors: [] 
  } 
})

const heartbeatRef = ref(null)
const sentimentRef = ref(null)
let hbChart = null
let stChart = null

const initCharts = () => {
  // 1. 音律心跳
  if (heartbeatRef.value && poemAnalysis.value?.chart_data?.tonal_sequence?.length) {
    if (hbChart) hbChart.dispose()
    hbChart = echarts.init(heartbeatRef.value)
    hbChart.setOption({
      grid: { top: 10, bottom: 20, left: 10, right: 10 },
      xAxis: { type: 'category', data: poemAnalysis.value.chart_data.char_labels, show: false },
      yAxis: { show: false, min: -1.5, max: 1.5 },
      series: [{
        data: poemAnalysis.value.chart_data.tonal_sequence,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#A61B1B', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(166, 27, 27, 0.4)' },
            { offset: 1, color: 'rgba(166, 27, 27, 0)' }
          ])
        }
      }],
      tooltip: { trigger: 'axis', formatter: p => `${p[0].name}: ${p[0].value === 1 ? '平' : '仄'}` }
    })
  }

  // 2. 意境雷达
  if (sentimentRef.value && poemAnalysis.value?.chart_data?.sentiment?.length) {
    if (stChart) stChart.dispose()
    stChart = echarts.init(sentimentRef.value)
    const indicators = poemAnalysis.value.chart_data.sentiment.map(s => ({ name: s.name, max: 100 }))
    const values = poemAnalysis.value.chart_data.sentiment.map(s => s.value)
    stChart.setOption({
      radar: {
        indicator: indicators,
        shape: 'circle',
        splitNumber: 3,
        axisName: { color: '#666', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(166, 27, 27, 0.1)' } },
        splitArea: { show: false },
        axisLine: { lineStyle: { color: 'rgba(166, 27, 27, 0.1)' } }
      },
      series: [{
        type: 'radar',
        data: [{
          value: values,
          itemStyle: { color: '#A61B1B' },
          areaStyle: { color: 'rgba(166, 27, 27, 0.3)' }
        }]
      }]
    })
  }
}

const updatePoemCharts = () => {
  // 使用 nextTick 并稍微延迟，确保 DOM 稳定且尺寸就绪
  nextTick(() => {
    setTimeout(initCharts, 200)
  })
}

const handleResize = () => {
  if (hbChart) hbChart.resize()
  if (stChart) stChart.resize()
}

let resizeObserver = null

onMounted(() => {
  window.addEventListener('resize', handleResize)
  
  // 使用 ResizeObserver 监听容器，防止尺寸为0时加载失败
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      handleResize()
    })
    if (heartbeatRef.value) resizeObserver.observe(heartbeatRef.value)
    if (sentimentRef.value) resizeObserver.observe(sentimentRef.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeObserver) resizeObserver.disconnect()
  if (hbChart) hbChart.dispose()
  if (stChart) stChart.dispose()
})

// 可视化数据
const dynastyData = ref([
  { name: '唐', count: 156, percentage: 85, color: 'linear-gradient(90deg, #ff6b6b, #ee5a6f)' },
  { name: '宋', count: 89, percentage: 65, color: 'linear-gradient(90deg, #4ecdc4, #44a08d)' },
  { name: '元', count: 45, percentage: 40, color: 'linear-gradient(90deg, #45b7d1, #2196f3)' },
  { name: '明', count: 67, percentage: 55, color: 'linear-gradient(90deg, #f9ca24, #f0932b)' }
])

const themeTags = ref([
  { name: '山水', size: 18, color: '#67c3cc' },
  { name: '月色', size: 16, color: '#ff9a9e' },
  { name: '春风', size: 14, color: '#a8e6cf' },
  { name: '秋思', size: 15, color: '#ffd93d' },
  { name: '梅雪', size: 13, color: '#c7ceea' },
  { name: '江流', size: 12, color: '#ff8b94' },
  { name: '松风', size: 11, color: '#b4a7d6' },
  { name: '竹影', size: 10, color: '#8fcaca' }
])

const timeData = ref([
  { angle: 0, height: 30, color: '#ffeaa7' },
  { angle: 45, height: 60, color: '#fab1a0' },
  { angle: 90, height: 45, color: '#ff7675' },
  { angle: 135, height: 75, color: '#fd79a8' },
  { angle: 180, height: 40, color: '#a29bfe' },
  { angle: 225, height: 55, color: '#6c5ce7' },
  { angle: 270, height: 65, color: '#74b9ff' },
  { angle: 315, height: 35, color: '#81ecec' }
])

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

const parsedTonalSummary = computed(() => {
  if (!dailyPoem.value || !dailyPoem.value.tonal_summary) return { ping: 0, ze: 0, ratio: 0 }
  try {
    return JSON.parse(dailyPoem.value.tonal_summary)
  } catch (e) {
    return { ping: 0, ze: 0, ratio: 0 }
  }
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
    fetchPoemAnalysis(dailyPoem.value.id)
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

const fetchPoemAnalysis = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}/analysis`)
    poemAnalysis.value = res.data
    // 触发图表更新
    updatePoemCharts()
  } catch(e) { 
    console.error('获取诗歌分析失败:', e)
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

const fetchPoemById = async (id) => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/poem/${id}`)
    dailyPoem.value = res.data
    fetchReviews(id)
    fetchAllusions(id)
    fetchPoemHelper(id)
    fetchPoemAnalysis(id)
  } catch (e) {
    console.error('获取指定诗歌失败:', e)
  }
}

onMounted(() => {
  if (route.query.poemId) {
    fetchPoemById(route.query.poemId)
  } else {
    getAnotherPoem()
  }
  fetchUserProfile()
})

// 监听路由参数变化，支持搜索结果切换
watch(() => route.query.poemId, (newId) => {
  if (newId) {
    fetchPoemById(newId)
  }
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


/* ==================== MAIN STAGE ==================== */
.main-stage {
  flex: 1;
  display: flex;
  align-items: flex-start; /* Fix top position */
  justify-content: center;
  padding: 45px var(--content-padding);
  width: 100%;
  overflow-y: hidden;
}

/* ==================== UNIFIED CARD ==================== */
.unified-card {
  width: 100%;
  max-width: var(--content-max-width);
  height: calc(100vh - var(--header-height) - 90px); /* Taller at the bottom */
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  
  background: var(--paper-white);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-radius: var(--radius-main);
  transition: opacity 0.2s ease;
  opacity: 0;
  animation: simpleFadeIn 0.3s ease forwards;
}

.unified-header {
  display: flex;
  flex: 1;
  height: 100%;
  overflow: hidden;
  gap: 1px;
  background: rgba(0, 0, 0, 0.05);
}

.unified-section {
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--paper-white);
}

.unified-section.left-section {
  width: 380px;
  flex-shrink: 0;
}

.unified-section.center-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.unified-section.right-section {
  width: 380px;
  flex-shrink: 0;
}

.section-header {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  background: rgba(248, 249, 250, 0.5);
}

.section-header h3 {
  font-family: "Noto Serif SC", serif;
  font-size: 17px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.section-header h3:hover {
  color: var(--cinnabar-red);
}

.section-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 28px;
}

.reviews-content {
  display: flex;
  flex-direction: column;
}

.poem-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  justify-content: flex-start;
  align-items: center;
  padding: 20px 24px;
}

.viz-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  padding: 0 8px;
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

/* 作者区域 - 并排布局 */
.author-section {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

/* 推荐理由 - 并排样式 */
.recommend-reason {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: linear-gradient(135deg, rgba(207, 63, 53, 0.08), rgba(207, 63, 53, 0.12));
  border-radius: 16px;
  color: var(--cinnabar-red);
  font-family: "Noto Serif SC", serif;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.05em;
  transition: all 0.3s ease;
  border: 1px solid rgba(207, 63, 53, 0.15);
  box-shadow: 0 2px 6px rgba(207, 63, 53, 0.08);
}

.recommend-reason:hover {
  background: linear-gradient(135deg, rgba(207, 63, 53, 0.12), rgba(207, 63, 53, 0.18));
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(207, 63, 53, 0.15);
}

.recommend-reason .n-icon {
  font-size: 12px;
  color: var(--cinnabar-red);
  animation: sparkle 2s ease-in-out infinite;
}

@keyframes sparkle {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

/* Poem Body - Horizontal Reading with Vertical Layout */
.poem-body {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 12px 24px 16px;
  min-height: 0;
  overflow-y: auto;
  max-height: calc(100% - 100px);
  width: 100%;
}

.poem-verses-horizontal {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 600px;
  text-align: center;
}

.verse-line {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 32px;
}

.verse-text {
  font-family: "Noto Serif SC", serif;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.8;
  letter-spacing: 0.05em;
  transition: all 0.2s ease;
  word-break: break-all;
  overflow-wrap: break-word;
}

/* Poem Footer */
.poem-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px 0 16px;
  flex-shrink: 0;
  position: relative;
}

.poem-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(207, 63, 53, 0.3), transparent);
}

.action-btn-circle {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(207, 63, 53, 0.1), rgba(207, 63, 53, 0.15));
  color: var(--cinnabar-red);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid rgba(207, 63, 53, 0.2);
  font-size: 22px;
  position: relative;
  overflow: hidden;
}

.action-btn-circle::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: var(--cinnabar-red);
  transform: translate(-50%, -50%);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.action-btn-circle:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 25px rgba(207, 63, 53, 0.25);
  border-color: var(--cinnabar-red);
}

.action-btn-circle:hover::before {
  width: 100%;
  height: 100%;
}

.action-btn-circle:hover .n-icon {
  color: white;
  transform: rotate(180deg);
  z-index: 1;
  position: relative;
}

.action-btn-circle .n-icon {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
  position: relative;
}

.action-btn-circle:active {
  transform: translateY(0) scale(0.98);
}


/* ==================== REVIEWS & HELPERS ==================== */
.reviews-container,
.annotations-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.review-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0 8px 16px 0;
  min-height: 0;
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
  min-height: 200px;
}

.empty-state-mini:hover {
  color: var(--text-secondary);
}

.review-minimal {
  padding: 18px 20px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  transition: background-color 0.2s ease;
  margin-bottom: 14px;
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
  gap: 12px;
  align-items: center;
  padding: 16px 0 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
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

/* 发送按钮 - 红色主题 */
.submit-btn {
  background: var(--cinnabar-red) !important;
  border-color: var(--cinnabar-red) !important;
  color: white !important;
  transition: all 0.3s ease !important;
}

.submit-btn:hover:not(:disabled) {
  background: rgba(207, 63, 53, 0.9) !important;
  border-color: rgba(207, 63, 53, 0.9) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(207, 63, 53, 0.3);
}

.submit-btn:active:not(:disabled) {
  background: rgba(207, 63, 53, 0.8) !important;
  transform: translateY(0);
}

.submit-btn:disabled {
  background: rgba(0, 0, 0, 0.1) !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
  color: rgba(0, 0, 0, 0.3) !important;
  cursor: not-allowed;
}

.submit-btn .n-icon {
  color: white !important;
}

/* ==================== VISUALIZATION PANEL ==================== */
.visualization-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
  padding: 4px;
}

.viz-card {
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sub);
  padding: 24px;
  transition: background-color 0.2s ease;
  margin-bottom: 18px;
}

.viz-card:last-child {
  margin-bottom: 0;
}

.viz-card:hover {
  background: rgba(0, 0, 0, 0.04);
}

.poem-title {
  font-family: "Noto Serif SC", serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--ink-black);
  margin: 0;
  letter-spacing: 0.1em;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.rhythm-tag {
  font-size: 14px;
  color: var(--cinnabar-red);
  background: rgba(166, 27, 27, 0.08);
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 500;
  border: 1px solid rgba(166, 27, 27, 0.2);
}

.author-section {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  justify-content: center;
}
/* 情感分析条形图 */
.sentiment-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sentiment-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sentiment-label {
  font-family: "Noto Serif SC", serif;
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 40px;
}

.sentiment-bar {
  flex: 1;
  height: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.sentiment-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.sentiment-value {
  font-size: 11px;
  color: var(--text-tertiary);
  min-width: 35px;
  text-align: right;
}

/* 朝代分布 */
.dynasty-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dynasty-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dynasty-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dynasty-name {
  font-family: "Noto Serif SC", serif;
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.dynasty-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.dynasty-bar {
  height: 4px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.dynasty-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 主题标签云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: center;
  padding: 12px;
}

.tag-item {
  font-family: "Noto Serif SC", serif;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: default;
  line-height: 1.2;
  padding: 4px 8px;
  border-radius: 6px;
}

.tag-item:hover {
  background: rgba(207, 63, 53, 0.1);
  transform: scale(1.05);
}

/* 时辰流转图 */
.time-chart {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.time-circle {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #ffeaa7 0deg, #fab1a0 45deg, #ff7675 90deg, #fd79a8 135deg, #a29bfe 180deg, #6c5ce7 225deg, #74b9ff 270deg, #81ecec 315deg, #ffeaa7 360deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.time-segment {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 50%;
  transform-origin: bottom center;
  border-radius: 1px;
  background: rgba(255, 255, 255, 0.3);
}

.time-pointer {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 3px;
  height: 40%;
  transform-origin: bottom center;
  background: var(--cinnabar-red);
  border-radius: 2px;
  transition: transform 0.5s ease;
}

.pointer-dot {
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--cinnabar-red);
  box-shadow: 0 2px 6px rgba(207, 63, 53, 0.4);
}

/* 实现说明样式 */
.implementation-note {
  margin-top: 20px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  border-left: 4px solid var(--cinnabar-red);
}

.implementation-note h4 {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  font-weight: 600;
  color: var(--cinnabar-red);
  margin: 0 0 12px 0;
}

.implementation-note p {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 6px 0;
}

.time-label {
  font-family: "Noto Serif SC", serif;
  font-size: 10px;
  color: var(--text-secondary);
  font-weight: 500;
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
  .unified-card {
    max-width: 1200px;
  }
  
  .unified-section.left-section,
  .unified-section.right-section {
    width: 340px;
  }
}

@media (max-width: 900px) {
  .unified-card {
    max-width: 900px;
    height: auto;
    min-height: 650px;
  }
  
  .unified-header {
    flex-direction: column;
    height: auto;
    gap: 0;
    background: transparent;
  }
  
  .unified-section {
    border: none;
    width: 100%;
  }
  
  .unified-section.left-section,
  .unified-section.right-section {
    width: 100%;
    border: none;
  }
  
  .unified-section.center-section {
    order: -1;
  }
  
  .section-header {
    padding: 16px 24px;
    height: auto;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }
  
  .section-content {
    padding: 20px 24px;
  }
  
  .poem-content {
    padding: 24px;
  }
  
  .viz-content {
    gap: 16px;
    padding: 0 12px;
  }
}

@media (max-width: 600px) {
  .main-stage {
    padding: 16px;
  }
  
  .unified-card {
    min-height: 550px;
  }
  
  .unified-header {
    display: none;
  }
  
  .unified-section {
    width: 100%;
    border: none;
  }
  
  .unified-section.center-section {
    order: -1;
  }
  
  .section-header {
    padding: 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }
  
  .section-content {
    padding: 16px;
  }
  
  .poem-content {
    padding: 16px;
  }
  
  .viz-card {
    padding: 16px;
    margin-bottom: 12px;
  }
  
  .viz-title {
    font-size: 14px;
    margin-bottom: 12px;
  }
  
  .tag-cloud {
    padding: 8px;
    gap: 8px;
  }
  
  .time-chart {
    padding: 16px;
  }
  
  .time-circle {
    width: 100px;
    height: 100px;
  }
}
/* 音律分析相关样式 */
.rhythm-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 10px;
}

.rhythm-stat-box {
  background: rgba(0, 0, 0, 0.03);
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.rhythm-stat-box.wide {
  grid-column: span 2;
  align-items: flex-start;
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.stat-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--cinnabar-red);
  font-family: "Arial";
}

.stat-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.appreciation-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  text-align: justify;
  margin-top: 10px;
}

.scrollable-note {
  max-height: 300px;
  overflow-y: auto;
}

/* 声律矩阵样式 */
.tonal-matrix {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: rgba(0,0,0,0.02);
  border-radius: 8px;
  align-items: center;
}

.matrix-row {
  display: flex;
  gap: 4px;
}

.matrix-cell {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  font-size: 10px;
  transition: all 0.2s;
}

.is-ping { background: rgba(166, 27, 27, 0.1); color: #A61B1B; }
.is-ze { background: rgba(0, 0, 0, 0.7); color: #fff; }
.is-unknown { background: rgba(0, 0, 0, 0.05); color: #999; }

.matrix-legend {
  display: flex;
  justify-content: center;
  gap: 15px;
  font-size: 11px;
  margin-top: 8px;
  color: var(--text-tertiary);
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}
.dot.ping { background: #A61B1B; opacity: 0.5; }
.dot.ze { background: #000; }

/* 韵脚流转样式 */
.rhyme-flow-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
}

.rhyme-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rhyme-marker {
  font-size: 10px;
  color: #999;
  width: 14px;
}

.rhyme-char-box {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 10px;
  background: rgba(0,0,0,0.02);
  border-radius: 4px;
  font-family: "Noto Serif SC", serif;
}

.is-rhyming {
  background: rgba(166, 27, 27, 0.05);
  border-left: 2px solid #A61B1B;
}

.r-char { font-weight: 700; color: #333; }
.r-pinyin { font-size: 11px; color: #A61B1B; font-family: "Arial"; font-style: italic; }

.viz-hint {
  font-size: 10px;
  color: #999;
  text-align: center;
  margin-top: 5px;
}

.rhyme-flow-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.rhyme-capsule {
  padding: 4px 8px;
  background: rgba(0,0,0,0.02);
  border-radius: 12px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.rhyme-capsule small {
  font-size: 10px;
  color: #A61B1B;
}

.gold-border {
  border: 1px solid rgba(166, 27, 27, 0.2);
  background: rgba(166, 27, 27, 0.03);
}

/* 调色盘样式 */
.color-palette {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 10px 0;
}

.color-drop {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  border: 2px solid #fff;
  transition: transform 0.2s;
  cursor: help;
}

.color-drop:hover {
  transform: scale(1.1) translateY(-4px);
}

.color-name {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 0 4px rgba(0,0,0,0.5);
  filter: invert(1) grayscale(1) contrast(100); /* 简单根据背景反转对比 */
  mix-blend-mode: difference;
}

</style>
