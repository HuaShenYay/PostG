<template>
  <div class="global-analysis-container">
    <!-- 顶部导航 (Consistent with Home) -->
    <nav class="top-nav glass-card">
      <div class="nav-brand">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      
      <div class="nav-actions">
        <!-- 搜索 -->
        <div class="nav-btn-card" @click="goToSearch" title="Search">
            <n-icon><NSearch /></n-icon>
            <span>搜索</span>
        </div>
        
        <!-- 个人万象 -->
        <div class="nav-btn-card" @click="goToPersonalAnalysis" title="Personal Analysis">
             <n-icon><NPersonOutline /></n-icon>
             <span>个人万象</span>
        </div>
        
        <!-- 全站万象 (Active) -->
        <div class="nav-btn-card active" title="Global Analysis">
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
    <main class="analysis-main anim-enter">
        <!-- 页面头部 -->
        <div class="page-zen-header">
            <h1 class="zen-title">全站万象</h1>
            <p class="zen-subtitle">探索诗云社区的数据宏观图景</p>
            
            <div class="header-mode-switcher">
                <n-button-group round size="small">
                    <n-button 
                        :type="viewMode === 'overview' ? 'primary' : 'default'"
                        @click="viewMode = 'overview'"
                    >总览</n-button>
                    <n-button 
                        :type="viewMode === 'trends' ? 'primary' : 'default'"
                        @click="viewMode = 'trends'"
                    >趋势</n-button>
                    <n-button 
                        :type="viewMode === 'compare' ? 'primary' : 'default'"
                        @click="viewMode = 'compare'"
                    >对比</n-button>
                </n-button-group>
            </div>
            <div class="zen-divider"></div>
        </div>

        <!-- 总览模式 -->
        <div v-if="viewMode === 'overview'" class="mode-content overview-mode">
            <!-- 全站统计 -->
            <div class="stats-row">
                <div class="stat-zen-item">
                    <span class="stat-label">诗歌馆藏</span>
                    <span class="stat-value">{{ globalStats.totalPoems.toLocaleString() }}</span>
                </div>
                <div class="stat-zen-item border-left">
                    <span class="stat-label">活跃墨客</span>
                    <span class="stat-value">{{ globalStats.totalUsers.toLocaleString() }}</span>
                </div>
                <div class="stat-zen-item border-left">
                    <span class="stat-label">累计雅评</span>
                    <span class="stat-value">{{ globalStats.totalReviews.toLocaleString() }}</span>
                </div>
                <div class="stat-zen-item border-left">
                    <span class="stat-label">互动频次</span>
                    <span class="stat-value">{{ globalStats.avgEngagement }}</span>
                </div>
            </div>

            <div class="analysis-grid">
                <!-- 热门排行 -->
                <div class="glass-card section-card">
                    <div class="section-zen-header">
                        <h3><n-icon><NBookOutline /></n-icon> 热门诗篇</h3>
                        <n-select v-model:value="popularTimeRange" :options="timeRangeOptions" size="small" style="width: 100px" />
                    </div>
                    <div class="popular-list">
                        <div v-for="(poem, index) in popularPoems" :key="poem.id" class="popular-item" :class="{ 'top-item': index < 3 }">
                            <div class="rank">{{ index + 1 }}</div>
                            <div class="p-info">
                                <span class="p-title">{{ poem.title }}</span>
                                <span class="p-author">{{ poem.author }} · {{ poem.dynasty }}</span>
                            </div>
                            <div class="p-stats">
                                <span><n-icon><NHeartOutline /></n-icon> {{ (poem.likes/1000).toFixed(1) }}k</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 分布图表组 -->
                <div class="charts-column">
                    <div class="glass-card viz-card">
                        <div class="section-zen-header">
                            <h3><n-icon><NPieChart /></n-icon> 主题宏图</h3>
                        </div>
                        <div ref="themeChartRef" style="height: 240px;"></div>
                    </div>
                    <div class="glass-card viz-card">
                        <div class="section-zen-header">
                            <h3><n-icon><NTrendingUpOutline /></n-icon> 朝代热度</h3>
                        </div>
                        <div ref="dynastyChartRef" style="height: 240px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 趋势模式 -->
        <div v-if="viewMode === 'trends'" class="mode-content">
            <div class="glass-card viz-card-large">
                <div class="section-zen-header">
                    <h3><n-icon><NTrendingUpOutline /></n-icon> 社区活跃脉动</h3>
                </div>
                <div ref="trendChartRef" style="height: 400px;"></div>
            </div>
        </div>

        <!-- 对比模式 -->
        <div v-if="viewMode === 'compare'" class="mode-content">
            <div class="glass-card viz-card-large">
                <div class="section-zen-header">
                    <h3><n-icon><NCompare /></n-icon> 维度深度博弈</h3>
                </div>
                <div ref="compareChartRef" style="height: 400px;"></div>
            </div>
        </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'
import { 
  NIcon, 
  NButton,
  NButtonGroup,
  NSelect,
  NTag
} from 'naive-ui'
import { 
  HomeOutline as NHome,
  GlobeOutline as NGlobeOutline,
  PersonOutline as NPersonOutline,
  BookOutline as NBookOutline,
  PeopleOutline as NPeopleOutline,
  ChatbubbleEllipsesOutline as NChatOutline,
  TrendingUpOutline as NTrendingUpOutline,
  HeartOutline as NHeartOutline,
  RefreshOutline as NRefreshOutline,
  Search as NSearch,
  TimerOutline as NClock,
  BriefcaseOutline as NCompare
} from '@vicons/ionicons5'

const router = useRouter()
const currentUser = localStorage.getItem('user') || '访客'

// 状态
const viewMode = ref('overview')
const popularTimeRange = ref('week')

// 图表引用
const themeChartRef = ref(null)
const dynastyChartRef = ref(null)
const trendChartRef = ref(null)
const compareChartRef = ref(null)

let charts = []

// 模拟数据
const globalStats = ref({
  totalPoems: 48562,
  totalUsers: 12847,
  totalReviews: 95731,
  avgEngagement: '78.5%'
})

const popularPoems = ref([
  { id: 1, title: '春江花月夜', dynasty: '唐', author: '张若虚', likes: 8742 },
  { id: 2, title: '将进酒', dynasty: '唐', author: '李白', likes: 7521 },
  { id: 3, title: '水调歌头', dynasty: '宋', author: '苏轼', likes: 6894 },
  { id: 4, title: '登高', dynasty: '唐', author: '杜甫', likes: 5623 },
  { id: 5, title: '琵琶行', dynasty: '唐', author: '白居易', likes: 4987 }
])

const timeRangeOptions = [
  { label: '今日', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' }
]

// 初始化图表
const initCharts = () => {
  charts.forEach(c => c.dispose())
  charts = []

  if (viewMode.value === 'overview') {
    if (themeChartRef.value) {
      const c = echarts.init(themeChartRef.value)
      c.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
          data: [
            { value: 1048, name: '山水', itemStyle: { color: '#A61B1B' } },
            { value: 735, name: '思乡', itemStyle: { color: '#bfa46f' } },
            { value: 580, name: '咏物', itemStyle: { color: '#1a1a1a' } },
            { value: 484, name: '边塞', itemStyle: { color: '#8a1616' } }
          ],
          label: { show: false }
        }]
      })
      charts.push(c)
    }
    if (dynastyChartRef.value) {
      const c = echarts.init(dynastyChartRef.value)
      c.setOption({
        xAxis: { type: 'category', data: ['唐', '宋', '元', '明', '清'], axisLine: { show: false }, axisTick: { show: false } },
        yAxis: { show: false },
        series: [{
          data: [2840, 1980, 860, 1240, 980],
          type: 'bar',
          itemStyle: { 
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#A61B1B' },
                { offset: 1, color: 'rgba(166, 27, 27, 0.3)' }
            ]),
            borderRadius: [4, 4, 0, 0]
          }
        }],
        grid: { top: 20, bottom: 30, left: 10, right: 10 }
      })
      charts.push(c)
    }
  } else if (viewMode.value === 'trends') {
    if (trendChartRef.value) {
        const c = echarts.init(trendChartRef.value)
        c.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] },
            yAxis: { type: 'value' },
            series: [{
                data: [820, 932, 901, 934, 1290, 1330, 1320],
                type: 'line',
                smooth: true,
                lineStyle: { color: '#A61B1B', width: 4 }
            }]
        })
        charts.push(c)
    }
  } else if (viewMode.value === 'compare') {
      if (compareChartRef.value) {
          const c = echarts.init(compareChartRef.value)
          c.setOption({
              radar: {
                  indicator: [
                      { name: '唐', max: 100 },
                      { name: '宋', max: 100 },
                      { name: '元', max: 100 },
                      { name: '明', max: 100 },
                      { name: '清', max: 100 }
                  ]
              },
              series: [{
                  type: 'radar',
                  data: [
                      { value: [90, 80, 40, 60, 50], name: '互动指数', itemStyle: { color: '#A61B1B' } }
                  ]
              }]
          })
          charts.push(c)
      }
  }
}

watch(viewMode, () => {
    nextTick(() => initCharts())
})

const handleResize = () => charts.forEach(c => c.resize())

onMounted(() => {
    initCharts()
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
})

const goHome = () => router.push('/')
const goToSearch = () => router.push('/search')
const goToPersonalAnalysis = () => router.push('/personal-analysis')
const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.global-analysis-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--gradient-bg);
  color: var(--ink-black);
}


/* Layout */
.analysis-main {
    flex: 1;
    max-width: var(--content-max-width);
    margin: 40px auto;
    padding: 0 var(--content-padding);
    width: 100%;
}

.page-zen-header {
    text-align: center;
    margin-bottom: 60px;
}

.zen-title {
    font-family: "Noto Serif SC", serif;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 0.2em;
    margin-bottom: 12px;
    color: var(--ink-black);
}

.zen-subtitle {
    font-size: 14px;
    color: var(--text-tertiary);
    letter-spacing: 0.1em;
    margin-bottom: 32px;
}

.zen-divider {
    width: 60px;
    height: 2px;
    background: var(--cinnabar-red);
    margin: 32px auto;
    opacity: 0.5;
}

/* Stats */
.stats-row {
    display: flex;
    justify-content: space-around;
    padding: 24px;
    background: var(--paper-white);
    border-radius: var(--radius-main);
    margin-bottom: 40px;
    border: 1px solid rgba(0,0,0,0.03);
}

.stat-zen-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
}

.stat-zen-item.border-left {
    border-left: 1px solid rgba(0,0,0,0.05);
}

.stat-label {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-bottom: 4px;
}

.stat-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--ink-black);
    font-family: "Playfair Display", serif;
}

/* Grid */
.analysis-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
}

.section-zen-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}

.section-zen-header h3 {
    font-family: "Noto Serif SC", serif;
    font-size: 18px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
}

.section-zen-header h3 .n-icon {
    color: var(--cinnabar-red);
}

/* Popular List */
.popular-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.popular-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: rgba(0,0,0,0.02);
    border-radius: var(--radius-sub);
    transition: var(--transition-fast);
}

.popular-item:hover {
    background: rgba(0,0,0,0.04);
}

.popular-item.top-item .rank {
    color: var(--cinnabar-red);
    font-weight: 800;
}

.rank {
    width: 32px;
    font-family: "Playfair Display", serif;
    font-size: 20px;
    color: var(--text-tertiary);
}

.p-info {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.p-title {
    font-size: 15px;
    font-weight: 600;
}

.p-author {
    font-size: 11px;
    color: var(--text-tertiary);
}

.p-stats {
    font-size: 12px;
    color: var(--text-secondary);
}

/* Responsive */
@media (max-width: 1024px) {
    .analysis-grid {
        grid-template-columns: 1fr;
    }
}
</style>
