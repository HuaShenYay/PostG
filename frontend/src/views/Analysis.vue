<template>
  <div class="analysis-container">
    <div class="header-section">
      <div class="back-btn" @click="goHome">
        <el-icon><ArrowLeft /></el-icon>
        <span>回廊</span>
      </div>
      <div class="page-title">
        <span class="main-title">万象</span>
        <span class="sub-title">系统全览与数据洞察</span>
      </div>
    </div>

    <div class="dashboard-grid" v-if="loaded && stats.counts">
      <!-- 统计卡片 -->
      <div class="stat-card-row">
        <div class="stat-item">
          <div class="stat-num">{{ stats.counts.users }}</div>
          <div class="stat-label">雅士</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{{ stats.counts.poems }}</div>
          <div class="stat-label">诗章</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{{ stats.counts.reviews }}</div>
          <div class="stat-label">雅评</div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-area">
        <!-- 词云 -->
        <div class="chart-card large">
          <div class="chart-header">
            <span class="chart-title">热门关键词</span>
          </div>
          <div ref="wordCloudRef" class="chart-body"></div>
        </div>

        <!-- 诗韵雷达 (System Radar) -->
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">诗歌主题分布</span>
          </div>
          <div ref="radarRef" class="chart-body"></div>
        </div>

        <!-- 诗人-主题流向 (Sankey) -->
        <div class="chart-card wide">
          <div class="chart-header">
            <span class="chart-title">诗人与主题关系</span>
          </div>
          <div ref="sankeyRef" class="chart-body"></div>
        </div>
      </div>
    </div>
    
    <div v-else class="loading-wrapper">
      <el-icon class="is-loading"><Loading /></el-icon>
      <div>观象推演中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

const router = useRouter()
const loaded = ref(false)
const stats = ref({})

const wordCloudRef = ref(null)
const radarRef = ref(null)
const sankeyRef = ref(null)

const goHome = () => router.push('/')

const initCharts = async () => {
  // 获取当前用户
  const currentUser = localStorage.getItem('user') || ''
  console.log('Current user:', currentUser)
  
  // 1. 系统统计 + 复杂图表 (雷达 & 桑基)
  try {
    // 调用API时传递user_id参数
    const statsRes = await axios.get('http://127.0.0.1:5000/api/visual/stats', {
      params: { user_id: currentUser }
    })
    stats.value = statsRes.data
    console.log('Stats data:', stats.value)
    
    // 等待 DOM 更新
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // --- 渲染雷达图 (Radar) ---
    if (radarRef.value && stats.value.radar_data?.indicator && stats.value.radar_data?.value) {
      const radarChart = echarts.init(radarRef.value)
      radarChart.setOption({
        color: ['#A61B1B'],
        tooltip: {},
        radar: {
          indicator: stats.value.radar_data.indicator,
          splitArea: {
            areaStyle: {
              color: ['rgba(166,27,27,0.02)', 'rgba(166,27,27,0.05)']
            }
          },
          axisLine: { lineStyle: { color: 'rgba(166,27,27,0.3)' } },
          splitLine: { lineStyle: { color: 'rgba(166,27,27,0.1)' } }
        },
        series: [{
          name: currentUser ? '个人主题偏好' : '系统意象分布',
          type: 'radar',
          data: [{
            value: stats.value.radar_data.value,
            name: currentUser ? '个人偏好' : '全站综合',
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.1, 0.6, 1, [
                { color: 'rgba(166, 27, 27, 0.5)', offset: 0 },
                { color: 'rgba(166, 27, 27, 0.1)', offset: 1 }
              ])
            }
          }]
        }]
      })
    }

    // --- 渲染桑基图 (Sankey) ---
    if (sankeyRef.value && stats.value.sankey_data?.nodes && stats.value.sankey_data?.links) {
      const sankeyChart = echarts.init(sankeyRef.value)
      sankeyChart.setOption({
        tooltip: { trigger: 'item', triggerOn: 'mousemove' },
        series: [{
          type: 'sankey',
          data: stats.value.sankey_data.nodes,
          links: stats.value.sankey_data.links,
          layoutIterations: 64,
          emphasis: { focus: 'adjacency' },
          lineStyle: {
            color: 'gradient',
            curveness: 0.5,
            opacity: 0.4
          },
          itemStyle: {
            color: '#A61B1B',
            borderColor: '#fff',
            borderWidth: 1
          },
          label: {
            color: '#333',
            fontFamily: 'Noto Serif SC',
            fontSize: 12
          }
        }]
      })
    }

  } catch(e) { 
    console.error("Stats Error", e)
    loaded.value = true
  }

  // 2. 词云 (个性化)
  try {
    // 调用API时传递user_id参数
    const wcRes = await axios.get('http://127.0.0.1:5000/api/visual/wordcloud', {
      params: { user_id: localStorage.getItem('user') || '' }
    })
    console.log('Wordcloud data:', wcRes.data)
    
    if (wordCloudRef.value) {
      const wcChart = echarts.init(wordCloudRef.value)
      wcChart.setOption({
        tooltip: {},
        series: [{
          type: 'wordCloud',
          gridSize: 10,
          sizeRange: [12, 50],
          rotationRange: [-45, 45],
          shape: 'circle',
          textStyle: {
            fontFamily: 'Noto Serif SC',
            fontWeight: 'bold',
            color: function () {
              return 'rgb(' + [
                Math.round(Math.random() * 100),
                Math.round(Math.random() * 50),
                Math.round(Math.random() * 50)
              ].join(',') + ')';
            }
          },
          data: wcRes.data
        }]
      })
    }
  } catch(e) { 
    console.error("WordCloud Error", e)
  }

  loaded.value = true
}

onMounted(() => {
  // Slight delay to ensure DOM is ready and animation plays nicely
  setTimeout(() => {
    loaded.value = true // Pre-set to allow simple render flow
    // But data fetch is async
    initCharts()
  }, 500)
})
</script>

<style scoped>
.analysis-container {
  min-height: 100vh;
  background: var(--gradient-warm);
  padding: 40px;
  font-family: "Noto Serif SC", serif;
  background-attachment: fixed;
}

.header-section {
  display: flex;
  align-items: center;
  margin-bottom: 40px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: color 0.3s;
  margin-right: 40px;
}

.back-btn:hover {
  color: #A61B1B;
}

.page-title {
  display: flex;
  flex-direction: column;
}

.main-title {
  font-size: 32px;
  color: #1a1a1a;
  letter-spacing: 0.2em;
  background: linear-gradient(135deg, var(--modern-black) 0%, var(--accent-red) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sub-title {
  font-size: 12px;
  color: #999;
  letter-spacing: 0.1em;
  margin-top: 5px;
}

.stat-card-row {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.stat-item {
  flex: 1;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 25px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(0, 0, 0, 0.05);
  text-align: center;
  transition: var(--transition-smooth);
  box-shadow: var(--soft-shadow);
}

.stat-item:hover {
  transform: translateY(-5px);
  box-shadow: var(--modern-shadow);
  background: rgba(255, 255, 255, 0.95);
}

.stat-num {
  font-size: 36px;
  font-weight: 600;
  color: #A61B1B;
  font-family: "Arial", sans-serif;
  background: linear-gradient(135deg, var(--accent-red) 0%, var(--accent-red-dark) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  margin-top: 10px;
  color: #666;
  font-size: 14px;
  letter-spacing: 0.2em;
}

.dashboard-grid {
  max-width: 1200px;
  margin: 0 auto;
}

.charts-area {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 25px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 25px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(0, 0, 0, 0.05);
  height: 350px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--soft-shadow);
  transition: var(--transition-smooth);
}

.chart-card:hover {
  box-shadow: var(--modern-shadow);
  transform: translateY(-3px);
}

.large {
  grid-row: span 1;
}

.wide {
  grid-column: span 2;
  height: 300px;
}

.chart-header {
  margin-bottom: 20px;
  border-left: 3px solid #A61B1B;
  padding-left: 10px;
}

.chart-title {
  font-size: 16px;
  color: #333;
  letter-spacing: 0.1em;
  font-weight: bold;
}

.chart-body {
  flex: 1;
  width: 100%;
  height: 100%;
}

.loading-wrapper {
  height: 80vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #999;
  font-size: 14px;
  gap: 15px;
}
</style>