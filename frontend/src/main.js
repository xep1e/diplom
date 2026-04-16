import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'

import Register from './pages/Register.vue'
import Login from './pages/Login.vue'
import Chat from './pages/Chat.vue'
import Metrics from './pages/Metrics.vue'
import Tasks from './pages/Tasks.vue'
import AdminChats from './pages/AdminChats.vue'
import OperatorChats from './pages/OperatorChats.vue'

import { getMe } from './api/authApi'

const routes = [
  { path: '/', component: Login },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/chat', component: Chat },
  { path: '/metrics', component: Metrics },
  { path: '/tasks', component: Tasks },
  { path: '/my-chats', component: OperatorChats},

  {
    path: '/admin/chats',
    component: AdminChats,
    meta: { role: 'admin' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 🔐 GLOBAL GUARD
 */
router.beforeEach(async (to, from, next) => {
  try {
    const token = localStorage.getItem('token')

    // если нет токена → только login/register
    if (!token && to.path !== '/login' && to.path !== '/register') {
      return next('/login')
    }

    // проверка роли (если нужно)
    if (to.meta.role) {
      const user = await getMe()

      if (!user || user.role !== to.meta.role) {
        return next('/chat')
      }
    }

    next()
  } catch (e) {
    next('/login')
  }
})

createApp(App).use(router).mount('#app')