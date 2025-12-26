import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Home from './views/Home.vue'
import PoemDetail from './views/PoemDetail.vue'

const routes = [
    { path: '/', component: Home }, // 首页就是每日一诗
    { path: '/login', component: Login },
    { path: '/poem/:id', component: PoemDetail }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 简单的路由守卫：检查是否登录
router.beforeEach((to, from, next) => {
    const user = localStorage.getItem('user');
    if (to.path !== '/login' && !user) {
        next('/login');
    } else {
        next();
    }
})

export default router
