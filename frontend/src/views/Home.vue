<template>
  <div class="home-container fade-in">
    <!-- 侧边抽屉：兴趣画像与推荐 -->
    <div :class="['sidebar', { active: showSidebar }]">
      <div class="sidebar-handle" @click="showSidebar = !showSidebar">
        <span class="vertical-text">{{ showSidebar ? '收 起' : '探 索' }}</span>
      </div>
      <div class="sidebar-content">
        <h2 class="section-title">兴趣画像</h2>
        <div v-if="userProfile" class="profile-box">
          <p>主攻流派：<span class="highlight">{{ userProfile.top_interest.join('、') }}</span></p>
          <div class="topic-bars">
            <div v-for="p in userProfile.preference" :key="p.topic_id" class="bar-row">
              <span class="bar-label">主题{{ p.topic_id }}</span>
              <div class="bar-bg"><div class="bar-fill" :style="{ width: (p.score*100)+'%' }"></div></div>
            </div>
          </div>
          <button @click="getRecommendations" class="ink-btn" style="margin-top:20px; width:100%">获取推荐</button>
        </div>
        
        <h2 class="section-title" style="margin-top:40px">为您荐诗</h2>
        <div class="recommend-list">
          <div v-for="rec in recommendations" :key="rec.title" class="rec-item" @click="jumpToPoem(rec.title)">
            <div class="rec-title">{{ rec.title }}</div>
            <div class="rec-reason">{{ rec.reason }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 顶部 -->
    <nav class="top-nav">
      <div class="logo">诗云 <span class="sub-logo">LDA-CF 精选</span></div>
      <div class="nav-right">
        <span class="user-name">{{ currentUser }}</span>
        <button @click="logout" class="logout-link">[ 离席 ]</button>
      </div>
    </nav>

    <!-- 主展示区 -->
    <main class="poem-main">
      <div v-if="dailyPoem" class="poem-card">
        <div class="poem-paper">
          <div class="poem-content-wrap">
            <h1 class="poem-title vertical-text">{{ dailyPoem.title }}</h1>
            <div class="poem-author vertical-text">[{{ dailyPoem.author }}]</div>
            <div class="poem-text vertical-text">{{ dailyPoem.content }}</div>
          </div>
          <div class="paper-texture"></div>
        </div>
        
        <div class="poem-actions">
           <button class="action-btn" @click="toggleComments">
             <i class="icon">评</i> 
             <span>{{ showComments ? '收起评论' : '雅评 (' + reviews.length + ')' }}</span>
           </button>
           <button class="action-btn" @click="getAnotherPoem">
             <i class="icon">换</i> <span>易章</span>
           </button>
        </div>
      </div>
      <div v-else class="loading-state">
        <div class="brush-stroke"></div>
        <p>研墨中...</p>
      </div>
    </main>

    <!-- 评论浮层 -->
    <transition name="slide-up">
      <div v-if="showComments" class="comments-drawer">
        <div class="drawer-header">
           <h2>诗友雅评</h2>
           <button @click="showComments = false" class="close-btn">×</button>
        </div>
        <div class="comments-list">
           <div v-for="r in reviews" :key="r.id" class="comment-card">
             <div class="comment-meta">
               <span class="author">{{ r.user_id }}</span>
               <span class="rating">评分: {{ r.rating }}</span>
             </div>
             <p class="text">{{ r.comment }}</p>
           </div>
           <div v-if="reviews.length === 0" class="empty-hint">寂寂无声，虚位以待。</div>
        </div>
        <div class="comment-form">
          <textarea v-model="newComment" placeholder="写下你的感悟..." class="ink-textarea"></textarea>
          <div class="form-footer">
            <select v-model="newRating" class="ink-select">
              <option :value="5">上品 (5分)</option>
              <option :value="4">中上 (4分)</option>
              <option :value="3">中品 (3分)</option>
            </select>
            <button @click="submitComment" class="ink-btn primary">发表</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
    } catch(e) { console.error("无法加载画像", e) }
}

const getRecommendations = async () => {
    try {
        const res = await axios.get(`http://127.0.0.1:5000/api/recommend_personal/${currentUser}`)
        recommendations.value = res.data
        alert("已根据您的画像更新荐诗")
    } catch(e) { console.error(e) }
}

const getAnotherPoem = async () => {
  dailyPoem.value = null
  try {
    const res = await axios.get('http://127.0.0.1:5000/api/poems')
    const list = res.data
    dailyPoem.value = list[Math.floor(Math.random() * list.length)]
    fetchReviews(dailyPoem.value.id)
  } catch (e) {
    console.error(e)
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
    if(!newComment.value) return;
    try {
        const res = await axios.post('http://127.0.0.1:5000/api/poem/review', {
            username: currentUser,
            poem_id: dailyPoem.value.id,
            rating: newRating.value,
            comment: newComment.value
        })
        if(res.data.status === 'success') {
            // 重新获取评论列表以同步显示
            fetchReviews(dailyPoem.value.id)
            newComment.value = ''
            alert("已收录您的雅评")
        }
    } catch(e) {
        alert("雅评收录失败")
        console.error(e)
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
  position: relative;
  display: flex;
  flex-direction: column;
}

/* 侧边栏 */
.sidebar {
  position: fixed;
  left: -280px;
  top: 0;
  width: 320px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  z-index: 100;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 10px 0 30px rgba(0,0,0,0.05);
  display: flex;
}
.sidebar.active { left: 0; }
.sidebar-handle {
  width: 40px;
  background: var(--ink-black);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  order: 2;
}
.sidebar-content {
  flex: 1;
  padding: 40px 20px;
  overflow-y: auto;
}

.section-title {
    font-size: 1.2rem;
    border-left: 4px solid var(--seal-red);
    padding-left: 10px;
    margin-bottom: 20px;
}

.top-nav {
  padding: 30px 60px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.logo { font-size: 1.8rem; font-weight: bold; }
.sub-logo { font-size: 0.8rem; font-weight: normal; color: var(--seal-red); margin-left: 10px; border: 1px solid; padding: 2px 5px; }
.user-name { font-weight: 500; margin-right: 15px; }
.logout-link { background: none; border: none; cursor: pointer; color: #999; }

.poem-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-bottom: 100px;
}

.poem-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.poem-paper {
  background: white;
  padding: 60px 80px;
  box-shadow: 20px 20px 60px rgba(0,0,0,0.05);
  position: relative;
  border: 1px solid rgba(0,0,0,0.02);
}

.poem-content-wrap {
  display: flex;
  flex-direction: row-reverse;
  height: 450px;
  gap: 50px;
}

.poem-title { font-size: 2.2rem; margin-left: 20px; }
.poem-author { font-size: 1.1rem; color: var(--seal-red); margin-top: 30px; }
.poem-text { font-size: 1.4rem; line-height: 2.5; white-space: pre-wrap; font-weight: 300; }

.poem-actions {
  margin-top: 50px;
  display: flex;
  gap: 30px;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: inherit;
  transition: transform 0.3s;
}
.action-btn:hover { transform: translateY(-3px); }
.action-btn .icon {
  width: 36px;
  height: 36px;
  border: 1px solid var(--ink-black);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 评论弹窗 */
.comments-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 60vh;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -20px 50px rgba(0,0,0,0.1);
  z-index: 200;
  display: flex;
  flex-direction: column;
  padding: 40px 10%;
}

.drawer-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
}
.close-btn { font-size: 2rem; background: none; border: none; cursor: pointer; }

.comments-list {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding-bottom: 20px;
}

.comment-card {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 4px;
    border-left: 3px solid var(--ink-black);
}

.comment-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #999;
    margin-bottom: 10px;
}

.comment-form {
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 20px;
}

.ink-textarea {
    width: 100%;
    padding: 15px;
    border: 1px solid #ddd;
    font-family: inherit;
    resize: none;
    outline: none;
    background: #fdfdfd;
}

.form-footer {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    margin-top: 15px;
}

.ink-select {
    padding: 5px 15px;
    border: 1px solid #ddd;
    font-family: inherit;
}

/* 动画 */
.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.4s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }

.loading-state { text-align: center; }
.brush-stroke { width: 100px; height: 5px; background: var(--ink-black); margin: 0 auto 20px; border-radius: 50%; opacity: 0.2; }
</style>
