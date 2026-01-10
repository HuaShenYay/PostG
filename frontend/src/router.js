import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Home from './views/Home.vue'
import Analysis from './views/Analysis.vue'
import PreferenceGuide from './views/PreferenceGuide.vue'

const routes = [
    { path: '/', component: Home }, // 首页就是每日一诗
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/guide', component: PreferenceGuide },
    { path: '/analysis', component: Analysis }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 简单的路由守卫：检查是否登录
router.beforeEach((to, from, next) => {
    const user = localStorage.getItem('user');
    const publicPages = ['/login', '/register', '/guide'];
    const authRequired = !publicPages.includes(to.path);

    if (authRequired && !user) {
        next('/login');
    } else {
        next();
    }
})

export default router
